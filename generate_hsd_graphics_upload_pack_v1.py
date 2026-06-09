from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import quote, unquote, urlparse

try:
    import requests
except Exception:
    requests = None

try:
    import cairosvg
except Exception:
    cairosvg = None


VERSION = "hsd-graphics-upload-pack-v1.4"

INPUT_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts_v2.md")
INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")
INPUT_RENDER_MANIFEST = os.environ.get("HSD_RENDER_MANIFEST", "studio_render_manifest_v2.json")

OUT_DIR = Path("graphics_chat_upload_pack")
OUT_ZIP_DIR = Path("graphics_chat_upload_pack_zips")
OUT_MANIFEST_CSV = "graphics_chat_upload_manifest.csv"
OUT_MANIFEST_JSON = "graphics_chat_upload_manifest.json"
OUT_INSTRUCTIONS = "graphics_chat_upload_instructions.md"
OUT_DIRECT_HANDOFF = "graphics_chat_direct_handoff.md"

FIELDS = [
    "bundle_id", "post_slug", "bundle_name", "entity_name", "entity_type", "approved_asset_id",
    "approved_variant", "source_url", "source_domain", "local_asset_path", "local_png_path",
    "asset_filename", "png_filename", "download_status", "conversion_status", "upload_instruction"
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", clean(value).lower()).strip("-") or "asset"


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def prompt_for_bundle(prompts_md: str, bundle_name: str) -> str:
    if not prompts_md:
        return ""
    escaped = re.escape(bundle_name)
    pat = rf"##\s+{escaped}\s*\n(.*?)(?=\n##\s+|\Z)"
    m = re.search(pat, prompts_md, flags=re.S)
    if m:
        return f"# {bundle_name}\n\n{m.group(1).strip()}\n"
    # fallback by first title-ish phrase
    return prompts_md


def url_ext(url: str, content_type: str = "") -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    suffix = Path(urlparse(url).path).suffix
    if suffix:
        return suffix
    return ".asset"


def wikimedia_file_title_from_url(url: str) -> str:
    name = unquote(Path(urlparse(url).path).name)
    if not name:
        return ""
    return name


def mediawiki_image_url(file_name: str) -> str:
    if not requests or not file_name:
        return ""
    title = "File:" + file_name
    for api in ["https://en.wikipedia.org/w/api.php", "https://commons.wikimedia.org/w/api.php"]:
        try:
            r = requests.get(
                api,
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "imageinfo",
                    "iiprop": "url|mime",
                    "format": "json",
                },
                headers={"User-Agent": "HSDGraphicsUploadPack/1.0"},
                timeout=20,
            )
            if r.status_code >= 400:
                continue
            pages = r.json().get("query", {}).get("pages", {})
            for page in pages.values():
                infos = page.get("imageinfo", [])
                if infos and infos[0].get("url"):
                    return infos[0]["url"]
        except Exception:
            continue
    return ""


def download_url(url: str, dest_dir: Path, base_name: str) -> Tuple[str, str]:
    """Return local path and status."""
    if not requests or not url:
        return "", "no_requests_or_url"

    urls_to_try = [url]
    if "wikimedia.org" in urlparse(url).netloc:
        file_name = wikimedia_file_title_from_url(url)
        api_url = mediawiki_image_url(file_name)
        if api_url and api_url not in urls_to_try:
            urls_to_try.append(api_url)
        if file_name:
            urls_to_try.append(f"https://en.wikipedia.org/wiki/Special:Redirect/file/{quote(file_name)}")
            urls_to_try.append(f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{quote(file_name)}")

    for candidate in urls_to_try:
        try:
            r = requests.get(
                candidate,
                headers={
                    "User-Agent": "HSDGraphicsUploadPack/1.0",
                    "Accept": "image/svg+xml,image/png,image/jpeg,image/webp,*/*",
                },
                timeout=30,
                allow_redirects=True,
            )
            if r.status_code >= 400 or not r.content:
                continue
            ctype = r.headers.get("content-type", "")
            ext = url_ext(candidate, ctype)
            if ext.lower() in {".html", ".htm"} and b"<svg" not in r.content[:500].lower():
                continue
            if b"<svg" in r.content[:500].lower():
                ext = ".svg"
            dest = dest_dir / f"{base_name}{ext}"
            dest.write_bytes(r.content)
            return dest.as_posix(), f"downloaded:{r.status_code}"
        except Exception as exc:
            last_error = str(exc)
            continue
    return "", "download_failed"


def copy_or_download(asset: Dict[str, str], dest_dir: Path) -> Tuple[str, str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    entity_slug = slugify(asset.get("entity_name"))
    variant_slug = slugify(asset.get("approved_variant") or asset.get("entity_type") or "asset")
    approved_id = clean(asset.get("approved_asset_id"))
    base_name = f"{entity_slug}_{variant_slug}_{approved_id[-6:] if approved_id else 'asset'}"

    for field in ["master_path", "web_path"]:
        src = clean(asset.get(field))
        if src and Path(src).exists():
            ext = Path(src).suffix or ".asset"
            dest = dest_dir / f"{base_name}{ext}"
            shutil.copy2(src, dest)
            return dest.as_posix(), "copied_local"

    return download_url(clean(asset.get("source_url")), dest_dir, base_name)


def convert_to_png(local_path: str, dest_dir: Path) -> Tuple[str, str]:
    if not local_path:
        return "", "no_local_asset"
    p = Path(local_path)
    if not p.exists():
        return "", "local_asset_missing"
    dest_dir.mkdir(parents=True, exist_ok=True)

    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        # Still copy a PNG-named preferred version only if already PNG.
        if p.suffix.lower() == ".png":
            return p.as_posix(), "already_png"
        return p.as_posix(), "raster_no_conversion"

    if p.suffix.lower() == ".svg":
        if cairosvg is None:
            return "", "cairosvg_not_installed"
        out = dest_dir / f"{p.stem}.png"
        try:
            cairosvg.svg2png(url=p.as_posix(), write_to=out.as_posix(), output_width=1200, output_height=1200)
            return out.as_posix(), "converted_svg_to_png"
        except Exception as exc:
            return "", f"conversion_failed:{exc}"

    return "", "unsupported_conversion"


def bundle_asset_map(render_manifest: Dict[str, Any], approved_assets: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    by_id = {a.get("approved_asset_id"): a for a in approved_assets if a.get("approved_asset_id")}
    out: Dict[str, List[Dict[str, str]]] = {}
    for bundle in render_manifest.get("bundles", []):
        assets = []
        for aid in bundle.get("asset_ids", []):
            if aid in by_id:
                assets.append(by_id[aid])
        out[bundle.get("post_slug", "")] = assets
    return out


def zip_folder(folder: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(folder))


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    if OUT_ZIP_DIR.exists():
        shutil.rmtree(OUT_ZIP_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_ZIP_DIR.mkdir(parents=True, exist_ok=True)

    prompts_md = read_text(INPUT_PROMPTS)
    approved_assets = read_csv(INPUT_APPROVED_ASSETS)
    render_manifest = read_json(INPUT_RENDER_MANIFEST)
    asset_map = bundle_asset_map(render_manifest, approved_assets)

    manifest_rows: List[Dict[str, Any]] = []

    for bundle in render_manifest.get("bundles", []):
        post_slug = clean(bundle.get("post_slug")) or slugify(bundle.get("bundle_name"))
        bundle_name = clean(bundle.get("bundle_name")) or post_slug
        bundle_id = clean(bundle.get("bundle_id"))

        folder = OUT_DIR / post_slug
        asset_folder = folder / "assets_original"
        png_folder = folder / "assets_png_preferred"
        folder.mkdir(parents=True, exist_ok=True)
        asset_folder.mkdir(parents=True, exist_ok=True)
        png_folder.mkdir(parents=True, exist_ok=True)

        prompt_text = prompt_for_bundle(prompts_md, bundle_name)
        (folder / "00_PROMPT_TO_PASTE.md").write_text(prompt_text, encoding="utf-8")
        for extra_name in ["graphics_slide_blueprints.md", "graphics_production_specs.json", "player_image_requirements.csv", "player_image_sourcing_report.md"]:
            extra = Path(extra_name)
            if extra.exists():
                shutil.copy2(extra, folder / extra_name)

        instructions = [
            f"# Upload instructions: {bundle_name}",
            "",
            "Upload `00_PROMPT_TO_PASTE.md` and the files inside `assets_png_preferred/` to the graphics chat.",
            "",
            "If a PNG preferred asset is missing, upload the matching file from `assets_original/`.",
            "",
            "Do not let the graphics chat fetch logo or player image URLs. Logos and player/person images must be attached as files.",
            "",
        ]

        for asset in asset_map.get(post_slug, []):
            local_path, status = copy_or_download(asset, asset_folder)
            png_path, conversion_status = convert_to_png(local_path, png_folder)
            upload_path = png_path or local_path
            upload_instruction = f"Upload {Path(upload_path).name}" if upload_path else "No file created, use text-forward for this asset"

            manifest_rows.append({
                "bundle_id": bundle_id,
                "post_slug": post_slug,
                "bundle_name": bundle_name,
                "entity_name": asset.get("entity_name", ""),
                "entity_type": asset.get("entity_type", ""),
                "approved_asset_id": asset.get("approved_asset_id", ""),
                "approved_variant": asset.get("approved_variant", ""),
                "source_url": asset.get("source_url", ""),
                "source_domain": urlparse(asset.get("source_url", "")).netloc,
                "local_asset_path": local_path,
                "local_png_path": png_path,
                "asset_filename": Path(local_path).name if local_path else "",
                "png_filename": Path(png_path).name if png_path else "",
                "download_status": status,
                "conversion_status": conversion_status,
                "upload_instruction": upload_instruction,
            })

            instructions.extend([
                f"## {asset.get('entity_name')}",
                "",
                f"- Preferred upload: `{Path(png_path).name if png_path else 'missing'}`",
                f"- Original asset: `{Path(local_path).name if local_path else 'missing'}`",
                f"- Source URL: {asset.get('source_url')}",
                f"- Status: {status}; {conversion_status}",
                "",
            ])

        (folder / "01_UPLOAD_INSTRUCTIONS.md").write_text("\n".join(instructions), encoding="utf-8")
        zip_folder(folder, OUT_ZIP_DIR / f"{post_slug}_graphics_chat_upload_pack.zip")

    write_csv(OUT_MANIFEST_CSV, manifest_rows, FIELDS)
    Path(OUT_MANIFEST_JSON).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "input_prompts": INPUT_PROMPTS,
        "input_approved_assets": INPUT_APPROVED_ASSETS,
        "input_render_manifest": INPUT_RENDER_MANIFEST,
        "counts": {
            "bundles": len(render_manifest.get("bundles", [])),
            "asset_rows": len(manifest_rows),
            "files_created": sum(1 for r in manifest_rows if r.get("local_asset_path") or r.get("local_png_path")),
            "png_preferred_created": sum(1 for r in manifest_rows if r.get("local_png_path")),
        },
        "outputs": [
            OUT_DIR.as_posix(),
            OUT_ZIP_DIR.as_posix(),
            OUT_MANIFEST_CSV,
            OUT_MANIFEST_JSON,
            OUT_INSTRUCTIONS,
        ],
    }, indent=2), encoding="utf-8")

    instructions = [
        "# HSD Graphics Chat Upload Instructions",
        "",
        "The graphics chat cannot reliably fetch external logo URLs. Use this upload pack instead.",
        "",
        "For the post you are making:",
        "",
        "1. Open `graphics_chat_upload_pack/<post_slug>/`.",
        "2. Upload `00_PROMPT_TO_PASTE.md`.",
        "3. Upload every file in `assets_png_preferred/`, including player/person images if present.",
        "4. If a PNG is missing, upload the matching file in `assets_original/`.",
        "5. Tell the graphics chat: use only the attached assets, do not fetch or invent logos or player images.",
        "",
        "Quick ZIPs are in `graphics_chat_upload_pack_zips/`.",
        "",
        "For Main WNBA Result, upload:",
        "",
        "- `graphics_chat_upload_pack_zips/main-wnba-result_graphics_chat_upload_pack.zip`",
        "",
    ]
    Path(OUT_INSTRUCTIONS).write_text("\n".join(instructions), encoding="utf-8")

    # Build a short direct handoff file for the most likely first graphic.
    direct = [
        "# HSD Graphics Chat Direct Handoff",
        "",
        "Use the ZIP below for the graphics chat. Upload the ZIP contents if the chat cannot unzip.",
        "",
    ]
    main_zip = OUT_ZIP_DIR / "main-wnba-result_graphics_chat_upload_pack.zip"
    if main_zip.exists():
        direct += [
            "## Main WNBA Result",
            "",
            f"Recommended ZIP: `{main_zip.as_posix()}`",
            "",
            "Instructions to paste into the graphics chat:",
            "",
            "```text",
            "Use the uploaded prompt, uploaded logo files, and uploaded player/person image files only. Do not fetch logo URLs. Do not fetch player image URLs. Do not substitute logos or players. Do not invent player bodies, jerseys, or numbers. If required player/person images are missing, stop and ask for the files. Output separate slide files.",
            "```",
            "",
        ]
    else:
        direct += [
            "Main WNBA Result ZIP was not created. Check graphics_chat_upload_manifest.csv for missing asset download rows.",
            "",
        ]
    Path(OUT_DIRECT_HANDOFF).write_text("\n".join(direct), encoding="utf-8")

    print("Created HSD graphics upload pack")
    print(json.dumps(json.loads(Path(OUT_MANIFEST_JSON).read_text())["counts"], indent=2))


if __name__ == "__main__":
    main()

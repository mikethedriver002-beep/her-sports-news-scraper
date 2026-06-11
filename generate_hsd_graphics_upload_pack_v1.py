from __future__ import annotations

import csv
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


VERSION = "hsd-graphics-upload-pack-v3.2.4-bebe-ops-v2.3"

INPUT_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts_v2.md")
INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")
INPUT_RENDER_MANIFEST = os.environ.get("HSD_RENDER_MANIFEST", "studio_render_manifest_v2.json")
INPUT_CLEAN_PROMPTS_DIR = Path(os.environ.get("HSD_CLEAN_PROMPTS_DIR", "graphics_clean_prompts"))

OUT_DIR = Path("graphics_chat_upload_pack")
OUT_ZIP_DIR = Path("graphics_chat_upload_pack_zips")
OUT_MANIFEST_CSV = "graphics_chat_upload_manifest.csv"
OUT_MANIFEST_JSON = "graphics_chat_upload_manifest.json"
OUT_STATUS_CSV = "graphics_upload_pack_status.csv"
OUT_STATUS_JSON = "graphics_upload_pack_status.json"
OUT_INSTRUCTIONS = "graphics_chat_upload_instructions.md"
OUT_DIRECT_HANDOFF = "graphics_chat_direct_handoff.md"

FIELDS = [
    "bundle_id", "post_slug", "bundle_name", "entity_name", "entity_type", "approved_asset_id",
    "approved_variant", "source_url", "source_domain", "local_asset_path", "local_png_path",
    "asset_filename", "png_filename", "download_status", "conversion_status", "asset_ready",
    "required_for_bundle", "upload_instruction"
]

STATUS_FIELDS = [
    "bundle_id", "post_slug", "bundle_name", "upload_pack_status", "assets_expected",
    "assets_ready", "assets_missing", "missing_asset_names", "zip_path", "notes"
]

# Official/local fallback routes used only when the approved source URL cannot be turned
# into a local file. These do not change the approved asset source, they only make the
# upload pack reliable for graphics-chat handoff.
TEAM_LOGO_DOWNLOAD_FALLBACKS = {
    "Los Angeles Sparks": [
        "https://cdn.wnba.com/logos/wnba/1611661320/primary/L/logo.svg",
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Los_Angeles_Sparks_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Los_Angeles_Sparks_logo.svg",
    ],
    "Minnesota Lynx": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Minnesota_Lynx_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Minnesota_Lynx_logo.svg",
    ],
    "Portland Fire": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Portland_Fire_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Portland_Fire_logo.svg",
    ],
    "Atlanta Dream": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Atlanta_Dream_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Atlanta_Dream_logo.svg",
    ],
    "Chicago Sky": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Chicago_Sky_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Chicago_Sky_logo.svg",
    ],
    "Connecticut Sun": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Connecticut_Sun_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Connecticut_Sun_logo.svg",
    ],
    "Toronto Tempo": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Toronto_Tempo_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Toronto_Tempo_logo.svg",
        "https://upload.wikimedia.org/wikipedia/en/1/1b/Toronto_Tempo_logo.svg",
    ],
    "Indiana Fever": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Indiana_Fever_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Indiana_Fever_logo.svg",
    ],
    "New York Liberty": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/New_York_Liberty_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/New_York_Liberty_logo.svg",
    ],
    "Washington Mystics": [
        "https://en.wikipedia.org/wiki/Special:Redirect/file/Washington_Mystics_logo.svg",
        "https://en.wikipedia.org/wiki/Special:FilePath/Washington_Mystics_logo.svg",
    ],
}


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


def read_status_map(path: str, key_field: str) -> Dict[str, Dict[str, str]]:
    return {r.get(key_field, ""): r for r in read_csv(path) if r.get(key_field)}


def freshness_status_for(post_slug: str) -> Dict[str, str]:
    return read_status_map("studio_freshness_gate.csv", "bundle_slug").get(post_slug, {})


def player_fit_rows_for(post_slug: str) -> List[Dict[str, str]]:
    return [r for r in read_csv("player_image_fit_gate.csv") if r.get("bundle_slug") == post_slug]


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
    return prompts_md


DEFAULT_BANNED_PROMPT_TERMS = ["Verified Final", "VERIFIED FINAL", "Winner", "Loser", "BUNDLE LOCKED FACTS", "source-safe context", "graphics-safe context", "Do not alter", "Accuracy lock"]


def sanitize_prompt_text(prompt_text: str) -> str:
    out: List[str] = []
    for raw_line in prompt_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        lower = line.lower()
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        if any(term.lower() in lower for term in ["bundle locked facts", "source-safe context", "graphics-safe context", "do not alter", "accuracy lock"]):
            continue
        if line.startswith("```"):
            continue
        line = re.sub(r"(?i)verified final", "Final", line)
        line = re.sub(r"(?i)\bwinner\b", "winning team", line)
        line = re.sub(r"(?i)\bloser\b", "opposing team", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            out.append(line)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out).strip() + ("\n" if out else "")


def clean_prompt_for_bundle(prompts_md: str, post_slug: str, bundle_name: str) -> str:
    clean_path = INPUT_CLEAN_PROMPTS_DIR / post_slug / "00_PROMPT_TO_PASTE.md"
    if clean_path.exists():
        return read_text(clean_path.as_posix())
    raw = prompt_for_bundle(prompts_md, bundle_name)
    sanitized = sanitize_prompt_text(raw)
    return sanitized or raw


def url_ext(url: str, content_type: str = "") -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    suffix = Path(urlparse(url).path).suffix
    return suffix or ".asset"


def wikimedia_file_title_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    parts = [p for p in path.split("/") if p]
    if not parts:
        return ""
    # Upload thumb URLs look like /wikipedia/commons/thumb/1/1d/File.jpg/1280px-File.jpg
    # The real file name is the second-to-last segment.
    if "thumb" in parts and len(parts) >= 2:
        return parts[-2]
    if "Special:Redirect" in path or "Special:FilePath" in path:
        return parts[-1]
    return parts[-1]


def title_variants(file_name: str) -> List[str]:
    if not file_name:
        return []
    raw = unquote(file_name)
    variants = [
        raw,
        raw.replace("_", " "),
        raw.replace(" ", "_"),
    ]
    out = []
    for v in variants:
        if v and v not in out:
            out.append(v)
    return out


def mediawiki_image_urls(file_name: str) -> List[str]:
    if not requests or not file_name:
        return []
    urls: List[str] = []
    for title_name in title_variants(file_name):
        title = "File:" + title_name
        for api in ["https://en.wikipedia.org/w/api.php", "https://commons.wikimedia.org/w/api.php"]:
            try:
                r = requests.get(
                    api,
                    params={
                        "action": "query",
                        "titles": title,
                        "redirects": "1",
                        "prop": "imageinfo",
                        "iiprop": "url|mime",
                        "format": "json",
                    },
                    headers={"User-Agent": "HSDGraphicsUploadPack/1.5.1"},
                    timeout=25,
                )
                if r.status_code >= 400:
                    continue
                pages = r.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    for info in page.get("imageinfo", []) or []:
                        u = info.get("url")
                        if u and u not in urls:
                            urls.append(u)
            except Exception:
                continue
    return urls


def candidate_urls_for_asset(asset: Dict[str, str]) -> List[str]:
    source = clean(asset.get("source_url"))
    entity = clean(asset.get("entity_name"))
    candidates: List[str] = []

    def add(url: str) -> None:
        if url and url not in candidates:
            candidates.append(url)

    add(source)

    if "wikimedia.org" in urlparse(source).netloc or "wikipedia.org" in urlparse(source).netloc:
        file_name = wikimedia_file_title_from_url(source)
        for u in mediawiki_image_urls(file_name):
            add(u)
        for variant in title_variants(file_name):
            quoted = quote(variant, safe="")
            add(f"https://en.wikipedia.org/wiki/Special:Redirect/file/{quoted}")
            add(f"https://en.wikipedia.org/wiki/Special:FilePath/{quoted}")
            add(f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{quoted}")
            add(f"https://commons.wikimedia.org/wiki/Special:FilePath/{quoted}")

    for fallback in TEAM_LOGO_DOWNLOAD_FALLBACKS.get(entity, []):
        add(fallback)

    return candidates


def looks_like_image_payload(raw: bytes, content_type: str, url: str) -> Tuple[bool, str]:
    head = raw[:800].lower()
    ctype = content_type.lower()
    if "image/" in ctype:
        return True, "content_type_image"
    if b"<svg" in head:
        return True, "svg_payload"
    if raw.startswith(b"\x89PNG"):
        return True, "png_signature"
    if raw.startswith(b"\xff\xd8"):
        return True, "jpeg_signature"
    if raw.startswith(b"RIFF") and b"WEBP" in raw[:20]:
        return True, "webp_signature"
    # Some Wikimedia Special pages return HTML. Do not save those as images.
    return False, "not_image_payload"


def download_candidates(asset: Dict[str, str], dest_dir: Path, base_name: str) -> Tuple[str, str]:
    if not requests:
        return "", "no_requests"
    errors: List[str] = []
    for url in candidate_urls_for_asset(asset):
        try:
            r = requests.get(
                url,
                headers={
                    "User-Agent": "HSDGraphicsUploadPack/1.5.1",
                    "Accept": "image/svg+xml,image/png,image/jpeg,image/webp,*/*",
                    "Referer": "https://www.wikipedia.org/",
                },
                timeout=40,
                allow_redirects=True,
            )
            if r.status_code >= 400 or not r.content:
                errors.append(f"{url} -> status_{r.status_code}")
                continue
            ok, reason = looks_like_image_payload(r.content, r.headers.get("content-type", ""), r.url)
            if not ok:
                errors.append(f"{url} -> {reason}")
                continue
            ext = url_ext(r.url or url, r.headers.get("content-type", ""))
            if b"<svg" in r.content[:800].lower():
                ext = ".svg"
            if ext.lower() in {".html", ".htm", ".php", ".aspx", ".asset"}:
                ext = ".svg" if b"<svg" in r.content[:800].lower() else ".png"
            dest = dest_dir / f"{base_name}{ext}"
            dest.write_bytes(r.content)
            return dest.as_posix(), f"downloaded:{r.status_code}:{reason}"
        except Exception as exc:
            errors.append(f"{url} -> {type(exc).__name__}")
            continue
    detail = "; ".join(errors[:4])
    return "", f"download_failed:{detail}" if detail else "download_failed"


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

    return download_candidates(asset, dest_dir, base_name)



def create_team_text_badge(asset: Dict[str, str], dest_dir: Path) -> Tuple[str, str]:
    """Create a simple text-only team badge SVG when an exact logo cannot be downloaded.
    This is deliberately not a fake logo. It is a plain text label asset.
    """
    if clean(asset.get("entity_type")) != "team":
        return "", ""
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = clean(asset.get("entity_name"))
    if not name:
        return "", ""
    entity_slug = slugify(name)
    approved_id = clean(asset.get("approved_asset_id"))
    dest = dest_dir / f"{entity_slug}_text-team-badge-fallback_{approved_id[-6:] if approved_id else 'asset'}.svg"
    safe = name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    words = safe.split()
    if len(words) > 2:
        line1 = " ".join(words[:-1])
        line2 = words[-1]
    elif len(words) == 2:
        line1, line2 = words
    else:
        line1, line2 = safe, ""
    y1 = "520" if line2 else "620"
    size1 = "150" if len(line1) < 11 else "112"
    size2 = "150" if len(line2) < 11 else "112"
    second = ""
    if line2:
        second = f'<text x="600" y="705" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="{size2}" font-weight="900" fill="#ffffff" letter-spacing="4">{line2.upper()}</text>'
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">
  <rect width="1200" height="1200" rx="150" fill="#101018"/>
  <rect x="54" y="54" width="1092" height="1092" rx="120" fill="none" stroke="#ffffff" stroke-width="22" opacity="0.78"/>
  <text x="600" y="{y1}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="{size1}" font-weight="900" fill="#ffffff" letter-spacing="4">{line1.upper()}</text>
  {second}
  <text x="600" y="1010" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="54" font-weight="700" fill="#ffffff" opacity="0.62">TEXT TEAM BADGE</text>
</svg>"""
    dest.write_text(svg, encoding="utf-8")
    return dest.as_posix(), "generated_text_team_badge_fallback_not_logo"


def convert_to_png(local_path: str, dest_dir: Path) -> Tuple[str, str]:
    if not local_path:
        return "", "no_local_asset"
    p = Path(local_path)
    if not p.exists():
        return "", "local_asset_missing"
    dest_dir.mkdir(parents=True, exist_ok=True)

    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
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
            return "", f"conversion_failed:{type(exc).__name__}"

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
    status_rows: List[Dict[str, Any]] = []

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

        prompt_text = clean_prompt_for_bundle(prompts_md, post_slug, bundle_name)
        (folder / "00_PROMPT_TO_PASTE.md").write_text(prompt_text, encoding="utf-8")

        for extra_name in [
            "graphics_slide_blueprints.md",
            "graphics_production_specs.json",
            "player_image_requirements.csv",
            "player_image_sourcing_report.md",
            "graphics_copy_style_guide.md",
            "graphics_display_copy.csv",
            "graphics_banned_language.csv",
            "graphics_asset_usage_map.csv",
            "graphics_layout_blueprint.csv",
            "graphics_prompt_sanitizer_rules.md",
            "graphics_prompt_clean_report.md",
            "graphics_prompt_clean_manifest.json",
            "studio_freshness_gate.csv",
            "studio_freshness_report.md",
            "player_image_fit_gate.csv",
            "player_image_fit_report.md",
            "rendered_slide_qa_report.md",
            "studio_freshness_gate.csv",
            "studio_freshness_report.md",
            "player_image_fit_gate.csv",
            "player_image_fit_report.md",
            "rendered_slide_qa.csv",
            "rendered_slide_qa_report.md",
        ]:
            extra = Path(extra_name)
            if extra.exists():
                shutil.copy2(extra, folder / extra_name)

        instructions = [
            f"# Upload instructions: {bundle_name}",
            "",
            "Upload `00_PROMPT_TO_PASTE.md` and the files inside `assets_png_preferred/` to the graphics chat. The prompt file is already sanitized for display-safe use.",
            "",
            "If a PNG preferred asset is missing, upload the matching file from `assets_original/`.",
            "",
            "Do not let the graphics chat fetch logo or player image URLs. Logos and player/person images must be attached as files. Use graphics_display_copy.csv and graphics_copy_style_guide.md for display language. Do not render banned language from graphics_banned_language.csv.",
            "",
        ]

        expected_assets = asset_map.get(post_slug, [])
        ready_count = 0
        missing_names: List[str] = []
        fallback_names: List[str] = []

        for asset in expected_assets:
            local_path, status = copy_or_download(asset, asset_folder)
            png_path, conversion_status = convert_to_png(local_path, png_folder)
            used_text_badge_fallback = False
            if not (png_path or local_path):
                fallback_path, fallback_status = create_team_text_badge(asset, asset_folder)
                if fallback_path:
                    local_path = fallback_path
                    status = fallback_status
                    png_path, conversion_status = convert_to_png(local_path, png_folder)
                    used_text_badge_fallback = True
            upload_path = png_path or local_path
            asset_ready = bool(upload_path and Path(upload_path).exists())
            if asset_ready:
                ready_count += 1
                if used_text_badge_fallback:
                    fallback_names.append(clean(asset.get("entity_name")))
                    upload_instruction = f"Upload {Path(upload_path).name} (text team badge fallback, not a logo)"
                else:
                    upload_instruction = f"Upload {Path(upload_path).name}"
            else:
                missing_names.append(clean(asset.get("entity_name")))
                upload_instruction = "MISSING REQUIRED FILE: rerun upload pack or add this asset manually"

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
                "asset_ready": "Yes" if asset_ready else "No",
                "required_for_bundle": "Yes",
                "upload_instruction": upload_instruction,
            })

            instructions.extend([
                f"## {asset.get('entity_name')}",
                "",
                f"- Preferred upload: `{Path(png_path).name if png_path else 'missing'}`",
                f"- Original asset: `{Path(local_path).name if local_path else 'missing'}`",
                f"- Source URL: {asset.get('source_url')}",
                f"- Status: {status}; {conversion_status}",
                f"- Ready: {'Yes' if asset_ready else 'No'}",
                "",
            ])

        freshness = freshness_status_for(post_slug)
        freshness_decision = freshness.get("freshness_decision", "")
        freshness_blocked = freshness_decision == "block"
        freshness_review = freshness_decision == "review"
        if freshness:
            instructions.extend([
                "## Freshness gate",
                "",
                f"- Decision: {freshness_decision or 'unknown'}",
                f"- Status: {freshness.get('freshness_status', '')}",
                f"- Event date: {freshness.get('event_date', '') or 'missing'}",
                f"- Recommended label: {freshness.get('recommended_label', '') or 'none'}",
                f"- Reason: {freshness.get('reason', '')}",
                "",
            ])

        fit_rows = player_fit_rows_for(post_slug)
        review_fit = [r for r in fit_rows if r.get("fit_status") == "review"]
        blocked_fit = [r for r in fit_rows if r.get("fit_status", "").startswith("blocked")]
        if fit_rows:
            instructions.extend([
                "## Player image fit gate",
                "",
                "Use player photos exactly as mapped. If a player image is flagged for tight crop, crop to face/head-and-shoulders and avoid showing wrong-team, overseas, college, or national-team jersey marks.",
                "",
            ])
            for r in fit_rows:
                instructions.append(f"- {r.get('player_name')}: {r.get('usage_mode')} | {r.get('prompt_instruction')}")
            instructions.append("")

        missing_count = len(missing_names)
        if missing_count:
            upload_status = "blocked_missing_required_assets"
        elif freshness_blocked:
            upload_status = "blocked_freshness_gate"
        elif blocked_fit:
            upload_status = "blocked_player_image_fit"
        elif freshness_review or review_fit or fallback_names:
            upload_status = "ready_with_review"
        else:
            upload_status = "ready"

        if upload_status != "ready":
            instructions.extend([
                "## REVIEW OR BLOCKED",
                "",
                f"Upload pack status: {upload_status}",
                "",
            ])
            if missing_count:
                instructions.extend(["Missing assets:", "", *[f"- {name}" for name in missing_names], ""])
            if fallback_names:
                instructions.extend(["Text-badge fallback assets were generated for:", "", *[f"- {name}" for name in fallback_names], "", "These are not fake logos. They are text-only team labels.", ""])
            if freshness_blocked:
                instructions.extend(["Freshness gate blocked this packet. Do not post unless you intentionally relabel it as carryover/yesterday and accept the risk.", ""])
            if blocked_fit:
                instructions.extend(["Player image fit blocked one or more player images. Do not substitute players.", ""])

        (folder / "01_UPLOAD_INSTRUCTIONS.md").write_text("\n".join(instructions), encoding="utf-8")
        zip_path = OUT_ZIP_DIR / f"{post_slug}_graphics_chat_upload_pack.zip"
        zip_folder(folder, zip_path)

        status_rows.append({
            "bundle_id": bundle_id,
            "post_slug": post_slug,
            "bundle_name": bundle_name,
            "upload_pack_status": upload_status,
            "assets_expected": len(expected_assets),
            "assets_ready": ready_count,
            "assets_missing": missing_count,
            "missing_asset_names": "; ".join(missing_names),
            "zip_path": zip_path.as_posix(),
            "notes": "Upload pack is complete." if upload_status == "ready" else "Ready with review or blocked. Check upload instructions.",
        })

    write_csv(OUT_MANIFEST_CSV, manifest_rows, FIELDS)
    write_csv(OUT_STATUS_CSV, status_rows, STATUS_FIELDS)

    counts = {
        "bundles": len(render_manifest.get("bundles", [])),
        "asset_rows": len(manifest_rows),
        "files_created": sum(1 for r in manifest_rows if r.get("local_asset_path") or r.get("local_png_path")),
        "png_preferred_created": sum(1 for r in manifest_rows if r.get("local_png_path")),
        "upload_packs_ready": sum(1 for r in status_rows if r.get("upload_pack_status") == "ready"),
        "upload_packs_blocked": sum(1 for r in status_rows if r.get("upload_pack_status") != "ready"),
    }

    Path(OUT_MANIFEST_JSON).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "input_prompts": INPUT_PROMPTS,
        "input_approved_assets": INPUT_APPROVED_ASSETS,
        "input_render_manifest": INPUT_RENDER_MANIFEST,
        "counts": counts,
        "outputs": [
            OUT_DIR.as_posix(),
            OUT_ZIP_DIR.as_posix(),
            OUT_MANIFEST_CSV,
            OUT_MANIFEST_JSON,
            OUT_STATUS_CSV,
            OUT_STATUS_JSON,
            OUT_INSTRUCTIONS,
            OUT_DIRECT_HANDOFF,
            "graphics_copy_style_guide.md",
            "graphics_display_copy.csv",
            "graphics_banned_language.csv",
            "graphics_asset_usage_map.csv",
            "graphics_layout_blueprint.csv",
            "graphics_prompt_sanitizer_rules.md",
            "graphics_prompt_clean_report.md",
            "graphics_prompt_clean_manifest.json",
            "studio_freshness_gate.csv",
            "studio_freshness_report.md",
            "player_image_fit_gate.csv",
            "player_image_fit_report.md",
            "rendered_slide_qa_report.md",
        ],
    }, indent=2), encoding="utf-8")

    Path(OUT_STATUS_JSON).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "counts": counts,
        "bundles": status_rows,
    }, indent=2), encoding="utf-8")

    instructions = [
        "# HSD Graphics Chat Upload Instructions",
        "",
        "The graphics chat cannot reliably fetch external logo or player image URLs. Use this upload pack instead.",
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
        "Upload pack status is in `graphics_upload_pack_status.csv`.",
        "",
    ]
    Path(OUT_INSTRUCTIONS).write_text("\n".join(instructions), encoding="utf-8")

    direct = [
        "# HSD Graphics Chat Direct Handoff",
        "",
        "Use the ZIP below for the graphics chat. The lite review artifact should also include the ZIP under `hsd_pipeline_lite_review/ready_upload_packs/`.",
        "",
        "Workflow: upload/open the ZIP, attach `00_PROMPT_TO_PASTE.md` plus the files in `assets_png_preferred/`, then paste the instructions below.",
        "",
    ]
    any_ready = False
    for srow in status_rows:
        if srow.get("upload_pack_status") in {"ready", "ready_with_review"}:
            any_ready = True
            post_slug = clean(srow.get("post_slug"))
            bundle_name = clean(srow.get("bundle_name")) or post_slug
            prompt_path = OUT_DIR / post_slug / "00_PROMPT_TO_PASTE.md"
            upload_inst_path = OUT_DIR / post_slug / "01_UPLOAD_INSTRUCTIONS.md"
            prompt_text = read_text(prompt_path.as_posix()).strip()
            upload_inst = read_text(upload_inst_path.as_posix()).strip()
            direct += [
                f"## {bundle_name}",
                "",
                f"Recommended ZIP: `{srow.get('zip_path')}`",
                f"Lite review copy: `hsd_pipeline_lite_review/ready_upload_packs/{Path(srow.get('zip_path', '')).name}`",
                "",
                f"Status: {srow.get('upload_pack_status').upper()}",
                "",
                "### Paste this after uploading the ZIP contents",
                "",
                "```text",
                "Use the sanitized uploaded prompt and uploaded asset files only. Use uploaded logo files, text team badge fallback files, and uploaded player/person image files only if present for this specific bundle. Do not fetch logo URLs. Do not fetch player image URLs. Do not substitute logos or players. Do not invent player bodies, jerseys, jersey numbers, fake player images, or fake logos. If a text team badge fallback is included, treat it as a plain team label, not as a logo. If no approved player/person image is present for this bundle, stay text-forward. Output 4 separate 1080x1350 slide files.",
                "```",
                "",
            ]
            if prompt_text:
                direct += [
                    "### Sanitized prompt included in the upload pack",
                    "",
                    "```text",
                    prompt_text,
                    "```",
                    "",
                ]
            if upload_inst:
                direct += [
                    "### Upload checklist from the pack",
                    "",
                    "```text",
                    upload_inst[:7000],
                    "```",
                    "",
                ]
    if not any_ready:
        direct += [
            "No ready upload pack was created. Check graphics_upload_pack_status.csv.",
            "",
        ]

    Path(OUT_DIRECT_HANDOFF).write_text("\n".join(direct), encoding="utf-8")

    print("Created HSD graphics upload pack")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()

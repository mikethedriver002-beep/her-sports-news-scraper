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
from urllib.parse import quote, unquote, urljoin, urlparse

try:
    import requests
except Exception:
    requests = None

try:
    import cairosvg
except Exception:
    cairosvg = None

VERSION = "hsd-graphics-upload-pack-v3.2.9-bebe-ops-v2.8-current-logo-lock"

INPUT_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts_v2.md")
INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")
INPUT_RENDER_MANIFEST = os.environ.get("HSD_RENDER_MANIFEST", "studio_render_manifest_v2.json")
INPUT_CLEAN_PROMPTS_DIR = Path(os.environ.get("HSD_CLEAN_PROMPTS_DIR", "graphics_clean_prompts"))
INPUT_LOGO_REGISTRY = Path(os.environ.get("HSD_VERIFIED_LOGO_REGISTRY", "config/hsd_verified_logo_registry_v1.json"))

OUT_DIR = Path("graphics_chat_upload_pack")
OUT_ZIP_DIR = Path("graphics_chat_upload_pack_zips")
OUT_MANIFEST_CSV = "graphics_chat_upload_manifest.csv"
OUT_MANIFEST_JSON = "graphics_chat_upload_manifest.json"
OUT_STATUS_CSV = "graphics_upload_pack_status.csv"
OUT_STATUS_JSON = "graphics_upload_pack_status.json"
OUT_INSTRUCTIONS = "graphics_chat_upload_instructions.md"
OUT_DIRECT_HANDOFF = "graphics_chat_direct_handoff.md"

OPERATOR_LOGO_DIRS = [
    Path("operator/assets/brand_logos"),
    Path("operator/assets/team_logos"),
    Path("data/assets/operator_approved/team_logos"),
]
OPERATOR_PLAYER_DIRS = [
    Path("operator/assets/player_images"),
    Path("operator/assets/players"),
    Path("data/assets/operator_approved/player_images"),
]
ASSET_EXTS = [".svg", ".png", ".jpg", ".jpeg", ".webp"]

FIELDS = [
    "bundle_id", "post_slug", "bundle_name", "entity_name", "entity_type", "approved_asset_id",
    "approved_variant", "source_url", "source_domain", "local_asset_path", "local_png_path",
    "asset_filename", "png_filename", "download_status", "conversion_status", "asset_ready",
    "exact_asset_status", "required_for_bundle", "upload_instruction"
]

STATUS_FIELDS = [
    "bundle_id", "post_slug", "bundle_name", "upload_pack_status", "assets_expected",
    "assets_ready", "assets_missing", "missing_asset_names", "missing_team_logos", "missing_player_images",
    "zip_path", "notes"
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


def read_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_text(path: str | Path) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def read_status_map(path: str, key_field: str) -> Dict[str, Dict[str, str]]:
    return {r.get(key_field, ""): r for r in read_csv(path) if r.get(key_field)}


def freshness_status_for(post_slug: str) -> Dict[str, str]:
    return read_status_map("studio_freshness_gate.csv", "bundle_slug").get(post_slug, {})


def player_fit_rows_for(post_slug: str) -> List[Dict[str, str]]:
    return [r for r in read_csv("player_image_fit_gate.csv") if r.get("bundle_slug") == post_slug]


def prompt_for_bundle(prompts_md: str, bundle_name: str) -> str:
    if not prompts_md:
        return ""
    escaped = re.escape(bundle_name)
    pat = rf"##\s+{escaped}\s*\n(.*?)(?=\n##\s+|\Z)"
    m = re.search(pat, prompts_md, flags=re.S)
    if m:
        return f"# {bundle_name}\n\n{m.group(1).strip()}\n"
    return prompts_md


def sanitize_prompt_text(prompt_text: str) -> str:
    out: List[str] = []
    banned_line_terms = [
        "bundle locked facts", "source-safe context", "graphics-safe context", "do not alter",
        "accuracy lock", "all games listed are for the target date", "title date", "titale date",
    ]
    replacements = [
        (r"Treat the game facts, scores, team names, and player names as locked facts and preserve them exactly\.",
         "Treat the game facts, team names, and player names as locked facts and preserve them exactly."),
        (r"huge result typography", "huge matchup typography"),
        (r"Results worth knowing", "Games worth watching"),
        (r"results worth knowing", "games worth watching"),
        (r"result labels", "postgame labels"),
        (r"Final reminder", "Reminder"),
        (r"All games listed are for the target date", "Four games. One night."),
        (r"All games listed are for the titale date", "Four games. One night."),
        (r"All times local", "All times ET"),
        (r"Use only approved exact player assets", "Use only the exact player images attached for this pack."),
    ]
    for raw_line in prompt_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        lower = line.lower()
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        if line.startswith("```"):
            continue
        if any(term in lower for term in banned_line_terms):
            continue
        for old, new in replacements:
            line = re.sub(old, new, line, flags=re.I)
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
    raw = read_text(clean_path) if clean_path.exists() else prompt_for_bundle(prompts_md, bundle_name)
    cleaned = sanitize_prompt_text(raw)
    strict_asset_rule = (
        "\n\nASSET RULE: Use the exact attached team logo files and exact attached player/person image files only. "
        "Do not fetch external logos or images in the graphics chat. Do not use text badges as logo replacements. "
        "Do not redraw, invent, recolor, or substitute logos. If an exact team logo or exact player image is missing, stop and report the missing asset instead of designing around it.\n"
    )
    return cleaned.rstrip() + strict_asset_rule


def url_ext(url: str, content_type: str = "") -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    suffix = Path(urlparse(url).path).suffix
    return suffix or ".asset"


def load_logo_registry() -> Dict[str, Any]:
    data = read_json(INPUT_LOGO_REGISTRY)
    teams = data.get("teams") if isinstance(data.get("teams"), dict) else {}
    return teams


def registry_for_team(entity: str) -> Dict[str, Any]:
    return load_logo_registry().get(entity, {})


def url_is_blocked_for_team(url: str, entity: str, registry: Dict[str, Any]) -> bool:
    if not url:
        return False
    low = url.lower()
    for token in registry.get("blocked_url_substrings", []) or []:
        if str(token).lower() in low:
            return True
    return False


def local_exact_files(entity: str, dirs: List[Path]) -> List[Path]:
    slug = slugify(entity)
    patterns = [slug, slug.replace("-", "_"), clean(entity).replace(" ", "_").lower(), clean(entity).lower().replace(" ", "-")]
    found: List[Path] = []
    for base in dirs:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in ASSET_EXTS:
                continue
            stem = p.stem.lower()
            if any(stem == pat or stem.startswith(pat + "_") or stem.startswith(pat + "-") for pat in patterns):
                found.append(p)
    return sorted(found, key=lambda p: (len(p.name), p.as_posix()))


def copy_first_local(entity: str, dirs: List[Path], dest_dir: Path, base_name: str) -> Tuple[str, str]:
    for src in local_exact_files(entity, dirs):
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{base_name}{src.suffix.lower()}"
        shutil.copy2(src, dest)
        return dest.as_posix(), f"copied_operator_exact:{src.as_posix()}"
    return "", ""


def wikimedia_file_title_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    parts = [p for p in path.split("/") if p]
    if not parts:
        return ""
    if "thumb" in parts and len(parts) >= 2:
        return parts[-2]
    if "Special:Redirect" in path or "Special:FilePath" in path:
        return parts[-1]
    return parts[-1]


def title_variants(file_name: str) -> List[str]:
    if not file_name:
        return []
    raw = unquote(file_name)
    variants = [raw, raw.replace("_", " "), raw.replace(" ", "_")]
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
                    params={"action": "query", "titles": title, "redirects": "1", "prop": "imageinfo", "iiprop": "url|mime", "format": "json"},
                    headers={"User-Agent": "HSDExactAssetPack/2.7"},
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


def extract_logo_urls_from_page(page_url: str, entity: str) -> List[str]:
    if not requests or not page_url:
        return []
    try:
        r = requests.get(page_url, headers={"User-Agent": "HSDExactAssetPack/2.7"}, timeout=25)
        if r.status_code >= 400 or not r.text:
            return []
    except Exception:
        return []
    html = r.text
    urls: List[str] = []
    team_slug = slugify(entity)
    terms = ["logo", "primary", "mark", "icon", team_slug, team_slug.replace("-", "")]
    for m in re.finditer(r'''(?:src|href|content)=["']([^"']+)["']''', html, flags=re.I):
        raw = m.group(1).strip()
        if not raw or raw.startswith("data:"):
            continue
        low = raw.lower()
        if not any(t in low for t in terms):
            continue
        if not any(ext in low for ext in [".svg", ".png", ".jpg", ".jpeg", ".webp"]):
            continue
        u = urljoin(page_url, raw)
        if u not in urls:
            urls.append(u)
    return urls[:20]


def source_is_exact_for_team(source: str, entity: str, registry: Dict[str, Any]) -> bool:
    if not source or url_is_blocked_for_team(source, entity, registry):
        return False
    if source in set(registry.get("direct_urls", []) or []):
        return True
    # For teams with blocked legacy patterns, only accept registry-direct or official-page extracted candidates.
    # This prevents stale but slug-matching files such as legacy Portland_Fire_logo.svg from passing.
    if registry.get("blocked_url_substrings"):
        return False
    low = source.lower()
    slug = slugify(entity)
    compact = slug.replace("-", "")
    file_title = wikimedia_file_title_from_url(source).lower().replace("_", "-")
    return slug in low or compact in low.replace("-", "").replace("_", "") or slug in file_title


def candidate_urls_for_team_logo(asset: Dict[str, str]) -> List[str]:
    entity = clean(asset.get("entity_name"))
    registry = registry_for_team(entity)
    source = clean(asset.get("source_url"))
    candidates: List[str] = []

    def add(url: str) -> None:
        if not url:
            return
        if url_is_blocked_for_team(url, entity, registry):
            return
        if url not in candidates:
            candidates.append(url)

    for url in registry.get("direct_urls", []) or []:
        add(url)
        if "wikimedia.org" in urlparse(url).netloc or "wikipedia.org" in urlparse(url).netloc:
            file_name = wikimedia_file_title_from_url(url)
            for u in mediawiki_image_urls(file_name):
                add(u)
            for variant in title_variants(file_name):
                quoted = quote(variant, safe="")
                add(f"https://en.wikipedia.org/wiki/Special:Redirect/file/{quoted}")
                add(f"https://en.wikipedia.org/wiki/Special:FilePath/{quoted}")
                add(f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{quoted}")
                add(f"https://commons.wikimedia.org/wiki/Special:FilePath/{quoted}")

    if source_is_exact_for_team(source, entity, registry):
        add(source)
        if "wikimedia.org" in urlparse(source).netloc or "wikipedia.org" in urlparse(source).netloc:
            file_name = wikimedia_file_title_from_url(source)
            for u in mediawiki_image_urls(file_name):
                add(u)

    for page_url in registry.get("page_urls", []) or []:
        for u in extract_logo_urls_from_page(page_url, entity):
            add(u)

    return candidates


def candidate_urls_for_asset(asset: Dict[str, str]) -> List[str]:
    source = clean(asset.get("source_url"))
    entity_type = clean(asset.get("entity_type")).lower()
    candidates: List[str] = []

    def add(url: str) -> None:
        if url and url not in candidates:
            candidates.append(url)

    if entity_type == "team":
        return candidate_urls_for_team_logo(asset)

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
    return False, "not_image_payload"


def download_candidates(asset: Dict[str, str], dest_dir: Path, base_name: str) -> Tuple[str, str]:
    if not requests:
        return "", "no_requests"
    errors: List[str] = []
    urls = candidate_urls_for_asset(asset)
    for url in urls:
        try:
            r = requests.get(
                url,
                headers={
                    "User-Agent": "HSDExactAssetPack/2.7",
                    "Accept": "image/svg+xml,image/png,image/jpeg,image/webp,*/*",
                    "Referer": "https://www.wnba.com/",
                },
                timeout=45,
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
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f"{base_name}{ext}"
            dest.write_bytes(r.content)
            return dest.as_posix(), f"downloaded_exact_candidate:{r.status_code}:{reason}"
        except Exception as exc:
            errors.append(f"{url} -> {type(exc).__name__}")
            continue
    detail = "; ".join(errors[:6])
    return "", f"download_failed_exact_candidates:{detail}" if detail else "download_failed_no_candidates"


def copy_or_download(asset: Dict[str, str], dest_dir: Path) -> Tuple[str, str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    entity = clean(asset.get("entity_name"))
    entity_type = clean(asset.get("entity_type")).lower()
    entity_slug = slugify(entity)
    variant_slug = slugify(asset.get("approved_variant") or entity_type or "asset")
    approved_id = clean(asset.get("approved_asset_id"))
    base_name = f"{entity_slug}_{variant_slug}_{approved_id[-6:] if approved_id else 'asset'}"

    if entity_type == "team":
        local, status = copy_first_local(entity, OPERATOR_LOGO_DIRS, dest_dir, base_name)
        if local:
            return local, status
        # Critical brand rule: do NOT reuse auto-generated team-logo files from
        # data/assets/approved. Those can preserve a stale or mismapped upstream logo.
        # Team logos must come from operator-approved local files or the verified
        # exact-logo registry acquisition path.
        return download_candidates(asset, dest_dir, base_name)

    if entity_type in {"player", "person", "athlete"}:
        local, status = copy_first_local(entity, OPERATOR_PLAYER_DIRS, dest_dir, base_name)
        if local:
            return local, status

    for field in ["master_path", "web_path"]:
        src = clean(asset.get(field))
        if src and Path(src).exists():
            ext = Path(src).suffix or ".asset"
            dest = dest_dir / f"{base_name}{ext}"
            shutil.copy2(src, dest)
            return dest.as_posix(), "copied_local_approved_asset"

    return download_candidates(asset, dest_dir, base_name)


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
            "graphics_slide_blueprints.md", "graphics_production_specs.json",
            "player_image_requirements.csv", "player_image_sourcing_report.md",
            "graphics_copy_style_guide.md", "graphics_display_copy.csv", "graphics_banned_language.csv",
            "graphics_asset_usage_map.csv", "graphics_layout_blueprint.csv",
            "graphics_prompt_sanitizer_rules.md", "graphics_prompt_clean_report.md", "graphics_prompt_clean_manifest.json",
            "studio_freshness_gate.csv", "studio_freshness_report.md",
            "player_image_fit_gate.csv", "player_image_fit_report.md",
            "exact_asset_audit.csv", "exact_asset_audit_report.md", "exact_asset_audit_manifest.json",
            "rendered_slide_qa.csv", "rendered_slide_qa_report.md",
        ]:
            extra = Path(extra_name)
            if extra.exists():
                shutil.copy2(extra, folder / extra_name)

        instructions = [
            f"# Upload instructions: {bundle_name}",
            "",
            "Upload `00_PROMPT_TO_PASTE.md` and every file inside `assets_png_preferred/` to the graphics chat.",
            "",
            "Hard rule: every team logo must be a real exact logo file. Every player/person image must be an exact mapped image file. No text-logo fallback, no placeholder, no AI-redrawn logo, no logo recolor, no substitute player image.",
            "",
            "If an exact logo or exact player image is missing, stop. Do not generate the graphic until the missing asset is added or acquired.",
            "",
            "Do not let the graphics chat fetch logo or player image URLs. The graphics chat may use attached files only.",
            "",
        ]

        expected_assets = asset_map.get(post_slug, [])
        ready_count = 0
        missing_names: List[str] = []
        missing_team_logos: List[str] = []
        missing_player_images: List[str] = []

        for asset in expected_assets:
            entity = clean(asset.get("entity_name"))
            entity_type = clean(asset.get("entity_type")).lower()
            local_path, status = copy_or_download(asset, asset_folder)
            png_path, conversion_status = convert_to_png(local_path, png_folder)
            upload_path = png_path or local_path
            asset_ready = bool(upload_path and Path(upload_path).exists())
            exact_status = "exact_file_ready" if asset_ready else "missing_exact_file"

            if asset_ready:
                ready_count += 1
                upload_instruction = f"Upload exact asset file: {Path(upload_path).name}"
            else:
                missing_names.append(entity)
                if entity_type == "team":
                    missing_team_logos.append(entity)
                    upload_instruction = "BLOCKED: missing exact team logo. Add/acquire the real logo file. Do not use text fallback."
                elif entity_type in {"player", "person", "athlete"}:
                    missing_player_images.append(entity)
                    upload_instruction = "BLOCKED: missing exact player/person image. Add/acquire the exact image file. Do not substitute."
                else:
                    upload_instruction = "BLOCKED: missing required exact asset file."

            manifest_rows.append({
                "bundle_id": bundle_id,
                "post_slug": post_slug,
                "bundle_name": bundle_name,
                "entity_name": entity,
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
                "exact_asset_status": exact_status,
                "required_for_bundle": "Yes",
                "upload_instruction": upload_instruction,
            })

            instructions.extend([
                f"## {entity}",
                "",
                f"- Entity type: {asset.get('entity_type', '')}",
                f"- Preferred upload: `{Path(png_path).name if png_path else 'missing'}`",
                f"- Original asset: `{Path(local_path).name if local_path else 'missing'}`",
                f"- Source URL: {asset.get('source_url')}",
                f"- Status: {status}; {conversion_status}",
                f"- Exact asset status: {exact_status}",
                f"- Ready: {'Yes' if asset_ready else 'No'}",
                f"- Instruction: {upload_instruction}",
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
        if missing_team_logos:
            upload_status = "blocked_missing_exact_team_logos"
        elif missing_player_images:
            upload_status = "blocked_missing_exact_player_images"
        elif missing_count:
            upload_status = "blocked_missing_required_exact_assets"
        elif freshness_blocked:
            upload_status = "blocked_freshness_gate"
        elif blocked_fit:
            upload_status = "blocked_player_image_fit"
        elif freshness_review or review_fit:
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
            if missing_team_logos:
                instructions.extend(["Missing exact team logos:", "", *[f"- {name}" for name in missing_team_logos], "", "Do not use text fallback. Do not ask the graphics chat to draw a logo. Add/acquire the real logo file and rerun.", ""])
            if missing_player_images:
                instructions.extend(["Missing exact player/person images:", "", *[f"- {name}" for name in missing_player_images], "", "Do not substitute player images. Add/acquire exact images and rerun.", ""])
            if missing_count and not (missing_team_logos or missing_player_images):
                instructions.extend(["Missing assets:", "", *[f"- {name}" for name in missing_names], ""])
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
            "missing_team_logos": "; ".join(missing_team_logos),
            "missing_player_images": "; ".join(missing_player_images),
            "zip_path": zip_path.as_posix(),
            "notes": "Exact asset pack is complete." if upload_status == "ready" else "Ready with review or blocked. Check upload instructions. No text/logo fallback is allowed.",
        })

    write_csv(OUT_MANIFEST_CSV, manifest_rows, FIELDS)
    write_csv(OUT_STATUS_CSV, status_rows, STATUS_FIELDS)

    counts = {
        "bundles": len(render_manifest.get("bundles", [])),
        "asset_rows": len(manifest_rows),
        "files_created": sum(1 for r in manifest_rows if r.get("local_asset_path") or r.get("local_png_path")),
        "png_preferred_created": sum(1 for r in manifest_rows if r.get("local_png_path")),
        "upload_packs_ready": sum(1 for r in status_rows if r.get("upload_pack_status") == "ready"),
        "upload_packs_review": sum(1 for r in status_rows if r.get("upload_pack_status") == "ready_with_review"),
        "upload_packs_blocked": sum(1 for r in status_rows if r.get("upload_pack_status") not in {"ready", "ready_with_review"}),
    }

    Path(OUT_MANIFEST_JSON).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "input_prompts": INPUT_PROMPTS,
        "input_approved_assets": INPUT_APPROVED_ASSETS,
        "input_render_manifest": INPUT_RENDER_MANIFEST,
        "input_logo_registry": INPUT_LOGO_REGISTRY.as_posix(),
        "rule": "Exact real logos/images required. No text fallback.",
        "counts": counts,
        "outputs": [OUT_DIR.as_posix(), OUT_ZIP_DIR.as_posix(), OUT_MANIFEST_CSV, OUT_MANIFEST_JSON, OUT_STATUS_CSV, OUT_STATUS_JSON, OUT_INSTRUCTIONS, OUT_DIRECT_HANDOFF],
    }, indent=2), encoding="utf-8")

    Path(OUT_STATUS_JSON).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "rule": "Exact real logos/images required. No text fallback.",
        "counts": counts,
        "bundles": status_rows,
    }, indent=2), encoding="utf-8")

    instructions = [
        "# HSD Graphics Chat Upload Instructions",
        "",
        "Use attached exact asset files only.",
        "",
        "For the post you are making:",
        "",
        "1. Open `graphics_chat_upload_pack/<post_slug>/`.",
        "2. Upload `00_PROMPT_TO_PASTE.md`.",
        "3. Upload every file in `assets_png_preferred/`, including exact team logos and exact player/person images if present.",
        "4. If any required exact logo or player image is missing, stop and acquire the file. No text fallback is allowed.",
        "5. Tell the graphics chat: use only attached assets, do not fetch or invent logos or player images.",
        "",
        "Quick ZIPs are in `graphics_chat_upload_pack_zips/`.",
        "Upload pack status is in `graphics_upload_pack_status.csv`.",
        "",
    ]
    Path(OUT_INSTRUCTIONS).write_text("\n".join(instructions), encoding="utf-8")

    direct = [
        "# HSD Graphics Chat Direct Handoff",
        "",
        "Only use a ZIP if its `graphics_upload_pack_status.csv` row is READY or READY_WITH_REVIEW. Exact real logo/player assets are required; text fallback is prohibited.",
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
            prompt_text = read_text(prompt_path).strip()
            upload_inst = read_text(upload_inst_path).strip()
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
                "Use the sanitized uploaded prompt and uploaded exact asset files only. Use attached team logos and attached player/person image files exactly as mapped. Do not fetch logo URLs. Do not fetch player image URLs. Do not substitute logos or players. Do not invent player bodies, jerseys, jersey numbers, fake player images, fake logos, text-logo fallbacks, or placeholder badges. Output 4 separate 1080x1350 slide files.",
                "```",
                "",
            ]
            if prompt_text:
                direct += ["### Sanitized prompt included in the upload pack", "", "```text", prompt_text, "```", ""]
            if upload_inst:
                direct += ["### Upload checklist from the pack", "", "```text", upload_inst[:9000], "```", ""]
    if not any_ready:
        direct += [
            "No ready upload pack was created.",
            "",
            "Check `graphics_upload_pack_status.csv`. If the reason is missing exact team logos or player images, acquire those exact files and rerun. Do not use text fallback.",
            "",
        ]
    Path(OUT_DIRECT_HANDOFF).write_text("\n".join(direct), encoding="utf-8")

    print("Created HSD exact-asset graphics upload pack")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()

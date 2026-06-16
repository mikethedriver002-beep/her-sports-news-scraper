from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "v1-player-toggle-variant-packs"
ROOT = Path("outputs/latest/production_graphics_director")
OUT = ROOT / "graphics_variant_packs"
ZIP_DIR = OUT / "zips"
CONTEXT = ROOT / "context_engine" / "context_bank.csv"
COPY_BANK = ROOT / "copy_director" / "copy_bank.csv"
CAROUSEL_MANIFEST = ROOT / "carousel_director" / "carousel_manifest.csv"
DOSSIER_DIR = ROOT / "manual_prompt_dossiers"
TEAM_LOGOS = Path("data/asset_registry/wnba/team_logos.csv")
ATHLETES = Path("data/asset_registry/wnba/athletes.csv")
ATHLETE_IMAGES = Path("data/asset_registry/wnba/athlete_images.csv")
ATHLETE_NEEDS_FIX = Path("data/asset_registry/wnba/athlete_image_needs_fix.csv")
WATERMARK = Path("assets/branding/official_hsd_watermark.png")
SUMMARY = Path("outputs/latest/summary.json")

MANIFEST_FIELDS = [
    "package_id", "headline", "variant", "zip_path", "folder_path", "team_assets", "player_assets", "player_mode", "status", "notes"
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "item"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def copy_asset(src: Path, dst_dir: Path, name_prefix: str = "") -> Path | None:
    if not src.exists() or not src.is_file():
        return None
    dst_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", (name_prefix + src.name)).strip("-")
    dst = dst_dir / safe_name
    shutil.copy2(src, dst)
    return dst


def team_logo_map() -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for row in read_csv(TEAM_LOGOS):
        tid = row.get("team_id", "")
        path = Path(row.get("file_path", ""))
        if tid and path.exists():
            out[tid] = path
    return out


def athlete_maps() -> Tuple[Dict[str, Dict[str, str]], Dict[str, List[Dict[str, str]]], set[str]]:
    athlete_rows = {r.get("athlete_id", ""): r for r in read_csv(ATHLETES) if r.get("athlete_id")}
    image_paths: Dict[str, str] = {}
    for row in read_csv(ATHLETE_IMAGES):
        aid = row.get("athlete_id", "")
        path = clean(row.get("file_path"))
        if row.get("image_type") == "headshot" and row.get("approved") == "true" and Path(path).exists() and Path(path + ".approved").exists():
            image_paths[aid] = path
    needs_fix = {r.get("athlete_id", "") for r in read_csv(ATHLETE_NEEDS_FIX) if r.get("athlete_id")}
    approved: Dict[str, Dict[str, str]] = {}
    by_team: Dict[str, List[Dict[str, str]]] = {}
    for aid, row in athlete_rows.items():
        if aid in image_paths and aid not in needs_fix:
            item = dict(row)
            item["headshot_path"] = image_paths[aid]
            approved[aid] = item
            by_team.setdefault(item.get("team_id", ""), []).append(item)
    return approved, by_team, needs_fix


def index_by(rows: List[Dict[str, str]], key: str) -> Dict[str, Dict[str, str]]:
    return {r.get(key, ""): r for r in rows if r.get(key)}


def package_dossier(package_id: str) -> str:
    path = DOSSIER_DIR / f"{slug(package_id)}.md"
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def select_players(row: Dict[str, str], approved: Dict[str, Dict[str, str]], by_team: Dict[str, List[Dict[str, str]]]) -> Tuple[List[Dict[str, str]], str]:
    selected: List[Dict[str, str]] = []
    seen: set[str] = set()
    for aid in [x for x in row.get("approved_players", "").split(";") if x]:
        if aid in approved and aid not in seen:
            selected.append(approved[aid])
            seen.add(aid)
    if selected:
        return selected[:6], "context_approved_players"
    team_ids = [x for x in row.get("teams", "").split(";") if x]
    for tid in team_ids:
        count = 0
        for player in by_team.get(tid, []):
            aid = player.get("athlete_id", "")
            if aid and aid not in seen:
                selected.append(player)
                seen.add(aid)
                count += 1
            if count >= 2:
                break
    if selected:
        return selected[:6], "team_candidate_players_review_required"
    return [], "no_approved_players_available"


def variant_prompt(row: Dict[str, str], copy_row: Dict[str, str], carousel_row: Dict[str, str], dossier: str, variant: str, player_mode: str, players: List[Dict[str, str]]) -> str:
    headline = clean(row.get("headline"))
    caption = clean(copy_row.get("caption"))
    teams = clean(row.get("teams"))
    player_lines = "\n".join([f"- {p.get('display_name')} | {p.get('team_id')} | uploaded file: assets/players/{p.get('athlete_id')}.png" for p in players]) or "- None"
    if variant == "with_players":
        variant_rules = (
            "PLAYER MODE: WITH PLAYERS.\n"
            "Use the uploaded approved player headshots if they improve the graphic. Do not invent player photos. Do not use generic blank headshots. "
            "If player_mode says team_candidate_players_review_required, these images are optional visual candidates, not locked statistical claims. Do not add player stats unless supplied in the dossier."
        )
    else:
        variant_rules = (
            "PLAYER MODE: LOGOS ONLY.\n"
            "Do not use player photos even if present elsewhere. Build this as a logo-forward, scoreboard-forward, or text-forward HSD graphic."
        )
    return f"""HSD GRAPHICS PRODUCTION.

Use the uploaded ZIP only.

Create premium Her Sports Daily graphics for:
{headline}

Variant: {variant}
{variant_rules}

Detected teams: {teams}

Approved / candidate player assets included:
{player_lines}

Non-negotiables:
- Use only uploaded assets.
- Do not fetch logos.
- Do not invent players.
- Do not invent stats.
- Do not use fake player photos.
- Do not use generic blank headshots.
- Do not create white dashboard cards.
- Do not render internal QA labels or workflow language.
- Keep all text readable and inside safe zones.
- Use the official HSD watermark only if included.
- Export each slide as a separate PNG.
- Send the finished images in a ZIP.

Use the premium HSD style:
dark cinematic sports-media background, bold condensed typography, strong team color accents, clean hierarchy, ESPN/BR energy, no clutter.

Caption to use after graphics are generated:
{caption}

Manual prompt dossier:
{dossier}
"""


def make_zip(src_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in src_dir.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(src_dir.parent))


def build_variant(row: Dict[str, str], copy_row: Dict[str, str], carousel_row: Dict[str, str], logos: Dict[str, Path], approved: Dict[str, Dict[str, str]], by_team: Dict[str, List[Dict[str, str]]], variant: str) -> Dict[str, Any]:
    package_id = row.get("package_id", "")
    headline = clean(row.get("headline"))
    folder = OUT / variant / slug(package_id)
    if folder.exists():
        shutil.rmtree(folder)
    assets_dir = folder / "assets"
    logo_dir = assets_dir / "logos"
    player_dir = assets_dir / "players"
    folder.mkdir(parents=True, exist_ok=True)
    team_assets: List[str] = []
    for tid in [x for x in row.get("teams", "").split(";") if x]:
        if tid in logos:
            copied = copy_asset(logos[tid], logo_dir, f"{tid}_")
            if copied:
                team_assets.append(copied.as_posix())
    if WATERMARK.exists():
        copy_asset(WATERMARK, assets_dir, "official_hsd_")
    players, player_mode = select_players(row, approved, by_team)
    player_assets: List[str] = []
    if variant == "with_players":
        for player in players:
            src = Path(player.get("headshot_path", ""))
            aid = player.get("athlete_id", "player")
            copied = copy_asset(src, player_dir, f"{aid}_")
            if copied:
                player_assets.append(copied.as_posix())
    else:
        players = []
        player_mode = "logos_only_forced"
    dossier = package_dossier(package_id)
    prompt = variant_prompt(row, copy_row, carousel_row, dossier, variant, player_mode, players)
    (folder / "00_PROMPT_TO_PASTE.md").write_text(prompt, encoding="utf-8")
    (folder / "content_summary.json").write_text(json.dumps({
        "version": VERSION,
        "package_id": package_id,
        "headline": headline,
        "variant": variant,
        "teams": row.get("teams", ""),
        "player_mode": player_mode,
        "players": [{"athlete_id": p.get("athlete_id"), "display_name": p.get("display_name"), "team_id": p.get("team_id")} for p in players],
        "team_assets": team_assets,
        "player_assets": player_assets,
    }, indent=2), encoding="utf-8")
    if copy_row:
        write_csv(folder / "copy_package.csv", [copy_row], list(copy_row.keys()))
    if carousel_row:
        write_csv(folder / "carousel_package.csv", [carousel_row], list(carousel_row.keys()))
    zip_path = ZIP_DIR / f"{variant}_{slug(package_id)}.zip"
    make_zip(folder, zip_path)
    return {
        "package_id": package_id,
        "headline": headline,
        "variant": variant,
        "zip_path": zip_path.as_posix(),
        "folder_path": folder.as_posix(),
        "team_assets": len(team_assets),
        "player_assets": len(player_assets),
        "player_mode": player_mode,
        "status": "ready" if team_assets or player_assets else "review_missing_assets",
        "notes": "with_players includes approved/candidate headshots" if variant == "with_players" else "logos-only safe variant",
    }


def update_summary(fields: Dict[str, Any]) -> None:
    data = read_json(SUMMARY)
    data.update(fields)
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    context_rows = read_csv(CONTEXT)
    copy_rows = index_by(read_csv(COPY_BANK), "package_id")
    carousel_rows = index_by(read_csv(CAROUSEL_MANIFEST), "package_id")
    logos = team_logo_map()
    approved, by_team, needs_fix = athlete_maps()
    manifest: List[Dict[str, Any]] = []
    for row in context_rows:
        package_id = row.get("package_id", "")
        if not package_id:
            continue
        copy_row = copy_rows.get(package_id, {})
        carousel_row = carousel_rows.get(package_id, {})
        for variant in ["logos_only", "with_players"]:
            manifest.append(build_variant(row, copy_row, carousel_row, logos, approved, by_team, variant))
    write_csv(OUT / "variant_manifest.csv", manifest, MANIFEST_FIELDS)
    report = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "packages": len(context_rows),
        "variant_packs": len(manifest),
        "logos_only_packs": len([r for r in manifest if r.get("variant") == "logos_only"]),
        "with_players_packs": len([r for r in manifest if r.get("variant") == "with_players"]),
        "with_players_ready": len([r for r in manifest if r.get("variant") == "with_players" and int(r.get("player_assets") or 0) > 0]),
        "needs_fix_athletes_blocked": len(needs_fix),
        "output_folder": OUT.as_posix(),
    }
    (OUT / "variant_pack_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "variant_pack_report.md").write_text(
        "# HSD Graphics Variant Packs v1\n\n"
        f"Generated: {report['generated_at_utc']}\n\n"
        "## Counts\n\n"
        f"- packages: {report['packages']}\n"
        f"- variant packs: {report['variant_packs']}\n"
        f"- logos-only packs: {report['logos_only_packs']}\n"
        f"- with-players packs: {report['with_players_packs']}\n"
        f"- with-players packs with player assets: {report['with_players_ready']}\n"
        f"- needs-fix athletes blocked: {report['needs_fix_athletes_blocked']}\n\n"
        "## How to use\n\n"
        "Open `zips/`. For each package, use either `logos_only_...zip` or `with_players_...zip`. The with-players version includes approved player headshots when available.\n",
        encoding="utf-8",
    )
    update_summary({
        "graphics_variant_packs_version": VERSION,
        "graphics_variant_packs": len(manifest),
        "graphics_variant_with_players_ready": report["with_players_ready"],
    })
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

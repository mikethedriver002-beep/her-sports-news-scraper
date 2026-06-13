
from __future__ import annotations
import csv, json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Iterable

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_csv(path: str | Path) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def write_csv(path: str | Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    p = Path(path)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def read_json(path: str | Path, default=None):
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {} if default is None else default

def story_id(*parts: Any) -> str:
    h = hashlib.sha1("|".join(clean(p) for p in parts).encode("utf-8")).hexdigest()[:14]
    return "story_" + h

def score_priority(league: str, kind: str, source_state: str = "") -> str:
    l = clean(league).upper()
    if kind in {"breaking", "rumor_confirmed"}:
        return "P0"
    if l == "WNBA":
        return "P1"
    if l in {"WTA", "NWSL"}:
        return "P2"
    if l in {"LPGA", "VNL", "VOLLEYBALL"}:
        return "P3"
    return "P4"

VERSION = "v3.3.0-mermaid-player-registry-v2"
REGISTRY = Path("operator/assets/player_registry/player_registry.csv")
TEMPLATE = Path("operator/assets/player_registry/player_registry_template.csv")
FOCUS = Path("preview_player_focus.csv")
MANIFEST = Path("graphics_chat_upload_manifest.csv")
OUT_REGISTRY = "player_asset_registry.csv"
OUT_DEBT = "player_asset_debt.csv"
OUT_MD = "player_registry_status.md"
OUT_JSON = "player_registry_manifest.json"
FIELDS = ["league","team_name","player_name","approved_asset_path","source_url","source_type","current_team_verified","identity_verified","rights_status","usage_status","coverage_status","notes"]
DEBT_FIELDS = ["league","team_name","needed_for","missing_player_options","debt_type","priority","recommended_action"]

def load_registry() -> List[Dict[str,str]]:
    if REGISTRY.exists():
        return read_csv(REGISTRY)
    return []

def manifest_player_rows() -> List[Dict[str,str]]:
    rows = []
    for r in read_csv(MANIFEST):
        if clean(r.get("entity_type")).lower() == "player":
            rows.append({
                "league": "WNBA",
                "team_name": "", # filled from focus if possible
                "player_name": clean(r.get("entity_name")),
                "approved_asset_path": clean(r.get("local_png_path") or r.get("local_asset_path")),
                "source_url": clean(r.get("source_url")),
                "source_type": "upload_manifest_exact_asset",
                "current_team_verified": "Review",
                "identity_verified": "Review",
                "rights_status": "review",
                "usage_status": "active",
                "coverage_status": "candidate_from_upload_manifest",
                "notes": "Imported from current upload manifest; needs registry confirmation for team/current context."
            })
    return rows

def main() -> None:
    rows = load_registry()
    if not rows and TEMPLATE.exists():
        rows = []  # template is not real registry data
    rows += manifest_player_rows()

    # Map preview focus teams to available exact players.
    focus = read_csv(FOCUS)
    available = {clean(r.get("player_name")): r for r in rows if clean(r.get("player_name")) and clean(r.get("approved_asset_path"))}
    coverage_rows = []
    debt = []
    for f in focus:
        team = clean(f.get("team_name"))
        player = clean(f.get("player_name"))
        league = "WNBA"
        if player in available:
            base = available[player].copy()
            base["team_name"] = base.get("team_name") or team
            base["coverage_status"] = "exact_asset_present_needs_team_context_review" if base.get("current_team_verified") != "Yes" else "exact_asset_ready"
            coverage_rows.append(base)
        else:
            debt.append({
                "league": league,
                "team_name": team,
                "needed_for": "preview_player_graphics",
                "missing_player_options": player,
                "debt_type": "missing_exact_player_asset",
                "priority": "P1" if team else "P2",
                "recommended_action": "Add official roster/player-page headshot to operator/assets/player_registry and player_registry.csv."
            })

    # Include registry rows not in focus too.
    seen = {(r.get("team_name",""), r.get("player_name","")) for r in coverage_rows}
    for r in rows:
        key = (r.get("team_name",""), r.get("player_name",""))
        if key not in seen:
            rr = r.copy()
            rr.setdefault("coverage_status", "registry_available")
            coverage_rows.append(rr)

    write_csv(OUT_REGISTRY, coverage_rows, FIELDS)
    write_csv(OUT_DEBT, debt, DEBT_FIELDS)
    lines = ["# HSD Player Asset Registry v2", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", f"- registry rows: {len(coverage_rows)}", f"- asset debt rows: {len(debt)}", ""]
    if debt:
        lines += ["## Asset debt", ""]
        for d in debt:
            lines.append(f"- **{d['team_name']}** needs exact player asset for: {d['missing_player_options']}")
    else:
        lines.append("No preview player asset debt found.")
    Path(OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(OUT_JSON).write_text(json.dumps({"version": VERSION, "generated_at": now_iso(), "registry_rows": len(coverage_rows), "asset_debt": len(debt)}, indent=2), encoding="utf-8")
    print(json.dumps({"player_registry_rows": len(coverage_rows), "player_asset_debt": len(debt)}, indent=2))

if __name__ == "__main__":
    main()

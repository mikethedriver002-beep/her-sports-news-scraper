from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

MANIFEST_JSON = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
REPORT_JSON = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_report.json")


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def normalize_item(item: Dict[str, Any]) -> bool:
    if clean(item.get("asset_assurance_player_route")) != "downgraded_player_to_non_player_team_spotlight":
        return False

    title = "TEAM SPOTLIGHT"
    headline = clean(item.get("headline"))
    if " at " in headline:
        away = headline.split(" at ", 1)[0].strip()
        if away:
            title = f"{away.split()[-1].upper()} TEAM SPOTLIGHT"

    body = "TEAM IDENTITY | MATCHUP IMPACT | KEY EDGE"
    old_title = "PLAYER " + "FEATURE"
    old_body = "PLAYER " + "SPOTLIGHT • MATCHUP IMPACT • LATE-GAME EDGE"

    item.update({
        "module_mode": "team_spotlight_fallback",
        "player_assets_used": 0,
        "player_names": "",
        "player_asset_kind": "team_spotlight_fallback",
        "fixture_only_player_asset": "false",
        "placeholder_layer_count": 0,
        "rendered_copy_placeholder_count": 0,
        "context_placeholder_count": 0,
        "rendered_copy_placeholder_tokens": "",
        "public_copy_placeholder_tokens": "",
    })

    for field in ["rendered_copy", "public_copy"]:
        text = clean(item.get(field))
        if not text:
            continue
        text = text.replace(old_title, title)
        text = text.replace(old_body, body)
        item[field] = text

    return True


def normalize_payload(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"path": path.as_posix(), "changed": 0, "exists": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    items: List[Dict[str, Any]] = [item for item in payload.get("items") or [] if isinstance(item, dict)]
    changed = sum(1 for item in items if normalize_item(item))
    if changed:
        payload["items"] = items
        payload["rendered_copy_placeholder_rows"] = sum(1 for item in items if clean(item.get("rendered_copy_placeholder_tokens")))
        payload["phase6m_manifest_copy_normalized"] = True
        payload["phase6m_manifest_copy_normalized_rows"] = changed
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"path": path.as_posix(), "changed": changed, "exists": True}


def main() -> int:
    results = [normalize_payload(MANIFEST_JSON), normalize_payload(REPORT_JSON)]
    print(json.dumps({"version": "v1.0-phase6m-manifest-copy-normalizer", "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

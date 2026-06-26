from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generate_hsd_template_renderer_v4_phase6l as phase6l
from hsd_asset_assurance_core import VERSION as ASSET_CORE_VERSION
from hsd_asset_assurance_core import assurance_from_item, clean, image_decodable, resolve_player_asset, resolve_team_asset, slug

VERSION = "v4.6-phase6k-story-context-cta-polish"
PHASE6M_EFFECTIVE_VERSION = "v4.8-phase6m-asset-assurance-core"
ASSURANCE_OUT = Path("outputs/latest/HSD_ASSET_ASSURANCE")

EXTRA_FIELDS = [
    "phase6m_effective_renderer_version", "asset_assurance_version", "asset_assurance_status",
    "asset_assurance_reasons", "asset_render_safe", "asset_live_candidate_eligible",
    "asset_live_ready_pre_human", "asset_requires_visual_approval", "asset_release_lane",
    "team_asset_count", "team_exact_logo_count", "team_fallback_badge_count",
    "asset_assurance_player_mode", "asset_assurance_player_route", "requested_module_mode",
    "asset_fallback_review_cue",
]

_CONFIGURED = False
_ORIGINALS: Dict[str, Any] = {}
_TEAM_RESOLUTIONS: List[Dict[str, Any]] = []
_PLAYER_ROUTES: List[Dict[str, Any]] = []


def _base() -> Any:
    return phase6l.phase6k.base


def _team_metadata() -> Dict[str, Dict[str, str]]:
    base = _base()
    return {clean(row.get("team_id")): dict(row) for row in base.read_csv(base.TEAMS) if clean(row.get("team_id"))}


def _safe_team_id(team: str, aliases: Dict[str, str]) -> str:
    try:
        return clean(_base().resolve_team(team, aliases)) or slug(team)
    except Exception:
        return slug(team)


def _paste_badge(image: Image.Image, path: Path, box: Tuple[int, int, int, int], accent: Tuple[int, int, int]) -> None:
    base = _base()
    x, y, width, height = box
    base.panel(image, box, accent, 10, (1, 2, 5, 220), 2)
    badge = Image.open(path).convert("RGBA")
    badge.thumbnail((max(1, width - 34), max(1, height - 34)), Image.Resampling.LANCZOS)
    image.alpha_composite(badge, (x + (width - badge.width) // 2, y + (height - badge.height) // 2))


def _assured_draw_team_asset(image: Image.Image, team: str, box: Tuple[int, int, int, int], aliases: Dict[str, str], logos: Dict[str, str], accent: Tuple[int, int, int]) -> str:
    team_id = _safe_team_id(team, aliases)
    meta = _team_metadata().get(team_id, {})
    raw = clean(logos.get(team_id))
    exact = Path(raw) if raw else None
    resolution = resolve_team_asset(
        sport_id="wnba", entity_id=team_id, display_name=team, exact_path=exact, output_root=ASSURANCE_OUT,
        primary_hex=clean(meta.get("primary_hex")) or "#DFA126", secondary_hex=clean(meta.get("secondary_hex")) or "#080A10",
    )
    mode = clean(resolution.get("resolution_mode"))
    if mode == "approved_logo":
        original_mode = _ORIGINALS["draw_team_asset"](image, team, box, aliases, logos, accent)
        if original_mode == "approved_logo":
            _TEAM_RESOLUTIONS.append({**resolution, "renderer_mode": original_mode})
            return original_mode
        resolution = resolve_team_asset(
            sport_id="wnba", entity_id=team_id, display_name=team, exact_path=None, output_root=ASSURANCE_OUT,
            primary_hex=clean(meta.get("primary_hex")) or "#DFA126", secondary_hex=clean(meta.get("secondary_hex")) or "#080A10",
        )
        mode = "hsd_team_badge"
    fallback = Path(clean(resolution.get("resolved_path")))
    if not image_decodable(fallback):
        raise RuntimeError(f"asset assurance badge failed for {team}")
    _paste_badge(image, fallback, box, accent)
    _TEAM_RESOLUTIONS.append({**resolution, "renderer_mode": mode})
    return mode


def _original_player_candidate(team: str, aliases: Dict[str, str], index: Dict[str, List[Dict[str, str]]], fixtures: bool) -> Optional[Dict[str, str]]:
    return _ORIGINALS["select_player"](team, aliases, index, fixtures)


def _approved_player(resolution: Dict[str, Any]) -> bool:
    return clean(resolution.get("resolution_mode")) == "approved_player_asset"


def _team_spotlight_sentinel(team: str, aliases: Dict[str, str]) -> Dict[str, str]:
    return {"name": "", "team_id": _safe_team_id(team, aliases), "path": "", "asset_kind": "team_spotlight_fallback", "fixture_only": "false", "asset_assurance_fallback": "true"}


def _assured_select_player(team: str, aliases: Dict[str, str], index: Dict[str, List[Dict[str, str]]], fixtures: bool = False) -> Optional[Dict[str, str]]:
    candidate = _original_player_candidate(team, aliases, index, fixtures)
    resolution = resolve_player_asset(candidate, requested=True, team_name=team)
    return candidate if _approved_player(resolution) else _team_spotlight_sentinel(team, aliases)


def _assured_select_player_for_final(team: str, row: Dict[str, Any], aliases: Dict[str, str], index: Dict[str, List[Dict[str, str]]], fixtures: bool) -> Optional[Dict[str, str]]:
    base = _base()
    candidate = _ORIGINALS["select_player_for_final"](team, row, aliases, index, fixtures)
    resolution = resolve_player_asset(candidate, requested=True, team_name=team)
    if _approved_player(resolution):
        return candidate
    _PLAYER_ROUTES.append({
        "source_id": clean(row.get("event_id") or row.get("event_uid") or row.get("canonical_key")),
        "headline": base.headline_for(row, "hsd_game_recap_final_score_b"),
        "requested_module_mode": "with_player",
        "effective_module_mode": "logos_only_downgrade",
        "route_decision": "downgraded_final_b_missing_approved_player_asset",
        **resolution,
    })
    return None


def _assured_render_tonight(row: Dict[str, Any], aliases: Dict[str, str], logos: Dict[str, str], players: Dict[str, List[Dict[str, str]]], module_mode: str, fixtures: bool):
    base = _base()
    if clean(module_mode).lower() != "player":
        return _ORIGINALS["render_tonight"](row, aliases, logos, players, module_mode, fixtures)
    away = base.first_value(row, ["away_team_name", "away_team_display", "away_team", "team_away"])
    candidate = _original_player_candidate(away, aliases, players, fixtures)
    resolution = resolve_player_asset(candidate, requested=True, team_name=away)
    if _approved_player(resolution):
        image, meta = _ORIGINALS["render_tonight"](row, aliases, logos, players, module_mode, fixtures)
        meta.update({"requested_module_mode": "player", "asset_assurance_player_mode": resolution["resolution_mode"], "asset_assurance_player_route": "rendered_verified_player_asset"})
        _PLAYER_ROUTES.append({"source_id": clean(row.get("event_id") or row.get("event_uid") or row.get("canonical_key")), "headline": base.headline_for(row, "hsd_tonight_in_the_w_a"), "requested_module_mode": "player", "effective_module_mode": "player", **resolution})
        return image, meta
    safe_row = dict(row)
    team_label = clean(base.short_team(away)) or clean(away) or "TEAM"
    safe_row["watch_title"] = f"{team_label} TEAM SPOTLIGHT"
    safe_row["watch_body"] = "TEAM IDENTITY • MATCHUP IMPACT • KEY EDGE"
    image, meta = _ORIGINALS["render_tonight"](safe_row, aliases, logos, players, "watch_point", fixtures)
    meta.update({
        "requested_module_mode": "player",
        "asset_assurance_player_mode": "team_spotlight_fallback",
        "asset_assurance_player_route": "downgraded_player_to_non_player_team_spotlight",
        "player_assets_used": 0,
        "player_names": "",
        "player_asset_kind": "team_spotlight_fallback",
        "fixture_only_player_asset": "false",
        "placeholder_layer_count": 0,
        "rendered_copy_placeholder_count": 0,
        "context_placeholder_count": 0,
    })
    _PLAYER_ROUTES.append({"source_id": clean(row.get("event_id") or row.get("event_uid") or row.get("canonical_key")), "headline": base.headline_for(row, "hsd_tonight_in_the_w_a"), "requested_module_mode": "player", "effective_module_mode": "team_spotlight_fallback", **resolution})
    return image, meta


def _phase6m_near_ready(item: Dict[str, Any], assurance: Dict[str, Any]) -> bool:
    if assurance.get("asset_render_safe") != "true":
        return False
    if int(float(clean(item.get("placeholder_layer_count")) or "0")) != 0:
        return False
    if int(float(clean(item.get("zone_overflow_count")) or "0")) != 0:
        return False
    if clean(item.get("fixture_only_player_asset")).lower() == "true":
        return False
    if clean(item.get("public_copy_quality_status")) not in {"", "passed_public_copy_quality"}:
        return False
    if clean(item.get("template_id")) == "hsd_game_recap_final_score_c_story" and clean(item.get("story_cta_status")) != "passed_story_context_cta":
        return False
    return True


def _patch_manifest_item(original_make_manifest_item):
    def wrapped_make_manifest_item(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        item = original_make_manifest_item(*args, **kwargs)
        meta = kwargs.get("meta")
        if meta is None and len(args) >= 8:
            meta = args[7]
        meta = dict(meta or {})
        requested_mode = clean(meta.get("requested_module_mode") or item.get("module_mode"))
        player_route = clean(meta.get("asset_assurance_player_route"))
        player_mode = clean(meta.get("asset_assurance_player_mode"))
        item["requested_module_mode"] = requested_mode
        item["asset_assurance_player_route"] = player_route
        item["asset_assurance_player_mode"] = player_mode
        if player_route == "downgraded_player_to_non_player_team_spotlight":
            item.update({
                "module_mode": "team_spotlight_fallback",
                "player_assets_used": 0,
                "player_names": "",
                "player_asset_kind": "team_spotlight_fallback",
                "fixture_only_player_asset": "false",
                "placeholder_layer_count": 0,
                "rendered_copy_placeholder_count": 0,
                "context_placeholder_count": 0,
            })
        assurance = assurance_from_item(item)
        item.update(assurance)
        item["phase6m_effective_renderer_version"] = PHASE6M_EFFECTIVE_VERSION
        item["near_post_ready_candidate"] = "true" if _phase6m_near_ready(item, assurance) else "false"
        item["notes"] = player_route or clean(item.get("notes"))
        return item
    return wrapped_make_manifest_item


def _patch_reports() -> None:
    base = _base()
    for path in [base.MANIFEST_JSON, base.REPORT_JSON]:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
        payload.update({
            "phase6m_effective_renderer_version": PHASE6M_EFFECTIVE_VERSION,
            "phase6m_asset_assurance": True,
            "asset_assurance_version": ASSET_CORE_VERSION,
            "phase6m_input_rows_skipped_for_assets": 0,
            "asset_render_safe_rows": sum(clean(item.get("asset_render_safe")) == "true" for item in items),
            "asset_live_candidate_eligible_rows": sum(clean(item.get("asset_live_candidate_eligible")) == "true" for item in items),
            "asset_exact_rows": sum(clean(item.get("asset_release_lane")) == "exact_assets" for item in items),
            "asset_hsd_badge_review_rows": sum(clean(item.get("asset_release_lane")) == "hsd_badge_review" for item in items),
            "asset_team_spotlight_rows": sum(clean(item.get("asset_release_lane")) == "team_spotlight_review" for item in items),
            "team_asset_resolutions": list(_TEAM_RESOLUTIONS),
            "player_asset_routes": list(_PLAYER_ROUTES),
        })
        payload["near_post_ready_candidates"] = sum(clean(item.get("near_post_ready_candidate")) == "true" for item in items)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if base.REPORT_MD.exists():
        base.REPORT_MD.write_text("\n".join([
            "# HSD Template Renderer v4.8 Phase 6M", "", f"Compatibility renderer: `{VERSION}`", f"Phase 6M effective renderer: `{PHASE6M_EFFECTIVE_VERSION}`", f"Asset assurance core: `{ASSET_CORE_VERSION}`", "",
            "Every source row remains renderable when a logo or verified player image is unavailable.",
            "Missing logos use HSD team badges; missing or fixture-only players route to non-player TEAM SPOTLIGHT cards.",
            "Render-safe and live-ready remain separate. Human visual approval, production-cutover blocks, and auto-publish blocks remain active.", "",
        ]), encoding="utf-8")


def configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _TEAM_RESOLUTIONS.clear()
    _PLAYER_ROUTES.clear()
    phase6l.configure()
    base = _base()
    _ORIGINALS["draw_team_asset"] = base.draw_team_asset
    _ORIGINALS["select_player"] = phase6l._ORIGINALS.get("base_select_player", base.select_player)
    _ORIGINALS["select_player_for_final"] = base.select_player_for_final
    _ORIGINALS["render_tonight"] = base.render_tonight
    original_read_rows = phase6l._ORIGINALS.get("base_read_rows")
    if callable(original_read_rows):
        base.read_rows = original_read_rows
    base.draw_team_asset = _assured_draw_team_asset
    base.select_player = _assured_select_player
    base.select_player_for_final = _assured_select_player_for_final
    base.render_tonight = _assured_render_tonight
    for field in EXTRA_FIELDS:
        if field not in base.MANIFEST_FIELDS:
            base.MANIFEST_FIELDS.append(field)
    base.make_manifest_item = _patch_manifest_item(base.make_manifest_item)
    _CONFIGURED = True


def main(argv: Optional[List[str]] = None) -> int:
    configure()
    base = _base()
    exit_code = base.main(argv)
    phase6l._patch_reports()
    _patch_reports()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

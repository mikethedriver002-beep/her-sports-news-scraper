from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, strip_volatile_markdown_lines, write_csv, write_json, write_text


VERSION = "hsd-wnba-graphics-visual-rubric-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_graphics_visual_rubric_v1.py"
OUT_DIR_REL = Path("wnba_graphics_visual_rubric_v1")
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
REPORT_NAME = "wnba_graphics_visual_rubric.md"
CSV_NAME = "wnba_graphics_visual_rubric.csv"
README_NAME = "README.md"
MANIFEST_NAME = "manifest.json"

SOURCE_FAMILIES = [
    {
        "family_id": "current_wnba_source_led_handoff",
        "label": "Current WNBA source-led handoff",
        "relative_root": Path("render_handoff_top_packet"),
        "role": "positive_control",
    },
    {
        "family_id": "review_only_premium_social_archetypes",
        "label": "Review-only premium social archetypes",
        "relative_root": Path("review_only_premium_social_archetypes"),
        "role": "negative_control",
    },
    {
        "family_id": "jackie_young_renderer_proof_v1",
        "label": "Jackie Young renderer proof v1",
        "relative_root": Path("jackie_young_renderer_proof_v1"),
        "role": "negative_control",
    },
    {
        "family_id": "jackie_young_visual_upgrade_v2",
        "label": "Jackie Young visual upgrade v2",
        "relative_root": Path("jackie_young_visual_upgrade_v2"),
        "role": "negative_control",
    },
]

REQUIRED_MANUAL_FIELDS = [
    "packet_id",
    "headline",
    "dek",
    "visual_mode",
    "hero_asset_required",
    "template_fit_reason",
    "approval_gate",
    "active_asset_stop_go",
    "asset_requirement",
    "active_logo_readiness_status",
    "active_athlete_identity_status",
    "manual_review_packet",
    "operator_copy_target",
    "required_manual_checks",
    "allowed_manual_outcomes",
    "review_only",
    "approval_state_change",
    "publish_ready",
    "asset_downloads",
    "publishing",
]

POSITIVE_SOURCE_TERMS = [
    "photo_first_performer",
    "approved_local_athlete_photo",
    "verified player/stat context is present",
    "source-led",
    "photo-first",
    "lead with the result",
]

STAGE_MOCKUP_TERMS = [
    "stage",
    "shell",
    "boxed",
    "panel",
    "gray floor",
    "grey floor",
    "gray-panel",
    "gray panel",
]

COMPLIANCE_TERMS = [
    "review only",
    "review-only",
    "manual review",
    "human check required",
    "not publish-ready",
    "not approved",
    "quarantine",
    "operator review required",
    "do not publish",
    "do not auto-post",
]

CANONICAL_DIMENSIONS = {(1080, 1350), (1080, 1920), (1080, 1080)}
NEUTRAL_PIXEL_BAND = 18
NEUTRAL_LUMA_MIN = 36
NEUTRAL_LUMA_MAX = 230
EXCESS_COMPLIANCE_DENSITY = 0.035


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def packet_root() -> Path:
    root = run_output_dir()
    if root:
        return root if root.name == OUT_DIR_REL.name else root / OUT_DIR_REL
    return repo_root() / "outputs" / "local" / "tmp" / OUT_DIR_REL


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_csv_headers(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            return list(csv.DictReader(handle).fieldnames or [])
    except Exception:
        return []


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def iter_text_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".csv", ".json", ".txt", ".py"}
    )


def iter_image_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})


def visual_image_files(root: Path) -> list[Path]:
    review_drafts = root / "review_drafts"
    if review_drafts.exists():
        files = sorted(
            path
            for path in review_drafts.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            and "contact_sheet" not in path.name.lower()
        )
        if files:
            return files
    files = []
    for path in iter_image_files(root):
        name = path.name.lower()
        if "contact_sheet" in name or name.startswith("draft_preview"):
            continue
        files.append(path)
    return files


def collect_text_blob(root: Path) -> str:
    parts: list[str] = []
    for path in iter_text_files(root):
        parts.append(f"\n\n## {path.as_posix()}\n")
        parts.append(read_text(path))
    return "\n".join(parts)


def count_keyword_hits(text: str, terms: list[str]) -> Counter[str]:
    lowered = text.lower()
    hits: Counter[str] = Counter()
    for term in terms:
        count = lowered.count(term.lower())
        if count:
            hits[term] = count
    return hits


def sample_neutral_share(image: Image.Image) -> tuple[float, float]:
    resized = image.convert("RGB").resize((120, max(1, round(120 * image.height / image.width))))
    width, height = resized.size
    if width <= 0 or height <= 0:
        return 0.0, 0.0
    pixels = resized.load()
    total = width * height
    neutral = 0
    midtone = 0
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            avg = (r + g + b) / 3
            if (
                abs(r - g) <= NEUTRAL_PIXEL_BAND
                and abs(g - b) <= NEUTRAL_PIXEL_BAND
                and NEUTRAL_LUMA_MIN <= avg <= NEUTRAL_LUMA_MAX
            ):
                neutral += 1
                if 72 <= avg <= 210:
                    midtone += 1
    return neutral / total, midtone / total


def image_dimensions(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def image_quality_rows(root: Path) -> tuple[list[dict[str, Any]], list[tuple[int, int]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    dims: list[tuple[int, int]] = []
    image_paths = visual_image_files(root)
    if not image_paths:
        return rows, dims, {"neutral_share": 0.0, "midtone_share": 0.0}
    for image_path in image_paths:
        with Image.open(image_path) as image:
            dim = image.size
            dims.append(dim)
            neutral_share, midtone_share = sample_neutral_share(image)
            stats = ImageStat.Stat(image.convert("RGB"))
            rows.append(
                {
                    "path": image_path.as_posix(),
                    "width": dim[0],
                    "height": dim[1],
                    "aspect": f"{dim[0]}:{dim[1]}",
                    "neutral_share": round(neutral_share, 4),
                    "midtone_share": round(midtone_share, 4),
                    "mean_luma": round(sum(stats.mean) / 3, 2),
                }
            )
    aggregate = {
        "neutral_share": round(sum(row["neutral_share"] for row in rows) / len(rows), 4) if rows else 0.0,
        "midtone_share": round(sum(row["midtone_share"] for row in rows) / len(rows), 4) if rows else 0.0,
    }
    return rows, dims, aggregate


def canonical_dimensions_ok(dims: list[tuple[int, int]]) -> bool:
    return bool(dims) and all(dim in CANONICAL_DIMENSIONS for dim in dims)


def manual_field_headers(root: Path) -> set[str]:
    headers: set[str] = set()
    for path in root.rglob("*.csv"):
        headers.update(read_csv_headers(path))
    return headers


def score_family(root: Path, family: dict[str, Any]) -> dict[str, Any]:
    text_blob = collect_text_blob(root)
    text_lower = text_blob.lower()
    image_rows, dims, image_stats = image_quality_rows(root)
    headers = manual_field_headers(root)

    positive_hits = count_keyword_hits(text_lower, POSITIVE_SOURCE_TERMS)
    stage_hits = count_keyword_hits(text_lower, STAGE_MOCKUP_TERMS)
    compliance_hits = count_keyword_hits(text_lower, COMPLIANCE_TERMS)

    dimension_ok = canonical_dimensions_ok(dims)
    manual_missing = [field for field in REQUIRED_MANUAL_FIELDS if field not in headers]
    manual_ok = not manual_missing
    source_led_ok = bool(positive_hits) and "review-only-premium-social-archetypes" not in text_lower
    stage_mockup_risk = bool(stage_hits) or image_stats["neutral_share"] >= 0.22 or image_stats["midtone_share"] >= 0.18
    compliance_hit_count = sum(compliance_hits.values())
    compliance_density = compliance_hit_count / max(len(text_lower.split()), 1)

    if not dimension_ok:
        overall = "reject"
        decision_reason = "dimension_mismatch"
    elif not manual_ok:
        overall = "reject"
        decision_reason = "missing_manual_fields"
    elif not source_led_ok:
        overall = "reject"
        decision_reason = "not_source_led"
    elif family["family_id"] != "current_wnba_source_led_handoff" and stage_mockup_risk:
        overall = "reject"
        decision_reason = "stage_mockup_risk"
    elif compliance_density >= EXCESS_COMPLIANCE_DENSITY:
        overall = "flag"
        decision_reason = "excess_compliance_text"
    else:
        overall = "pass"
        decision_reason = "meets_rubric"

    notes = []
    if dims:
        notes.append("dimensions=" + ",".join(f"{w}x{h}" for w, h in dims))
    if positive_hits:
        notes.append("source_led_hits=" + ",".join(sorted(positive_hits.keys())))
    if stage_hits:
        notes.append("stage_mockup_hits=" + ",".join(sorted(stage_hits.keys())))
    if compliance_hits:
        notes.append("compliance_hits=" + ",".join(sorted(compliance_hits.keys())))
    if manual_missing:
        notes.append("missing_manual_fields=" + ",".join(manual_missing))
    if image_stats["neutral_share"]:
        notes.append(f"avg_neutral_share={image_stats['neutral_share']:.3f}")

    return {
        "family_id": family["family_id"],
        "label": family["label"],
        "role": family["role"],
        "root": root.as_posix(),
        "present": root.exists(),
        "image_count": len(image_rows),
        "dimension_ok": dimension_ok,
        "manual_fields_ok": manual_ok,
        "source_led_ok": source_led_ok,
        "stage_mockup_risk": stage_mockup_risk,
        "compliance_hit_count": compliance_hit_count,
        "compliance_density": round(compliance_density, 4),
        "missing_manual_fields": manual_missing,
        "overall": overall,
        "decision_reason": decision_reason,
        "image_rows": image_rows,
        "notes": " | ".join(notes),
    }


def build_packet(head_commit: str | None = None) -> dict[str, Any]:
    packet_dir = packet_root()
    source_root = repo_root() / LATEST_FILES_ROOT
    rows = []
    family_results = []
    for family in SOURCE_FAMILIES:
        root = source_root / family["relative_root"]
        result = score_family(root, family)
        family_results.append(result)
        rows.append(
            {
                "family_id": result["family_id"],
                "label": result["label"],
                "role": result["role"],
                "root": result["root"],
                "present": str(result["present"]).lower(),
                "image_count": result["image_count"],
                "dimension_ok": str(result["dimension_ok"]).lower(),
                "manual_fields_ok": str(result["manual_fields_ok"]).lower(),
                "source_led_ok": str(result["source_led_ok"]).lower(),
                "stage_mockup_risk": str(result["stage_mockup_risk"]).lower(),
                "compliance_hit_count": result["compliance_hit_count"],
                "compliance_density": result["compliance_density"],
                "missing_manual_fields": ";".join(result["missing_manual_fields"]),
                "overall": result["overall"],
                "decision_reason": result["decision_reason"],
                "notes": result["notes"],
            }
        )

    passing = sum(row["overall"] == "pass" for row in rows)
    flagged = sum(row["overall"] == "flag" for row in rows)
    rejected = sum(row["overall"] == "reject" for row in rows)
    present = sum(row["present"] == "true" for row in rows)
    status = "wnba_graphics_visual_rubric_ready" if rejected or flagged or passing else "wnba_graphics_visual_rubric_missing_sources"

    current_anchor = next((result for result in family_results if result["family_id"] == "current_wnba_source_led_handoff"), {})

    manifest = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "repo_head": head_commit or "unknown",
        "status": status,
        "review_only": True,
        "asset_downloads": False,
        "source_auto_enabled": False,
        "approval_state_change": False,
        "publish_ready": False,
        "publishing": False,
        "move_files": False,
        "paid_apis": False,
        "family_count": len(rows),
        "present_family_count": present,
        "passing_family_count": passing,
        "flagged_family_count": flagged,
        "rejected_family_count": rejected,
        "required_manual_fields": REQUIRED_MANUAL_FIELDS,
        "families": rows,
        "current_anchor": {
            "family_id": current_anchor.get("family_id", ""),
            "overall": current_anchor.get("overall", ""),
            "decision_reason": current_anchor.get("decision_reason", ""),
            "dimension_ok": current_anchor.get("dimension_ok", False),
            "manual_fields_ok": current_anchor.get("manual_fields_ok", False),
            "source_led_ok": current_anchor.get("source_led_ok", False),
            "stage_mockup_risk": current_anchor.get("stage_mockup_risk", False),
            "compliance_density": current_anchor.get("compliance_density", 0.0),
        },
    }

    packet_dir.mkdir(parents=True, exist_ok=True)
    write_csv(packet_dir / CSV_NAME, rows, [
        "family_id",
        "label",
        "role",
        "root",
        "present",
        "image_count",
        "dimension_ok",
        "manual_fields_ok",
        "source_led_ok",
        "stage_mockup_risk",
        "compliance_hit_count",
        "compliance_density",
        "missing_manual_fields",
        "overall",
        "decision_reason",
        "notes",
    ])

    report = render_report(manifest, family_results)
    write_text(packet_dir / REPORT_NAME, strip_volatile_markdown_lines(report))

    readme = render_readme(manifest, family_results)
    write_text(packet_dir / README_NAME, strip_volatile_markdown_lines(readme))

    write_json(packet_dir / MANIFEST_NAME, manifest, sort_keys=True)
    return manifest


def render_readme(manifest: dict[str, Any], family_results: list[dict[str, Any]]) -> str:
    current = next((row for row in family_results if row["family_id"] == "current_wnba_source_led_handoff"), {})
    return f"""# WNBA Graphics Visual Rubric

Status: `{manifest['status']}`
Version: `{manifest['version']}`
Generated: `{manifest['generated_at_utc']}`

This is a review-only WNBA graphics rubric lane. It scores the current local WNBA handoff and older WNBA proof families against a strict bar that rejects boxed-stage, gray-floor, and gray-panel proof language.

## Reading Order

1. `wnba_graphics_visual_rubric.md`
2. `wnba_graphics_visual_rubric.csv`
3. `manifest.json`

## Current Anchor

- Family: `{current.get('label', '')}`
- Decision: `{current.get('overall', '')}`
- Reason: `{current.get('decision_reason', '')}`

## Guardrails

- review-only
- asset_downloads=false
- source_auto_enabled=false
- approval_state_change=false
- publish_ready=false
- publishing=false
- move_files=false
- paid_apis=false
"""


def render_report(manifest: dict[str, Any], family_results: list[dict[str, Any]]) -> str:
    lines = [
        "# WNBA Graphics Visual Rubric",
        "",
        f"Status: `{manifest['status']}`",
        f"Version: `{manifest['version']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "This lane is review-only. It does not create finished graphics, change approval state, move files, or publish anything.",
        "",
        "## Strict Bar",
        "",
        "- Dimensions must stay canonical for the packet family.",
        "- The image must read source-led or photo-first, not stage-led or mockup-led.",
        "- Excess compliance language is tolerated only as a warning in the control packet, not in the visual proof itself.",
        "- Boxed-stage, gray-floor, gray-panel, shell, and mockup-heavy routes are reject signals.",
        "- Required manual review fields must be present; missing operator fields are a hard reject.",
        "",
        "## Required Manual Fields",
        "",
    ]
    lines.extend(f"- `{field}`" for field in REQUIRED_MANUAL_FIELDS)
    lines.extend(["", "## Family Scores", ""])
    for result in family_results:
        lines.extend(
            [
                f"### {result['label']}",
                "",
                f"- Root: `{result['root']}`",
                f"- Role: `{result['role']}`",
                f"- Images: `{result['image_count']}`",
                f"- Decision: `{result['overall']}`",
                f"- Reason: `{result['decision_reason']}`",
                f"- Dimensions OK: `{result['dimension_ok']}`",
                f"- Manual fields OK: `{result['manual_fields_ok']}`",
                f"- Source-led OK: `{result['source_led_ok']}`",
                f"- Stage/mockup risk: `{result['stage_mockup_risk']}`",
                f"- Compliance density: `{result['compliance_density']}`",
                f"- Missing manual fields: `{', '.join(result['missing_manual_fields']) if result['missing_manual_fields'] else 'None'}`",
                f"- Notes: {result['notes'] or 'None'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Hard Reject Vocabulary",
            "",
            "- `boxed-stage`",
            "- `gray-floor`",
            "- `gray-panel`",
            "- `stage`",
            "- `mockup`",
            "- `shell`",
            "- `panel`",
            "",
            "## Control Read",
            "",
            "- The current local WNBA handoff is the best source-led anchor because it carries photo-first template cues and the operator fields needed for manual review.",
            "- The older Jackie Young proof families stay rejectable under this bar because they are proof-heavy, shell-heavy, and too close to staged mockup language.",
            "- The premium social archetypes are also rejectable because they are explicit stage compositions without the source-led performer context this lane wants.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the WNBA graphics visual rubric packet.")
    parser.add_argument("--head-commit", default="", help="Optional git commit recorded into the manifest.")
    args = parser.parse_args(argv)

    manifest = build_packet(head_commit=clean(args.head_commit) or "unknown")
    print(json.dumps({"status": manifest["status"], "family_count": manifest["family_count"], "rejected": manifest["rejected_family_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

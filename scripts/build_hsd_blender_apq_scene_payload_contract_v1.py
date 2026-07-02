from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-blender-apq-scene-payload-contract-v1-review-only"
SCHEMA_VERSION = "blender_apq_scene_payload_contract.v1"
GENERATED_BY = "scripts/build_hsd_blender_apq_scene_payload_contract_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
OUT_DIR_REL = Path("blender_apq_scene_payload_contract")

APQ_REVIEW_DIR = Path("apq001_action_photo_composition_review")
BLENDER_SMOKE_DIR = Path("blender_renderer_smoke")

APQ_MANIFEST_REL = APQ_REVIEW_DIR / "manifest.json"
APQ_REVIEW_MD_REL = APQ_REVIEW_DIR / "composition_review.md"
APQ_MANUAL_INTAKE_REL = APQ_REVIEW_DIR / "manual_composition_intake.csv"
BLENDER_SMOKE_MANIFEST_REL = BLENDER_SMOKE_DIR / "blender_renderer_smoke_manifest.json"
BLENDER_SMOKE_PAYLOAD_REL = BLENDER_SMOKE_DIR / "scene_payload.json"

OUT_MANIFEST_REL = OUT_DIR_REL / "manifest.json"
OUT_SCHEMA_REL = OUT_DIR_REL / "scene_payload_schema.json"
OUT_SAMPLE_REL = OUT_DIR_REL / "sample_apq001_scene_payload.json"
OUT_README_REL = OUT_DIR_REL / "README.md"
OUT_MANUAL_INTAKE_REL = OUT_DIR_REL / "manual_contract_review_intake.csv"

DEFAULT_APQ001_QUARANTINE_PATH = (
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/"
    "apq001_review_only_candidate.jpg"
)
QUARANTINE_ROOT = "data/assets/quarantine/review_only_candidates"
REVIEW_BURN_IN_TEXT = "REVIEW ONLY - APQ001 BLENDER CONTRACT SAMPLE"

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "candidate_state_change": False,
    "cutout_file_writes": False,
    "download_performed": False,
    "headshot_writes": False,
    "logo_writes": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "production_renderer_replacement": False,
    "renderer_behavior_change": False,
    "segmentation_writes": False,
    "source_auto_enablement": False,
    "source_fetching": False,
}

TRUE_CONTRACT_FLAGS = {
    "review_only": True,
    "artifact_only": True,
    "apq001_quarantine_only": True,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def rel_or_arg(value: str | None, fallback: Path) -> Path:
    return Path(value) if value else fallback


def input_candidates(path: Path) -> list[Path]:
    if path.is_absolute():
        return [path]
    candidates: list[Path] = []
    run_root = run_output_dir()
    if run_root:
        candidates.append(run_root / path)
    candidates.append(LATEST_FILES_ROOT / path)
    candidates.append(path)
    return candidates


def input_status(path: Path) -> dict[str, Any]:
    candidates = input_candidates(path)
    found = next((candidate for candidate in candidates if candidate.exists() and candidate.is_file()), None)
    resolved = (found or candidates[0]).resolve()
    return {
        "path": resolved.as_posix(),
        "present": found is not None,
        "candidate_paths": [candidate.resolve().as_posix() for candidate in candidates],
    }


def read_json_if_present(path: Path) -> dict[str, Any]:
    status = input_status(path)
    if not status["present"]:
        return {}
    try:
        return json.loads(Path(status["path"]).read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}


def read_text_if_present(path: Path) -> str:
    status = input_status(path)
    if not status["present"]:
        return ""
    return Path(status["path"]).read_text(encoding="utf-8", errors="replace")


def read_csv_if_present(path: Path) -> list[dict[str, str]]:
    status = input_status(path)
    if not status["present"]:
        return []
    with Path(status["path"]).open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def out_dir() -> Path:
    return output_path(OUT_DIR_REL)


def output_artifact_paths() -> dict[str, str]:
    return {
        "manifest": output_path(OUT_MANIFEST_REL).as_posix(),
        "scene_payload_schema": output_path(OUT_SCHEMA_REL).as_posix(),
        "sample_apq001_scene_payload": output_path(OUT_SAMPLE_REL).as_posix(),
        "readme": output_path(OUT_README_REL).as_posix(),
        "manual_contract_review_intake": output_path(OUT_MANUAL_INTAKE_REL).as_posix(),
    }


def const_schema(value: Any) -> dict[str, Any]:
    return {"const": value}


def false_guardrail_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": sorted(FALSE_GUARDRAILS),
        "additionalProperties": False,
        "properties": {key: const_schema(False) for key in sorted(FALSE_GUARDRAILS)},
    }


def make_scene_payload_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://hsd.local/schemas/blender_apq_scene_payload_contract_v1.schema.json",
        "title": "HSD Blender/APQ Scene Payload Contract v1",
        "description": "Review-only contract for future APQ001/action-photo-aware Blender 4:5 prototypes.",
        "type": "object",
        "required": [
            "schema_version",
            "review_only",
            "artifact_only",
            "canvas",
            "source_context",
            "action_photo_slot",
            "score_context",
            "headline_context",
            "blender_scene",
            "burn_in",
            "guardrails",
        ],
        "additionalProperties": False,
        "properties": {
            "schema_version": const_schema(SCHEMA_VERSION),
            "review_only": const_schema(True),
            "artifact_only": const_schema(True),
            "canvas": {
                "type": "object",
                "required": ["width", "height", "aspect_ratio", "output_kind", "safe_zones"],
                "additionalProperties": False,
                "properties": {
                    "width": {"type": "integer", "minimum": 1},
                    "height": {"type": "integer", "minimum": 1},
                    "aspect_ratio": const_schema("4:5"),
                    "output_kind": const_schema("review_only_blender_scene_payload"),
                    "safe_zones": {
                        "type": "object",
                        "required": ["top_px", "right_px", "bottom_px", "left_px", "notes"],
                        "additionalProperties": False,
                        "properties": {
                            "top_px": {"type": "integer", "minimum": 0},
                            "right_px": {"type": "integer", "minimum": 0},
                            "bottom_px": {"type": "integer", "minimum": 0},
                            "left_px": {"type": "integer", "minimum": 0},
                            "notes": {"type": "string"},
                        },
                    },
                },
            },
            "source_context": {
                "type": "object",
                "required": [
                    "source_family",
                    "apq_candidate_id",
                    "quarantine_only",
                    "quarantine_root",
                    "approved_input",
                    "source_artifacts",
                    "source_status",
                ],
                "additionalProperties": False,
                "properties": {
                    "source_family": const_schema("apq001_action_photo_composition_review"),
                    "apq_candidate_id": const_schema("APQ001"),
                    "quarantine_only": const_schema(True),
                    "quarantine_root": const_schema(QUARANTINE_ROOT),
                    "approved_input": const_schema(False),
                    "source_artifacts": {"type": "object"},
                    "source_status": {"type": "object"},
                },
            },
            "action_photo_slot": {
                "type": "object",
                "required": [
                    "slot_id",
                    "asset_reference_kind",
                    "quarantine_path",
                    "quarantine_reference",
                    "asset_approved",
                    "crop_notes",
                    "focus_notes",
                    "face_readability",
                    "action_readability",
                    "identity_confidence",
                    "rights_class",
                    "intended_review_only_use",
                ],
                "additionalProperties": False,
                "properties": {
                    "slot_id": const_schema("apq001_action_photo_slot"),
                    "asset_reference_kind": const_schema("quarantine_path_reference_only"),
                    "quarantine_path": {"type": "string"},
                    "quarantine_reference": const_schema("APQ001"),
                    "asset_approved": const_schema(False),
                    "crop_notes": {"type": "string"},
                    "focus_notes": {"type": "string"},
                    "face_readability": {"type": "object"},
                    "action_readability": {"type": "object"},
                    "identity_confidence": {"type": "string"},
                    "rights_class": {"type": "string"},
                    "intended_review_only_use": {"type": "string"},
                },
            },
            "score_context": {"type": "object"},
            "headline_context": {"type": "object"},
            "blender_scene": {
                "type": "object",
                "required": ["renderer_invocation", "camera", "lights", "stage_primitives", "background_treatment"],
                "additionalProperties": False,
                "properties": {
                    "renderer_invocation": const_schema("not_in_scope_contract_only"),
                    "source_smoke_payload_path": {"type": "string"},
                    "render_engine_hint": {"type": "string"},
                    "camera": {"type": "object"},
                    "lights": {"type": "array"},
                    "stage_primitives": {"type": "array"},
                    "background_treatment": {"type": "object"},
                },
            },
            "burn_in": {
                "type": "object",
                "required": ["required", "text", "placement", "production_disable_allowed"],
                "additionalProperties": False,
                "properties": {
                    "required": const_schema(True),
                    "text": {"type": "string"},
                    "placement": {"type": "string"},
                    "production_disable_allowed": const_schema(False),
                },
            },
            "guardrails": false_guardrail_schema(),
        },
    }


def source_artifacts_from_statuses(statuses: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    return {name: clean(payload.get("path")) for name, payload in statuses.items()}


def source_status_from_inputs(
    statuses: Mapping[str, Mapping[str, Any]],
    *,
    apq_manifest: Mapping[str, Any],
    blender_manifest: Mapping[str, Any],
    blender_payload: Mapping[str, Any],
    manual_rows: list[dict[str, str]],
    composition_review: str,
) -> dict[str, Any]:
    return {
        "apq_manifest_present": bool(statuses["apq_manifest"]["present"]),
        "composition_review_present": bool(statuses["composition_review"]["present"]),
        "manual_composition_intake_present": bool(statuses["manual_composition_intake"]["present"]),
        "manual_composition_intake_rows": len(manual_rows),
        "blender_smoke_manifest_present": bool(statuses["blender_smoke_manifest"]["present"]),
        "blender_smoke_payload_present": bool(statuses["blender_smoke_payload"]["present"]),
        "apq_manifest_status": clean(apq_manifest.get("status")),
        "blender_smoke_status": clean(blender_manifest.get("status")),
        "blender_smoke_payload_version": clean(blender_payload.get("version")),
        "composition_review_character_count": len(composition_review),
    }


def infer_canvas(blender_payload: Mapping[str, Any]) -> dict[str, Any]:
    render = blender_payload.get("render") if isinstance(blender_payload.get("render"), dict) else {}
    width = int(render.get("width") or 1080)
    height = int(render.get("height") or 1350)
    return {
        "width": width,
        "height": height,
        "aspect_ratio": "4:5",
        "output_kind": "review_only_blender_scene_payload",
        "safe_zones": {
            "top_px": 96,
            "right_px": 72,
            "bottom_px": 132,
            "left_px": 72,
            "notes": "Reserved for review labels, burn-in, and mobile crop tolerance.",
        },
    }


def infer_quarantine_path(apq_manifest: Mapping[str, Any]) -> str:
    candidate = clean(apq_manifest.get("candidate_path"))
    if candidate:
        normalized = candidate.replace("\\", "/")
        quarantine_marker = f"{QUARANTINE_ROOT}/"
        if quarantine_marker in normalized:
            return normalized[normalized.index(quarantine_marker) :]
        return normalized
    return DEFAULT_APQ001_QUARANTINE_PATH


def make_sample_payload(
    *,
    statuses: Mapping[str, Mapping[str, Any]],
    apq_manifest: Mapping[str, Any],
    blender_manifest: Mapping[str, Any],
    blender_payload: Mapping[str, Any],
    manual_rows: list[dict[str, str]],
    composition_review: str,
) -> dict[str, Any]:
    render = blender_payload.get("render") if isinstance(blender_payload.get("render"), dict) else {}
    camera = blender_payload.get("camera") if isinstance(blender_payload.get("camera"), dict) else {}
    lights = blender_payload.get("lights") if isinstance(blender_payload.get("lights"), list) else []
    return {
        "schema_version": SCHEMA_VERSION,
        "review_only": True,
        "artifact_only": True,
        "canvas": infer_canvas(blender_payload),
        "source_context": {
            "source_family": "apq001_action_photo_composition_review",
            "apq_candidate_id": "APQ001",
            "quarantine_only": True,
            "quarantine_root": QUARANTINE_ROOT,
            "approved_input": False,
            "source_artifacts": source_artifacts_from_statuses(statuses),
            "source_status": source_status_from_inputs(
                statuses,
                apq_manifest=apq_manifest,
                blender_manifest=blender_manifest,
                blender_payload=blender_payload,
                manual_rows=manual_rows,
                composition_review=composition_review,
            ),
        },
        "action_photo_slot": {
            "slot_id": "apq001_action_photo_slot",
            "asset_reference_kind": "quarantine_path_reference_only",
            "quarantine_path": infer_quarantine_path(apq_manifest),
            "quarantine_reference": "APQ001",
            "asset_approved": False,
            "crop_notes": "",
            "focus_notes": "",
            "face_readability": {
                "operator_assessment": "",
                "notes": "",
                "contract_field_only": True,
            },
            "action_readability": {
                "operator_assessment": "",
                "notes": "",
                "contract_field_only": True,
            },
            "identity_confidence": "",
            "rights_class": "",
            "intended_review_only_use": "",
        },
        "score_context": {
            "status": "placeholder_not_renderer_bound",
            "home_team": "",
            "away_team": "",
            "scoreline": "",
            "source_artifact_path": "",
            "notes": "Reserved for a future APQ-aware prototype; this builder does not bind live score data.",
        },
        "headline_context": {
            "status": "placeholder_not_renderer_bound",
            "headline": "",
            "dek": "",
            "context_line": "",
            "copy_review_state": "manual_only",
            "notes": "Reserved for future renderer text placement; no publishing state is implied.",
        },
        "blender_scene": {
            "renderer_invocation": "not_in_scope_contract_only",
            "source_smoke_payload_path": clean(statuses["blender_smoke_payload"].get("path")),
            "render_engine_hint": clean(render.get("engine") or blender_manifest.get("render_engine") or "CYCLES"),
            "camera": {
                "slot": "contract_placeholder",
                "location": camera.get("location") or [0.0, -7.9, 2.8],
                "target": camera.get("target") or [0.0, 0.0, -0.45],
                "lens": camera.get("lens") or 42.0,
                "notes": "Future prototype may adjust framing after manual APQ001 crop notes.",
            },
            "lights": lights
            or [
                {"light_id": "key", "type": "area", "role": "primary_subject_readability", "notes": ""},
                {"light_id": "rim", "type": "area", "role": "separate_action_photo_from_stage", "notes": ""},
            ],
            "stage_primitives": [
                {
                    "primitive_id": "action_photo_plane",
                    "type": "image_plane_slot",
                    "source": "action_photo_slot.quarantine_path",
                    "notes": "Reference-only slot; no image loading or file movement is performed by this contract.",
                },
                {
                    "primitive_id": "score_panel",
                    "type": "layout_slot",
                    "source": "score_context",
                    "notes": "Placeholder for future 4:5 score treatment.",
                },
                {
                    "primitive_id": "headline_panel",
                    "type": "layout_slot",
                    "source": "headline_context",
                    "notes": "Placeholder for future headline/dek treatment.",
                },
            ],
            "background_treatment": {
                "kind": "slot",
                "palette_reference": "",
                "treatment_notes": "",
            },
        },
        "burn_in": {
            "required": True,
            "text": REVIEW_BURN_IN_TEXT,
            "placement": "visible bottom-band or equivalent watermark on every review render",
            "production_disable_allowed": False,
        },
        "guardrails": dict(FALSE_GUARDRAILS),
    }


def validate_sample_payload(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = [
        "schema_version",
        "review_only",
        "artifact_only",
        "canvas",
        "source_context",
        "action_photo_slot",
        "score_context",
        "headline_context",
        "blender_scene",
        "burn_in",
        "guardrails",
    ]
    for key in required:
        if key not in payload:
            issues.append({"field": key, "issue": "missing_required_field"})
    if payload.get("schema_version") != SCHEMA_VERSION:
        issues.append({"field": "schema_version", "issue": "unexpected_schema_version"})
    if payload.get("review_only") is not True:
        issues.append({"field": "review_only", "issue": "must_be_true"})
    if payload.get("artifact_only") is not True:
        issues.append({"field": "artifact_only", "issue": "must_be_true"})

    canvas = payload.get("canvas") if isinstance(payload.get("canvas"), Mapping) else {}
    if canvas.get("width") != 1080 or canvas.get("height") != 1350 or canvas.get("aspect_ratio") != "4:5":
        issues.append({"field": "canvas", "issue": "must_remain_1080x1350_4x5"})

    source_context = payload.get("source_context") if isinstance(payload.get("source_context"), Mapping) else {}
    if source_context.get("quarantine_only") is not True:
        issues.append({"field": "source_context.quarantine_only", "issue": "must_be_true"})
    if source_context.get("approved_input") is not False:
        issues.append({"field": "source_context.approved_input", "issue": "must_be_false"})
    if source_context.get("quarantine_root") != QUARANTINE_ROOT:
        issues.append({"field": "source_context.quarantine_root", "issue": "unexpected_quarantine_root"})

    action_photo_slot = payload.get("action_photo_slot") if isinstance(payload.get("action_photo_slot"), Mapping) else {}
    quarantine_path = clean(action_photo_slot.get("quarantine_path"))
    if not quarantine_path.startswith(QUARANTINE_ROOT):
        issues.append({"field": "action_photo_slot.quarantine_path", "issue": "must_remain_quarantine_path"})
    if action_photo_slot.get("asset_approved") is not False:
        issues.append({"field": "action_photo_slot.asset_approved", "issue": "must_be_false"})
    for field in ["crop_notes", "focus_notes", "face_readability", "action_readability"]:
        if field not in action_photo_slot:
            issues.append({"field": f"action_photo_slot.{field}", "issue": "missing_review_field"})

    blender_scene = payload.get("blender_scene") if isinstance(payload.get("blender_scene"), Mapping) else {}
    if blender_scene.get("renderer_invocation") != "not_in_scope_contract_only":
        issues.append({"field": "blender_scene.renderer_invocation", "issue": "renderer_must_not_be_invoked"})
    for field in ["camera", "lights", "stage_primitives", "background_treatment"]:
        if field not in blender_scene:
            issues.append({"field": f"blender_scene.{field}", "issue": "missing_scene_slot"})

    burn_in = payload.get("burn_in") if isinstance(payload.get("burn_in"), Mapping) else {}
    if burn_in.get("required") is not True or "REVIEW ONLY" not in clean(burn_in.get("text")).upper():
        issues.append({"field": "burn_in", "issue": "review_burn_in_required"})
    if burn_in.get("production_disable_allowed") is not False:
        issues.append({"field": "burn_in.production_disable_allowed", "issue": "must_be_false"})

    guardrails = payload.get("guardrails") if isinstance(payload.get("guardrails"), Mapping) else {}
    for key, expected in FALSE_GUARDRAILS.items():
        if guardrails.get(key) is not expected:
            issues.append({"field": f"guardrails.{key}", "issue": "guardrail_must_remain_false"})
    return issues


def build_manual_contract_review_rows(sample: Mapping[str, Any]) -> list[dict[str, str]]:
    source_artifacts = sample["source_context"]["source_artifacts"]  # type: ignore[index]
    base = {
        "review_only": "true",
        "artifact_only": "true",
        "apq001_quarantine_only": "true",
        "asset_approved": "false",
        "approval_state_change": "false",
        "asset_downloads": "false",
        "download_performed": "false",
        "move_files": "false",
        "publish_ready": "false",
        "publishing": "false",
        "production_renderer_replacement": "false",
        "renderer_behavior_change": "false",
        "paid_apis": "false",
    }
    rows = [
        {
            "review_item_id": "BAPQSC001",
            "review_focus": "schema_shape",
            "source_artifact_path": source_artifacts["apq_manifest"],
            "question": "Does the schema include the required APQ-to-Blender handoff fields for a future 4:5 prototype?",
            "operator_notes": "",
            **base,
        },
        {
            "review_item_id": "BAPQSC002",
            "review_focus": "quarantine_reference",
            "source_artifact_path": sample["action_photo_slot"]["quarantine_path"],  # type: ignore[index]
            "question": "Does the action photo slot stay a quarantine-path reference with blank manual notes fields?",
            "operator_notes": "",
            **base,
        },
        {
            "review_item_id": "BAPQSC003",
            "review_focus": "scene_slots",
            "source_artifact_path": source_artifacts["blender_smoke_payload"],
            "question": "Are camera, light, stage, and background slots explicit enough for a later prototype lane?",
            "operator_notes": "",
            **base,
        },
        {
            "review_item_id": "BAPQSC004",
            "review_focus": "burn_in_and_guardrails",
            "source_artifact_path": output_path(OUT_SAMPLE_REL).as_posix(),
            "question": "Does every future review render implied by this contract keep a visible review-only burn-in and false guardrails?",
            "operator_notes": "",
            **base,
        },
    ]
    return rows


def render_readme(manifest: Mapping[str, Any], sample: Mapping[str, Any]) -> str:
    source_status = sample["source_context"]["source_status"]  # type: ignore[index]
    return f"""# Blender/APQ Scene Payload Contract v1

Status: `{manifest['status']}`
Schema version: `{SCHEMA_VERSION}`

This packet defines a review-only JSON payload contract between the APQ001 composition review artifacts and a future Blender 4:5 prototype lane. It is contract, schema, and sample data only.

## Artifacts

- `scene_payload_schema.json`: JSON Schema-style contract for future scene payloads.
- `sample_apq001_scene_payload.json`: sample payload using APQ001 quarantine-only references.
- `manual_contract_review_intake.csv`: manual review worksheet for the contract shape.
- `manifest.json`: artifact manifest and source input status.

## Source Inputs

- APQ manifest present: `{source_status['apq_manifest_present']}`
- APQ manual intake rows: `{source_status['manual_composition_intake_rows']}`
- Blender smoke manifest present: `{source_status['blender_smoke_manifest_present']}`
- Blender smoke payload present: `{source_status['blender_smoke_payload_present']}`

## Boundaries

- APQ001 remains a quarantine-only reference.
- The sample payload sets `action_photo_slot.asset_approved=false`.
- This builder does not call Blender, download assets, edit images, move files, change approval state, or replace production renderer behavior.
- Any later prototype must keep a visible review-only burn-in until a human operator asks for a separate lane.

## Next Use

A later APQ-aware Blender prototype can read this contract to know where canvas, source context, action-photo slot, score/headline placeholders, scene slots, burn-in, and guardrail fields belong. That later lane still has to implement actual rendering, image loading, manual crop interpretation, and visual QA.
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    out_dir().mkdir(parents=True, exist_ok=True)
    input_paths = {
        "apq_manifest": rel_or_arg(args.apq_manifest, APQ_MANIFEST_REL),
        "composition_review": rel_or_arg(args.composition_review, APQ_REVIEW_MD_REL),
        "manual_composition_intake": rel_or_arg(args.manual_composition_intake, APQ_MANUAL_INTAKE_REL),
        "blender_smoke_manifest": rel_or_arg(args.blender_smoke_manifest, BLENDER_SMOKE_MANIFEST_REL),
        "blender_smoke_payload": rel_or_arg(args.blender_smoke_payload, BLENDER_SMOKE_PAYLOAD_REL),
    }
    statuses = {name: input_status(path) for name, path in input_paths.items()}
    apq_manifest = read_json_if_present(input_paths["apq_manifest"])
    blender_manifest = read_json_if_present(input_paths["blender_smoke_manifest"])
    blender_payload = read_json_if_present(input_paths["blender_smoke_payload"])
    manual_rows = read_csv_if_present(input_paths["manual_composition_intake"])
    composition_review = read_text_if_present(input_paths["composition_review"])

    schema = make_scene_payload_schema()
    sample = make_sample_payload(
        statuses=statuses,
        apq_manifest=apq_manifest,
        blender_manifest=blender_manifest,
        blender_payload=blender_payload,
        manual_rows=manual_rows,
        composition_review=composition_review,
    )
    validation_issues = validate_sample_payload(sample)
    missing_source_count = sum(1 for status in statuses.values() if not status["present"])
    status = "blender_apq_scene_payload_contract_ready"
    if missing_source_count:
        status = "blender_apq_scene_payload_contract_ready_with_missing_optional_inputs"
    if validation_issues:
        status = "blender_apq_scene_payload_contract_failed_validation"

    manual_rows_out = build_manual_contract_review_rows(sample)
    write_json(output_path(OUT_SCHEMA_REL), schema, sort_keys=True)
    write_json(output_path(OUT_SAMPLE_REL), sample, sort_keys=True)
    write_csv(
        output_path(OUT_MANUAL_INTAKE_REL),
        manual_rows_out,
        [
            "review_item_id",
            "review_focus",
            "source_artifact_path",
            "question",
            "operator_notes",
            "review_only",
            "artifact_only",
            "apq001_quarantine_only",
            "asset_approved",
            "approval_state_change",
            "asset_downloads",
            "download_performed",
            "move_files",
            "publish_ready",
            "publishing",
            "production_renderer_replacement",
            "renderer_behavior_change",
            "paid_apis",
        ],
    )

    manifest = {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": status,
        "output_dir": out_dir().as_posix(),
        "artifacts": output_artifact_paths(),
        "source_inputs": statuses,
        "source_missing_count": missing_source_count,
        "sample_validation_issue_count": len(validation_issues),
        "sample_validation_issues": validation_issues,
        "manual_contract_review_rows": len(manual_rows_out),
        **TRUE_CONTRACT_FLAGS,
        **FALSE_GUARDRAILS,
    }
    write_json(output_path(OUT_MANIFEST_REL), manifest, sort_keys=True)
    write_text(output_path(OUT_README_REL), render_readme(manifest, sample))
    return {
        "manifest": manifest,
        "schema": schema,
        "sample": sample,
        "manual_rows": manual_rows_out,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the review-only Blender/APQ scene payload contract v1 artifacts.")
    parser.add_argument("--apq-manifest", default=APQ_MANIFEST_REL.as_posix())
    parser.add_argument("--composition-review", default=APQ_REVIEW_MD_REL.as_posix())
    parser.add_argument("--manual-composition-intake", default=APQ_MANUAL_INTAKE_REL.as_posix())
    parser.add_argument("--blender-smoke-manifest", default=BLENDER_SMOKE_MANIFEST_REL.as_posix())
    parser.add_argument("--blender-smoke-payload", default=BLENDER_SMOKE_PAYLOAD_REL.as_posix())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    result = build_payload(parse_args(argv))
    manifest = result["manifest"]
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "source_missing_count": manifest["source_missing_count"],
                "sample_validation_issue_count": manifest["sample_validation_issue_count"],
                "output_dir": manifest["output_dir"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if manifest["sample_validation_issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

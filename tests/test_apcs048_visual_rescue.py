from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_apcs048_visual_rescue_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_apcs048_visual_rescue_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_source(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (926, 695), (18, 22, 30))
    draw = ImageDraw.Draw(image)
    draw.rectangle((360, 110, 680, 640), fill=(204, 168, 84))
    draw.ellipse((430, 80, 560, 210), fill=(122, 74, 54))
    draw.rectangle((0, 0, 925, 150), fill=(236, 216, 90))
    draw.rectangle((40, 420, 260, 690), fill=(210, 64, 72))
    image.save(path, "PNG")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_visual_rescue_specs_abandon_boxed_stage_route() -> None:
    module = load_module()
    specs = module.build_variant_specs()

    assert len(specs) == 6
    assert [spec["variant_id"] for spec in specs] == [
        "rescue_01_gold_confetti_hero",
        "rescue_02_score_window_right",
        "rescue_03_medal_closeup_cover",
        "rescue_04_motion_stack_feature",
        "rescue_05_clean_news_cover",
        "rescue_06_black_gold_result_poster",
    ]
    assert all(spec["source_use"] for spec in specs)
    assert all("stage" not in spec["visual_direction"].lower() for spec in specs)
    assert all("grid" not in spec["visual_direction"].lower() for spec in specs)
    spec_text = json.dumps(specs)
    assert "ATLANTA UNITED" not in spec_text
    assert "ATLANTA" not in spec_text
    assert "Athletes Unlimited" not in spec_text
    assert "ATHLETES UNLIMITED" in spec_text
    assert specs[0]["carry_forward_recommendation"] == "carry_forward_first"
    assert specs[1]["carry_forward_recommendation"] == "carry_forward_second"


def test_resolve_source_image_prefers_repo_local_quarantine_candidate(tmp_path: Path) -> None:
    module = load_module()
    source = (
        tmp_path
        / "repo"
        / "data"
        / "assets"
        / "quarantine"
        / "review_only_candidates"
        / "action_photo_candidates"
        / "manual_decision_batch"
        / "au_volleyball_jordan_thompson"
        / "apcs048_operator_review.png"
    )
    write_source(source)

    resolved = module.resolve_source_image(None, tmp_path / "repo")

    assert resolved == source.resolve()


def test_resolve_source_image_allows_explicit_external_worktree_source(tmp_path: Path) -> None:
    module = load_module()
    explicit = (
        tmp_path
        / "external-worktree"
        / "her-sports-news-scraper"
        / "data"
        / "assets"
        / "quarantine"
        / "review_only_candidates"
        / "action_photo_candidates"
        / "manual_decision_batch"
        / "au_volleyball_jordan_thompson"
        / "apcs048_operator_review.png"
    )
    write_source(explicit)

    resolved = module.resolve_source_image(str(explicit), tmp_path / "repo")

    assert resolved == explicit.resolve()


def test_resolve_source_image_requires_explicit_path_when_repo_local_missing(tmp_path: Path) -> None:
    module = load_module()

    try:
        module.resolve_source_image(None, tmp_path / "repo")
    except FileNotFoundError as exc:
        assert "No repo-local APCS048 quarantine source/reference was found" in str(exc)
        assert "Pass --source-image explicitly" in str(exc)
        assert "data/assets/quarantine/review_only_candidates" in str(exc)
    else:
        raise AssertionError("resolve_source_image should require explicit external source when repo-local source is missing")


def test_build_packet_writes_six_review_only_source_led_variants(tmp_path: Path) -> None:
    module = load_module()
    source = (
        tmp_path
        / "other-worktree"
        / "her-sports-news-scraper"
        / "data"
        / "assets"
        / "quarantine"
        / "review_only_candidates"
        / "action_photo_candidates"
        / "manual_decision_batch"
        / "au_volleyball_jordan_thompson"
        / "apcs048_operator_review.png"
    )
    output_dir = tmp_path / "outputs" / "local" / "tmp" / "apcs048_visual_rescue_v1"
    write_source(source)

    manifest = module.build_packet(source_image=source, output_dir=output_dir, head_commit="abc123")

    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    rubric = json.loads((output_dir / "visual_rubric.json").read_text(encoding="utf-8"))
    report = (output_dir / "visual_report.md").read_text(encoding="utf-8")
    rows = read_csv(output_dir / "manual_visual_review_intake.csv")

    assert manifest["status"] == "apcs048_visual_rescue_ready"
    assert manifest_json["version"] == "hsd-apcs048-visual-rescue-v1-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["source_image_present"] is True
    assert manifest_json["source_dimensions"] == [926, 695]
    assert manifest_json["variant_count"] == 6
    assert manifest_json["failed_prior_route_verdict"] == "fail_do_not_polish"
    assert manifest_json["strongest_carry_forward_variant"] == "rescue_01_gold_confetti_hero"
    assert manifest_json["score_template_variant"] == "rescue_02_score_window_right"
    assert manifest_json["review_only"] is True
    assert manifest_json["quarantine_review_lock"] is True
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["download_performed"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert manifest_json["publishing"] is False
    assert manifest_json["paid_apis"] is False
    assert manifest_json["source_auto_enabled"] is False
    assert manifest_json["source_fetching"] is False

    for row in manifest_json["variant_rows"]:
        path = Path(row["output_png_path"])
        assert path.exists()
        assert row["dimensions"] == [1080, 1350]
        assert Image.open(path).size == (1080, 1350)
        assert row["review_only"] is True
        assert "source" in row["source_use"]

    assert Image.open(output_dir / "contact_sheet.png").size == (1680, 2140)
    assert len(rows) == 6
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert all(row["approval_state_change"] == "false" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["publishing"] == "false" for row in rows)

    assert rubric["failed_route"]["verdict"] == "fail_do_not_polish"
    assert rubric["best_candidate"] == "rescue_01_gold_confetti_hero"
    assert "boxed 3D stage" in report
    assert "Do not polish that direction" in report
    assert "approval marker files written=false" in report


def test_build_packet_blocks_when_source_missing(tmp_path: Path) -> None:
    module = load_module()

    try:
        module.build_packet(source_image=tmp_path / "missing.png", output_dir=tmp_path / "out")
    except FileNotFoundError as exc:
        assert "APCS048 source/reference is inaccessible" in str(exc)
    else:
        raise AssertionError("build_packet should stop when the APCS048 source/reference is inaccessible")

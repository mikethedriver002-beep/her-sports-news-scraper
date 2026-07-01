from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_apq001_quarantine_4x5_render_sandbox_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_apq001_quarantine_4x5_render_sandbox_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_source_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1440, 1800), (18, 24, 34))
    draw = ImageDraw.Draw(image)
    for y in range(0, image.height, 60):
        tone = 22 + (y // 60) * 3
        draw.rectangle((0, y, image.width, y + 59), fill=(tone, tone + 14, tone + 28))
    draw.ellipse((290, 230, 1120, 1540), fill=(214, 132, 46))
    draw.ellipse((420, 310, 1000, 1360), fill=(54, 88, 132))
    draw.rectangle((80, 1380, 1360, 1710), fill=(12, 18, 24))
    draw.text((96, 1410), "APQ001", fill=(255, 255, 255))
    image.save(path)


def create_reference_render(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    reference = Image.new("RGB", (1080, 1350), (24, 30, 42))
    ImageDraw.Draw(reference).text((48, 48), "REFERENCE", fill=(240, 240, 240))
    reference.save(path)


def test_builds_apq001_quarantine_4x5_render_sandbox(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()

    source_path = run_dir / module.SOURCE_CANDIDATE_REL
    reference_path = run_dir / module.REFERENCE_RENDER_REL
    create_source_image(source_path)
    create_reference_render(reference_path)
    source_hash_before = sha256_file(source_path)

    assert module.main([]) == 0

    out = run_dir / "apq001_quarantine_4x5_render_sandbox"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    report = (out / "report.md").read_text(encoding="utf-8")
    image = Image.open(out / "prototype_ig_feed_4x5.png")
    source = Image.open(source_path)
    diff = ImageChops.difference(source.resize(image.size), image.convert("RGB"))

    assert manifest["version"] == "hsd-apq001-quarantine-4x5-render-sandbox-v1-review-only"
    assert manifest["status"] == "apq001_quarantine_4x5_render_sandbox_ready"
    assert manifest["handoff_status"] == "quarantine_review_lock"
    assert manifest["burn_in_label"] == "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER"
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["image_edits"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["new_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["headshot_writes"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["move_files"] is False
    assert manifest["auto_publish"] is False
    assert manifest["source_candidate_present"] is True
    assert manifest["source_candidate_readable"] is True
    assert manifest["reference_render_present"] is True
    assert manifest["source_candidate_sha256"] == source_hash_before
    assert tuple(manifest["render_size"]) == (1080, 1350)
    assert manifest["validation_issue_count"] == 0
    assert manifest["validation_issue"] == ""
    assert manifest["png_metadata_keys"] == [
        "artifact_only",
        "asset_downloads",
        "burn_in_label",
        "handoff_status",
        "image_edits",
        "move_files",
        "publish_ready",
        "publishing",
        "review_only",
        "version",
    ]
    assert image.size == (1080, 1350)
    assert image.info["burn_in_label"] == "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER"
    assert image.info["handoff_status"] == "quarantine_review_lock"
    assert image.info["review_only"] == "true"
    assert image.info["artifact_only"] == "true"
    assert image.info["image_edits"] == "false"
    assert image.info["publish_ready"] == "false"
    assert image.info["publishing"] == "false"
    assert diff.getbbox() is not None
    assert sha256_file(source_path) == source_hash_before
    assert "Visible burn-in watermark" in report
    assert "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER" in report
    assert "open score typography" in report.lower()
    assert "middle dots" in report.lower()


def test_reports_missing_apq001_source_without_fake_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()

    assert module.main([]) == 1

    out = run_dir / "apq001_quarantine_4x5_render_sandbox"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    report = (out / "report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "apq001_quarantine_4x5_render_sandbox_blocked_missing_source"
    assert manifest["source_candidate_present"] is False
    assert manifest["source_candidate_readable"] is False
    assert manifest["validation_issue"] == "missing_source"
    assert manifest["validation_issue_count"] == 1
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["image_edits"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["move_files"] is False
    assert "Required source candidate" in report
    assert module.SOURCE_CANDIDATE_REL.as_posix() in report
    assert "exact missing file path" in report.lower()

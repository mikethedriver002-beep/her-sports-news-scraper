from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_research_bundle_v1.py"
ACTION_PHOTO_ROOT = Path("data/asset_registry/action_photo_candidates")


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_research_bundle_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_required_artifacts(run_dir: Path, module) -> None:
    for raw_path in module.expected_artifact_paths():
        path = run_dir / raw_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text(
                json.dumps(
                    {
                        "status": "ready",
                        "review_only": True,
                        "artifact_only": True,
                        "asset_downloads": False,
                        "email_sending": False,
                        "approval_state_change": False,
                        "publish_ready": False,
                    }
                ),
                encoding="utf-8",
            )
        elif path.suffix == ".csv":
            path.write_text("id,download_approved,review_only,publish_ready\nAP001,no,true,false\n", encoding="utf-8")
        else:
            path.write_text("# Review-only action-photo artifact\n\nNo sending, downloads, approvals, or publishing.\n", encoding="utf-8")


def test_builds_exact_review_only_bundle_and_optional_zip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_required_artifacts(run_dir, module)

    assert module.main(["--bundle-name", "packet-check", "--head-commit", "abc123", "--zip"]) == 0

    bundle_dir = run_dir / "action_photo_external_research_bundles" / "packet-check"
    manifest = json.loads((bundle_dir / "packet_manifest.json").read_text(encoding="utf-8"))
    latest = json.loads((run_dir / "action_photo_external_research_bundle_latest.json").read_text(encoding="utf-8"))
    readme = (bundle_dir / "README.md").read_text(encoding="utf-8")
    zip_path = bundle_dir.with_suffix(".zip")

    assert manifest["version"] == "hsd-action-photo-research-bundle-v1-review-only"
    assert manifest["status"] == "action_photo_external_research_bundle_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["included_file_count"] == len(module.expected_artifact_paths())
    assert manifest["zip_created"] is True
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["paid_apis"] is False
    assert manifest["external_network"] is False
    assert manifest["source_fetching"] is False
    assert manifest["source_auto_enablement"] is False
    assert manifest["automatic_downloads"] is False
    assert manifest["email_sending"] is False
    assert manifest["gmail_payload_created"] is False
    assert manifest["auto_approval"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["headshot_writes"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert latest["zip_path"] == str(zip_path)
    assert "creates no Gmail payload" in readme
    assert "No files from approved asset folders or publish-ready lanes." in readme

    included_paths = [item["path"] for item in manifest["included_files"]]
    assert included_paths == module.expected_artifact_paths()
    assert all(path.startswith(ACTION_PHOTO_ROOT.as_posix()) for path in included_paths)
    assert all("approved/" not in path.lower() for path in included_paths)
    assert all("publish_ready" not in path.lower() for path in included_paths)

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert "README.md" in names
    assert "packet_manifest.json" in names
    for raw_path in module.expected_artifact_paths():
        assert f"files/{raw_path}" in names
    assert all(not name.endswith(".zip") for name in names)
    assert all("approved/" not in name.lower() for name in names)


def test_bundle_rejects_files_outside_review_only_allowlist(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_required_artifacts(run_dir, module)
    approved_path = tmp_path / "assets" / "graphics" / "v4" / "approved" / "layout_references" / "card.png"
    approved_path.parent.mkdir(parents=True)
    approved_path.write_text("not allowed", encoding="utf-8")

    try:
        module.resolve_review_only_artifact(
            "assets/graphics/v4/approved/layout_references/card.png",
            tmp_path,
        )
    except ValueError as exc:
        assert "artifact_not_in_action_photo_review_only_allowlist" in str(exc)
    else:
        raise AssertionError("approved asset path should be rejected")

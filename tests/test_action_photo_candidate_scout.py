from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_candidate_scout_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_candidate_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_seed_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "seed_id",
            "entity_id",
            "source_page_url",
            "source_type",
            "source_label",
            "notes",
            "operator_fair_use_asserted",
            "download_approved",
            "rights_class",
            "identity_confidence",
            "intended_review_only_use",
            "quarantine_target_hint",
        ])
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def seed_row(seed_id: str, url: str, source_type: str = "official_team_gallery") -> dict[str, str]:
    return {
        "seed_id": seed_id,
        "entity_id": f"entity:{seed_id.lower()}",
        "source_page_url": url,
        "source_type": source_type,
        "source_label": "fixture",
        "notes": "fixture seed",
        "operator_fair_use_asserted": "yes",
        "download_approved": "no",
        "rights_class": "",
        "identity_confidence": "",
        "intended_review_only_use": "review_only_action_photo_candidate_scout",
        "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/operator_fill_required.jpg",
    }


def test_action_photo_candidate_scout_extracts_review_only_metadata(tmp_path: Path) -> None:
    module = load_module()
    seed_csv = tmp_path / "seed.csv"
    write_seed_csv(seed_csv, [seed_row("SCOUT001", "https://fixtures.test/story")])

    html = """
    <html>
      <head>
        <title>Player drives during WNBA game</title>
        <meta name="description" content="Action photo from a public recap page.">
        <meta name="author" content="Staff Photographer">
      </head>
      <body>
        <figure>
          <img src="/images/action-1.jpg" alt="Guard drives to the basket during the game" width="1200" height="1500">
          <figcaption>Open floor action with room on the left.</figcaption>
        </figure>
        <img src="/images/logo.png" alt="Team logo" width="120" height="120">
      </body>
    </html>
    """

    def fetcher(url: str):
        if url == "https://fixtures.test/robots.txt":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/plain"}, body=b"User-agent: *\nAllow: /\n")
        if url == "https://fixtures.test/story":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=html.encode("utf-8"))
        raise AssertionError(f"Unexpected URL: {url}")

    manifest = module.scout_packet(
        seed_path=seed_csv,
        output_dir=tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1",
        fetcher=fetcher,
        sleep_fn=lambda _: None,
    )

    out_dir = tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1"
    rows = read_csv(out_dir / "action_photo_candidate_intake.csv")
    report = (out_dir / "action_photo_candidate_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "action_photo_candidate_scout_ready"
    assert manifest["extracted_candidate_rows"] == 1
    assert manifest["validation_issue_count"] == 0
    assert len(rows) == 1
    assert rows[0]["scout_candidate_id"] == "APCS001"
    assert rows[0]["fetch_status"] == "candidate_metadata_extracted"
    assert rows[0]["candidate_image_url"] == "https://fixtures.test/images/action-1.jpg"
    assert rows[0]["candidate_photo_url"] == "https://fixtures.test/story"
    assert rows[0]["source_url"] == "https://fixtures.test/story"
    assert rows[0]["image_caption"] == "Open floor action with room on the left."
    assert rows[0]["credit_byline"] == "Staff Photographer"
    assert rows[0]["operator_fair_use_asserted"] == "yes"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[0]["four_by_five_crop_potential"] in {"likely", "possible"}
    assert "does not bulk download image files" in report
    assert "do not adjudicate fair use or rights" in report


def test_action_photo_candidate_scout_records_robots_and_paywall_skips(tmp_path: Path) -> None:
    module = load_module()
    seed_csv = tmp_path / "seed.csv"
    write_seed_csv(
        seed_csv,
        [
            seed_row("SCOUT001", "https://blocked.test/gallery"),
            seed_row("SCOUT002", "https://paywall.test/story", source_type="reputable_newsroom_gallery"),
        ],
    )

    def fetcher(url: str):
        if url == "https://blocked.test/robots.txt":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/plain"}, body=b"User-agent: *\nDisallow: /gallery\n")
        if url == "https://paywall.test/robots.txt":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/plain"}, body=b"User-agent: *\nAllow: /\n")
        if url == "https://paywall.test/story":
            return module.FetchedResponse(
                url=url,
                status=403,
                headers={"Content-Type": "text/html"},
                body=b"<html><body>Sign in to continue</body></html>",
            )
        raise AssertionError(f"Unexpected URL: {url}")

    manifest = module.scout_packet(
        seed_path=seed_csv,
        output_dir=tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1",
        fetcher=fetcher,
        sleep_fn=lambda _: None,
    )

    out_dir = tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1"
    rows = read_csv(out_dir / "action_photo_candidate_intake.csv")
    manifest_json = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["output_rows"] == 2
    assert manifest["robots_denied_rows"] == 1
    assert manifest["auth_or_paywall_skipped_rows"] == 1
    assert manifest_json["status"] == "action_photo_candidate_scout_ready"
    assert rows[0]["fetch_status"] == "skipped_robots_disallow"
    assert rows[0]["candidate_image_url"] == ""
    assert rows[1]["fetch_status"] == "skipped_auth_or_paywall"
    assert rows[1]["manual_next_action"] == "Do not bypass auth or a paywall. Replace this seed with a reachable public page."

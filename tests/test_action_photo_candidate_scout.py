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


def test_action_photo_candidate_scout_filters_tracking_and_banner_like_images(tmp_path: Path) -> None:
    module = load_module()
    seed_csv = tmp_path / "seed.csv"
    write_seed_csv(seed_csv, [seed_row("SCOUT001", "https://fixtures.test/2026/story")])

    html = """
    <html>
      <head>
        <title>Player attacks the rim during a rivalry game</title>
        <meta name="description" content="Public recap with one useful action photo and several low-value assets.">
      </head>
    <body>
        <img src="/images/tracker-pixel.png" width="1" height="1" alt="tracking pixel">
        <img src="/images/campaign-banner-970x90.png" alt="campaign banner">
        <img src="/wp-content/uploads/sb-instagram-feed-images/sitewide-social-feed.webp" alt="Sitewide social feed image" width="1080" height="1350">
        <img src="/services/stat_handler.aspx?rp_id=22" alt="player card">
        <img src="/images/2024/pregame-fit-player.jpg" alt="pregame fit arrival" width="1200" height="1500">
        <img src="/images/2024/archive-drive.jpg" alt="Guard drives to the basket" width="1200" height="1500">
        <figure>
          <img src="/images/2026/action-1.jpg" alt="Forward elevates for a layup during the game" width="1200" height="1500">
          <img src="/images/2026/action-1.jpg?im=AspectCrop=(16,9),xPosition=.5,yPosition=.5" alt="Forward elevates for a layup during the game" width="1200" height="1500">
          <figcaption>Action frame with room above the player.</figcaption>
        </figure>
      </body>
    </html>
    """

    def fetcher(url: str):
        if url == "https://fixtures.test/robots.txt":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/plain"}, body=b"User-agent: *\nAllow: /\n")
        if url == "https://fixtures.test/2026/story":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=html.encode("utf-8"))
        raise AssertionError(f"Unexpected URL: {url}")

    manifest = module.scout_packet(
        seed_path=seed_csv,
        output_dir=tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1",
        fetcher=fetcher,
        sleep_fn=lambda _: None,
    )

    rows = read_csv(tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1" / "action_photo_candidate_intake.csv")

    assert manifest["extracted_candidate_rows"] == 1
    assert len(rows) == 1
    assert rows[0]["candidate_image_url"] == "https://fixtures.test/images/2026/action-1.jpg"


def test_action_photo_candidate_scout_filters_wta_lpga_navigation_and_store_badges(tmp_path: Path) -> None:
    module = load_module()
    seed_csv = tmp_path / "seed.csv"
    write_seed_csv(seed_csv, [seed_row("SCOUT001", "https://fixtures.test/2026/wta-lpga-story")])

    html = """
    <html>
      <head>
        <title>Player wins during a tennis final</title>
        <meta name="description" content="Official recap with one useful action photo and several navigation assets.">
      </head>
      <body>
        <img src="https://photoresources.wtatennis.com/photo-resources/2025/07/24/a446fa8d-49f3-41dd-9a5e-014c856e3492/WTA_Web_Quick-Links_Tiles-Scores_288x288.png?width=142&height=142" alt="WTA_Web_Quick-Links_Tiles-Scores_288x288">
        <img src="https://photoresources.wtatennis.com/photo-resources/2025/04/25/120eae50-524a-4a37-a45f-345a0b38d3eb/Corpay_400x160.png?width=200&height=80" alt="Corpay_400x160">
        <img src="https://www.lpga.com/-/media/images/replace_me/android_googleplaystore.png" alt="Android Google Play Store">
        <img src="https://photoresources.wtatennis.com/wta/photo/2026/06/06/d70766be-dc26-404a-b255-15d53dd04b24/Mirra_Andreeva_-_Roland_Garros_2026_-_Day_14-DSC_8506A.jpg" alt="Mirra Andreeva hits a forehand during the Roland Garros final" width="1200" height="1600">
      </body>
    </html>
    """

    def fetcher(url: str):
        if url == "https://fixtures.test/robots.txt":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/plain"}, body=b"User-agent: *\nAllow: /\n")
        if url == "https://fixtures.test/2026/wta-lpga-story":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=html.encode("utf-8"))
        raise AssertionError(f"Unexpected URL: {url}")

    manifest = module.scout_packet(
        seed_path=seed_csv,
        output_dir=tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1",
        fetcher=fetcher,
        sleep_fn=lambda _: None,
    )

    rows = read_csv(tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1" / "action_photo_candidate_intake.csv")

    assert manifest["extracted_candidate_rows"] == 1
    assert len(rows) == 1
    assert rows[0]["candidate_image_url"].endswith("Mirra_Andreeva_-_Roland_Garros_2026_-_Day_14-DSC_8506A.jpg")


def test_action_photo_candidate_scout_extracts_open_graph_image_metadata(tmp_path: Path) -> None:
    module = load_module()
    seed_csv = tmp_path / "seed.csv"
    write_seed_csv(seed_csv, [seed_row("SCOUT001", "https://fixtures.test/2026/pwhl-story", "official_league_recap")])

    html = """
    <html>
      <head>
        <title>Star scores overtime goal in PWHL playoff game</title>
        <meta name="description" content="Forward celebrates after a clutch playoff goal during the game.">
        <meta property="og:image" content="https://res.cloudinary.com/pwhl-low/image/upload/c_fill,g_faces:auto,h_630,w_1200/q_auto/f_jpg/20260520-mtl-ott-action?_a=DATA">
      </head>
      <body></body>
    </html>
    """

    def fetcher(url: str):
        if url == "https://fixtures.test/robots.txt":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/plain"}, body=b"User-agent: *\nAllow: /\n")
        if url == "https://fixtures.test/2026/pwhl-story":
            return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=html.encode("utf-8"))
        raise AssertionError(f"Unexpected URL: {url}")

    manifest = module.scout_packet(
        seed_path=seed_csv,
        output_dir=tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1",
        fetcher=fetcher,
        sleep_fn=lambda _: None,
    )

    rows = read_csv(tmp_path / "outputs/local/tmp/action_photo_candidate_scout_v1" / "action_photo_candidate_intake.csv")

    assert manifest["extracted_candidate_rows"] == 1
    assert rows[0]["fetch_status"] == "candidate_metadata_extracted"
    assert rows[0]["candidate_image_url"].startswith("https://res.cloudinary.com/pwhl-low/image/upload/")
    assert rows[0]["image_alt"] == "Forward celebrates after a clutch playoff goal during the game."
    assert rows[0]["source_provenance_clarity"] == "clear"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["asset_downloads"] == "false"


def test_action_photo_candidate_scout_ausl_seed_defaults_guardrails() -> None:
    module = load_module()
    seed_csv = (
        REPO
        / "data"
        / "asset_registry"
        / "action_photo_candidates"
        / "review_only_action_photo_candidate_scout_ausl_source_expansion_v1.csv"
    )

    rows = read_csv(seed_csv)

    assert rows
    with seed_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == module.SEED_FIELDS
        assert all(None not in row for row in reader)
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_league_site" for row in rows)
    assert all(row["intended_review_only_use"] == "review_only_action_photo_candidate_scout" for row in rows)


def test_action_photo_candidate_scout_wta_lpga_seed_defaults_guardrails() -> None:
    module = load_module()
    seed_csv = (
        REPO
        / "data"
        / "asset_registry"
        / "action_photo_candidates"
        / "review_only_action_photo_candidate_scout_wta_lpga_source_expansion_v1.csv"
    )

    rows = read_csv(seed_csv)

    assert len(rows) == 8
    with seed_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == module.SEED_FIELDS
        assert all(None not in row for row in reader)
    assert {row["seed_id"] for row in rows} == {f"WTALPGASCOUT{index:03d}" for index in range(1, 9)}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_league_site" for row in rows)
    assert all(row["intended_review_only_use"] == "review_only_action_photo_candidate_scout" for row in rows)
    assert all(row["source_page_url"].startswith(("https://www.wtatennis.com/", "https://www.lpga.com/")) for row in rows)


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

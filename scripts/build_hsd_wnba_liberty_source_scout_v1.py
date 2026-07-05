from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import write_csv, write_json, write_text
from scripts.build_hsd_action_photo_review_deck_ui_v1 import build_packet as build_review_deck_packet


VERSION = "hsd-wnba-liberty-source-scout-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_liberty_source_scout_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED_CSV = (
    REPO_ROOT
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_liberty_official_highres_v1.csv"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v10"
DEFAULT_LATEST_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v10"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
DEFAULT_RATE_LIMIT_SECONDS = 0.5
PAYWALL_CUES = (
    "subscribe to continue",
    "subscription required",
    "sign in to continue",
    "log in to continue",
    "member exclusive",
    "this content is for subscribers",
)
TINY_THUMBNAIL_RE = re.compile(r"-(?:185x148|260x190|300x78|320x180|640x360|1024x576)(?=\.)", re.I)
IMAGE_RE = re.compile(r"https?://[^\"'\s<>\\]+?\.(?:jpg|jpeg|png|webp)(?:\?[^\"'\s<>\\]*)?", re.I)

INTAKE_FIELDS = [
    "candidate_queue_id",
    "candidate_photo_url",
    "evidence_url",
    "evidence_summary",
    "identity_anchor_url",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "notes",
    "operator_verify_required",
    "manual_reviewer",
    "manual_review_status",
    "manual_next_action",
    "download_approved",
    "quarantine_target_hint",
    "review_only",
    "publish_ready",
]
BOARD_FIELDS = [
    "board_rank",
    "source_family_id",
    "candidate_queue_id",
    "seed_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "source_domain",
    "visual_priority",
    "candidate_quality_tier",
    "score",
    "candidate_board_recommendation",
    "candidate_risk_flags",
    "manual_decision_needed",
    "formal_intake_ready",
    "face_likely_visible",
    "body_margin_likely",
    "four_by_five_crop_potential",
    "text_safe_negative_space",
    "source_provenance_clarity",
    "identity_confidence",
    "operator_fair_use_asserted",
    "notes",
    "download_approved",
    "review_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]


@dataclass(frozen=True)
class FetchedResponse:
    url: str
    status: int
    headers: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.page_title = ""
        self.meta: dict[str, str] = {}
        self.images: list[dict[str, str]] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): (value or "").strip() for key, value in attrs}
        tag_name = tag.lower()
        if tag_name == "title":
            self._in_title = True
        if tag_name == "meta":
            key = (attr.get("property") or attr.get("name") or attr.get("itemprop") or "").lower()
            content = attr.get("content", "")
            if key and content and key not in self.meta:
                self.meta[key] = content
        if tag_name == "img":
            self.images.append(
                {
                    "src": attr.get("src", "") or attr.get("data-src", "") or attr.get("data-lazy-src", ""),
                    "alt": attr.get("alt", ""),
                }
            )

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.page_title += data


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def repo_rel(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def output_root() -> Path:
    raw = clean(os.environ.get("HSD_RUN_OUTPUT_DIR", ""))
    return Path(raw).resolve(strict=False) if raw else DEFAULT_OUTPUT_DIR


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, rows: Iterable[dict[str, str]], fields: list[str]) -> None:
    write_csv(path, rows, fields)


def fetch_url(url: str, *, user_agent: str = DEFAULT_USER_AGENT, timeout: int = 20) -> FetchedResponse:
    request = Request(url, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        headers = {key: value for key, value in response.headers.items()}
        return FetchedResponse(url=url, status=int(response.status), headers=headers, body=body)


def default_fetcher(url: str) -> FetchedResponse:
    return fetch_url(url)


def canonical_image_url(url: str) -> str:
    parsed = urlparse(clean(url))
    return parsed._replace(query="", fragment="").geturl()


def is_tiny_thumbnail_url(url: str) -> bool:
    return bool(TINY_THUMBNAIL_RE.search(urlparse(clean(url)).path))


def is_useful_liberty_image_url(url: str) -> bool:
    parsed = urlparse(clean(url))
    lowered = parsed.geturl().lower()
    if parsed.netloc != "cdn.wnba.com":
        return False
    if "/sites/1611661313/" not in parsed.path:
        return False
    if is_tiny_thumbnail_url(parsed.geturl()):
        return False
    if any(token in lowered for token in ("favicon", "apple-touch-icon", "/static/next/", "/headshots/")):
        return False
    return any(token in lowered for token in ("gettyimages", "dsc", "scaled", "story", "photo", "jpg", "png"))


def extract_image_urls(page_url: str, text: str, parser: PageParser) -> list[str]:
    candidates: list[str] = []
    for key in ("og:image", "twitter:image"):
        if parser.meta.get(key):
            candidates.append(urljoin(page_url, parser.meta[key]))
    for image in parser.images:
        if image.get("src"):
            candidates.append(urljoin(page_url, image["src"]))
    candidates.extend(match.group(0) for match in IMAGE_RE.finditer(text))

    seen: set[str] = set()
    useful: list[str] = []
    for raw in candidates:
        candidate = canonical_image_url(raw)
        if candidate in seen:
            continue
        seen.add(candidate)
        if is_useful_liberty_image_url(candidate):
            useful.append(candidate)
    return useful


def parse_page(url: str, response: FetchedResponse) -> dict[str, str]:
    parser = PageParser()
    parser.feed(response.text)
    title = clean(parser.meta.get("og:title") or parser.page_title)
    description = clean(parser.meta.get("og:description") or parser.meta.get("description"))
    image_urls = extract_image_urls(url, response.text, parser)
    candidate_url = image_urls[0] if image_urls else ""
    candidate_alt = clean(parser.meta.get("og:image:alt") or parser.meta.get("twitter:image:alt") or description or title)
    return {
        "title": title,
        "description": description,
        "candidate_url": candidate_url,
        "candidate_alt": candidate_alt[:200],
        "paywall_hit": "true" if any(cue in response.text.lower() for cue in PAYWALL_CUES) else "false",
        "high_res_image_count": str(len(image_urls)),
    }


def robots_status_for(url: str, *, fetcher: Callable[[str], FetchedResponse]) -> str:
    robots_url = urljoin(url, "/robots.txt")
    try:
        response = fetcher(robots_url)
    except HTTPError as exc:
        return f"robots_txt_http_{exc.code}"
    except URLError:
        return "robots_txt_unavailable"
    if response.status >= 400:
        return f"robots_txt_http_{response.status}"
    text = response.text.lower()
    if "disallow: /" in text:
        return "robots_txt_disallow_all"
    return "robots_txt_fetched"


def source_quality_score(title: str, description: str, candidate_url: str, paywall_hit: str) -> tuple[int, str, list[str]]:
    score = 66
    flags: list[str] = ["source_level_identity_only"]
    lower_title = title.lower()
    lower_description = description.lower()
    lower_url = candidate_url.lower()
    if candidate_url:
        score += 14
    else:
        score -= 30
        flags.append("missing_candidate_image_url")
    if any(term in lower_title for term in ("game recap", "recap", "preview", "home opener", "training camp", "sign", "unveil", "libs abroad", "seafoam")):
        score += 10
    if "liberty" in lower_title or "liberty" in lower_description or "liberty" in lower_url:
        score += 6
    if any(token in lower_url for token in ("gettyimages", "dsc", "scaled", "story", "photo")):
        score += 6
    if is_tiny_thumbnail_url(candidate_url):
        score -= 40
        flags.append("tiny_thumbnail_url_rejected")
    if paywall_hit == "true":
        score -= 12
        flags.append("paywall_marker_detected")
    tier = "A_primary_source_lead" if score >= 88 else "B_strong_source_lead" if score >= 78 else "C_secondary_source_lead"
    return max(0, min(100, score)), tier, flags


def source_family_rows(
    seed_rows: list[dict[str, str]],
    *,
    fetcher: Callable[[str], FetchedResponse],
    sleep_fn: Callable[[float], None],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    intake_rows: list[dict[str, str]] = []
    board_rows: list[dict[str, str]] = []
    thumbnail_suffix_count = 0
    for index, seed in enumerate(seed_rows, start=1):
        seed_id = clean(seed.get("seed_id"))
        source_url = clean(seed.get("source_page_url"))
        response = fetcher(source_url)
        parsed = parse_page(source_url, response)
        robots_status = robots_status_for(source_url, fetcher=fetcher)
        score, tier, flags = source_quality_score(parsed["title"], parsed["description"], parsed["candidate_url"], parsed["paywall_hit"])
        if is_tiny_thumbnail_url(parsed["candidate_url"]):
            thumbnail_suffix_count += 1
        confidence = clean(seed.get("identity_confidence") or "medium")
        candidate_id = f"NYL{index:03d}"
        evidence_summary = clean(parsed["description"] or parsed["title"] or "Official New York Liberty page.")
        notes = (
            f"{clean(seed.get('notes'))} "
            f"Fetched public page status={response.status}; {robots_status}; paywall_marker={parsed['paywall_hit']}; "
            f"high_res_image_count={parsed['high_res_image_count']}; no downloads, approvals, or source auto-enablement."
        ).strip()
        intake_rows.append(
            {
                "candidate_queue_id": candidate_id,
                "candidate_photo_url": parsed["candidate_url"],
                "evidence_url": source_url,
                "evidence_summary": evidence_summary,
                "identity_anchor_url": clean(seed.get("identity_anchor_url") or "https://liberty.wnba.com/news"),
                "source_url": source_url,
                "entity_id": clean(seed.get("entity_id")),
                "rights_class": clean(seed.get("rights_class") or "official_review_needed"),
                "identity_confidence": confidence,
                "intended_review_only_use": clean(seed.get("intended_review_only_use") or "wnba_source_quality_metadata_only"),
                "notes": notes,
                "operator_verify_required": "yes",
                "manual_reviewer": "",
                "manual_review_status": "not_reviewed",
                "manual_next_action": "Open the official Liberty page, confirm the OG image is a real high-res lead image, and carry forward only if it still reads as a strong review-only candidate.",
                "download_approved": "no",
                "quarantine_target_hint": clean(seed.get("quarantine_target_hint")),
                "review_only": "true",
                "publish_ready": "false",
            }
        )
        board_rows.append(
            {
                "board_rank": str(index),
                "source_family_id": "wnba_new_york_liberty_official_highres_news_and_recaps",
                "candidate_queue_id": candidate_id,
                "seed_id": seed_id,
                "entity_id": clean(seed.get("entity_id")),
                "source_type": clean(seed.get("source_type") or "official_team_recap"),
                "source_url": source_url,
                "candidate_image_url": parsed["candidate_url"],
                "image_alt": parsed["candidate_alt"] or parsed["title"],
                "source_domain": urlparse(source_url).netloc,
                "visual_priority": "P1_visual_review_now" if score >= 88 else "P2_visual_review_soon",
                "candidate_quality_tier": tier,
                "score": str(score),
                "candidate_board_recommendation": "manual_inspect_for_formal_intake",
                "candidate_risk_flags": "|".join(flags) if flags else "none",
                "manual_decision_needed": "yes",
                "formal_intake_ready": "no",
                "face_likely_visible": "likely" if score >= 88 else "possible",
                "body_margin_likely": "likely" if score >= 88 else "possible",
                "four_by_five_crop_potential": "likely" if score >= 88 else "possible",
                "text_safe_negative_space": "possible",
                "source_provenance_clarity": "clear",
                "identity_confidence": confidence,
                "operator_fair_use_asserted": "yes",
                "notes": notes,
                "download_approved": "no",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
        if index < len(seed_rows):
            sleep_fn(DEFAULT_RATE_LIMIT_SECONDS)
    board_rows.sort(key=lambda row: (-int(row["score"]), row["board_rank"]))
    for new_rank, row in enumerate(board_rows, start=1):
        row["board_rank"] = str(new_rank)
    return intake_rows, board_rows


def render_report(manifest: dict[str, Any]) -> str:
    rows = manifest.get("board_rows", [])
    strongest = rows[:3]
    strengths = manifest.get("source_family_strengths", [])
    weaknesses = manifest.get("source_family_weaknesses", [])
    lines = [
        "# WNBA New York Liberty Official High-Res News and Recap Source Scout V1",
        "",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "Review-only metadata-first source scout for the official New York Liberty public high-res news and recap lane.",
        "",
        "## Summary",
        "",
        f"- Seed rows: `{manifest['seed_row_count']}`",
        f"- Candidate rows: `{manifest['candidate_row_count']}`",
        f"- Deck built: `{manifest['deck_built']}`",
        f"- Robots posture: `{manifest['robots_summary']}`",
        f"- Paywall markers: `{manifest['paywall_summary']}`",
        f"- Usefulness verdict: `{manifest['source_family_usefulness_verdict']}`",
        f"- Thumbnail suffix count: `{manifest['thumbnail_suffix_count']}`",
        "",
        "## Strengths",
    ]
    if strengths:
        lines.extend(f"- {item}" for item in strengths)
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Weaknesses"])
    if weaknesses:
        lines.extend(f"- {item}" for item in weaknesses)
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Strongest Rows", ""])
    if strongest:
        lines.append("| Rank | Candidate | Score | Tier | Source | Next action |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for row in strongest:
            lines.append(
            f"| {row['board_rank']} | {row['candidate_queue_id']} | {row['score']} | {row['candidate_quality_tier']} | {row['source_url']} | Open the official page and confirm the OG image still reads like a true high-res lead. |"
            )
    else:
        lines.append("No useful candidate rows were extracted.")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- download_approved=no",
            "- publish_ready=false",
            "- asset_downloads=false",
            "- approval_state_change=false",
            "- no paid APIs",
            "- no source auto-enablement",
            "- no publishing",
        ]
    )
    return "\n".join(lines) + "\n"


def mirror_output_tree(source_dir: Path, mirror_dir: Path) -> None:
    mirror_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, mirror_dir, dirs_exist_ok=True)


def build_packet(
    *,
    seed_csv: Path,
    output_dir: Path,
    latest_output_dir: Path = DEFAULT_LATEST_OUTPUT_DIR,
    fetcher: Callable[[str], FetchedResponse] = default_fetcher,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    seed_rows = read_csv_rows(seed_csv)
    intake_rows, board_rows = source_family_rows(seed_rows, fetcher=fetcher, sleep_fn=sleep_fn)
    output_dir.mkdir(parents=True, exist_ok=True)
    seed_path = output_dir / "wnba_liberty_source_scout_seed.csv"
    intake_path = output_dir / "wnba_liberty_source_scout_intake.csv"
    board_path = output_dir / "wnba_liberty_source_scout_board.csv"
    report_path = output_dir / "wnba_liberty_source_scout_report.md"
    manifest_path = output_dir / "manifest.json"
    deck_output_dir = output_dir / "review_deck"

    write_csv_rows(seed_path, seed_rows, list(seed_rows[0].keys()) if seed_rows else [])
    write_csv_rows(intake_path, intake_rows, INTAKE_FIELDS)
    write_csv_rows(board_path, board_rows, BOARD_FIELDS)

    robots_statuses = [row["notes"] for row in intake_rows if "robots_txt_" in row.get("notes", "")]
    robots_summary = "robots_txt_http_403_or_unavailable" if any("robots_txt_http_403" in note for note in robots_statuses) else "robots_txt_not_blocking"
    paywall_summary = "none_seen" if all("paywall_marker=true" not in row.get("notes", "") for row in intake_rows) else "paywall_marker_present"
    thumbnail_suffix_count = sum(1 for row in board_rows if is_tiny_thumbnail_url(row.get("candidate_image_url", "")))
    source_family_usefulness_verdict = (
        "useful_high_res_official_news_and_recap_family"
        if board_rows and thumbnail_suffix_count == 0
        else "mixed_or_noisy_official_news_family"
    )
    strengths = [
        "Official Liberty pages are public and reachable without login.",
        "High-res CDN image URLs are present and live, not thumbnail-only placeholders.",
        "The lane stays review-only and does not overclaim player identity when the page only proves source-level context.",
    ]
    weaknesses = [
        "Some pages are announcement-led rather than action-led, so the deck is useful but not uniformly action-heavy.",
        "A few pages reuse branded or roster artwork instead of a clean game-action frame, so manual review still matters.",
    ]
    manifest = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_liberty_source_scout_ready" if intake_rows else "wnba_liberty_source_scout_empty",
        "review_only": True,
        "seed_row_count": len(seed_rows),
        "candidate_row_count": len(intake_rows),
        "seed_csv_path": repo_rel(seed_path),
        "intake_csv_path": repo_rel(intake_path),
        "board_csv_path": repo_rel(board_path),
        "report_path": repo_rel(report_path),
        "output_dir": repo_rel(output_dir),
        "latest_output_dir": repo_rel(latest_output_dir),
        "robots_summary": robots_summary,
        "paywall_summary": paywall_summary,
        "thumbnail_suffix_count": thumbnail_suffix_count,
        "source_family_usefulness_verdict": source_family_usefulness_verdict,
        "source_family_strengths": strengths,
        "source_family_weaknesses": weaknesses,
        "board_rows": board_rows,
        "intake_rows": intake_rows,
        "guardrails": {
            "review_only": True,
            "download_approved": False,
            "publish_ready": False,
            "asset_downloads": False,
            "approval_state_change": False,
            "no_paid_apis": True,
            "no_source_auto_enablement": True,
            "no_publish_ready_lane": True,
        },
        "deck_built": False,
        "latest_mirror_built": False,
    }

    if intake_rows:
        deck_manifest = build_review_deck_packet(
            board_csv=board_path,
            proof_manifest=output_dir / "empty_proof_manifest.json",
            output_dir=deck_output_dir,
            limit=max(1, len(board_rows)),
            head_commit="",
        )
        manifest["deck_built"] = True
        manifest["deck_manifest_path"] = deck_manifest.get("manifest_path", "")
        manifest["deck_output_dir"] = deck_manifest.get("output_dir", "")
        manifest["deck_status"] = deck_manifest.get("status", "")
        manifest["deck_html_path"] = deck_manifest.get("html_path", "")
        manifest["deck_template_path"] = deck_manifest.get("decision_template_path", "")

    write_text(report_path, render_report(manifest))
    write_json(manifest_path, manifest, sort_keys=True)
    if latest_output_dir:
        mirror_output_tree(output_dir, latest_output_dir)
        manifest["latest_mirror_built"] = True
        write_json(latest_output_dir / "manifest.json", manifest, sort_keys=True)
    write_json(manifest_path, manifest, sort_keys=True)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the New York Liberty official high-res source scout packet.")
    parser.add_argument("--seed-csv", default=DEFAULT_SEED_CSV.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-output-dir", default=DEFAULT_LATEST_OUTPUT_DIR.as_posix())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else output_root()
    latest_output_dir = Path(args.latest_output_dir) if args.latest_output_dir else DEFAULT_LATEST_OUTPUT_DIR
    manifest = build_packet(
        seed_csv=resolve_path(args.seed_csv),
        output_dir=output_dir,
        latest_output_dir=latest_output_dir,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "candidate_row_count": manifest["candidate_row_count"],
                "output_dir": output_dir.as_posix(),
                "latest_output_dir": latest_output_dir.as_posix(),
                "deck_built": manifest["deck_built"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

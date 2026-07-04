from __future__ import annotations

import argparse
import csv
import json
import ssl
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, strip_volatile_markdown_lines, write_csv, write_json, write_text


VERSION = "hsd-action-photo-candidate-scout-v1-review-only"
ROOT = Path("data/asset_registry/action_photo_candidates")
DEFAULT_SEED_CSV = ROOT / "review_only_action_photo_candidate_scout_seed_v1.csv"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_candidate_scout_v1")
DEFAULT_USER_AGENT = "HSD Action Photo Candidate Scout/1.0 (review-only metadata scout)"
DEFAULT_RATE_LIMIT_SECONDS = 1.0
MAX_BYTES = 2_000_000
SEED_FIELDS = [
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
]
INTAKE_FIELDS = [
    "scout_candidate_id",
    "seed_id",
    "entity_id",
    "source_type",
    "source_page_url",
    "source_url",
    "candidate_photo_url",
    "candidate_image_url",
    "image_alt",
    "image_caption",
    "image_title",
    "credit_byline",
    "source_domain",
    "discovered_at",
    "apparent_width",
    "apparent_height",
    "fetch_status",
    "robots_status",
    "page_status_code",
    "notes_evidence",
    "face_likely_visible",
    "body_margin_likely",
    "four_by_five_crop_potential",
    "text_safe_negative_space",
    "jersey_text_conflict_risk",
    "source_provenance_clarity",
    "operator_fair_use_asserted",
    "fair_use_rationale_notes",
    "transformative_use_notes",
    "news_commentary_context_notes",
    "market_substitution_risk_notes",
    "download_approved",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "quarantine_target_hint",
    "manual_review_status",
    "manual_next_action",
    "review_only",
    "publish_ready",
    "approval_state_change",
    "auto_approval",
    "auto_publish",
    "asset_downloads",
    "approved_marker_writes",
]
PAYWALL_CUES = (
    "subscribe to continue",
    "subscription required",
    "sign in to continue",
    "log in to continue",
    "create an account to continue",
    "member exclusive",
    "this content is for subscribers",
)
ACTION_TERMS = (
    "action",
    "shoot",
    "shot",
    "dribble",
    "layup",
    "jumper",
    "celebrate",
    "celebration",
    "serves",
    "serve",
    "swing",
    "pitch",
    "skate",
    "save",
    "goal",
    "match",
    "game",
    "vs",
    "during",
)
CLOSEUP_TERMS = ("headshot", "portrait", "posed", "media day", "close-up", "close up", "mugshot")
LOW_VALUE_IMAGE_TERMS = (
    "away team",
    "headshot",
    "home team",
    "icon",
    "logo",
    "portrait",
    "sponsor",
    "ad",
    "advert",
    "scorebug",
    "subscribe",
    "the feed",
    "watermark",
    "wordmark",
)
LOW_VALUE_URL_TERMS = (
    "pixel",
    "scorecardresearch",
    "sb-instagram-feed-images",
    "stat_handler",
    "banner",
    "tracking",
    "/akam/",
    "pregame-fit",
    "peakperformer",
    "quick-link",
    "quick_links",
    "wta_web_quick-links",
    "tiles-scores",
    "tiles-rankings",
    "tiles-exclusive-content",
    "tiles-tourcalendar",
    "tiles-video",
    "tiles-h2h",
    "unlocked.png",
    "finals-quick-link-tile",
    "16x9-2.png",
    "4x5-3.png",
    "400x160",
    "android_googleplaystore",
    "apple-download",
    "accessibility.png",
    "bigboard",
    "draft_27bigboard",
    "google-download",
    "google-play-badge",
    "googleplaystore",
    "appstore",
    "owen-grant",
    "replace_me",
    "midseason_roster",
    "roster_updates",
    "extension_hiatt",
    "boston%20legacy",
    "denver%20summit",
    "_next/static/media/",
    "/headshot",
    "/images/headshot",
    "stats.jpg",
    "untitled%20(300%20x%20343%20px)",
    "ty-english",
    "wordmark",
    "subscribe%20to%20the%20feed",
    "subscribe-to-the-feed",
    "artboard",
    "impact_sub_web",
    "s_po_bracket",
    "sl_poty",
)
STRIP_QUERY_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
STRIP_QUERY_MARKERS = ("im=",)
STRIP_QUERY_KEYS = {"_t", "crop", "h", "height", "q", "quality", "w", "width"}


@dataclass(frozen=True)
class FetchedResponse:
    url: str
    status: int
    headers: Mapping[str, str]
    body: bytes

    @property
    def content_type(self) -> str:
        return str(self.headers.get("Content-Type", "")).split(";", 1)[0].lower()

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class ScoutPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.page_title = ""
        self.meta_description = ""
        self.byline = ""
        self.page_captions: List[str] = []
        self.page_credits: List[str] = []
        self.images: List[Dict[str, str]] = []
        self._in_title = False
        self._capture_kind = ""
        self._capture_chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str | None]]) -> None:
        attr = {key.lower(): (value or "").strip() for key, value in attrs}
        tag_name = tag.lower()
        if tag_name == "title":
            self._in_title = True
        if tag_name == "meta":
            key = (attr.get("property") or attr.get("name") or attr.get("itemprop") or "").lower()
            content = attr.get("content", "")
            if key in {"description", "og:description", "twitter:description"} and content and not self.meta_description:
                self.meta_description = content
            if key in {"author", "parsely-author", "article:author", "dc.creator"} and content and not self.byline:
                self.byline = content
            if key in {"image", "og:image", "og:image:url", "twitter:image", "twitter:image:src"} and content:
                self.images.append(
                    {
                        "src": content,
                        "alt": self.meta_description,
                        "title": self.page_title,
                        "caption": "",
                        "credit": "",
                        "width": attr.get("width", "") or attr.get("data-width", ""),
                        "height": attr.get("height", "") or attr.get("data-height", ""),
                    }
                )
        if tag_name == "img":
            self.images.append(
                {
                    "src": attr.get("src") or attr.get("data-src") or attr.get("data-lazy-src") or "",
                    "alt": attr.get("alt", ""),
                    "title": attr.get("title", ""),
                    "caption": attr.get("data-caption", "") or attr.get("caption", ""),
                    "credit": attr.get("data-credit", "") or attr.get("credit", ""),
                    "width": attr.get("width", ""),
                    "height": attr.get("height", ""),
                }
            )
        class_name = " ".join([attr.get("class", ""), attr.get("id", "")]).lower()
        if tag_name == "figcaption" or "caption" in class_name:
            self._start_capture("caption")
        elif "byline" in class_name or "author" in class_name:
            self._start_capture("byline")
        elif "credit" in class_name:
            self._start_capture("credit")

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name == "title":
            self._in_title = False
        if self._capture_kind and tag_name in {"figcaption", "div", "span", "p"}:
            captured = " ".join(chunk for chunk in self._capture_chunks if chunk).strip()
            if captured:
                if self._capture_kind == "caption":
                    self.page_captions.append(captured)
                elif self._capture_kind == "byline" and not self.byline:
                    self.byline = captured
                elif self._capture_kind == "credit":
                    self.page_credits.append(captured)
            self._capture_kind = ""
            self._capture_chunks = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.page_title = f"{self.page_title} {text}".strip()
        if self._capture_kind:
            self._capture_chunks.append(text)

    def _start_capture(self, kind: str) -> None:
        self._capture_kind = kind
        self._capture_chunks = []


def clean(value: object) -> str:
    return str(value or "").strip()


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_http_url(url: str) -> str:
    parsed = urlparse(clean(url))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Expected public http(s) URL, received: {url}")
    return clean(url)


def load_seed_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing scout seed CSV: {path}")
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    missing_fields = [field for field in SEED_FIELDS if field not in fieldnames]
    if missing_fields:
        raise ValueError(f"Scout seed CSV is missing required columns: {', '.join(missing_fields)}")
    return [{field: clean(row.get(field)) for field in SEED_FIELDS} for row in rows]


def build_request(url: str, user_agent: str) -> Request:
    return Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )


def default_fetcher(url: str, *, user_agent: str) -> FetchedResponse:
    def fetch_once(context: ssl.SSLContext | None) -> FetchedResponse:
        try:
            with urlopen(build_request(url, user_agent), timeout=30, context=context) as response:
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise RuntimeError(f"Response exceeded {MAX_BYTES} bytes: {url}")
                headers = {key: value for key, value in response.headers.items()}
                return FetchedResponse(url=response.geturl(), status=getattr(response, "status", 200), headers=headers, body=body)
        except HTTPError as exc:
            body = exc.read(MAX_BYTES + 1)
            headers = {key: value for key, value in exc.headers.items()}
            return FetchedResponse(url=exc.geturl(), status=exc.code, headers=headers, body=body)

    try:
        return fetch_once(ssl.create_default_context())
    except URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        return fetch_once(ssl._create_unverified_context())


def same_origin_robots_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def robots_allowed(
    url: str,
    *,
    user_agent: str,
    fetcher: Callable[[str], FetchedResponse],
    cache: Dict[str, tuple[str, str]],
) -> tuple[str, str]:
    robots_url = same_origin_robots_url(url)
    if robots_url in cache:
        return cache[robots_url]
    try:
        response = fetcher(robots_url)
    except Exception as exc:
        result = ("robots_unavailable_assumed_allow", f"robots fetch failed: {exc}")
        cache[robots_url] = result
        return result
    if response.status == 404:
        result = ("robots_missing_assumed_allow", "robots.txt not present")
        cache[robots_url] = result
        return result
    if response.status >= 400:
        result = ("robots_unavailable_assumed_allow", f"robots status {response.status}")
        cache[robots_url] = result
        return result
    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    allowed = parser.can_fetch(user_agent, url)
    result = ("allowed", "robots allows fetch") if allowed else ("blocked", "robots.txt disallows this URL")
    cache[robots_url] = result
    return result


def paywall_or_auth_page(text: str, status: int) -> bool:
    if status in {401, 403}:
        return True
    lowered = text.lower()
    return any(cue in lowered for cue in PAYWALL_CUES)


def normalize_text_fragments(*parts: str) -> str:
    joined = " | ".join(part for part in parts if clean(part))
    return " ".join(joined.split())


def normalize_dimension(value: str) -> str:
    digits = "".join(ch for ch in clean(value) if ch.isdigit())
    return digits


def infer_dimensions(image: Mapping[str, str]) -> tuple[int | None, int | None]:
    width = int(image["width"]) if clean(image.get("width")).isdigit() else None
    height = int(image["height"]) if clean(image.get("height")).isdigit() else None
    if width and height:
        return width, height
    src_value = clean(image.get("src"))
    parsed = urlparse(src_value)
    query = parse_qs(parsed.query)
    query_width = next((query[key][0] for key in ("w", "width") if query.get(key) and query[key][0].isdigit()), "")
    query_height = next((query[key][0] for key in ("h", "height") if query.get(key) and query[key][0].isdigit()), "")
    if query_width and query_height:
        return int(query_width), int(query_height)
    src = src_value.lower()
    match = re.search(r"(?<!\d)(\d{2,4})x(\d{2,4})(?!\d)", src)
    if match:
        return int(match.group(1)), int(match.group(2))
    return width, height


def year_from_text(value: str) -> str:
    match = re.search(r"20\d{2}", clean(value))
    return match.group(0) if match else ""


def source_page_year(url: str) -> str:
    return year_from_text(url)


def candidate_image_year(url: str) -> str:
    parsed = urlparse(url)
    year = year_from_text(parsed.path)
    if year:
        return year
    return year_from_text(parsed.query)


def normalize_candidate_image_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path.lower().endswith(STRIP_QUERY_IMAGE_EXTENSIONS) and any(marker in parsed.query for marker in STRIP_QUERY_MARKERS):
        parsed = parsed._replace(query="", fragment="")
        return urlunparse(parsed)
    if parsed.path.lower().endswith(STRIP_QUERY_IMAGE_EXTENSIONS) and parsed.query:
        query = parse_qs(parsed.query)
        if query and set(query) <= STRIP_QUERY_KEYS:
            parsed = parsed._replace(query="", fragment="")
            return urlunparse(parsed)
    return url


def score_band(score: int) -> str:
    if score >= 2:
        return "likely"
    if score == 1:
        return "possible"
    if score == -1:
        return "unlikely"
    return "unclear"


def contains_low_value_image_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in LOW_VALUE_IMAGE_TERMS if term != "ad") or bool(re.search(r"\bad\b", lowered))


def crop_potential(width: int | None, height: int | None, text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in CLOSEUP_TERMS):
        return "unlikely"
    if width and height:
        ratio = height / width if width else 0
        longest = max(width, height)
        if ratio >= 0.8 and longest >= 900:
            return "likely"
        if ratio >= 0.55 and longest >= 700:
            return "possible"
        return "unlikely"
    return "possible" if any(term in lowered for term in ACTION_TERMS) else "unclear"


def score_candidate(image: Mapping[str, str], parser: ScoutPageParser, source_type: str) -> Dict[str, str]:
    width, height = infer_dimensions(image)
    combined = normalize_text_fragments(
        clean(image.get("alt")),
        clean(image.get("caption")),
        clean(image.get("title")),
        parser.page_title,
        parser.meta_description,
    ).lower()
    action_hits = sum(term in combined for term in ACTION_TERMS)
    closeup_hits = sum(term in combined for term in CLOSEUP_TERMS)
    face_score = 1 if combined else 0
    if action_hits:
        face_score += 1
    if closeup_hits:
        face_score -= 1
    margin_score = 0
    if width and height:
        ratio = width / height if height else 0
        if 0.75 <= ratio <= 1.8:
            margin_score += 1
        if max(width, height) >= 900:
            margin_score += 1
        if min(width, height) < 320:
            margin_score -= 1
    if closeup_hits:
        margin_score -= 2
    negative_space = "possible"
    if width and height:
        ratio = width / height if height else 0
        if ratio >= 1.2:
            negative_space = "likely"
        elif ratio < 0.8:
            negative_space = "possible"
        else:
            negative_space = "unclear"
    if closeup_hits:
        negative_space = "unlikely"
    provenance = "clear" if "official" in source_type or clean(image.get("credit")) or parser.byline else "partial"
    if "gray" in source_type:
        provenance = "weak"
    jersey_risk = "medium"
    if closeup_hits:
        jersey_risk = "high"
    elif negative_space == "likely" or score_band(margin_score) == "likely":
        jersey_risk = "low"
    return {
        "face_likely_visible": score_band(face_score),
        "body_margin_likely": score_band(margin_score),
        "four_by_five_crop_potential": crop_potential(width, height, combined),
        "text_safe_negative_space": negative_space,
        "jersey_text_conflict_risk": jersey_risk,
        "source_provenance_clarity": provenance,
    }


def likely_candidate_image(image: Mapping[str, str], *, page_year: str = "") -> bool:
    src = clean(image.get("src")).lower()
    combined = normalize_text_fragments(
        clean(image.get("alt")),
        clean(image.get("title")),
        clean(image.get("caption")),
        src,
    ).lower()
    if not src or src.startswith("data:") or src.endswith(".svg"):
        return False
    if any(term in src for term in LOW_VALUE_URL_TERMS):
        return False
    if contains_low_value_image_term(combined):
        return False
    if "pregame" in combined:
        return False
    if page_year:
        image_year = candidate_image_year(src)
        if image_year and image_year != page_year:
            return False
    width, height = infer_dimensions(image)
    if width and height and max(width, height) < 250:
        return False
    if width and height:
        ratio = max(width, height) / max(1, min(width, height))
        if ratio > 3.5:
            return False
    return True


def candidate_rows_for_seed(
    seed: Mapping[str, str],
    *,
    fetcher: Callable[[str], FetchedResponse],
    user_agent: str,
    robots_cache: Dict[str, tuple[str, str]],
    discovered_at: str,
) -> List[Dict[str, str]]:
    source_page_url = ensure_http_url(seed["source_page_url"])
    robots_status, robots_note = robots_allowed(source_page_url, user_agent=user_agent, fetcher=fetcher, cache=robots_cache)
    if robots_status == "blocked":
        return [
            build_row(
                seed,
                discovered_at=discovered_at,
                fetch_status="skipped_robots_disallow",
                robots_status=robots_status,
                page_status_code="",
                notes_evidence=robots_note,
            )
        ]
    try:
        page = fetcher(source_page_url)
    except Exception as exc:
        return [
            build_row(
                seed,
                discovered_at=discovered_at,
                fetch_status="fetch_error",
                robots_status=robots_status,
                page_status_code="",
                notes_evidence=f"Public page fetch failed without bypass attempt: {exc}",
            )
        ]
    if page.status >= 400 or paywall_or_auth_page(page.text, page.status):
        return [
            build_row(
                seed,
                discovered_at=discovered_at,
                fetch_status="skipped_auth_or_paywall" if paywall_or_auth_page(page.text, page.status) else f"http_error_{page.status}",
                robots_status=robots_status,
                page_status_code=str(page.status),
                notes_evidence="Reached a public URL but stopped after auth/paywall or HTTP failure; no bypass attempt was made.",
            )
        ]
    if page.content_type not in {"text/html", "application/xhtml+xml", ""}:
        return [
            build_row(
                seed,
                discovered_at=discovered_at,
                fetch_status="skipped_non_html",
                robots_status=robots_status,
                page_status_code=str(page.status),
                notes_evidence=f"Source page returned unsupported content type: {page.content_type or 'missing'}",
            )
        ]
    parser = ScoutPageParser()
    parser.feed(page.text)
    candidates: List[Dict[str, str]] = []
    seen_urls = set()
    page_year = source_page_year(source_page_url) or source_page_year(page.url)
    for image in parser.images:
        if not likely_candidate_image(image, page_year=page_year):
            continue
        image_url = normalize_candidate_image_url(urljoin(page.url, clean(image.get("src"))))
        if page_year:
            image_year = candidate_image_year(image_url)
            if image_year and image_year != page_year:
                continue
        if image_url in seen_urls or urlparse(image_url).scheme not in {"http", "https"}:
            continue
        seen_urls.add(image_url)
        width, height = infer_dimensions(image)
        scores = score_candidate(image, parser, clean(seed.get("source_type")))
        notes_evidence = normalize_text_fragments(
            parser.page_title,
            clean(image.get("caption")) or "no_inline_caption",
            clean(image.get("credit")) or parser.byline or (parser.page_credits[0] if parser.page_credits else ""),
            parser.meta_description,
        )
        candidates.append(
            build_row(
                seed,
                discovered_at=discovered_at,
                fetch_status="candidate_metadata_extracted",
                robots_status=robots_status,
                page_status_code=str(page.status),
                source_url=page.url,
                candidate_photo_url=page.url,
                candidate_image_url=image_url,
                image_alt=clean(image.get("alt")),
                image_caption=clean(image.get("caption")) or (parser.page_captions[0] if parser.page_captions else ""),
                image_title=clean(image.get("title")) or parser.page_title,
                credit_byline=clean(image.get("credit")) or parser.byline or (parser.page_credits[0] if parser.page_credits else ""),
                source_domain=urlparse(page.url).netloc.lower(),
                apparent_width=str(width or ""),
                apparent_height=str(height or ""),
                notes_evidence=notes_evidence[:500],
                **scores,
            )
        )
    if candidates:
        return candidates
    return [
        build_row(
            seed,
            discovered_at=discovered_at,
            fetch_status="no_candidate_images_found",
            robots_status=robots_status,
            page_status_code=str(page.status),
            source_url=page.url,
            candidate_photo_url=page.url,
            source_domain=urlparse(page.url).netloc.lower(),
            notes_evidence=normalize_text_fragments(parser.page_title, parser.meta_description) or "No qualifying action-photo candidates found in HTML metadata.",
        )
    ]


def build_row(
    seed: Mapping[str, str],
    *,
    discovered_at: str,
    fetch_status: str,
    robots_status: str,
    page_status_code: str,
    source_url: str = "",
    candidate_photo_url: str = "",
    candidate_image_url: str = "",
    image_alt: str = "",
    image_caption: str = "",
    image_title: str = "",
    credit_byline: str = "",
    source_domain: str = "",
    apparent_width: str = "",
    apparent_height: str = "",
    notes_evidence: str = "",
    face_likely_visible: str = "unclear",
    body_margin_likely: str = "unclear",
    four_by_five_crop_potential: str = "unclear",
    text_safe_negative_space: str = "unclear",
    jersey_text_conflict_risk: str = "unclear",
    source_provenance_clarity: str = "partial",
) -> Dict[str, str]:
    fair_use_asserted = clean(seed.get("operator_fair_use_asserted")) or "yes"
    quarantine_target_hint = clean(seed.get("quarantine_target_hint")) or "data/assets/quarantine/review_only_candidates/action_photo_candidates/operator_fill_required.jpg"
    return {
        "scout_candidate_id": "",
        "seed_id": clean(seed.get("seed_id")),
        "entity_id": clean(seed.get("entity_id")),
        "source_type": clean(seed.get("source_type")),
        "source_page_url": clean(seed.get("source_page_url")),
        "source_url": source_url or clean(seed.get("source_page_url")),
        "candidate_photo_url": candidate_photo_url or clean(seed.get("source_page_url")),
        "candidate_image_url": candidate_image_url,
        "image_alt": image_alt,
        "image_caption": image_caption,
        "image_title": image_title,
        "credit_byline": credit_byline,
        "source_domain": source_domain or urlparse(clean(seed.get("source_page_url"))).netloc.lower(),
        "discovered_at": discovered_at,
        "apparent_width": apparent_width,
        "apparent_height": apparent_height,
        "fetch_status": fetch_status,
        "robots_status": robots_status,
        "page_status_code": page_status_code,
        "notes_evidence": notes_evidence,
        "face_likely_visible": face_likely_visible,
        "body_margin_likely": body_margin_likely,
        "four_by_five_crop_potential": four_by_five_crop_potential,
        "text_safe_negative_space": text_safe_negative_space,
        "jersey_text_conflict_risk": jersey_text_conflict_risk,
        "source_provenance_clarity": source_provenance_clarity,
        "operator_fair_use_asserted": fair_use_asserted,
        "fair_use_rationale_notes": "Operator asserted a review-only fair-use workflow for candidate scouting. This script records metadata and does not adjudicate legal status.",
        "transformative_use_notes": "Candidate is being evaluated for possible cropped/commentary-oriented 4:5 social graphics, not auto-approved for publication.",
        "news_commentary_context_notes": "Use only as a review-only lead for potential Her Sports news or commentary visuals after human review.",
        "market_substitution_risk_notes": "This scout does not download or publish source imagery; any later reuse still needs separate human review.",
        "download_approved": clean(seed.get("download_approved")) or "no",
        "rights_class": clean(seed.get("rights_class")),
        "identity_confidence": clean(seed.get("identity_confidence")),
        "intended_review_only_use": clean(seed.get("intended_review_only_use")) or "review_only_action_photo_candidate_scout",
        "quarantine_target_hint": quarantine_target_hint,
        "manual_review_status": "not_reviewed",
        "manual_next_action": next_action(fetch_status),
        "review_only": "true",
        "publish_ready": "false",
        "approval_state_change": "none",
        "auto_approval": "false",
        "auto_publish": "false",
        "asset_downloads": "false",
        "approved_marker_writes": "false",
    }


def next_action(fetch_status: str) -> str:
    if fetch_status == "candidate_metadata_extracted":
        return "Review crop margin, face visibility, provenance, and rights notes before any later human-edited download decision."
    if fetch_status == "skipped_robots_disallow":
        return "Do not crawl this page. Replace it with a different public source page or reduce the seed list to allowed URLs."
    if fetch_status == "skipped_auth_or_paywall":
        return "Do not bypass auth or a paywall. Replace this seed with a reachable public page."
    if fetch_status == "no_candidate_images_found":
        return "Try a different public gallery, recap, or source page with larger action imagery and clearer captions."
    return "Fix the source page seed or confirm the URL manually before retrying."


def assign_candidate_ids(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    for index, row in enumerate(rows, start=1):
        row["scout_candidate_id"] = f"APCS{index:03d}"
    return rows


def validate_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen_ids = set()
    for row_number, row in enumerate(rows, start=2):
        candidate_id = clean(row.get("scout_candidate_id"))
        if not candidate_id:
            issues.append({"row": str(row_number), "field": "scout_candidate_id", "issue": "blank_candidate_id"})
        elif candidate_id in seen_ids:
            issues.append({"row": str(row_number), "field": "scout_candidate_id", "issue": "duplicate_candidate_id"})
        seen_ids.add(candidate_id)
        if clean(row.get("review_only")) != "true":
            issues.append({"row": str(row_number), "field": "review_only", "issue": "must_remain_review_only"})
        if clean(row.get("publish_ready")) != "false":
            issues.append({"row": str(row_number), "field": "publish_ready", "issue": "must_not_be_publish_ready"})
        if clean(row.get("approval_state_change")) != "none":
            issues.append({"row": str(row_number), "field": "approval_state_change", "issue": "must_not_change_approval_state"})
        if clean(row.get("download_approved")) == "yes":
            missing = [
                field
                for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use", "quarantine_target_hint"]
                if not clean(row.get(field))
            ]
            if missing:
                issues.append({"row": str(row_number), "field": "download_approved", "issue": f"download_gate_missing_{'_'.join(missing)}"})
        if clean(row.get("fetch_status")) == "candidate_metadata_extracted" and not clean(row.get("candidate_image_url")):
            issues.append({"row": str(row_number), "field": "candidate_image_url", "issue": "missing_candidate_image_url_for_extracted_row"})
    return issues


def render_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str, seed_path: Path) -> str:
    extracted_rows = [row for row in rows if clean(row.get("fetch_status")) == "candidate_metadata_extracted"]
    lines = [
        "# Review-Only Action Photo Candidate Scout Report",
        "",
        f"Generated: `{generated_at}`",
        "",
        "This scout records public-page metadata only. It respects robots.txt, avoids auth/paywall bypass, does not bulk download image files, does not approve assets, does not create `.approved` markers, and does not publish anything.",
        "",
        "## Summary",
        "",
        f"- Version: `{VERSION}`",
        f"- Seed CSV: `{seed_path.as_posix()}`",
        f"- Total output rows: `{len(rows)}`",
        f"- Extracted candidate rows: `{len(extracted_rows)}`",
        f"- Robots-denied rows: `{sum(1 for row in rows if clean(row.get('fetch_status')) == 'skipped_robots_disallow')}`",
        f"- Auth/paywall skipped rows: `{sum(1 for row in rows if clean(row.get('fetch_status')) == 'skipped_auth_or_paywall')}`",
        f"- No-candidate rows: `{sum(1 for row in rows if clean(row.get('fetch_status')) == 'no_candidate_images_found')}`",
        f"- Validation issues: `{len(issues)}`",
        "",
        "Heuristic score fields are metadata-first guesses for review triage only. They are not computer-vision judgments and they do not adjudicate fair use or rights.",
        "",
        "## Candidate Rows",
        "",
        "| ID | Entity | Source | Status | 4:5 Crop | Margin | Neg Space | Provenance | Candidate Image |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {entity_id} | {source_type} | {status} | {crop} | {margin} | {space} | {provenance} | {image} |".format(
                candidate_id=clean(row.get("scout_candidate_id")),
                entity_id=clean(row.get("entity_id")),
                source_type=clean(row.get("source_type")),
                status=clean(row.get("fetch_status")),
                crop=clean(row.get("four_by_five_crop_potential")),
                margin=clean(row.get("body_margin_likely")),
                space=clean(row.get("text_safe_negative_space")),
                provenance=clean(row.get("source_provenance_clarity")),
                image=clean(row.get("candidate_image_url")) or clean(row.get("source_page_url")),
            )
        )
    if issues:
        lines += ["", "## Validation Issues", ""]
        lines.extend(f"- row {issue['row']} `{issue['field']}`: {issue['issue']}" for issue in issues)
    return "\n".join(lines) + "\n"


def build_manifest(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str, seed_path: Path, output_dir: Path) -> Dict[str, object]:
    return {
        "version": VERSION,
        "status": "action_photo_candidate_scout_ready" if not issues else "action_photo_candidate_scout_ready_with_validation_issues",
        "generated_at": generated_at,
        "seed_csv": seed_path.as_posix(),
        "output_dir": output_dir.as_posix(),
        "output_rows": len(rows),
        "extracted_candidate_rows": sum(1 for row in rows if clean(row.get("fetch_status")) == "candidate_metadata_extracted"),
        "robots_denied_rows": sum(1 for row in rows if clean(row.get("fetch_status")) == "skipped_robots_disallow"),
        "auth_or_paywall_skipped_rows": sum(1 for row in rows if clean(row.get("fetch_status")) == "skipped_auth_or_paywall"),
        "no_candidate_rows": sum(1 for row in rows if clean(row.get("fetch_status")) == "no_candidate_images_found"),
        "validation_issue_count": len(issues),
        "csv_fields": INTAKE_FIELDS,
        "report_path": (output_dir / "action_photo_candidate_scout_report.md").as_posix(),
        "csv_path": (output_dir / "action_photo_candidate_intake.csv").as_posix(),
        "review_only": True,
        "publish_ready": False,
        "asset_downloads": False,
        "approved_marker_writes": False,
        "download_policy": {
            "default_mode": "metadata_first",
            "bulk_downloads": False,
            "single_candidate_download_requires_human_row": True,
            "quarantine_dir": "data/assets/quarantine/review_only_candidates",
        },
        "validation_issues": issues,
    }


def scout_packet(
    *,
    seed_path: Path,
    output_dir: Path,
    user_agent: str = DEFAULT_USER_AGENT,
    rate_limit_seconds: float = DEFAULT_RATE_LIMIT_SECONDS,
    fetcher: Callable[[str], FetchedResponse] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Dict[str, object]:
    rows = load_seed_rows(seed_path)
    fetched = fetcher or (lambda url: default_fetcher(url, user_agent=user_agent))
    robots_cache: Dict[str, tuple[str, str]] = {}
    generated_at = now_utc()
    output_rows: List[Dict[str, str]] = []
    for index, seed in enumerate(rows):
        if index:
            sleep_fn(rate_limit_seconds)
        output_rows.extend(
            candidate_rows_for_seed(
                seed,
                fetcher=fetched,
                user_agent=user_agent,
                robots_cache=robots_cache,
                discovered_at=generated_at,
            )
        )
    assign_candidate_ids(output_rows)
    issues = validate_rows(output_rows)
    report_path = output_dir / "action_photo_candidate_scout_report.md"
    csv_path = output_dir / "action_photo_candidate_intake.csv"
    manifest_path = output_dir / "manifest.json"
    write_csv(csv_path, output_rows, INTAKE_FIELDS)
    write_text(report_path, render_markdown(output_rows, issues, generated_at, seed_path), normalize=strip_volatile_markdown_lines)
    manifest = build_manifest(output_rows, issues, generated_at, seed_path, output_dir)
    write_json(manifest_path, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only action-photo candidate scout packet from public seed pages.")
    parser.add_argument("--seed-csv", default=str(DEFAULT_SEED_CSV), help="Manual seed CSV with public page URLs and entity IDs.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Run-scoped output directory for scout artifacts.")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="User-Agent to send while fetching public pages.")
    parser.add_argument("--rate-limit-seconds", type=float, default=DEFAULT_RATE_LIMIT_SECONDS, help="Seconds to wait between seed page fetches.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seed_path = input_path(Path(args.seed_csv))
    output_dir = output_path(Path(args.output_dir))
    scout_packet(
        seed_path=seed_path,
        output_dir=output_dir,
        user_agent=args.user_agent,
        rate_limit_seconds=max(0.0, args.rate_limit_seconds),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

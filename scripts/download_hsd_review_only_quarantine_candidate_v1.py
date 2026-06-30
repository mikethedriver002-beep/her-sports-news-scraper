from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterable, Mapping
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "hsd_review_only_asset_download_policy_v1.json"
DEFAULT_INTAKE_CSV = (
    ROOT
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_research_return_intake_v1.csv"
)
DEFAULT_OUTPUT_MANIFEST = ROOT / "outputs" / "local" / "latest" / "files" / "review_only_quarantine_download_manifest.json"
DEFAULT_OUTPUT_REPORT = ROOT / "outputs" / "local" / "latest" / "files" / "review_only_quarantine_download_report.md"
VERSION = "hsd-review-only-quarantine-downloader-v1"
MAX_HTML_BYTES = 2_000_000
MAX_IMAGE_BYTES = 20_000_000
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
IMAGE_META_KEYS = {
    "og:image",
    "og:image:url",
    "twitter:image",
    "twitter:image:src",
    "image",
}


class DownloadBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchedBytes:
    url: str
    content_type: str
    body: bytes


class ImageMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.image_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): (value or "").strip() for key, value in attrs}
        if tag.lower() == "meta":
            key = (attr.get("property") or attr.get("name") or attr.get("itemprop") or "").lower()
            content = attr.get("content", "")
            if key in IMAGE_META_KEYS and content:
                self.image_urls.append(content)
        if tag.lower() == "link":
            rel = attr.get("rel", "").lower()
            href = attr.get("href", "")
            if "image_src" in rel and href:
                self.image_urls.append(href)


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise DownloadBlocked(f"Missing intake CSV: {path}")
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def load_policy(path: Path = POLICY_PATH) -> dict[str, object]:
    if not path.exists():
        raise DownloadBlocked(f"Missing download policy config: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def find_candidate_row(rows: Iterable[Mapping[str, str]], candidate_id: str) -> Mapping[str, str]:
    wanted = clean(candidate_id).lower()
    for row in rows:
        if clean(row.get("candidate_queue_id")).lower() == wanted:
            return row
    raise DownloadBlocked(f"Candidate row not found: {candidate_id}")


def required_fields(policy: Mapping[str, object]) -> list[str]:
    fields = policy.get("required_human_intake_fields", [])
    if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
        raise DownloadBlocked("Download policy has invalid required_human_intake_fields.")
    return [*fields, "candidate_photo_url", "quarantine_target_hint"]


def validate_human_download_gate(row: Mapping[str, str], policy: Mapping[str, object]) -> None:
    gate = policy.get("download_gate", {})
    expected = "yes"
    if isinstance(gate, dict):
        expected = clean(gate.get("download_approved_value")) or expected
    if clean(row.get("download_approved")).lower() != expected.lower():
        raise DownloadBlocked("download_approved is not yes for this human intake row.")
    missing = [field for field in required_fields(policy) if not clean(row.get(field))]
    if missing:
        raise DownloadBlocked(f"Missing required quarantine download fields: {', '.join(missing)}")
    if clean(row.get("review_only")).lower() != "true":
        raise DownloadBlocked("review_only must be true.")
    if clean(row.get("publish_ready")).lower() != "false":
        raise DownloadBlocked("publish_ready must be false.")


def ensure_http_url(url: str, field_name: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise DownloadBlocked(f"{field_name} must be an http(s) URL.")
    return url


def safe_relative_path(raw_path: str) -> Path:
    normalized = clean(raw_path).replace("\\", "/").lstrip("/")
    if not normalized:
        raise DownloadBlocked("Empty quarantine target path.")
    parts = Path(normalized).parts
    if any(part in {"..", ""} for part in parts):
        raise DownloadBlocked("Quarantine target path must not contain parent traversal.")
    return Path(*parts)


def quarantine_root(policy: Mapping[str, object]) -> Path:
    root = clean(policy.get("sanctioned_quarantine_dir"))
    if not root:
        raise DownloadBlocked("Download policy is missing sanctioned_quarantine_dir.")
    return (ROOT / safe_relative_path(root)).resolve()


def validate_target_hint(row: Mapping[str, str], policy: Mapping[str, object]) -> Path:
    target_hint = (ROOT / safe_relative_path(clean(row.get("quarantine_target_hint")))).resolve()
    root = quarantine_root(policy)
    try:
        target_hint.relative_to(root)
    except ValueError as exc:
        raise DownloadBlocked("Quarantine target must stay under data/assets/quarantine/review_only_candidates.") from exc
    return target_hint


def extension_for(content_type: str, media_url: str) -> str:
    lowered = clean(content_type).split(";", 1)[0].lower()
    if lowered in IMAGE_EXTENSIONS:
        return IMAGE_EXTENSIONS[lowered]
    guessed = mimetypes.guess_extension(lowered)
    if guessed in IMAGE_EXTENSIONS.values():
        return guessed
    suffix = Path(urlparse(media_url).path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS.values():
        return suffix
    raise DownloadBlocked(f"Unsupported image content type: {content_type or 'missing'}")


def quarantine_target_path(row: Mapping[str, str], policy: Mapping[str, object], media_url: str, content_type: str) -> Path:
    target_hint = validate_target_hint(row, policy)
    ext = extension_for(content_type, media_url)
    candidate_id = re.sub(r"[^a-z0-9_-]+", "_", clean(row.get("candidate_queue_id")).lower()).strip("_")
    if not candidate_id:
        raise DownloadBlocked("Candidate id is required for quarantine filename.")
    if target_hint.name.lower().startswith("operator_fill_required"):
        return target_hint.parent / f"{candidate_id}_review_only_candidate{ext}"
    return target_hint.with_suffix(ext)


def fetch_url(url: str, *, accept: str, max_bytes: int) -> FetchedBytes:
    request = Request(
        url,
        headers={
            "User-Agent": "HSD review-only quarantine downloader/1.0",
            "Accept": accept,
        },
    )
    with urlopen(request, timeout=30) as response:
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise DownloadBlocked(f"Fetched content exceeded {max_bytes} byte limit.")
        content_type = clean(response.headers.get("Content-Type")).split(";", 1)[0].lower()
        final_url = response.geturl()
    return FetchedBytes(url=final_url, content_type=content_type, body=body)


def image_url_from_html(html_bytes: bytes, base_url: str) -> str:
    text = html_bytes.decode("utf-8", errors="replace")
    parser = ImageMetaParser()
    parser.feed(text)
    for raw_url in parser.image_urls:
        candidate = urljoin(base_url, raw_url)
        if urlparse(candidate).scheme in {"http", "https"}:
            return candidate
    raise DownloadBlocked("No OpenGraph/Twitter image URL found on candidate source page.")


def resolve_candidate_image(
    row: Mapping[str, str],
    fetcher: Callable[[str, str, int], FetchedBytes],
) -> tuple[str, FetchedBytes]:
    candidate_url = ensure_http_url(clean(row.get("candidate_photo_url")), "candidate_photo_url")
    first_fetch = fetcher(candidate_url, "text/html,image/*", MAX_HTML_BYTES)
    if first_fetch.content_type.startswith("image/"):
        return first_fetch.url, first_fetch
    if first_fetch.content_type not in {"text/html", "application/xhtml+xml", ""}:
        raise DownloadBlocked(f"candidate_photo_url is not an image or HTML page: {first_fetch.content_type}")
    media_url = image_url_from_html(first_fetch.body, first_fetch.url)
    media_fetch = fetcher(media_url, "image/*", MAX_IMAGE_BYTES)
    if not media_fetch.content_type.startswith("image/"):
        raise DownloadBlocked(f"Resolved media URL did not return image content: {media_fetch.content_type}")
    return media_fetch.url, media_fetch


def default_fetcher(url: str, accept: str, max_bytes: int) -> FetchedBytes:
    return fetch_url(url, accept=accept, max_bytes=max_bytes)


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_report(path: Path, manifest: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Review-Only Quarantine Download Report",
        "",
        f"- Version: `{manifest['version']}`",
        f"- Candidate: `{manifest['candidate_queue_id']}`",
        f"- Status: `{manifest['status']}`",
        f"- Source URL: `{manifest['source_url']}`",
        f"- Resolved image URL: `{manifest['resolved_image_url']}`",
        f"- Quarantine file: `{manifest['quarantine_path']}`",
        f"- SHA256: `{manifest['sha256']}`",
        f"- Review-only: `{manifest['review_only']}`",
        f"- Publish-ready: `{manifest['publish_ready']}`",
        f"- Approval state changed: `{manifest['approval_state_change']}`",
        f"- Approved marker writes: `{manifest['approved_marker_writes']}`",
        "",
        "This report records a quarantine-only candidate file. It does not approve the asset, does not move it into renderer folders, and does not publish anything.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def download_candidate(
    *,
    candidate_id: str,
    intake_csv: Path,
    manifest_path: Path,
    report_path: Path,
    dry_run: bool,
    overwrite: bool,
    fetcher: Callable[[str, str, int], FetchedBytes] = default_fetcher,
) -> dict[str, object]:
    policy = load_policy()
    rows = read_csv_rows(intake_csv)
    row = find_candidate_row(rows, candidate_id)
    validate_human_download_gate(row, policy)
    ensure_http_url(clean(row.get("source_url")), "source_url")
    resolved_image_url, media = resolve_candidate_image(row, fetcher)
    target = quarantine_target_path(row, policy, resolved_image_url, media.content_type)
    root = quarantine_root(policy)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise DownloadBlocked("Resolved target escaped quarantine root.") from exc
    if not dry_run and target.exists() and not overwrite:
        raise DownloadBlocked(f"Quarantine candidate already exists; use --overwrite only after manual review: {target}")
    sha256 = hashlib.sha256(media.body).hexdigest()
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(media.body)
    manifest = {
        "version": VERSION,
        "status": "dry_run_ok" if dry_run else "quarantine_candidate_downloaded_review_only",
        "candidate_queue_id": clean(row.get("candidate_queue_id")),
        "entity_id": clean(row.get("entity_id")),
        "rights_class": clean(row.get("rights_class")),
        "identity_confidence": clean(row.get("identity_confidence")),
        "intended_review_only_use": clean(row.get("intended_review_only_use")),
        "source_url": clean(row.get("source_url")),
        "resolved_image_url": resolved_image_url,
        "quarantine_path": target.relative_to(ROOT).as_posix(),
        "content_type": media.content_type,
        "byte_count": len(media.body),
        "sha256": sha256,
        "review_only": True,
        "publish_ready": False,
        "approval_state_change": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "source_fetching": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
    }
    write_json(manifest_path, manifest)
    write_report(report_path, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded HSD review-only quarantine candidate downloader.")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--intake-csv", type=Path, default=DEFAULT_INTAKE_CSV)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_OUTPUT_REPORT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = download_candidate(
            candidate_id=args.candidate_id,
            intake_csv=args.intake_csv,
            manifest_path=args.manifest,
            report_path=args.report,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
        )
    except DownloadBlocked as exc:
        print(json.dumps({"version": VERSION, "status": "blocked", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

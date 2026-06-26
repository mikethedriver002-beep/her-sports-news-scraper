from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import os
import re
import sys
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple

from hsd_run_io import output_path, write_json, write_text


VERSION = "hsd-identity-resolution-local-server-v1.0.0-manual-writeback"
INBOX_PATH = Path("operator/inbox/wnba_athlete_identity_resolution.csv")
OUT_JSON = output_path("identity_resolution_local_server.json")
OUT_MD = output_path("identity_resolution_local_server.md")

IDENTITY_RESOLUTION_FIELDS = [
    "athlete_id",
    "display_name",
    "team_id",
    "provider_player_id",
    "asset_path",
    "approved_marker_path",
    "highest_severity",
    "issue_count",
    "issue_codes",
    "audit_evidence",
    "recommended_operator_action",
    "allowed_decisions",
    "operator_decision",
    "identity_verified",
    "provider_player_id_verified",
    "approved_source_url",
    "secondary_source_url",
    "backfill_provider_player_id",
    "operator_notes",
    "operator_name",
    "reviewed_at_local",
    "issue_resolution_status",
    "copy_target",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "review_only_policy",
]

ALLOWED_DECISIONS = {
    "identity_verified_approved_for_review_renders",
    "hold_identity",
    "revise_asset",
    "backfill_provider_id_only",
}

FALSE_FIELDS = ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis"]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path.cwd().resolve()


def latest_files_dir(root: Path) -> Path:
    raw_candidates = [
        clean(os.environ.get("HSD_IDENTITY_UI_FILES_DIR")),
        clean(os.environ.get("HSD_RUN_OUTPUT_DIR")),
        (root / "outputs" / "local" / "latest" / "files").as_posix(),
    ]
    for raw in raw_candidates:
        if not raw:
            continue
        candidate = Path(raw)
        candidate = candidate if candidate.is_absolute() else root / candidate
        if (candidate / "operator_command_center.html").exists():
            return candidate.resolve()
    raise FileNotFoundError("No operator_command_center.html found. Run .\\hsd.cmd run -Mode render first.")


def resolve_child(root: Path, requested: str) -> Path | None:
    rel = requested.split("?", 1)[0].lstrip("/")
    if not rel:
        rel = "operator_command_center.html"
    if rel in {"identity-decision", "identity-decision/"}:
        rel = "operator_command_center.html"
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.exists() and candidate.is_file() else None


def read_existing_rows(path: Path) -> Tuple[List[str], int]:
    if not path.exists():
        return [], 0
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        return header, sum(1 for row in reader if any(clean(cell) for cell in row))


def validate_identity_row(row: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, str]]:
    normalized = {field: clean(row.get(field)) for field in IDENTITY_RESOLUTION_FIELDS}
    normalized["copy_target"] = INBOX_PATH.as_posix()
    normalized["approval_scope"] = "review_only_identity_resolution_for_local_draft_renders"
    normalized["review_only_policy"] = "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane"
    for field in FALSE_FIELDS:
        normalized[field] = "false"

    decision = normalized["operator_decision"]
    warnings: List[str] = []
    if decision not in ALLOWED_DECISIONS:
        warnings.append("operator_decision must be verify, hold, revise, or backfill_provider_id_only.")
    if not normalized["athlete_id"]:
        warnings.append("athlete_id is required.")
    if not normalized["operator_name"]:
        warnings.append("operator_name is required.")
    if not normalized["reviewed_at_local"]:
        warnings.append("reviewed_at_local is required.")
    if not normalized["operator_notes"]:
        warnings.append("operator_notes are required.")
    if decision == "identity_verified_approved_for_review_renders":
        if normalized["identity_verified"].lower() != "yes":
            warnings.append("Verify requires identity_verified=yes.")
        if normalized["provider_player_id_verified"].lower() != "yes" and not normalized["backfill_provider_player_id"]:
            warnings.append("Verify requires provider_player_id_verified=yes or a source-backed backfill_provider_player_id.")
        if not normalized["approved_source_url"]:
            warnings.append("Verify requires approved_source_url.")
        normalized["issue_resolution_status"] = "identity_verified"
    elif decision == "backfill_provider_id_only":
        if not normalized["backfill_provider_player_id"] and not normalized["provider_player_id"]:
            warnings.append("Backfill ID requires provider_player_id or backfill_provider_player_id.")
        if not normalized["approved_source_url"]:
            warnings.append("Backfill ID requires approved_source_url.")
        normalized["issue_resolution_status"] = "provider_id_backfill_ready_identity_still_held"
    elif decision == "revise_asset":
        normalized["issue_resolution_status"] = "needs_asset_revision"
    elif decision == "hold_identity":
        normalized["issue_resolution_status"] = "held_for_identity_review"
    return not warnings, warnings, normalized


def append_identity_row(root: Path, row: Dict[str, Any]) -> Dict[str, Any]:
    ok, warnings, normalized = validate_identity_row(row)
    if not ok:
        return {"ok": False, "status": "validation_failed", "warnings": warnings}

    inbox = (root / INBOX_PATH).resolve()
    try:
        inbox.relative_to(root)
    except ValueError:
        return {"ok": False, "status": "unsafe_inbox_path", "warnings": ["Inbox path resolved outside the repo."]}

    inbox.parent.mkdir(parents=True, exist_ok=True)
    header, before_count = read_existing_rows(inbox)
    if inbox.exists() and header and header != IDENTITY_RESOLUTION_FIELDS:
        return {
            "ok": False,
            "status": "header_mismatch",
            "warnings": ["Existing identity-resolution inbox header does not match the expected row contract."],
        }

    write_header = not inbox.exists() or not header
    with inbox.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=IDENTITY_RESOLUTION_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(normalized)
    _, after_count = read_existing_rows(inbox)
    return {
        "ok": True,
        "status": "identity_row_saved",
        "inbox_path": INBOX_PATH.as_posix(),
        "rows_before": before_count,
        "rows_after": after_count,
        "decision": normalized["operator_decision"],
        "athlete_id": normalized["athlete_id"],
        "guardrails": {
            "manual_only": True,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }


def write_startup_report(files_dir: Path, host: str, port: int) -> None:
    url = f"http://{host}:{port}/"
    manifest = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": "local_identity_decision_server_ready",
        "url": url,
        "served_files_dir": files_dir.as_posix(),
        "operator_inbox": INBOX_PATH.as_posix(),
        "guardrails": {
            "manual_only": True,
            "localhost_only": True,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_json(OUT_JSON, manifest)
    lines = [
        "# HSD Identity Resolution Local Server",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"URL: `{url}`",
        f"Served files: `{files_dir.as_posix()}`",
        f"Operator inbox: `{INBOX_PATH.as_posix()}`",
        "",
        "## Guardrails",
        "",
        "- Localhost-only manual write-back.",
        "- Writes only to the WNBA athlete identity-resolution inbox.",
        "- Does not approve, publish, move files, or create a publish-ready lane.",
        "- Paid APIs remain off.",
        "",
    ]
    write_text(OUT_MD, "\n".join(lines))


class IdentityResolutionHandler(BaseHTTPRequestHandler):
    server_version = "HSDIdentityResolutionLocal/1.0"

    def send_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @property
    def files_dir(self) -> Path:
        return self.server.files_dir  # type: ignore[attr-defined]

    @property
    def root(self) -> Path:
        return self.server.repo_root  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/identity-resolution/status":
            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "status": "identity_resolution_writeback_enabled",
                    "version": VERSION,
                    "inbox_path": INBOX_PATH.as_posix(),
                },
            )
            return
        target = resolve_child(self.files_dir, self.path)
        if not target:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        data = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/identity-resolution":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 100_000:
            self.send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"ok": False, "status": "payload_too_large"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "status": "invalid_json"})
            return
        row = payload.get("row") if isinstance(payload, dict) else None
        if not isinstance(row, dict):
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "status": "missing_row"})
            return
        result = append_identity_row(self.root, row)
        self.send_json(HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST, result)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("identity-decision: " + (format % args) + "\n")


def run_server(files_dir: Path, host: str, port: int, *, open_browser: bool) -> None:
    root = repo_root()
    server = ThreadingHTTPServer((host, port), IdentityResolutionHandler)
    server.repo_root = root  # type: ignore[attr-defined]
    server.files_dir = files_dir  # type: ignore[attr-defined]
    write_startup_report(files_dir, host, port)
    url = f"http://{host}:{port}/"
    print(json.dumps({"version": VERSION, "status": "serving", "url": url, "files_dir": files_dir.as_posix()}, indent=2))
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nIdentity decision server stopped.")
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the HSD Decision tab with local manual identity write-back.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("HSD_IDENTITY_UI_PORT", "8765")))
    parser.add_argument("--files-dir", type=Path, default=None)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--smoke-test", action="store_true", help="Validate startup inputs and write the startup report, then exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("Refusing non-localhost host. Use 127.0.0.1 or localhost.")
    root = repo_root()
    files_dir = args.files_dir.resolve() if args.files_dir else latest_files_dir(root)
    if not (files_dir / "operator_command_center.html").exists():
        raise SystemExit("operator_command_center.html is missing from the selected files directory.")
    if args.smoke_test:
        write_startup_report(files_dir, args.host, args.port)
        print(json.dumps({"version": VERSION, "status": "smoke_test_passed", "files_dir": files_dir.as_posix()}, indent=2))
        return
    run_server(files_dir, args.host, args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    main()

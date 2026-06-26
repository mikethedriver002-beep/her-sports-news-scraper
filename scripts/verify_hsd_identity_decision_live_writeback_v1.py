from __future__ import annotations

import csv
import json
import re
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_json, write_text
from serve_hsd_identity_resolution_ui_v1 import (
    IDENTITY_RESOLUTION_FIELDS,
    INBOX_PATH,
    IdentityResolutionHandler,
    latest_files_dir,
    validate_identity_row,
)


VERSION = "hsd-identity-decision-live-writeback-verifier-v1.0.0"
OUT_JSON = "identity_decision_live_writeback_verification.json"
OUT_MD = "identity_decision_live_writeback_verification.md"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: str) -> str:
    return clean(value).lower().replace("'", "").replace(".", "").replace("-", " ").strip().replace(" ", "-")


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def command_center_payload(files_dir: Path) -> Dict[str, Any]:
    path = files_dir / "operator_command_center.json"
    if not path.exists():
        raise FileNotFoundError(f"operator_command_center.json missing in {files_dir}")
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def select_athlete_row(payload: Dict[str, Any]) -> Dict[str, Any]:
    panel = payload.get("athlete_photo_onboarding_panel") if isinstance(payload.get("athlete_photo_onboarding_panel"), dict) else {}
    rows = panel.get("review_rows") if isinstance(panel.get("review_rows"), list) else []
    candidates = [
        row for row in rows
        if isinstance(row, dict)
        and clean(row.get("athlete_id"))
        and clean(row.get("team_id"))
        and isinstance(row.get("identity_resolution_candidate"), dict)
    ]
    if not candidates:
        raise ValueError("No real WNBA athlete identity-resolution row found in the command center payload.")
    featured = [row for row in candidates if row.get("featured") is True]
    return dict((featured or candidates)[0])


def build_command_center_identity_row(row: Dict[str, Any]) -> Dict[str, str]:
    candidate = row.get("identity_resolution_candidate") if isinstance(row.get("identity_resolution_candidate"), dict) else {}
    provider_id = clean(candidate.get("provider_player_id")) or clean(row.get("identity_provider_candidate"))
    source_url = clean(candidate.get("approved_source_url"))
    if not source_url and provider_id:
        source_url = f"https://www.wnba.com/player/{provider_id}/{slug(clean(candidate.get('display_name')) or clean(row.get('athlete_name')))}"
    out = {field: clean(candidate.get(field)) for field in IDENTITY_RESOLUTION_FIELDS}
    out.update(
        {
            "athlete_id": clean(candidate.get("athlete_id")) or clean(row.get("athlete_id")),
            "display_name": clean(candidate.get("display_name")) or clean(row.get("athlete_name")),
            "team_id": clean(candidate.get("team_id")) or clean(row.get("team_id")),
            "provider_player_id": provider_id,
            "asset_path": clean(candidate.get("asset_path")) or clean(row.get("source_headshot_path")),
            "issue_codes": clean(candidate.get("issue_codes")) or clean(row.get("identity_issue_codes")),
            "audit_evidence": clean(candidate.get("audit_evidence")) or clean(row.get("identity_evidence")),
            "allowed_decisions": "identity_verified_approved_for_review_renders|hold_identity|revise_asset|backfill_provider_id_only",
            "operator_decision": "identity_verified_approved_for_review_renders",
            "identity_verified": "yes",
            "provider_player_id_verified": "yes",
            "approved_source_url": source_url,
            "secondary_source_url": clean(candidate.get("secondary_source_url")),
            "backfill_provider_player_id": clean(candidate.get("backfill_provider_player_id")),
            "operator_notes": "Live writeback verifier: command-center draft row matched the saved localhost endpoint row; review-only verification artifact only.",
            "operator_name": "HSD live verifier",
            "reviewed_at_local": datetime.now(timezone.utc).isoformat(),
            "copy_target": INBOX_PATH.as_posix(),
            "approval_scope": "review_only_identity_resolution_for_local_draft_renders",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
            "review_only_policy": "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane",
        }
    )
    ok, warnings, normalized = validate_identity_row(out)
    if not ok:
        raise ValueError("Verifier row failed local validation: " + "; ".join(warnings))
    return normalized


def post_identity_row(url: str, row: Dict[str, str]) -> Dict[str, Any]:
    request = urllib.request.Request(
        f"{url}/api/identity-resolution",
        data=json.dumps({"row": row}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        try:
            return json.loads(payload)
        except Exception:
            return {"ok": False, "status": f"http_error_{exc.code}", "body": payload}


def compare_rows(expected: Dict[str, str], saved: Dict[str, str]) -> List[Dict[str, str]]:
    diffs: List[Dict[str, str]] = []
    for field in IDENTITY_RESOLUTION_FIELDS:
        if clean(expected.get(field)) != clean(saved.get(field)):
            diffs.append({"field": field, "expected": clean(expected.get(field)), "saved": clean(saved.get(field))})
    return diffs


def restore_inbox(inbox: Path, original: bytes | None) -> None:
    if original is None:
        if inbox.exists():
            inbox.unlink()
        return
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_bytes(original)


def run_verification(root: Path | None = None, files_dir: Path | None = None) -> Dict[str, Any]:
    root = (root or Path.cwd()).resolve()
    files_dir = (files_dir.resolve() if files_dir else latest_files_dir(root))
    payload = command_center_payload(files_dir)
    selected = select_athlete_row(payload)
    expected = build_command_center_identity_row(selected)
    inbox = (root / INBOX_PATH).resolve()
    original = inbox.read_bytes() if inbox.exists() else None
    original_count = len(read_csv_rows(inbox))
    server = ThreadingHTTPServer(("127.0.0.1", 0), IdentityResolutionHandler)
    server.repo_root = root  # type: ignore[attr-defined]
    server.files_dir = files_dir  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        response = post_identity_row(url, expected)
        if not response.get("ok"):
            raise RuntimeError("Live writeback failed: " + json.dumps(response))
        saved_rows = read_csv_rows(inbox)
        if len(saved_rows) != original_count + 1:
            raise RuntimeError(f"Expected one appended row; before={original_count}, after={len(saved_rows)}")
        saved = saved_rows[-1]
        diffs = compare_rows(expected, saved)
        status = "passed" if not diffs else "failed"
        result = {
            "version": VERSION,
            "status": status,
            "verified_at_utc": datetime.now(timezone.utc).isoformat(),
            "served_files_dir": files_dir.as_posix(),
            "endpoint": url,
            "athlete_id": clean(expected.get("athlete_id")),
            "display_name": clean(expected.get("display_name")),
            "team_id": clean(expected.get("team_id")),
            "rows_before": original_count,
            "rows_after_post": len(saved_rows),
            "diff_count": len(diffs),
            "diffs": diffs,
            "inbox_restored": True,
            "guardrails": {
                "manual_only": True,
                "auto_approval": False,
                "auto_publish": False,
                "move_files": False,
                "publish_ready": False,
                "paid_apis": False,
            },
        }
        return result
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        restore_inbox(inbox, original)


def write_report(result: Dict[str, Any]) -> Tuple[Path, Path]:
    json_path = write_json(OUT_JSON, result)
    lines = [
        "# HSD Identity Decision Live Writeback Verification",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{clean(result.get('status'))}`",
        f"Athlete: `{clean(result.get('display_name'))}` (`{clean(result.get('athlete_id'))}`)",
        f"Diff count: `{clean(result.get('diff_count'))}`",
        f"Inbox restored: `{clean(result.get('inbox_restored'))}`",
        "",
        "## Guardrails",
        "",
        "- Local/manual verification only.",
        "- No paid APIs.",
        "- No auto-approval.",
        "- No file movement.",
        "- No publishing.",
        "- No publish-ready lane.",
    ]
    md_path = write_text(OUT_MD, "\n".join(lines) + "\n")
    return json_path, md_path


def main() -> None:
    result = run_verification()
    write_report(result)
    print(json.dumps({"version": VERSION, "status": result["status"], "athlete_id": result["athlete_id"], "diff_count": result["diff_count"]}, indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

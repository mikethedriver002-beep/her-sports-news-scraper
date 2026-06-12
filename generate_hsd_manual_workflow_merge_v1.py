from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-manual-workflow-merge-v3.2.13-bebe-ops-v2.11"

INBOX_CSV = Path("operator/inbox/manual_workflow_inbox.csv")
INBOX_JSONL = Path("operator/inbox/manual_workflow_inbox.jsonl")
TEMPLATE_CSV = Path("operator/inbox/manual_workflow_inbox_template_v1.csv")

OUT_DIR = Path("manual_workflow_packets")
OUT_ZIP_DIR = Path("manual_workflow_handoff_packs")
OUT_PACKETS_JSONL = Path("manual_workflow_content_packets.jsonl")
OUT_PACKETS_CSV = Path("manual_workflow_content_packets.csv")
OUT_RENDER_PLAN_JSON = Path("manual_workflow_render_plans.json")
OUT_COPY_DESK = Path("manual_workflow_copy_desk.md")
OUT_THREADS = Path("manual_workflow_threads_copy.md")
OUT_FIRST_COMMENTS = Path("manual_workflow_first_comments.md")
OUT_PRIORITY = Path("manual_workflow_priority_report.md")
OUT_STATUS_CSV = Path("manual_workflow_pack_status.csv")
OUT_STATUS_JSON = Path("manual_workflow_pack_status.json")
OUT_HANDOFF = Path("manual_workflow_handoff.md")

PACKET_FIELDS = [
    "packet_id", "source_type", "status", "priority", "platform_targets", "content_family",
    "story_type", "headline", "angle", "sport", "league", "event_date", "teams", "players",
    "scores", "source_urls", "evidence_urls", "render_format", "content_readiness", "reason"
]
STATUS_FIELDS = [
    "packet_id", "headline", "content_family", "platform_targets", "content_readiness",
    "pack_status", "zip_path", "reason"
]

BANNED_PUBLIC_TERMS = [
    "Verified Final", "BUNDLE LOCKED FACTS", "source-safe context", "graphics-safe context",
    "target date", "workflow labels", "QA labels", "accuracy lock"
]

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def slugify(v: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", clean(v).lower()).strip("-") or "manual-item"

def sha_id(prefix: str, *parts: Any) -> str:
    return prefix + "_" + hashlib.sha1("|".join(clean(p) for p in parts).encode("utf-8")).hexdigest()[:14]

def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows

def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def split_list(v: Any) -> List[str]:
    if isinstance(v, list):
        return [clean(x) for x in v if clean(x)]
    s = clean(v)
    if not s:
        return []
    try:
        j = json.loads(s)
        if isinstance(j, list):
            return [clean(x) for x in j if clean(x)]
    except Exception:
        pass
    return [clean(x) for x in re.split(r"\s*(?:;|\||,)\s*", s) if clean(x)]

def json_obj(v: Any) -> Dict[str, Any]:
    if isinstance(v, dict):
        return v
    s = clean(v)
    if not s:
        return {}
    try:
        j = json.loads(s)
        return j if isinstance(j, dict) else {}
    except Exception:
        return {}

def normalize_manual_row(row: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    headline = clean(row.get("headline") or row.get("title") or row.get("story_title") or row.get("source_url"))
    source_urls = split_list(row.get("source_urls") or row.get("source_url") or row.get("url"))
    evidence_urls = split_list(row.get("evidence_urls") or row.get("evidence_urls_json"))
    item_id = clean(row.get("manual_item_id") or row.get("story_id") or row.get("id")) or sha_id("manual", headline, ";".join(source_urls))
    platform_targets = split_list(row.get("platform_targets") or "IG Feed; IG Stories; Threads")
    content_family = clean(row.get("content_family")) or clean(row.get("story_kind")) or "Manual Story"
    story_type = clean(row.get("story_type")) or clean(row.get("story_kind")) or "story"
    render_format = clean(row.get("render_format")) or ("story_1080x1920" if any("stor" in x.lower() for x in platform_targets) else "feed_1080x1350")
    status = clean(row.get("status")) or "queued"
    priority = clean(row.get("priority")) or "P2"
    facts = json_obj(row.get("fact_lock_json"))
    teams = split_list(row.get("teams") or facts.get("teams"))
    players = split_list(row.get("players") or facts.get("players"))
    scores = clean(row.get("scores") or facts.get("score") or facts.get("score_display"))
    angle = clean(row.get("angle") or row.get("summary") or row.get("caption_notes") or "")
    first_comment = clean(row.get("first_comment_question")) or "Which part of this story mattered most?"
    packet_id = sha_id("packet", item_id, headline, content_family, ";".join(platform_targets))
    reason = []
    if not headline:
        reason.append("missing headline")
    if not source_urls and not evidence_urls:
        reason.append("missing source/evidence URL")
    if status not in {"queued", "approved", "operator_verified", "ready"}:
        reason.append(f"status={status}")
    readiness = "ready_with_review" if not reason else "needs_manual_detail"
    return {
        "packet_id": packet_id,
        "manual_item_id": item_id,
        "source_type": source_type,
        "status": status,
        "priority": priority,
        "platform_targets": platform_targets,
        "content_family": content_family,
        "story_type": story_type,
        "headline": headline or "Untitled manual HSD story",
        "angle": angle,
        "sport": clean(row.get("sport")) or facts.get("sport", ""),
        "league": clean(row.get("league")) or facts.get("league", ""),
        "event_date": clean(row.get("event_date") or row.get("event_date_local") or facts.get("event_date", "")),
        "source_urls": source_urls,
        "evidence_urls": evidence_urls,
        "fact_lock": facts,
        "teams": teams,
        "players": players,
        "scores": scores,
        "asset_notes": clean(row.get("asset_notes")),
        "caption_notes": clean(row.get("caption_notes")),
        "threads_angle": clean(row.get("threads_angle")) or angle,
        "first_comment_question": first_comment,
        "graphics_intent": clean(row.get("graphics_intent")) or "Premium HSD editorial graphic package.",
        "render_format": render_format,
        "slide_count": clean(row.get("slide_count")),
        "story_frame_count": clean(row.get("story_frame_count")),
        "notes": clean(row.get("notes")),
        "content_readiness": readiness,
        "reason": "; ".join(reason) or "manual workflow packet ready for copy/render planning review",
    }

def packet_from_daily_slate(row: Dict[str, str]) -> Dict[str, Any]:
    headline = clean(row.get("headline"))
    item_id = clean(row.get("source_id")) or sha_id("slate", headline, row.get("event_date"))
    return normalize_manual_row({
        "manual_item_id": item_id,
        "status": "queued",
        "priority": clean(row.get("priority")) or "P2",
        "platform_targets": "IG Feed; Threads",
        "content_family": clean(row.get("content_type")) or "Daily Slate",
        "story_type": clean(row.get("content_type")) or "story",
        "headline": headline,
        "angle": clean(row.get("reason")),
        "sport": "basketball" if "WNBA" in headline else "",
        "league": "WNBA" if "WNBA" in headline or "Wings" in headline or "Fever" in headline else "",
        "event_date": clean(row.get("event_date")),
        "source_urls": clean(row.get("source_url")),
        "graphics_intent": "Daily slate candidate. Use only if editorial angle is strong.",
        "render_format": "feed_1080x1350",
    }, "daily_slate_reference")

def packet_from_story_queue(row: Dict[str, str]) -> Dict[str, Any]:
    return normalize_manual_row({
        "manual_item_id": clean(row.get("story_id")) or clean(row.get("story_slug")),
        "status": "queued",
        "priority": "P1",
        "platform_targets": "IG Stories; Threads",
        "content_family": clean(row.get("story_title")) or "Last Night in the W",
        "story_type": clean(row.get("story_type")) or "ig_story_final_scores",
        "headline": clean(row.get("story_title")) or "Last Night in the W",
        "angle": clean(row.get("score_summary")),
        "sport": "basketball",
        "league": "WNBA",
        "event_date": clean(row.get("event_date_local")),
        "teams": clean(row.get("teams_required")),
        "scores": clean(row.get("score_summary")),
        "source_urls": clean(row.get("zip_path")),
        "graphics_intent": "IG Story final-score result pack. Every selected final needs its own card.",
        "render_format": "story_1080x1920",
        "story_frame_count": clean(row.get("frames_count")),
    }, "final_score_story_reference")

def load_items() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in read_csv(INBOX_CSV):
        if any(clean(v) for v in row.values()):
            items.append(normalize_manual_row(row, "manual_workflow_inbox_csv"))
    for row in read_jsonl(INBOX_JSONL):
        items.append(normalize_manual_row(row, "manual_workflow_inbox_jsonl"))
    if not items:
        for row in read_csv(Path("story_candidates_manual.csv")):
            if row.get("publish_eligible") == "Yes" or row.get("verification_status") in {"operator_verified", "verified_official", "verified_multi_source"}:
                items.append(normalize_manual_row(row, "manual_story_candidate"))
    for row in read_csv(Path("ig_story_results_queue.csv")):
        if clean(row.get("story_slug")):
            items.append(packet_from_story_queue(row))
    for row in read_csv(Path("daily_slate_plan.csv")):
        if clean(row.get("headline")):
            items.append(packet_from_daily_slate(row))
    seen = set()
    out = []
    for item in items:
        key = (item.get("source_type"), item.get("headline"), item.get("event_date"), item.get("content_family"))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out

def public_text(s: str) -> str:
    out = clean(s)
    for term in BANNED_PUBLIC_TERMS:
        out = re.sub(re.escape(term), "", out, flags=re.I)
    return clean(out)

def content_packet(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema": "hsd.content_packet.v1",
        "packet_id": item["packet_id"],
        "generated_at_utc": now(),
        "source_type": item["source_type"],
        "status": item["status"],
        "priority": item["priority"],
        "platform_targets": item["platform_targets"],
        "content_family": item["content_family"],
        "story_type": item["story_type"],
        "headline": public_text(item["headline"]),
        "angle": public_text(item["angle"]),
        "facts": {
            "sport": item["sport"],
            "league": item["league"],
            "event_date": item["event_date"],
            "teams": item["teams"],
            "players": item["players"],
            "scores": item["scores"],
            "fact_lock": item["fact_lock"],
            "source_urls": item["source_urls"],
            "evidence_urls": item["evidence_urls"],
        },
        "asset_policy": {
            "team_logos": "exact_real_logo_required",
            "player_images": "exact_real_player_image_only_when_used",
            "no_fake_logos": True,
            "no_substitutions": True,
        },
        "editorial": {
            "graphics_intent": public_text(item["graphics_intent"]),
            "caption_notes": public_text(item["caption_notes"]),
            "threads_angle": public_text(item["threads_angle"]),
            "first_comment_question": public_text(item["first_comment_question"]),
            "notes": public_text(item["notes"]),
        },
        "readiness": {"status": item["content_readiness"], "reason": item["reason"]},
    }

def render_plan(packet: Dict[str, Any]) -> Dict[str, Any]:
    fmt = "story_1080x1920" if any("Stories" in x or "story" in x.lower() for x in packet.get("platform_targets", [])) else "feed_1080x1350"
    dimensions = {"story_1080x1920": [1080, 1920], "feed_1080x1350": [1080, 1350]}.get(fmt, [1080, 1350])
    frame_count = 4
    scores = clean(packet.get("facts", {}).get("scores"))
    if fmt == "story_1080x1920" and scores:
        frame_count = min(8, max(3, len([x for x in scores.split("|") if clean(x)]) + 2))
    return {
        "schema": "hsd.render_plan.v1",
        "plan_id": sha_id("plan", packet["packet_id"], fmt),
        "packet_id": packet["packet_id"],
        "render_profile": fmt,
        "dimensions": dimensions,
        "output_mode": "manual_graphics_handoff",
        "frame_count": frame_count,
        "watermark": {"position": "top-left", "one_only": True},
        "safe_margins": {"feed_px": 72, "story_px": 96, "watermark_px": 48},
        "asset_policy": packet["asset_policy"],
        "frames": [
            {"role": "cover", "headline": packet["headline"], "subhead": packet["angle"] or packet["content_family"]},
            {"role": "detail", "headline": "What matters", "subhead": scores or packet["angle"]},
            {"role": "cta", "headline": packet["editorial"]["first_comment_question"], "subhead": "Tap in with HSD"},
        ],
    }

def copy_docs(packet: Dict[str, Any]) -> Dict[str, str]:
    headline = packet["headline"]
    angle = packet.get("angle") or packet.get("content_family")
    question = packet["editorial"]["first_comment_question"] or "Which part mattered most?"
    scores = clean(packet.get("facts", {}).get("scores"))
    teams = ", ".join(packet.get("facts", {}).get("teams") or [])
    caption = f"{headline}\n\n{angle}\n\n{scores or teams}\n\n{question}"
    threads = f"{headline}\n\n{angle}\n\n{question}"
    first_comment = question
    graphics_prompt = (
        f"Create a premium Her Sports Daily graphic package for: {headline}\n\n"
        f"Angle: {angle}\n"
        f"Facts to preserve exactly: {scores or teams or 'Use only attached/verified packet facts.'}\n"
        "Use exact real team logos and exact mapped player images only. No fake logos, no substitutions, no internal QA language."
    )
    return {
        "02_COPY_DESK.md": "# HSD Copy Desk\n\n## IG caption draft\n\n" + caption + "\n",
        "03_THREADS_COPY.md": "# HSD Threads Copy\n\n" + threads + "\n",
        "04_FIRST_COMMENT.md": "# HSD First Comment\n\n" + first_comment + "\n",
        "00_PROMPT_TO_PASTE.md": graphics_prompt + "\n",
    }

def zip_folder(folder: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(folder))

def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    if OUT_ZIP_DIR.exists():
        shutil.rmtree(OUT_ZIP_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_ZIP_DIR.mkdir(parents=True, exist_ok=True)

    items = load_items()
    packets = []
    plans = []
    status_rows = []
    copy_lines = ["# HSD Manual Workflow Copy Desk", "", f"Generated: {now()}", f"Version: {VERSION}", ""]
    thread_lines = ["# HSD Manual Workflow Threads Copy", "", f"Generated: {now()}", f"Version: {VERSION}", ""]
    comment_lines = ["# HSD Manual Workflow First Comments", "", f"Generated: {now()}", f"Version: {VERSION}", ""]
    priority_lines = ["# HSD Manual Workflow Priority Report", "", f"Generated: {now()}", f"Version: {VERSION}", "", f"- packets created: {len(items)}", ""]

    for idx, item in enumerate(items, start=1):
        packet = content_packet(item)
        plan = render_plan(packet)
        docs = copy_docs(packet)
        slug = slugify(f"{idx:02d}-{packet['content_family']}-{packet['headline']}")
        folder = OUT_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "content_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
        (folder / "render_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
        for name, body in docs.items():
            (folder / name).write_text(body, encoding="utf-8")
        asset_index = {
            "schema": "hsd.asset_index.v1",
            "packet_id": packet["packet_id"],
            "required_teams": packet["facts"].get("teams", []),
            "required_players": packet["facts"].get("players", []),
            "policy": packet["asset_policy"],
            "status": "asset_resolution_not_run_in_manual_merge_v1",
        }
        (folder / "ASSET_INDEX.json").write_text(json.dumps(asset_index, indent=2), encoding="utf-8")
        (folder / "ASSET_INDEX.csv").write_text("packet_id,entity_type,entity_name,required,status\n", encoding="utf-8")
        checks = []
        for p in folder.rglob("*"):
            if p.is_file():
                checks.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(folder).as_posix()}")
        (folder / "CHECKSUMS.sha256").write_text("\n".join(checks) + "\n", encoding="utf-8")
        zip_path = OUT_ZIP_DIR / f"{slug}_manual_workflow_pack.zip"
        zip_folder(folder, zip_path)

        packets.append(packet)
        plans.append(plan)
        status_rows.append({
            "packet_id": packet["packet_id"],
            "headline": packet["headline"],
            "content_family": packet["content_family"],
            "platform_targets": "; ".join(packet["platform_targets"]),
            "content_readiness": packet["readiness"]["status"],
            "pack_status": "ready_with_review",
            "zip_path": zip_path.as_posix(),
            "reason": packet["readiness"]["reason"],
        })
        copy_lines += [f"## {idx}. {packet['headline']}", "", docs["02_COPY_DESK.md"], ""]
        thread_lines += [f"## {idx}. {packet['headline']}", "", docs["03_THREADS_COPY.md"], ""]
        comment_lines += [f"## {idx}. {packet['headline']}", "", docs["04_FIRST_COMMENT.md"], ""]
        priority_lines += [
            f"## {idx}. {packet['headline']}",
            "",
            f"- Source type: {packet['source_type']}",
            f"- Priority: {packet['priority']}",
            f"- Platforms: {', '.join(packet['platform_targets'])}",
            f"- Readiness: {packet['readiness']['status']}",
            f"- Reason: {packet['readiness']['reason']}",
            f"- Pack: `{zip_path.as_posix()}`",
            "",
        ]

    if not items:
        priority_lines += [
            "No manual workflow rows were found.",
            "",
            "Add rows to `operator/inbox/manual_workflow_inbox.csv` using `operator/inbox/manual_workflow_inbox_template_v1.csv`.",
            "",
        ]

    OUT_PACKETS_JSONL.write_text("\n".join(json.dumps(p, ensure_ascii=False) for p in packets) + ("\n" if packets else ""), encoding="utf-8")
    write_csv(OUT_PACKETS_CSV, [
        {
            "packet_id": p["packet_id"],
            "source_type": p["source_type"],
            "status": p["status"],
            "priority": p["priority"],
            "platform_targets": "; ".join(p["platform_targets"]),
            "content_family": p["content_family"],
            "story_type": p["story_type"],
            "headline": p["headline"],
            "angle": p["angle"],
            "sport": p["facts"].get("sport", ""),
            "league": p["facts"].get("league", ""),
            "event_date": p["facts"].get("event_date", ""),
            "teams": "; ".join(p["facts"].get("teams", [])),
            "players": "; ".join(p["facts"].get("players", [])),
            "scores": p["facts"].get("scores", ""),
            "source_urls": "; ".join(p["facts"].get("source_urls", [])),
            "evidence_urls": "; ".join(p["facts"].get("evidence_urls", [])),
            "render_format": next((pl["render_profile"] for pl in plans if pl["packet_id"] == p["packet_id"]), ""),
            "content_readiness": p["readiness"]["status"],
            "reason": p["readiness"]["reason"],
        } for p in packets
    ], PACKET_FIELDS)
    OUT_RENDER_PLAN_JSON.write_text(json.dumps({"version": VERSION, "generated_at_utc": now(), "plans": plans}, indent=2), encoding="utf-8")
    OUT_COPY_DESK.write_text("\n".join(copy_lines) + "\n", encoding="utf-8")
    OUT_THREADS.write_text("\n".join(thread_lines) + "\n", encoding="utf-8")
    OUT_FIRST_COMMENTS.write_text("\n".join(comment_lines) + "\n", encoding="utf-8")
    OUT_PRIORITY.write_text("\n".join(priority_lines) + "\n", encoding="utf-8")
    write_csv(OUT_STATUS_CSV, status_rows, STATUS_FIELDS)
    OUT_STATUS_JSON.write_text(json.dumps({"version": VERSION, "generated_at_utc": now(), "packs": status_rows}, indent=2), encoding="utf-8")
    OUT_HANDOFF.write_text(
        "# HSD Manual Workflow Merge Handoff\n\n"
        f"Generated: {now()}\nVersion: {VERSION}\n\n"
        f"- packets created: {len(packets)}\n"
        f"- handoff pack zips: {len(status_rows)}\n\n"
        "Use this layer to bring manual editorial decisions into BeBe before Multi-Post Desk v1. "
        "Each packet contains `content_packet.json`, `render_plan.json`, copy desk, Threads copy, first comment, asset index stub, and checksums.\n",
        encoding="utf-8",
    )
    print(json.dumps({"manual_workflow_packets": len(packets), "handoff_packs": len(status_rows)}, indent=2))

if __name__ == "__main__":
    main()

from __future__ import annotations
import csv, json, re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

VERSION = "hsd-multi-post-desk-mermaid-v1.0"
OUT_BOARD_MD = Path("multi_post_daily_board.md")
OUT_STATUS_CSV = Path("post_slot_status.csv")
OUT_FEED_CSV = Path("ig_feed_queue.csv")
OUT_STORY_CSV = Path("ig_story_queue.csv")
OUT_THREADS_CSV = Path("threads_queue.csv")
OUT_CAPTION_MD = Path("caption_bank.md")
OUT_COMMENT_MD = Path("first_comment_hooks.md")
OUT_MANIFEST_JSON = Path("multi_post_daily_board.json")

SLOT_FIELDS = [
    "slot_id","slot_name","platform","window_et","status","content_type","headline","content_family",
    "source_type","source_ref","recommended_asset","notes"
]
QUEUE_FIELDS = ["queue_rank","platform","content_type","headline","source_ref","status","asset_hint","notes"]

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def write_csv(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        if rows:
            w.writerows(rows)

def load_cfg() -> Dict[str, Any]:
    p = Path("config/hsd_multi_post_slots_v1.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"slots": []}

def readyish(row: Dict[str, str]) -> bool:
    return "ready" in clean(row.get("content_readiness") or row.get("status") or row.get("pack_status")).lower()

def pick_manual_packet(rows: List[Dict[str, str]], platform_contains: str = "", story_type: str = "") -> Optional[Dict[str, str]]:
    candidates = []
    for r in rows:
        if not readyish(r):
            continue
        platforms = clean(r.get("platform_targets"))
        if platform_contains and platform_contains.lower() not in platforms.lower():
            continue
        if story_type:
            hay = (clean(r.get("story_type")) + " " + clean(r.get("content_family"))).lower()
            if story_type.lower() not in hay:
                continue
        candidates.append(r)
    candidates.sort(key=lambda r: (clean(r.get("priority", "P9")), clean(r.get("headline"))))
    return candidates[0] if candidates else None

def pick_daily_slate(rows: List[Dict[str, str]], content_type: str = "") -> Optional[Dict[str, str]]:
    candidates = [r for r in rows if not content_type or clean(r.get("content_type")).lower() == content_type.lower()]
    if not candidates:
        return None
    candidates.sort(key=lambda r: (clean(r.get("priority","P9")), clean(r.get("headline"))))
    return candidates[0]

def qrow(rank: int, platform: str, content_type: str, headline: str, source_ref: str, status: str, asset_hint: str, notes: str) -> Dict[str, str]:
    return {
        "queue_rank": str(rank),
        "platform": platform,
        "content_type": content_type,
        "headline": headline,
        "source_ref": source_ref,
        "status": status,
        "asset_hint": asset_hint,
        "notes": notes,
    }

def main() -> None:
    now = datetime.now(timezone.utc)
    cfg = load_cfg()
    manual_packets = read_csv("manual_workflow_content_packets.csv")
    daily_slate = read_csv("daily_slate_plan.csv")
    story_pack_status = read_csv("ig_story_results_upload_pack_status.csv")

    story_ready = story_pack_status[0] if story_pack_status else {}
    story_zip = clean(story_ready.get("zip_path"))
    story_status = clean(story_ready.get("upload_pack_status"))

    preview_packet = pick_manual_packet(manual_packets, "IG Feed", "preview") or pick_daily_slate(daily_slate, "preview")
    story_packet = pick_manual_packet(manual_packets, "IG Stories", "ig_story_final_scores") or pick_manual_packet(manual_packets, "IG Stories")
    feed_packet = pick_manual_packet(manual_packets, "IG Feed") or pick_daily_slate(daily_slate)
    recap_packet = pick_manual_packet(manual_packets, "Threads") or pick_daily_slate(daily_slate, "result") or pick_daily_slate(daily_slate)

    slots: List[Dict[str, str]] = []
    feed_queue: List[Dict[str, str]] = []
    story_queue: List[Dict[str, str]] = []
    threads_queue: List[Dict[str, str]] = []

    for slot in cfg.get("slots", []):
        sid = slot["slot_id"]
        base = {
            "slot_id": sid,
            "slot_name": slot["slot_name"],
            "platform": slot["platform"],
            "window_et": slot["window_et"],
            "status": "skip_no_strong_angle",
            "content_type": "",
            "headline": "",
            "content_family": "",
            "source_type": "",
            "source_ref": "",
            "recommended_asset": "",
            "notes": "",
        }

        if sid == "threads_morning_board":
            bullets = []
            for src in [preview_packet, story_packet, recap_packet]:
                if src and clean(src.get("headline")) and clean(src.get("headline")) not in bullets:
                    bullets.append(clean(src.get("headline")))
            if bullets:
                base.update({
                    "status": "ready_with_review",
                    "content_type": "threads_board",
                    "headline": "Today in women’s sports",
                    "content_family": "threads_morning_board",
                    "source_type": "multi_source",
                    "source_ref": "; ".join(bullets[:3]),
                    "recommended_asset": "text_only",
                    "notes": "What we’re watching: " + " | ".join(bullets[:3]),
                })
                threads_queue.append(qrow(len(threads_queue)+1, "Threads", "threads_board", base["headline"], base["source_ref"], base["status"], "text_only", base["notes"]))

        elif sid == "ig_feed_noon" and feed_packet:
            headline = clean(feed_packet.get("headline"))
            source_ref = clean(feed_packet.get("packet_id") or feed_packet.get("source_id") or headline)
            asset_hint = clean(feed_packet.get("zip_path")) or "manual_workflow_packet"
            base.update({
                "status": "ready_with_review",
                "content_type": clean(feed_packet.get("story_type") or feed_packet.get("content_type") or "feed_story"),
                "headline": headline,
                "content_family": clean(feed_packet.get("content_family") or feed_packet.get("content_type") or "feature"),
                "source_type": clean(feed_packet.get("source_type") or "manual_workflow"),
                "source_ref": source_ref,
                "recommended_asset": asset_hint,
                "notes": "Best noon IG candidate based on current packets/slate.",
            })
            feed_queue.append(qrow(len(feed_queue)+1, "IG Feed", base["content_type"], headline, source_ref, base["status"], asset_hint, base["notes"]))

        elif sid == "ig_story_results" and story_status.startswith("ready"):
            headline = clean(story_packet.get("headline") if story_packet else "Last Night in the W")
            source_ref = clean(story_packet.get("packet_id") if story_packet else "ig_story_results_queue")
            base.update({
                "status": story_status,
                "content_type": "ig_story_final_scores",
                "headline": headline,
                "content_family": "Last Night in the W",
                "source_type": clean(story_packet.get("source_type") if story_packet else "final_score_story_reference"),
                "source_ref": source_ref,
                "recommended_asset": story_zip,
                "notes": "Story results pack is ready for graphics chat/manual review.",
            })
            story_queue.append(qrow(len(story_queue)+1, "IG Stories", "ig_story_final_scores", headline, source_ref, story_status, story_zip, base["notes"]))

        elif sid == "ig_feed_preview" and preview_packet:
            headline = clean(preview_packet.get("headline"))
            source_ref = clean(preview_packet.get("packet_id") or preview_packet.get("source_id") or headline)
            asset_hint = clean(preview_packet.get("zip_path")) or "graphics_chat_upload_pack_zips/tonight-in-the-w_graphics_chat_upload_pack.zip"
            base.update({
                "status": "ready_with_review",
                "content_type": "preview",
                "headline": headline,
                "content_family": clean(preview_packet.get("content_family") or "preview"),
                "source_type": clean(preview_packet.get("source_type") or "daily_slate_reference"),
                "source_ref": source_ref,
                "recommended_asset": asset_hint,
                "notes": "Use only if timing fits the live slate.",
            })
            feed_queue.append(qrow(len(feed_queue)+1, "IG Feed", "preview", headline, source_ref, base["status"], asset_hint, base["notes"]))

        elif sid == "threads_live_desk":
            src = preview_packet or recap_packet
            if src:
                headline = clean(src.get("headline"))
                source_ref = clean(src.get("packet_id") or src.get("source_id") or headline)
                base.update({
                    "status": "ready_with_review",
                    "content_type": "threads_live",
                    "headline": headline,
                    "content_family": "threads_live_desk",
                    "source_type": clean(src.get("source_type") or "daily_slate_reference"),
                    "source_ref": source_ref,
                    "recommended_asset": "text_only_or_score_crop",
                    "notes": "Use short debate/question-led live desk posts.",
                })
                threads_queue.append(qrow(len(threads_queue)+1, "Threads", "threads_live", headline, source_ref, base["status"], base["recommended_asset"], base["notes"]))

        elif sid == "night_recap" and recap_packet:
            headline = clean(recap_packet.get("headline"))
            source_ref = clean(recap_packet.get("packet_id") or recap_packet.get("source_id") or headline)
            asset_hint = clean(recap_packet.get("zip_path")) or story_zip or "text_only"
            base.update({
                "status": "ready_with_review",
                "content_type": clean(recap_packet.get("content_type") or recap_packet.get("story_type") or "recap"),
                "headline": headline,
                "content_family": clean(recap_packet.get("content_family") or "night_recap"),
                "source_type": clean(recap_packet.get("source_type") or "manual_workflow"),
                "source_ref": source_ref,
                "recommended_asset": asset_hint,
                "notes": "Use as late Threads debate/reaction post.",
            })
            threads_queue.append(qrow(len(threads_queue)+1, "Threads", "recap", headline, source_ref, base["status"], asset_hint, base["notes"]))

        slots.append(base)

    write_csv(OUT_STATUS_CSV, slots, SLOT_FIELDS)
    write_csv(OUT_FEED_CSV, feed_queue, QUEUE_FIELDS)
    write_csv(OUT_STORY_CSV, story_queue, QUEUE_FIELDS)
    write_csv(OUT_THREADS_CSV, threads_queue, QUEUE_FIELDS)

    board = [
        "# HSD Multi-Post Daily Board",
        "",
        f"Generated: {now.isoformat()}",
        f"Version: {VERSION}",
        "",
    ]
    for s in slots:
        board += [
            f"## {s['slot_name']} ({s['window_et']})",
            f"- Platform: {s['platform']}",
            f"- Status: {s['status']}",
            f"- Headline: {s['headline'] or '—'}",
            f"- Content type: {s['content_type'] or '—'}",
            f"- Source: {s['source_type'] or '—'}",
            f"- Asset: {s['recommended_asset'] or '—'}",
            f"- Notes: {s['notes'] or '—'}",
            "",
        ]
    OUT_BOARD_MD.write_text("\n".join(board) + "\n", encoding="utf-8")

    captions = [
        "# HSD Caption Bank",
        "",
        f"Generated: {now.isoformat()}",
        f"Version: {VERSION}",
        "",
    ]
    for row in feed_queue + story_queue:
        headline = row["headline"]
        captions += [
            f"## {headline}",
            f"- Platform: {row['platform']}",
            f"- Suggested caption: {headline}. What stands out most?",
            "- CTA: Tap in with HSD.",
            "",
        ]
    OUT_CAPTION_MD.write_text("\n".join(captions) + "\n", encoding="utf-8")

    comments = [
        "# HSD First Comment Hooks",
        "",
        f"Generated: {now.isoformat()}",
        f"Version: {VERSION}",
        "",
    ]
    for row in feed_queue:
        comments += [
            f"## {row['headline']}",
            "Which angle matters most here?",
            "What stood out first to you?",
            "",
        ]
    OUT_COMMENT_MD.write_text("\n".join(comments) + "\n", encoding="utf-8")

    OUT_MANIFEST_JSON.write_text(json.dumps({
        "generated_at": now.isoformat(),
        "version": VERSION,
        "slots": slots,
        "ig_feed_queue_count": len(feed_queue),
        "ig_story_queue_count": len(story_queue),
        "threads_queue_count": len(threads_queue),
    }, indent=2), encoding="utf-8")

    print(json.dumps({
        "slot_count": len(slots),
        "ig_feed_queue_count": len(feed_queue),
        "ig_story_queue_count": len(story_queue),
        "threads_queue_count": len(threads_queue),
        "version": VERSION,
    }, indent=2))

if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v3.3.6-mermaid-assignment-handoff-v2.6"
CFG = Path("config/hsd_mermaid_assignment_handoff_v2_6.json")
SLOTS = ["mermaid_assignment_final_slots.csv", "mermaid_assignment_content_slots.csv", "mermaid_content_slots_v2.csv"]
OUT_DIR = Path("assignment_handoff_packets")
ZIP_DIR = Path("assignment_handoff_zips")
OUT_INDEX = Path("assignment_handoff_index.csv")
OUT_REPORT = Path("assignment_handoff_report.md")
OUT_MANIFEST = Path("assignment_handoff_manifest.json")
OUT_STATUS = Path("assignment_handoff_status.csv")
OUT_FEED = Path("ig_feed_handoff_queue.csv")
OUT_STORY = Path("ig_story_handoff_queue.csv")
OUT_THREADS = Path("threads_handoff_queue.csv")

INDEX_FIELDS = ["packet_id", "slot_id", "platform", "headline", "league", "content_type", "status", "packet_dir", "zip_path", "public_prompt", "copy_desk", "threads_copy", "asset_instructions"]
STATUS_FIELDS = ["slot_id", "platform", "headline", "status", "reason", "packet_id"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def low(v: Any) -> str:
    return clean(v).lower()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", low(v)).strip("-") or "item"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: str | Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {} if default is None else default


def first_slots() -> List[Dict[str, str]]:
    for p in SLOTS:
        rows = read_csv(p)
        if rows:
            return rows
    return []


def ready(slot: Dict[str, Any]) -> tuple[bool, str]:
    status = low(slot.get("status"))
    fresh = low(slot.get("freshness_label"))
    if status and status != "ready_with_review":
        return False, f"status={status}"
    if any(x in fresh for x in ["blocked", "held", "stale"]):
        return False, f"freshness={fresh}"
    if not clean(slot.get("headline")):
        return False, "missing headline"
    return True, "ready"


def platform_kind(platform: str) -> str:
    p = clean(platform)
    if p == "IG Feed":
        return "graphics_prompt_plus_caption"
    if p == "IG Stories":
        return "story_frame_prompt_plus_sticker_copy"
    if p == "Threads":
        return "copy_only_or_optional_graphic"
    return "review"


def make_copy(slot: Dict[str, Any]) -> Dict[str, str]:
    headline = clean(slot.get("headline"))
    league = clean(slot.get("league"))
    platform = clean(slot.get("platform"))
    ctype = clean(slot.get("content_type"))
    hook = clean(slot.get("copy_hook")) or f"{league}: {headline}"
    first = clean(slot.get("first_comment")) or "What’s the angle people are missing?"
    caption = clean(slot.get("ig_caption_seed")) or f"{headline}\n\nHSD is tracking the bigger picture."
    threads = clean(slot.get("threads_copy")) or f"{headline}\n\n{first}"
    story = clean(slot.get("story_frame_text")) or f"ON THE BOARD: {headline}"
    return {"hook": hook, "first": first, "caption": caption, "threads": threads, "story": story, "headline": headline, "league": league, "platform": platform, "content_type": ctype}


def write_packet(slot: Dict[str, Any]) -> Dict[str, Any]:
    copy = make_copy(slot)
    packet_id = f"{slug(slot.get('platform'))}_{slug(slot.get('slot_id'))}_{slug(copy['headline'])}"[:120]
    pdir = OUT_DIR / packet_id
    pdir.mkdir(parents=True, exist_ok=True)
    zpath = ZIP_DIR / f"{packet_id}.zip"
    ZIP_DIR.mkdir(parents=True, exist_ok=True)

    public_prompt = f"# HSD Public Prompt\n\nCreate a premium Her Sports Daily social asset.\n\nPlatform: {copy['platform']}\nSlot: {clean(slot.get('slot_id'))}\nStory: {copy['headline']}\nLeague: {copy['league']}\nContent type: {copy['content_type']}\n\nPublic display direction:\n- {copy['hook']}\n- Keep it fast to read, premium, and social-first.\n- Use clean HSD editorial language.\n- CTA idea: {copy['first']}\n"
    control = f"# Control Rules - Do Not Render\n\nVersion: {VERSION}\nFreshness label: {clean(slot.get('freshness_label')) or 'fresh'}\nAsset policy: exact logos only; exact player assets only; no generated players, jerseys, logos, stats, quotes, injuries, or scores.\nUse player graphics when appropriate only if exact approved player assets exist.\nDo not use blocked or held preview instructions.\n"
    copy_desk = f"# Copy Desk\n\n{copy['caption']}\n\nFirst comment:\n{copy['first']}\n"
    threads = f"# Threads Copy\n\n{copy['threads']}\n"
    first = f"# First Comment\n\n{copy['first']}\n"
    assets = f"# Asset Instructions\n\nRecommended output: {platform_kind(copy['platform'])}\n\n- Use exact team/league logos only when visible.\n- Player graphics are required when appropriate, but only exact approved assets may be used.\n- If exact player assets are unavailable, use a text-forward editorial card with exact logos.\n- Do not fetch or invent assets inside graphics chat.\n"
    content_packet = {"version": VERSION, "slot": slot, "public_copy": copy, "packet_id": packet_id}
    render_plan = {"version": VERSION, "packet_id": packet_id, "platform": copy["platform"], "status": "ready_with_review", "asset_policy": "exact_assets_only"}

    files = {
        "00_PUBLIC_PROMPT_TO_PASTE.md": public_prompt,
        "01_CONTROL_RULES_DO_NOT_RENDER.md": control,
        "02_COPY_DESK.md": copy_desk,
        "03_THREADS_COPY.md": threads,
        "04_FIRST_COMMENT.md": first,
        "05_ASSET_INSTRUCTIONS.md": assets,
        "content_packet.json": json.dumps(content_packet, indent=2),
        "render_plan.json": json.dumps(render_plan, indent=2),
    }
    for name, text in files.items():
        (pdir / name).write_text(text, encoding="utf-8")
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in pdir.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(pdir))
    return {"packet_id": packet_id, "slot_id": slot.get("slot_id"), "platform": copy["platform"], "headline": copy["headline"], "league": copy["league"], "content_type": copy["content_type"], "status": "ready_with_review", "packet_dir": pdir.as_posix(), "zip_path": zpath.as_posix(), "public_prompt": (pdir / "00_PUBLIC_PROMPT_TO_PASTE.md").as_posix(), "copy_desk": (pdir / "02_COPY_DESK.md").as_posix(), "threads_copy": (pdir / "03_THREADS_COPY.md").as_posix(), "asset_instructions": (pdir / "05_ASSET_INSTRUCTIONS.md").as_posix()}


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    if ZIP_DIR.exists():
        shutil.rmtree(ZIP_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    slots = first_slots()
    index: List[Dict[str, Any]] = []
    status_rows: List[Dict[str, Any]] = []
    for s in slots:
        ok, reason = ready(s)
        if not ok:
            status_rows.append({"slot_id": s.get("slot_id"), "platform": s.get("platform"), "headline": s.get("headline"), "status": "held", "reason": reason, "packet_id": ""})
            continue
        row = write_packet(s)
        index.append(row)
        status_rows.append({"slot_id": s.get("slot_id"), "platform": s.get("platform"), "headline": s.get("headline"), "status": "packet_ready", "reason": "ready", "packet_id": row["packet_id"]})
    write_csv(OUT_INDEX, index, INDEX_FIELDS)
    write_csv(OUT_STATUS, status_rows, STATUS_FIELDS)
    write_csv(OUT_FEED, [r for r in index if r.get("platform") == "IG Feed"], INDEX_FIELDS)
    write_csv(OUT_STORY, [r for r in index if r.get("platform") == "IG Stories"], INDEX_FIELDS)
    write_csv(OUT_THREADS, [r for r in index if r.get("platform") == "Threads"], INDEX_FIELDS)
    OUT_MANIFEST.write_text(json.dumps({"version": VERSION, "generated_at": now_iso(), "slots_seen": len(slots), "packets_ready": len(index), "held": len(status_rows) - len(index)}, indent=2), encoding="utf-8")
    lines = ["# Mermaid Assignment Handoff v2.6", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", f"- slots seen: {len(slots)}", f"- packets ready: {len(index)}", f"- held: {len(status_rows) - len(index)}", "", "## Packets", ""]
    for r in index:
        lines.append(f"- {r['platform']} / {r['slot_id']}: {r['headline']} — `{r['zip_path']}`")
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Alias to an existing artifact path that is already uploaded.
    Path("manual_workflow_handoff.md").write_text(OUT_REPORT.read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps({"packets_ready": len(index), "held": len(status_rows) - len(index)}, indent=2))


if __name__ == "__main__":
    main()

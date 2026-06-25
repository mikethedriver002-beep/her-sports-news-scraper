from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from hsd_run_io import output_path, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - validated by runtime status report
    Image = None
    ImageDraw = None
    ImageFont = None


VERSION = "hsd-manual-review-renderer-v1.0.0-review-only"
HANDOFF_DIR_NAME = "render_handoff_top_packet"
OUT_DIR = output_path(HANDOFF_DIR_NAME)
OUT_PREVIEW = OUT_DIR / "draft_preview.png"
OUT_REPORT = output_path("manual_review_renderer_report.md")
OUT_MANIFEST = output_path("manual_review_renderer_manifest.json")


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def repo_root() -> Path:
    return Path.cwd().resolve()


def input_handoff_candidates() -> List[Path]:
    candidates: List[Path] = []
    run_dir = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if run_dir:
        candidates.append(Path(run_dir) / HANDOFF_DIR_NAME)
    candidates.append(repo_root() / HANDOFF_DIR_NAME)
    candidates.append(repo_root() / "outputs" / "local" / "latest" / "files" / HANDOFF_DIR_NAME)
    return candidates


def find_handoff_dir() -> Path | None:
    for candidate in input_handoff_candidates():
        if (candidate / "handoff_manifest.json").exists():
            return candidate
    return None


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def copy_handoff_to_output(src: Path) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        dest = OUT_DIR / item.name
        if item.resolve() == dest.resolve():
            continue
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


def font(size: int, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap_text(draw: Any, text: str, fnt: Any, max_width: int, max_lines: int) -> List[str]:
    words = clean(text).split()
    lines: List[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=fnt)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
            continue
        lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if words and len(lines) == max_lines:
        consumed = " ".join(lines).split()
        if len(consumed) < len(words):
            lines[-1] = lines[-1].rstrip(".") + "..."
    return lines


def draw_text_block(draw: Any, xy: tuple[int, int], text: str, fnt: Any, fill: tuple[int, int, int], max_width: int, max_lines: int, line_gap: int) -> int:
    x, y = xy
    for line in wrap_text(draw, text, fnt, max_width, max_lines):
        draw.text((x, y), line, font=fnt, fill=fill)
        bbox = draw.textbbox((x, y), line, font=fnt)
        y = bbox[3] + line_gap
    return y


def render_preview(packet: Dict[str, Any]) -> None:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for manual review rendering.")
    width, height = 1080, 1350
    image = Image.new("RGB", (width, height), (248, 246, 241))
    draw = ImageDraw.Draw(image)

    ink = (24, 28, 36)
    muted = (88, 96, 108)
    red = (190, 39, 54)
    blue = (35, 92, 148)
    gold = (222, 176, 70)
    line = (219, 217, 210)

    draw.rectangle((0, 0, width, 24), fill=blue)
    draw.rectangle((0, 24, width, 34), fill=gold)
    draw.rectangle((54, 74, width - 54, 150), fill=(255, 255, 255), outline=line, width=2)
    draw.text((82, 92), "HER SPORTS DAILY", font=font(30, True), fill=ink)
    draw.text((width - 346, 92), "DRAFT REVIEW ONLY", font=font(28, True), fill=red)

    y = 210
    draw.text((74, y), "REVIEW PREVIEW", font=font(28, True), fill=blue)
    y += 52
    y = draw_text_block(draw, (74, y), clean(packet.get("copy_headline")) or clean(packet.get("title")), font(68, True), ink, 920, 4, 12)
    y += 24
    draw.line((74, y, width - 74, y), fill=line, width=3)
    y += 34
    y = draw_text_block(draw, (74, y), clean(packet.get("copy_dek")) or "Operator fill-in after source review.", font(34, False), ink, 900, 5, 10)

    lower_top = 930
    draw.rectangle((54, lower_top, width - 54, height - 84), fill=(255, 255, 255), outline=line, width=2)
    draw.text((82, lower_top + 34), "Manual render context", font=font(28, True), fill=ink)
    context_lines = [
        f"Template: {clean(packet.get('template_fit'))}",
        f"Shape: {clean(packet.get('template_shape'))}",
        f"Assets: {clean(packet.get('asset_requirement'))}",
        f"Source: {clean(packet.get('source_artifact'))}",
        "Approval: human visual review required before any post",
    ]
    y = lower_top + 88
    for item in context_lines:
        y = draw_text_block(draw, (82, y), item, font(24, False), muted, 860, 2, 8)
        y += 4

    draw.rectangle((54, height - 62, width - 54, height - 36), fill=red)
    draw.text((70, height - 60), "NOT APPROVED - NOT PUBLISH READY - AUTO-RENDER OFF - AUTO-PUBLISH OFF", font=font(20, True), fill=(255, 255, 255))
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT_PREVIEW)


def report_lines(status: str, manifest: Dict[str, Any], preview_path: str, reason: str = "") -> List[str]:
    packet = manifest.get("packet") if isinstance(manifest.get("packet"), dict) else {}
    return [
        "# HSD Manual Review Renderer",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{status}`",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Guardrails",
        "",
        "- Manual-only mode.",
        "- Draft preview is for human review only.",
        "- Does not publish.",
        "- Does not approve the image.",
        "- Does not call paid APIs.",
        "",
        "## Output",
        "",
        f"- Preview: `{preview_path or 'not_created'}`",
        f"- Story: `{clean(packet.get('title')) or 'none'}`",
        f"- Reason: {reason or 'n/a'}",
        "",
    ]


def main() -> None:
    handoff = find_handoff_dir()
    if not handoff:
        manifest = {
            "version": VERSION,
            "status": "blocked_missing_handoff",
            "preview_path": "",
            "guardrails": {"manual_only": True, "auto_render": False, "auto_publish": False, "approved": False, "paid_apis": False},
        }
        write_json(OUT_MANIFEST, manifest)
        write_text(OUT_REPORT, "\n".join(report_lines("blocked_missing_handoff", {}, "", "render_handoff_top_packet/handoff_manifest.json was not found.")))
        print(json.dumps(manifest, indent=2))
        return

    copy_handoff_to_output(handoff)
    source_manifest = read_json(handoff / "handoff_manifest.json")
    packet = source_manifest.get("packet") if isinstance(source_manifest.get("packet"), dict) else {}
    status = "draft_preview_created"
    reason = ""
    preview = ""
    try:
        render_preview(packet)
        preview = OUT_PREVIEW.as_posix()
    except Exception as exc:
        status = "blocked_preview_not_created"
        reason = str(exc)

    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_handoff_dir": handoff.as_posix(),
        "output_handoff_dir": OUT_DIR.as_posix(),
        "preview_path": preview,
        "packet_id": clean(packet.get("packet_id")),
        "title": clean(packet.get("title")),
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "auto_render": False,
            "auto_publish": False,
            "approved": False,
            "paid_apis": False,
        },
        "approval_status": "not_approved_human_review_required",
        "reason": reason,
    }
    write_json(OUT_MANIFEST, manifest)
    write_text(OUT_REPORT, "\n".join(report_lines(status, source_manifest, preview, reason)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

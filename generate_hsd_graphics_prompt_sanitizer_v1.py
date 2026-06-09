from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "hsd-graphics-prompt-sanitizer-v1.7.2"
INPUT_PROMPTS = "studio_bundle_prompts_v2.md"
INPUT_RENDER_MANIFEST = "studio_render_manifest_v2.json"
INPUT_DISPLAY_COPY = "graphics_display_copy.csv"
INPUT_BANNED = "graphics_banned_language.csv"
INPUT_USAGE_MAP = "graphics_asset_usage_map.csv"
INPUT_LAYOUT = "graphics_layout_blueprint.csv"
OUT_DIR = Path("graphics_clean_prompts")
OUT_REPORT = "graphics_prompt_clean_report.md"
OUT_MANIFEST = "graphics_prompt_clean_manifest.json"

DEFAULT_BANNED = [
    "Verified Final",
    "VERIFIED FINAL",
    "Winner",
    "Loser",
    "BUNDLE LOCKED FACTS",
    "source-safe context",
    "graphics-safe context",
    "Do not alter",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def prompt_for_bundle(prompts_md: str, bundle_name: str) -> str:
    if not prompts_md:
        return ""
    escaped = re.escape(bundle_name)
    pat = rf"##\s+{escaped}\s*\n(.*?)(?=\n##\s+|\Z)"
    m = re.search(pat, prompts_md, flags=re.S)
    if m:
        return f"# {bundle_name}\n\n{m.group(1).strip()}\n"
    return prompts_md


def banned_rows() -> List[Dict[str, str]]:
    rows = read_csv(INPUT_BANNED)
    if rows:
        return rows
    return [{"term": t, "replacement": "", "severity": "hard_ban", "reason": "fallback"} for t in DEFAULT_BANNED]


def replacement_map(rows: List[Dict[str, str]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for r in rows:
        term = clean(r.get("term"))
        repl = str(r.get("replacement") or "")
        if term:
            out[term.lower()] = repl
    return out


def line_should_drop(line: str) -> bool:
    lower = line.lower()
    drop_patterns = [
        "bundle locked facts",
        "source-safe context",
        "graphics-safe context",
        "do not alter",
        "accuracy lock",
        "locked facts",
        "approved exact logos only",
    ]
    return any(p in lower for p in drop_patterns)


def sanitize_text(text: str, repl_map: Dict[str, str]) -> Tuple[str, Dict[str, int]]:
    removed = 0
    replaced = 0
    lines_out: List[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        if line_should_drop(line):
            removed += 1
            continue
        if line.strip().startswith("```"):
            removed += 1
            continue
        new_line = line
        for term, repl in repl_map.items():
            if term and re.search(re.escape(term), new_line, flags=re.I):
                if repl:
                    new_line = re.sub(re.escape(term), repl, new_line, flags=re.I)
                else:
                    new_line = re.sub(re.escape(term), "", new_line, flags=re.I)
                replaced += 1
        new_line = re.sub(r"\s+", " ", new_line).strip()
        if new_line:
            lines_out.append(new_line)
        elif lines_out and lines_out[-1] != "":
            lines_out.append("")
    collapsed: List[str] = []
    for line in lines_out:
        if line == "" and (not collapsed or collapsed[-1] == ""):
            continue
        collapsed.append(line)
    text_out = "\n".join(collapsed).strip()
    return text_out, {"removed_lines": removed, "replacements": replaced}


def sanitize_inline(text: str, repl_map: Dict[str, str]) -> str:
    value = clean(text)
    if not value:
        return ""
    for term, repl in repl_map.items():
        if term:
            value = re.sub(re.escape(term), repl, value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" -:;,.\t")
    # Drop any leftover internal-language fragments.
    if any(bit in value.lower() for bit in ["verified final", "winner", "loser", "bundle locked facts", "source-safe context", "graphics-safe context", "do not alter"]):
        return ""
    return value


def build_display_section(bundle_slug: str, display_rows: List[Dict[str, str]], repl_map: Dict[str, str]) -> List[str]:
    rows = [r for r in display_rows if clean(r.get("bundle_slug")) == bundle_slug]
    if not rows:
        return []
    lines = ["## Display-safe slide copy", ""]
    for r in sorted(rows, key=lambda x: int(x.get("slide_number") or 0)):
        lines += [
            f"### Slide {r.get('slide_number')} - {clean(r.get('slide_role')) or 'slide'}",
            f"- Headline: {sanitize_inline(r.get('display_headline'), repl_map)}",
            f"- Subhead: {sanitize_inline(r.get('display_subhead'), repl_map)}",
            f"- Kicker: {sanitize_inline(r.get('display_kicker'), repl_map)}",
        ]
        score_copy = sanitize_inline(r.get('score_copy'), repl_map)
        if score_copy:
            lines.append(f"- Score copy: {score_copy}")
        cta_copy = sanitize_inline(r.get('cta_copy'), repl_map)
        if cta_copy:
            lines.append(f"- CTA: {cta_copy}")
        notes = sanitize_inline(r.get('notes'), repl_map)
        if notes:
            lines.append(f"- Notes: {notes}")
        lines.append("")
    return lines


def build_layout_section(bundle_slug: str, layout_rows: List[Dict[str, str]], repl_map: Dict[str, str]) -> List[str]:
    rows = [r for r in layout_rows if clean(r.get("bundle_slug")) == bundle_slug]
    if not rows:
        return []
    lines = ["## Layout and composition requirements", ""]
    for r in sorted(rows, key=lambda x: int(x.get("slide_number") or 0)):
        parts = []
        if clean(r.get("required_left_entity")) or clean(r.get("required_right_entity")):
            parts.append(f"Left/Right entities: {clean(r.get('required_left_entity'))} | {clean(r.get('required_right_entity'))}")
        if clean(r.get("required_left_people")) or clean(r.get("required_right_people")):
            parts.append(f"Required people count: left {clean(r.get('required_left_people'))}, right {clean(r.get('required_right_people'))}")
        if clean(r.get("must_include_terms")):
            must_include = sanitize_inline(r.get('must_include_terms'), repl_map)
        if must_include:
            parts.append(f"Must include: {must_include}")
        composition = sanitize_inline(r.get('composition_rule'), repl_map)
        if composition:
            parts.append(f"Composition: {composition}")
        notes = sanitize_inline(r.get('notes'), repl_map)
        if notes:
            parts.append(f"Notes: {notes}")
        lines.append(f"- Slide {r.get('slide_number')}: " + " | ".join(parts))
    lines.append("")
    return lines


def build_asset_section(bundle_slug: str, usage_rows: List[Dict[str, str]], repl_map: Dict[str, str]) -> List[str]:
    rows = [r for r in usage_rows if clean(r.get("bundle_slug")) == bundle_slug]
    if not rows:
        return []
    lines = ["## Attached asset identity rules", ""]
    for r in rows:
        entity = clean(r.get("entity_name"))
        role = clean(r.get("asset_role"))
        team = clean(r.get("team_name"))
        allow = sanitize_inline(r.get("allowed_usage"), repl_map)
        forbid = sanitize_inline(r.get("forbidden_usage"), repl_map)
        bits = [f"{role}: {entity}"]
        if team:
            bits.append(team)
        if allow:
            bits.append(allow)
        if forbid:
            bits.append(f"Never: {forbid}")
        lines.append("- " + " | ".join(bits))
    lines.append("")
    return lines


def build_prompt(bundle_name: str, bundle_slug: str, raw_prompt: str, display_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]], usage_rows: List[Dict[str, str]], banned_terms: List[str], repl_map: Dict[str, str]) -> Tuple[str, Dict[str, int]]:
    cleaned_raw, stats = sanitize_text(raw_prompt, repl_map)
    lines = [
        f"# HSD Graphics Prompt: {bundle_name}",
        "",
        "Use the attached files only.",
        "Use the attached logo files and attached player/person image files exactly as mapped. Do not fetch, substitute, or invent any logos, player images, bodies, jerseys, or numbers.",
        "Treat the game facts, scores, team names, and player names as locked facts and preserve them exactly.",
        "Render only display-safe editorial language. Never render internal QA or prompt-control language.",
        "Create polished Her Sports Daily graphics with premium editorial sports-media styling.",
        "Output separate slide files.",
        "",
    ]
    if cleaned_raw:
        lines += ["## Cleaned production brief", "", cleaned_raw, ""]
    lines += build_display_section(bundle_slug, display_rows, repl_map)
    lines += build_layout_section(bundle_slug, layout_rows, repl_map)
    lines += build_asset_section(bundle_slug, usage_rows, repl_map)
    lines += [
        "## Internal-language rule",
        "",
        "Never render internal QA or verification labels. If a line sounds like workflow language instead of editorial sports language, rewrite it before rendering.",
        "",
        "## Final reminder",
        "",
        "Use natural, human sports-editor phrasing. Keep the facts exact and the wording clean.",
        "",
    ]
    return "\n".join(lines).strip() + "\n", stats


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompts_md = read_text(INPUT_PROMPTS)
    render_manifest = read_json(INPUT_RENDER_MANIFEST)
    display_rows = read_csv(INPUT_DISPLAY_COPY)
    usage_rows = read_csv(INPUT_USAGE_MAP)
    layout_rows = read_csv(INPUT_LAYOUT)
    banned = banned_rows()
    banned_terms = [clean(r.get("term")) for r in banned if clean(r.get("term"))]
    repl_map = replacement_map(banned)
    report = ["# HSD Graphics Prompt Sanitizer v1.7.2", "", f"Generated: {now()}", ""]
    bundles_out = []
    for b in render_manifest.get("bundles", []):
        slug = clean(b.get("post_slug")) or clean(b.get("bundle_slug"))
        name = clean(b.get("bundle_name")) or slug
        if not slug:
            continue
        raw = prompt_for_bundle(prompts_md, name)
        prompt_text, stats = build_prompt(name, slug, raw, display_rows, layout_rows, usage_rows, banned_terms, repl_map)
        folder = OUT_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)
        out_path = folder / "00_PROMPT_TO_PASTE.md"
        out_path.write_text(prompt_text, encoding="utf-8")
        bundles_out.append({
            "bundle_slug": slug,
            "bundle_name": name,
            "prompt_path": out_path.as_posix(),
            "raw_prompt_chars": len(raw),
            "clean_prompt_chars": len(prompt_text),
            **stats,
        })
        report += [
            f"## {name}",
            "",
            f"- Prompt path: `{out_path.as_posix()}`",
            f"- Raw prompt chars: {len(raw)}",
            f"- Clean prompt chars: {len(prompt_text)}",
            f"- Removed internal lines: {stats.get('removed_lines', 0)}",
            f"- Term replacements/removals: {stats.get('replacements', 0)}",
            "",
        ]
    Path(OUT_REPORT).write_text("\n".join(report), encoding="utf-8")
    Path(OUT_MANIFEST).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "bundle_count": len(bundles_out),
        "outputs": [OUT_DIR.as_posix(), OUT_REPORT, OUT_MANIFEST],
        "bundles": bundles_out,
    }, indent=2), encoding="utf-8")
    print("Created HSD graphics prompt sanitizer outputs")
    print(json.dumps({"bundle_count": len(bundles_out)}, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-action-photo-review-deck-ui-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_review_deck_ui_v1.py"
DEFAULT_BOARD_CSV = Path("outputs/local/latest/files/action_photo_next_candidate_board/action_photo_next_candidate_board.csv")
DEFAULT_PROOF_MANIFEST = Path("outputs/local/latest/files/jackie_young_renderer_proof_v1/manifest.json")
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_review_deck_ui_v1")
HTML_NAME = "action_photo_review_deck.html"
DECISION_TEMPLATE_NAME = "manual_decision_export_template.csv"
REPORT_NAME = "action_photo_review_deck_report.md"
MANIFEST_NAME = "manifest.json"
LEGACY_BROWSER_STORAGE_KEY = "hsd_action_photo_review_deck_v1"

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "approved_marker_writes": False,
    "asset_approved": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "headshot_writes": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "source_auto_enabled": False,
}

DECISION_FIELDS = [
    "deck_item_id",
    "item_kind",
    "candidate_id",
    "entity_id",
    "source_url",
    "image_or_render_url",
    "operator_decision",
    "operator_notes",
    "manual_reviewer",
    "reviewed_at_utc",
    "formal_intake_next_action",
    "review_only",
    "download_approved",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def read_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def file_uri(path: str | Path) -> str:
    return Path(path).resolve(strict=False).as_uri()


def candidate_items(board_rows: list[dict[str, str]], limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in board_rows[:limit]:
        candidate_id = row.get("scout_candidate_id") or row.get("candidate_queue_id") or row.get("board_id") or ""
        items.append(
            {
                "deck_item_id": f"candidate_{candidate_id or len(items) + 1}",
                "item_kind": "candidate_source",
                "candidate_id": candidate_id,
                "entity_id": row.get("entity_id", ""),
                "title": candidate_id or row.get("board_id", "Candidate"),
                "subtitle": row.get("entity_id", ""),
                "source_url": row.get("source_url", ""),
                "image_or_render_url": row.get("candidate_image_url", ""),
                "image_alt": row.get("image_alt", ""),
                "source_domain": row.get("source_domain", ""),
                "score": row.get("score", ""),
                "visual_priority": row.get("visual_priority", ""),
                "quality_tier": row.get("candidate_quality_tier", ""),
                "identity_confidence": row.get("identity_confidence", ""),
                "face_likely_visible": row.get("face_likely_visible", ""),
                "body_margin_likely": row.get("body_margin_likely", ""),
                "four_by_five_crop_potential": row.get("four_by_five_crop_potential", ""),
                "text_safe_negative_space": row.get("text_safe_negative_space", ""),
                "risk_flags": row.get("candidate_risk_flags", ""),
                "recommended_default": "needs_manual_visual_check",
            }
        )
    return items


def proof_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = manifest.get("proof_rows") if isinstance(manifest, dict) else []
    if not isinstance(rows, list):
        return []
    items: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        output_path = row.get("output_png_path", "")
        render_url = file_uri(output_path) if output_path else ""
        proof_id = str(row.get("proof_id", ""))
        items.append(
            {
                "deck_item_id": f"proof_{proof_id or len(items) + 1}",
                "item_kind": "renderer_proof",
                "candidate_id": "APCS039",
                "entity_id": "wnba_las_vegas_aces_jackie_young",
                "title": proof_id,
                "subtitle": str(row.get("proof_name", "")),
                "source_url": str(manifest.get("source_image_path", "")),
                "image_or_render_url": render_url,
                "image_alt": str(row.get("proof_name", "")),
                "source_domain": "local_quarantine_renderer_proof",
                "score": "",
                "visual_priority": "P1_visual_review_now",
                "quality_tier": str(row.get("visual_strength", "")),
                "identity_confidence": "human_selected_candidate",
                "face_likely_visible": "review_image",
                "body_margin_likely": "review_image",
                "four_by_five_crop_potential": "rendered_4x5",
                "text_safe_negative_space": "review_image",
                "risk_flags": str(row.get("known_limit", "")),
                "recommended_default": "review_render_proof",
            }
        )
    return items


def decision_template_rows(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in items:
        rows.append(
            {
                "deck_item_id": str(item["deck_item_id"]),
                "item_kind": str(item["item_kind"]),
                "candidate_id": str(item["candidate_id"]),
                "entity_id": str(item["entity_id"]),
                "source_url": str(item["source_url"]),
                "image_or_render_url": str(item["image_or_render_url"]),
                "operator_decision": "",
                "operator_notes": "",
                "manual_reviewer": "",
                "reviewed_at_utc": "",
                "formal_intake_next_action": "",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    return rows


def js_payload(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, ensure_ascii=False).replace("</", "<\\/")


def browser_storage_key(items: list[dict[str, Any]]) -> str:
    basis = json.dumps(
        [
            {
                "deck_item_id": item.get("deck_item_id", ""),
                "candidate_id": item.get("candidate_id", ""),
                "entity_id": item.get("entity_id", ""),
                "image_or_render_url": item.get("image_or_render_url", ""),
            }
            for item in items
        ],
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]
    return f"{LEGACY_BROWSER_STORAGE_KEY}:{digest}"


def build_html(items: list[dict[str, Any]], storage_key: str | None = None) -> str:
    payload = js_payload(items)
    storage_key = storage_key or browser_storage_key(items)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>HSD Action Photo Review Deck</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b0f16;
      --panel: #151b24;
      --ink: #f4f6fa;
      --muted: #aeb8c6;
      --line: #2a3342;
      --accent: #e7b75b;
      --bad: #f06464;
      --good: #5bd694;
      --hold: #8fb7ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at 20% 0%, #182131 0, #0b0f16 36rem);
      color: var(--ink);
      font: 15px/1.45 Arial, Helvetica, sans-serif;
    }}
    header {{
      display: grid;
      gap: 0.35rem;
      padding: 24px clamp(18px, 4vw, 44px) 12px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0; font-size: clamp(24px, 4vw, 42px); letter-spacing: 0; }}
    header p {{ margin: 0; color: var(--muted); max-width: 980px; }}
    main {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 18px;
      padding: 18px clamp(18px, 4vw, 44px) 34px;
    }}
    .stage {{
      min-height: 680px;
      border: 1px solid var(--line);
      background: rgba(14, 19, 28, 0.82);
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
    }}
    .card-head, .card-foot {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
    }}
    .card-foot {{ border-top: 1px solid var(--line); border-bottom: 0; flex-wrap: wrap; }}
    .title {{ font-size: 24px; font-weight: 800; }}
    .subtitle {{ color: var(--muted); }}
    .viewer {{
      display: grid;
      place-items: center;
      min-height: 0;
      padding: 18px;
      background: #05070a;
      overflow: hidden;
    }}
    .swipe-card {{
      position: relative;
      display: grid;
      place-items: center;
      max-width: 100%;
      cursor: grab;
      touch-action: pan-y;
      user-select: none;
      transition: transform 160ms ease, opacity 160ms ease;
      will-change: transform;
    }}
    .swipe-card.dragging {{
      cursor: grabbing;
      transition: none;
    }}
    .swipe-card img {{
      max-width: 100%;
      max-height: 72vh;
      object-fit: contain;
      border: 1px solid #3a4352;
      background: #111;
      box-shadow: 0 22px 60px rgba(0,0,0,.45);
      pointer-events: none;
    }}
    .swipe-label {{
      position: absolute;
      top: 22px;
      z-index: 2;
      opacity: 0;
      border: 2px solid currentColor;
      padding: 8px 12px;
      font-weight: 900;
      letter-spacing: 0;
      background: rgba(5,7,10,.78);
      pointer-events: none;
    }}
    .swipe-reject {{
      left: 18px;
      color: var(--bad);
      transform: rotate(-8deg);
    }}
    .swipe-carry {{
      right: 18px;
      color: var(--good);
      transform: rotate(8deg);
    }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    button, a.button {{
      border: 1px solid var(--line);
      background: #1d2532;
      color: var(--ink);
      padding: 10px 13px;
      text-decoration: none;
      cursor: pointer;
      font-weight: 700;
      min-height: 42px;
    }}
    button:hover, a.button:hover {{ border-color: var(--accent); }}
    .good {{ background: #123525; border-color: #286b4a; }}
    .bad {{ background: #3a171b; border-color: #7b2c33; }}
    .hold {{ background: #17233c; border-color: #334d82; }}
    aside {{
      border: 1px solid var(--line);
      background: rgba(15, 20, 29, 0.92);
      padding: 16px;
      display: grid;
      gap: 14px;
      align-content: start;
    }}
    .meta {{
      display: grid;
      gap: 8px;
    }}
    .meta div {{
      display: grid;
      grid-template-columns: 128px minmax(0, 1fr);
      gap: 8px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(255,255,255,.07);
    }}
    .meta b {{ color: #dce3ee; }}
    .meta span {{ color: var(--muted); overflow-wrap: anywhere; }}
    textarea {{
      width: 100%;
      min-height: 92px;
      resize: vertical;
      background: #0d121a;
      color: var(--ink);
      border: 1px solid var(--line);
      padding: 10px;
      font: inherit;
    }}
    .queue {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding: 12px 0 2px;
    }}
    .pill {{
      white-space: nowrap;
      border: 1px solid var(--line);
      padding: 7px 9px;
      color: var(--muted);
      cursor: pointer;
    }}
    .pill.active {{ color: var(--ink); border-color: var(--accent); }}
    .pill[data-decision=\"carry_forward_for_formal_intake\"] {{ border-color: var(--good); }}
    .pill[data-decision^=\"reject\"] {{ border-color: var(--bad); }}
    .pill[data-decision=\"hold_manual_check\"] {{ border-color: var(--hold); }}
    .guardrail {{
      color: var(--muted);
      font-size: 13px;
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }}
    .export-panel {{
      display: grid;
      gap: 10px;
      margin-top: 10px;
    }}
    .export-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    #csv-output {{
      min-height: 170px;
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre;
    }}
    #export-status {{
      color: var(--muted);
      font-size: 13px;
      min-height: 18px;
    }}
    .progress {{
      display: grid;
      gap: 7px;
    }}
    .progress-track {{
      height: 8px;
      background: #0b1018;
      border: 1px solid var(--line);
      overflow: hidden;
    }}
    .progress-fill {{
      display: block;
      height: 100%;
      width: 0;
      background: linear-gradient(90deg, var(--bad), var(--hold), var(--good));
      transition: width 160ms ease;
    }}
    #progress-label {{
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 920px) {{
      main {{ grid-template-columns: 1fr; }}
      .stage {{ min-height: 560px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>HSD Action Photo Review Deck</h1>
    <p>Manual review surface only. Decisions exported here do not approve assets, do not download files, and do not mark anything publish-ready.</p>
  </header>
  <main>
    <section class=\"stage\">
      <div class=\"card-head\">
        <div>
          <div class=\"title\" id=\"title\"></div>
          <div class=\"subtitle\" id=\"subtitle\"></div>
        </div>
        <div id=\"count\"></div>
      </div>
      <div class=\"viewer\">
        <div class=\"swipe-card\" id=\"swipe-card\" aria-label=\"Swipe review card\">
          <div class=\"swipe-label swipe-reject\" id=\"swipe-reject\">Reject</div>
          <img id=\"image\" alt=\"\">
          <div class=\"swipe-label swipe-carry\" id=\"swipe-carry\">Carry Forward</div>
        </div>
      </div>
      <div class=\"card-foot\">
        <div class=\"actions\">
          <button class=\"bad\" data-action=\"reject_wrong_person\">Reject Wrong Person</button>
          <button class=\"bad\" data-action=\"reject_bad_crop\">Reject Bad Crop</button>
          <button class=\"bad\" data-action=\"reject_group_photo\">Reject Group Photo</button>
          <button class=\"hold\" data-action=\"hold_manual_check\">Hold / Unsure</button>
          <button class=\"good\" data-action=\"carry_forward_for_formal_intake\">Carry Forward</button>
        </div>
        <div class=\"actions\">
          <button id=\"prev\">Back</button>
          <button id=\"next\">Next</button>
          <button id=\"clear-decision\">Clear Decision</button>
          <a id=\"source\" class=\"button\" target=\"_blank\" rel=\"noreferrer\">Open Source</a>
        </div>
      </div>
    </section>
    <aside>
      <div class=\"progress\">
        <div class=\"progress-track\"><span class=\"progress-fill\" id=\"progress-fill\"></span></div>
        <div id=\"progress-label\"></div>
      </div>
      <div class=\"queue\" id=\"queue\"></div>
      <div class=\"meta\" id=\"meta\"></div>
      <label>
        Operator notes
        <textarea id=\"notes\" placeholder=\"Optional manual note for exported decision CSV\"></textarea>
      </label>
      <div class=\"export-panel\">
        <div class=\"export-actions\">
          <button id=\"export\">Export Decision CSV</button>
          <button id=\"copy-csv\" type=\"button\">Copy CSV</button>
          <a id=\"download-link\" class=\"button\" download=\"hsd_action_photo_review_deck_manual_decisions.csv\" hidden>Download CSV Again</a>
        </div>
        <textarea id=\"csv-output\" readonly placeholder=\"Exported CSV will appear here if the browser blocks or hides the file download.\"></textarea>
        <div id=\"export-status\"></div>
      </div>
      <div class=\"guardrail\">
        Exported decisions are a manual intake surface. `download_approved` remains `no`; a separate formal intake is required before any later quarantine-only download.
      </div>
    </aside>
  </main>
  <script>
    const items = {payload};
    const legacyStateKey = "{LEGACY_BROWSER_STORAGE_KEY}";
    const stateKey = "{html.escape(storage_key)}";
    let index = 0;
    let exportObjectUrl = "";
    let swipe = {{ active: false, startX: 0, startY: 0, dx: 0, dy: 0 }};
    function parseStoredDecisions(key) {{
      try {{ return JSON.parse(localStorage.getItem(key) || "{{}}"); }}
      catch (error) {{ return {{}}; }}
    }}
    function loadScopedDecisions() {{
      const scoped = parseStoredDecisions(stateKey);
      const legacy = parseStoredDecisions(legacyStateKey);
      const validIds = new Set(items.map(item => item.deck_item_id));
      const migrated = {{}};
      Object.entries(legacy).forEach(([key, value]) => {{
        if (validIds.has(key)) migrated[key] = value;
      }});
      return Object.assign(migrated, scoped);
    }}
    const decisions = loadScopedDecisions();
    const fields = {json.dumps(DECISION_FIELDS)};

    function save() {{ localStorage.setItem(stateKey, JSON.stringify(decisions)); }}
    function esc(value) {{ return String(value ?? ""); }}
    function active() {{ return items[index]; }}
    function setDecision(value) {{
      const item = active();
      decisions[item.deck_item_id] = decisions[item.deck_item_id] || {{}};
      decisions[item.deck_item_id].operator_decision = value;
      decisions[item.deck_item_id].operator_notes = document.getElementById("notes").value;
      decisions[item.deck_item_id].reviewed_at_utc = new Date().toISOString();
      save();
      if (index < items.length - 1) index += 1;
      render();
    }}
    function renderQueue() {{
      const queue = document.getElementById("queue");
      queue.innerHTML = "";
      items.forEach((item, idx) => {{
        const pill = document.createElement("button");
        pill.className = "pill" + (idx === index ? " active" : "");
        pill.textContent = item.candidate_id || item.title || idx + 1;
        pill.dataset.decision = decisions[item.deck_item_id]?.operator_decision || "";
        pill.onclick = () => {{ index = idx; render(); }};
        queue.appendChild(pill);
      }});
    }}
    function render() {{
      const item = active();
      const decision = decisions[item.deck_item_id] || {{}};
      document.getElementById("title").textContent = item.title || item.candidate_id || item.deck_item_id;
      document.getElementById("subtitle").textContent = item.subtitle || item.item_kind;
      document.getElementById("count").textContent = `${{index + 1}} / ${{items.length}}`;
      const image = document.getElementById("image");
      image.src = item.image_or_render_url;
      image.alt = item.image_alt || item.title || "";
      resetSwipeCard();
      const source = document.getElementById("source");
      source.href = item.source_url || item.image_or_render_url || "#";
      source.textContent = item.item_kind === "renderer_proof" ? "Open Render" : "Open Source";
      document.getElementById("notes").value = decision.operator_notes || "";
      document.getElementById("meta").innerHTML = [
        ["Kind", item.item_kind],
        ["Candidate", item.candidate_id],
        ["Entity", item.entity_id],
        ["Priority", item.visual_priority],
        ["Tier", item.quality_tier],
        ["Identity", item.identity_confidence],
        ["Face", item.face_likely_visible],
        ["Body margin", item.body_margin_likely],
        ["4:5", item.four_by_five_crop_potential],
        ["Text safe", item.text_safe_negative_space],
        ["Risk", item.risk_flags],
        ["Decision", decision.operator_decision || ""]
      ].map(([k, v]) => `<div><b>${{k}}</b><span>${{esc(v)}}</span></div>`).join("");
      renderQueue();
      renderProgress();
    }}
    function renderProgress() {{
      const filled = filledDecisionCount();
      const percent = items.length ? Math.round((filled / items.length) * 100) : 0;
      document.getElementById("progress-fill").style.width = `${{percent}}%`;
      document.getElementById("progress-label").textContent = `${{filled}} / ${{items.length}} decisions recorded`;
    }}
    function resetSwipeCard() {{
      const card = document.getElementById("swipe-card");
      if (!card) return;
      card.classList.remove("dragging");
      card.style.transform = "";
      card.style.opacity = "1";
      document.getElementById("swipe-reject").style.opacity = "0";
      document.getElementById("swipe-carry").style.opacity = "0";
    }}
    function updateSwipeVisual(dx, dy) {{
      const card = document.getElementById("swipe-card");
      const reject = document.getElementById("swipe-reject");
      const carry = document.getElementById("swipe-carry");
      const rotate = Math.max(-14, Math.min(14, dx / 18));
      const opacity = Math.min(1, Math.abs(dx) / 120);
      card.style.transform = `translate(${{dx}}px, ${{dy * 0.24}}px) rotate(${{rotate}}deg)`;
      card.style.opacity = String(Math.max(0.78, 1 - Math.abs(dx) / 820));
      reject.style.opacity = dx < 0 ? String(opacity) : "0";
      carry.style.opacity = dx > 0 ? String(opacity) : "0";
    }}
    function finishSwipe() {{
      const threshold = 112;
      const dx = swipe.dx;
      document.getElementById("swipe-card").classList.remove("dragging");
      swipe.active = false;
      if (dx >= threshold) {{
        applySwipeDecision("carry_forward_for_formal_intake");
        return;
      }}
      if (dx <= -threshold) {{
        applySwipeDecision("reject_bad_crop");
        return;
      }}
      resetSwipeCard();
    }}
    function applySwipeDecision(value) {{
      setDecision(value);
    }}
    function clearDecision() {{
      const item = active();
      delete decisions[item.deck_item_id];
      save();
      render();
    }}
    function csvCell(value) {{
      const s = String(value ?? "");
      return /[\",\\n]/.test(s) ? `"${{s.replaceAll('"', '""')}}"` : s;
    }}
    function buildCsvText() {{
      const rows = items.map(item => {{
        const decision = decisions[item.deck_item_id] || {{}};
        return {{
          deck_item_id: item.deck_item_id,
          item_kind: item.item_kind,
          candidate_id: item.candidate_id,
          entity_id: item.entity_id,
          source_url: item.source_url,
          image_or_render_url: item.image_or_render_url,
          operator_decision: decision.operator_decision || "",
          operator_notes: decision.operator_notes || "",
          manual_reviewer: "",
          reviewed_at_utc: decision.reviewed_at_utc || "",
          formal_intake_next_action: decision.operator_decision === "carry_forward_for_formal_intake" ? "prepare_separate_formal_quarantine_download_intake_if_needed" : "",
          review_only: "true",
          download_approved: "no",
          asset_downloads: "false",
          approval_state_change: "false",
          publish_ready: "false",
          publishing: "false"
        }};
      }});
      return [fields.join(","), ...rows.map(row => fields.map(field => csvCell(row[field])).join(","))].join("\\n") + "\\n";
    }}
    function filledDecisionCount() {{
      return Object.values(decisions).filter(decision => decision.operator_decision).length;
    }}
    function showCsvFallback(text) {{
      const output = document.getElementById("csv-output");
      const status = document.getElementById("export-status");
      const link = document.getElementById("download-link");
      output.value = text;
      if (exportObjectUrl) URL.revokeObjectURL(exportObjectUrl);
      exportObjectUrl = URL.createObjectURL(new Blob([text], {{ type: "text/csv" }}));
      link.href = exportObjectUrl;
      link.hidden = false;
      status.textContent = `CSV ready: ${{filledDecisionCount()}} manual decisions recorded across ${{items.length}} deck items. If no file downloaded, use Copy CSV or Download CSV Again.`;
    }}
    function exportCsv() {{
      const text = buildCsvText();
      showCsvFallback(text);
      const blob = new Blob([text], {{ type: "text/csv" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "hsd_action_photo_review_deck_manual_decisions.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }}
    async function copyCsv() {{
      const output = document.getElementById("csv-output");
      const status = document.getElementById("export-status");
      if (!output.value) showCsvFallback(buildCsvText());
      try {{
        await navigator.clipboard.writeText(output.value);
        status.textContent = `CSV copied: ${{filledDecisionCount()}} manual decisions recorded across ${{items.length}} deck items.`;
      }} catch (error) {{
        output.focus();
        output.select();
        document.execCommand("copy");
        status.textContent = "CSV selected/copied with browser fallback. If copy did not land, press Ctrl+C while the CSV box is selected.";
      }}
    }}
    document.querySelectorAll("[data-action]").forEach(button => button.addEventListener("click", () => setDecision(button.dataset.action)));
    document.getElementById("notes").addEventListener("input", () => {{
      const item = active();
      decisions[item.deck_item_id] = decisions[item.deck_item_id] || {{}};
      decisions[item.deck_item_id].operator_notes = document.getElementById("notes").value;
      save();
    }});
    document.getElementById("prev").onclick = () => {{ index = Math.max(0, index - 1); render(); }};
    document.getElementById("next").onclick = () => {{ index = Math.min(items.length - 1, index + 1); render(); }};
    document.getElementById("clear-decision").onclick = clearDecision;
    document.getElementById("export").onclick = exportCsv;
    document.getElementById("copy-csv").onclick = copyCsv;
    const swipeCard = document.getElementById("swipe-card");
    swipeCard.addEventListener("pointerdown", event => {{
      swipe = {{ active: true, startX: event.clientX, startY: event.clientY, dx: 0, dy: 0 }};
      swipeCard.classList.add("dragging");
      swipeCard.setPointerCapture(event.pointerId);
    }});
    swipeCard.addEventListener("pointermove", event => {{
      if (!swipe.active) return;
      swipe.dx = event.clientX - swipe.startX;
      swipe.dy = event.clientY - swipe.startY;
      updateSwipeVisual(swipe.dx, swipe.dy);
    }});
    swipeCard.addEventListener("pointerup", finishSwipe);
    swipeCard.addEventListener("pointercancel", () => {{
      swipe.active = false;
      resetSwipeCard();
    }});
    window.addEventListener("keydown", event => {{
      if (event.target && ["TEXTAREA", "INPUT"].includes(event.target.tagName)) return;
      if (event.key === "ArrowLeft") setDecision("reject_bad_crop");
      if (event.key === "ArrowRight") setDecision("carry_forward_for_formal_intake");
      if (event.key === "ArrowDown") setDecision("hold_manual_check");
      if (event.key === "Backspace") clearDecision();
    }});
    render();
  </script>
</body>
</html>
"""


def build_report(manifest: dict[str, Any]) -> str:
    return f"""# Action Photo Review Deck UI V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet creates a local review-only approve/reject deck for action-photo candidates and renderer proofs. It is an operator decision surface only. It does not download assets, approve assets, move assets, mark anything publish-ready, or publish.

## Outputs

- HTML deck: `{manifest['html_path']}`
- Manual decision template: `{manifest['decision_template_path']}`
- Manifest: `{manifest['manifest_path']}`
- Browser storage key: `{manifest['browser_storage_key']}`

## Review Flow

1. Open the HTML deck locally.
2. Review each candidate/proof visually.
3. Choose carry forward, reject wrong person, reject bad crop, reject group photo, or hold.
4. Export the decision CSV from the browser.
5. Use any carry-forward rows as input to a separate formal intake lane only when needed.

## Guardrails

- review_only=true
- download_approved=no by default
- asset_downloads=false
- approval_state_change=false
- publish_ready=false
- publishing=false
"""


def build_packet(*, board_csv: Path, proof_manifest: Path, output_dir: Path, limit: int, head_commit: str = "") -> dict[str, Any]:
    board_csv = board_csv.resolve(strict=False)
    proof_manifest = proof_manifest.resolve(strict=False)
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)

    board_rows = read_csv_rows(board_csv)
    manifest_payload = read_json_payload(proof_manifest)
    items = candidate_items(board_rows, limit) + proof_items(manifest_payload)
    decision_rows = decision_template_rows(items)
    storage_key = browser_storage_key(items)

    html_path = write_text(output_dir / HTML_NAME, build_html(items, storage_key), if_changed=False)
    decision_path = write_csv(output_dir / DECISION_TEMPLATE_NAME, decision_rows, DECISION_FIELDS)
    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "action_photo_review_deck_ui_ready",
        "repo_head": head_commit,
        "board_csv": board_csv.as_posix(),
        "proof_manifest": proof_manifest.as_posix(),
        "output_dir": output_dir.as_posix(),
        "html_path": html_path.as_posix(),
        "decision_template_path": decision_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "report_path": report_path.as_posix(),
        "candidate_item_count": len([item for item in items if item["item_kind"] == "candidate_source"]),
        "renderer_proof_item_count": len([item for item in items if item["item_kind"] == "renderer_proof"]),
        "deck_item_count": len(items),
        "decision_fields": DECISION_FIELDS,
        "browser_storage_key": storage_key,
        "legacy_browser_storage_key": LEGACY_BROWSER_STORAGE_KEY,
        "review_only": True,
        "download_approved_default": "no",
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local review-only action-photo approve/reject deck.")
    parser.add_argument("--board-csv", default=DEFAULT_BOARD_CSV.as_posix())
    parser.add_argument("--proof-manifest", default=DEFAULT_PROOF_MANIFEST.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = resolve_output_dir(args.output_dir or None)
    manifest = build_packet(
        board_csv=resolve_path(args.board_csv),
        proof_manifest=resolve_path(args.proof_manifest),
        output_dir=output_dir,
        limit=max(1, args.limit),
        head_commit=args.head_commit,
    )
    print(json.dumps({"version": VERSION, "status": manifest["status"], "deck_item_count": manifest["deck_item_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

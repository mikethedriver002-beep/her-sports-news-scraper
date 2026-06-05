
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

OUTPUT_DIR = Path("dashboard")
OUTPUT_FILE = OUTPUT_DIR / "index.html"

CSV_FILES = {
    "command": "daily_command_file.csv",
    "dashboard": "master_posting_dashboard.csv",
    "context": "story_context_enriched.csv",
    "captions": "caption_bank_v2.csv",
    "queue_csv": "today_graphics_queue.csv",
}

TEXT_FILES = {
    "graphics_queue": "today_graphics_queue.md",
    "top3": "top_3_graphic_packets.md",
    "reels": "reel_script_package.md",
    "hub": "hsd_graphics_system_hub.md",
}

def clean(value: str) -> str:
    value = value or ""
    return re.sub(r"\s+", " ", str(value)).strip()

def load_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")

def split_graphic_packets(markdown_text: str) -> List[Dict[str, str]]:
    if not markdown_text:
        return []
    parts = re.split(r"(?=^## GRAPHIC\s+\d+:)", markdown_text, flags=re.M)
    packets = []
    for part in parts:
        part = part.strip()
        if not part.startswith("## GRAPHIC"):
            continue
        first_line = part.splitlines()[0]
        m = re.match(r"## GRAPHIC\s+(\d+):\s*(.*)", first_line)
        packet_num = m.group(1) if m else ""
        headline = clean(m.group(2)) if m else first_line.replace("##", "").strip()
        decision = ""
        action = ""
        template = ""
        family = ""
        for line in part.splitlines():
            if line.startswith("**Action:**"):
                action = clean(line.replace("**Action:**", ""))
            elif line.startswith("**Decision:**"):
                decision = clean(line.replace("**Decision:**", ""))
            elif line.startswith("**Template:**"):
                template = clean(line.replace("**Template:**", ""))
            elif line.startswith("**Content family:**"):
                family = clean(line.replace("**Content family:**", ""))
        packets.append({
            "packet_num": packet_num,
            "headline": headline,
            "decision": decision,
            "action": action,
            "template": template,
            "content_family": family,
            "packet": part,
        })
    return packets

def json_for_html(data) -> str:
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

def create_html(data: Dict) -> str:
    data_json = json_for_html(data)
    generated_at = data["generated_at"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Her Sports Daily Dashboard</title>
<style>
:root {{
  --bg:#0f1020;
  --panel:#181a2f;
  --panel2:#222543;
  --text:#f7f3ff;
  --muted:#b9b2d0;
  --accent:#ff4fd8;
  --accent2:#7cf7ff;
  --good:#70ffb0;
  --warn:#ffd166;
  --danger:#ff6b6b;
  --border:rgba(255,255,255,0.14);
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background:radial-gradient(circle at 20% 0%, rgba(255,79,216,.18), transparent 30%), radial-gradient(circle at 80% 0%, rgba(124,247,255,.14), transparent 30%), var(--bg);
  color:var(--text);
}}
header {{
  position:sticky;
  top:0;
  z-index:5;
  background:rgba(15,16,32,.88);
  backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border);
  padding:22px;
}}
.wrap {{ max-width:1280px; margin:0 auto; }}
.brand {{ display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }}
.logoRow {{ display:flex; align-items:center; gap:14px; }}
.bug {{
  width:52px;
  height:52px;
  border:2px solid var(--accent);
  border-radius:14px;
  display:grid;
  place-items:center;
  font-size:10px;
  font-weight:900;
  line-height:.92;
  text-align:center;
  background:linear-gradient(135deg, rgba(255,79,216,.24), rgba(124,247,255,.12));
}}
h1 {{ margin:0; font-size:clamp(24px,4vw,42px); letter-spacing:-.04em; }}
.sub {{ color:var(--muted); font-size:13px; margin-top:4px; }}
main {{ max-width:1280px; margin:0 auto; padding:22px; }}
button {{
  border:1px solid var(--border);
  background:var(--panel2);
  color:var(--text);
  padding:10px 12px;
  border-radius:12px;
  cursor:pointer;
  font-weight:800;
}}
button:hover {{ border-color:var(--accent); }}
.search {{
  width:100%;
  padding:14px 16px;
  border-radius:16px;
  border:1px solid var(--border);
  background:rgba(255,255,255,.07);
  color:var(--text);
  font-size:16px;
  margin-bottom:16px;
}}
.tabs {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:18px; }}
.tab {{ opacity:.72; }}
.tab.active {{ opacity:1; border-color:var(--accent); background:linear-gradient(135deg, rgba(255,79,216,.25), rgba(124,247,255,.10)); }}
.section {{ display:none; }}
.section.active {{ display:block; }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
@media(max-width:960px) {{ .grid {{ grid-template-columns:1fr; }} }}
.card {{
  background:rgba(24,26,47,.94);
  border:1px solid var(--border);
  border-radius:18px;
  padding:16px;
  box-shadow:0 12px 35px rgba(0,0,0,.25);
}}
.card h3 {{ margin:10px 0; line-height:1.15; font-size:18px; }}
.meta {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }}
.pill {{
  display:inline-flex;
  border:1px solid var(--border);
  color:var(--muted);
  padding:5px 8px;
  border-radius:999px;
  font-size:12px;
  font-weight:800;
}}
.must {{ color:var(--good); border-color:rgba(112,255,176,.4); }}
.maybe {{ color:var(--accent2); border-color:rgba(124,247,255,.4); }}
.weekend {{ color:var(--warn); border-color:rgba(255,209,102,.4); }}
.review {{ color:var(--danger); border-color:rgba(255,107,107,.4); }}
.small {{ color:var(--muted); font-size:13px; line-height:1.45; }}
pre {{
  background:rgba(0,0,0,.32);
  border:1px solid var(--border);
  padding:14px;
  border-radius:14px;
  white-space:pre-wrap;
  overflow:auto;
  line-height:1.45;
}}
.actions {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; }}
.empty {{ padding:22px; border:1px dashed var(--border); border-radius:16px; color:var(--muted); }}
.toast {{
  position:fixed;
  right:18px;
  bottom:18px;
  background:var(--panel2);
  border:1px solid var(--accent);
  padding:12px 14px;
  border-radius:14px;
  display:none;
}}
</style>
</head>
<body>
<header>
  <div class="wrap brand">
    <div class="logoRow">
      <div class="bug">HER<br>SPORTS<br>DAILY</div>
      <div>
        <h1>Her Sports Daily Dashboard</h1>
        <div class="sub">Generated {generated_at}. Use this instead of digging through every CSV.</div>
      </div>
    </div>
    <div class="actions">
      <button onclick="copyTop3()">Copy Top 3 Packets</button>
      <button onclick="copyQueue()">Copy Full Queue</button>
    </div>
  </div>
</header>
<main>
  <input id="search" class="search" placeholder="Search headline, sport, template, story type..." oninput="renderActive()">
  <div class="tabs">
    <button class="tab active" data-tab="priority" onclick="setTab('priority')">Priority Board</button>
    <button class="tab" data-tab="graphics" onclick="setTab('graphics')">Graphic Packets</button>
    <button class="tab" data-tab="context" onclick="setTab('context')">Story Context</button>
    <button class="tab" data-tab="captions" onclick="setTab('captions')">Captions</button>
    <button class="tab" data-tab="reels" onclick="setTab('reels')">Reels</button>
    <button class="tab" data-tab="files" onclick="setTab('files')">File Guide</button>
  </div>
  <section id="priority" class="section active"></section>
  <section id="graphics" class="section"></section>
  <section id="context" class="section"></section>
  <section id="captions" class="section"></section>
  <section id="reels" class="section"></section>
  <section id="files" class="section"></section>
</main>
<div id="toast" class="toast">Copied</div>
<script>
const DATA = {data_json};
let activeTab = "priority";
function norm(s) {{ return String(s || "").toLowerCase(); }}
function esc(s) {{ return String(s || "").replace(/[&<>"']/g, m => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[m])); }}
function searchTerm() {{ return norm(document.getElementById("search").value); }}
function matches(row) {{ const q = searchTerm(); return !q || norm(JSON.stringify(row)).includes(q); }}
function decisionClass(d) {{
  d = norm(d);
  if (d.includes("must")) return "must";
  if (d.includes("maybe")) return "maybe";
  if (d.includes("weekend")) return "weekend";
  if (d.includes("review") || d.includes("verify")) return "review";
  return "";
}}
function toast(text="Copied") {{
  const t = document.getElementById("toast");
  t.textContent = text;
  t.style.display = "block";
  setTimeout(() => t.style.display = "none", 1300);
}}
async function copyText(text) {{
  await navigator.clipboard.writeText(text || "");
  toast();
}}
function setTab(tab) {{
  activeTab = tab;
  document.querySelectorAll(".tab").forEach(el => el.classList.toggle("active", el.dataset.tab === tab));
  document.querySelectorAll(".section").forEach(el => el.classList.toggle("active", el.id === tab));
  renderActive();
}}
function renderActive() {{
  if (activeTab === "priority") renderPriority();
  if (activeTab === "graphics") renderGraphics();
  if (activeTab === "context") renderContext();
  if (activeTab === "captions") renderCaptions();
  if (activeTab === "reels") renderReels();
  if (activeTab === "files") renderFiles();
}}
function renderPriority() {{
  const rows = (DATA.command.length ? DATA.command : DATA.dashboard).filter(matches);
  const root = document.getElementById("priority");
  if (!rows.length) {{ root.innerHTML = '<div class="empty">No priority rows found.</div>'; return; }}
  root.innerHTML = '<div class="grid">' + rows.map((r, i) => {{
    const headline = r.headline || "";
    const decision = r.editorial_decision || "";
    const seq = r.post_sequence || r.posting_order || (i + 1);
    const template = r.template_name || "";
    const action = r.action || r.post_now_or_later || "";
    const family = r.content_family || "";
    const timing = r.timing || r.recommended_timing || "";
    return `
      <div class="card">
        <div class="meta">
          <span class="pill">#${{esc(seq)}}</span>
          <span class="pill ${{decisionClass(decision)}}">${{esc(decision)}}</span>
          <span class="pill">${{esc(family)}}</span>
        </div>
        <h3>${{esc(headline)}}</h3>
        <div class="small"><b>Action:</b> ${{esc(action)}}</div>
        <div class="small"><b>Template:</b> ${{esc(template)}}</div>
        <div class="small"><b>Timing:</b> ${{esc(timing)}}</div>
        <div class="actions"><button onclick='copyMatchingPacket(${{JSON.stringify(headline)}})'>Copy Graphic Packet</button></div>
      </div>`;
  }}).join("") + '</div>';
}}
function renderGraphics() {{
  const packets = DATA.packets.filter(matches);
  const root = document.getElementById("graphics");
  if (!packets.length) {{ root.innerHTML = '<div class="empty">No graphic packets found.</div>'; return; }}
  root.innerHTML = packets.map(p => `
    <div class="card" style="margin-bottom:14px">
      <div class="meta">
        <span class="pill">Graphic ${{esc(p.packet_num)}}</span>
        <span class="pill ${{decisionClass(p.decision)}}">${{esc(p.decision)}}</span>
        <span class="pill">${{esc(p.template)}}</span>
      </div>
      <h3>${{esc(p.headline)}}</h3>
      <div class="actions"><button onclick='copyText(${{JSON.stringify(p.packet)}})'>Copy This Packet</button></div>
      <pre>${{esc(p.packet)}}</pre>
    </div>`).join("");
}}
function renderContext() {{
  const rows = DATA.context.filter(matches);
  const root = document.getElementById("context");
  if (!rows.length) {{ root.innerHTML = '<div class="empty">No enriched context found.</div>'; return; }}
  root.innerHTML = '<div class="grid">' + rows.map(r => `
    <div class="card">
      <div class="meta">
        <span class="pill">${{esc(r.context_confidence || "Unknown")}} confidence</span>
        <span class="pill ${{norm(r.manual_review_flag).includes("yes") ? "review" : "maybe"}}">Review: ${{esc(r.manual_review_flag || "Unknown")}}</span>
      </div>
      <h3>${{esc(r.headline)}}</h3>
      <div class="small"><b>Summary:</b> ${{esc(r.story_summary)}}</div>
      <div class="small"><b>Fact 1:</b> ${{esc(r.key_fact_1)}}</div>
      <div class="small"><b>Fact 2:</b> ${{esc(r.key_fact_2)}}</div>
      <div class="small"><b>Key number:</b> ${{esc(r.key_number)}}</div>
      <div class="small"><b>Notes:</b> ${{esc(r.verified_context_notes)}}</div>
    </div>`).join("") + '</div>';
}}
function renderCaptions() {{
  const rows = DATA.captions.filter(matches);
  const root = document.getElementById("captions");
  if (!rows.length) {{ root.innerHTML = '<div class="empty">No captions found.</div>'; return; }}
  root.innerHTML = '<div class="grid">' + rows.map(r => `
    <div class="card">
      <div class="meta">
        <span class="pill">${{esc(r.caption_variant || r.caption_type || "caption")}}</span>
        <span class="pill ${{decisionClass(r.editorial_decision)}}">${{esc(r.editorial_decision)}}</span>
      </div>
      <h3>${{esc(r.headline)}}</h3>
      <pre>${{esc(r.caption)}}</pre>
      <button onclick='copyText(${{JSON.stringify(r.caption || "")}})'>Copy Caption</button>
    </div>`).join("") + '</div>';
}}
function renderReels() {{
  const root = document.getElementById("reels");
  if (!DATA.reels) {{ root.innerHTML = '<div class="empty">No reel script package found.</div>'; return; }}
  root.innerHTML = `<div class="card"><button onclick='copyText(${{JSON.stringify(DATA.reels)}})'>Copy Reel Scripts</button><pre>${{esc(DATA.reels)}}</pre></div>`;
}}
function renderFiles() {{
  document.getElementById("files").innerHTML = `
    <div class="grid">
      <div class="card">
        <h3>Use these daily</h3>
        <div class="small"><b>dashboard/index.html</b>: Start here.</div>
        <div class="small"><b>today_graphics_queue.md</b>: Full graphic packets.</div>
        <div class="small"><b>top_3_graphic_packets.md</b>: First three graphics.</div>
        <div class="small"><b>story_context_enriched.csv</b>: Confidence and review flags.</div>
      </div>
      <div class="card">
        <h3>Daily workflow</h3>
        <div class="small">1. Open Priority Board.</div>
        <div class="small">2. Copy the Post 1 graphic packet.</div>
        <div class="small">3. Paste it into the HSD Graphics Production chat.</div>
        <div class="small">4. If confidence is Low, verify before using exact stats.</div>
      </div>
      <div class="card">
        <h3>Accuracy reminder</h3>
        <div class="small">Do not invent jersey numbers, scores, records, or player details.</div>
        <div class="small">If the dashboard flags manual review, treat the packet as a research brief.</div>
      </div>
    </div>`;
}}
function copyMatchingPacket(headline) {{
  const packet = DATA.packets.find(p => norm(p.headline) === norm(headline)) || DATA.packets.find(p => norm(p.packet).includes(norm(headline)));
  if (packet) copyText(packet.packet);
  else toast("No packet found");
}}
function copyTop3() {{ copyText(DATA.top3 || DATA.packets.slice(0,3).map(p => p.packet).join("\\n\\n")); }}
function copyQueue() {{ copyText(DATA.graphics_queue || DATA.packets.map(p => p.packet).join("\\n\\n")); }}
renderActive();
</script>
</body>
</html>"""

def main() -> None:
    csv_data = {name: load_csv(path) for name, path in CSV_FILES.items()}
    text_data = {name: load_text(path) for name, path in TEXT_FILES.items()}
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "command": csv_data["command"],
        "dashboard": csv_data["dashboard"],
        "context": csv_data["context"],
        "captions": csv_data["captions"],
        "queue_csv": csv_data["queue_csv"],
        "graphics_queue": text_data["graphics_queue"],
        "top3": text_data["top3"],
        "reels": text_data["reels"],
        "hub": text_data["hub"],
        "packets": split_graphic_packets(text_data["graphics_queue"]),
    }
    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(create_html(data), encoding="utf-8")
    print(f"Created {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

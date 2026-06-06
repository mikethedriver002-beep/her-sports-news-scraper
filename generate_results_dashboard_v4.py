from __future__ import annotations
import csv, html, re
from pathlib import Path

def clean(v): return re.sub(r"\s+", " ", str(v or "")).strip()
def esc(v): return html.escape(clean(v))
def load_csv(path):
    p=Path(path)
    if not p.exists(): return []
    with p.open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))
def load_text(path):
    p=Path(path)
    return p.read_text(encoding='utf-8') if p.exists() else ''
def cards(rows, empty="Nothing to show"):
    if not rows: return f'<div class="empty">{esc(empty)}</div>'
    out=[]
    for r in rows:
        out.append(f"""<div class="card"><div class="meta"><span class="pill">{esc(r.get('sport_norm'))}</span><span class="pill">{esc(r.get('status_norm'))}</span><span class="pill">Confidence {esc(r.get('confidence'))}</span><span class="pill">Rank {esc(r.get('editorial_rank'))}</span></div><h3>{esc(r.get('graphics_headline'))}</h3><div class="small"><b>League:</b> {esc(r.get('league_norm'))}</div><div class="small"><b>Score:</b> {esc(r.get('away_team_norm'))} {esc(r.get('away_score'))} - {esc(r.get('home_team_norm'))} {esc(r.get('home_score'))}</div><div class="small"><b>Selected source:</b> {esc(r.get('selected_source'))}</div><div class="small"><b>Sources:</b> {esc(r.get('all_sources_json'))}</div><div class="small"><b>Manual review:</b> {esc(r.get('manual_review'))}</div></div>""")
    return '<div class="grid">'+'\n'.join(out)+'</div>'
def health_table(rows):
    body=[]
    for h in rows:
        body.append('<tr>'+''.join(f'<td>{esc(h.get(k))}</td>' for k in ['source_name','sport_or_league','date','ok','events_found','observations_emitted','notes'])+'</tr>')
    return '<table><thead><tr><th>Source</th><th>Sport/League</th><th>Date</th><th>OK</th><th>Events</th><th>Emitted</th><th>Notes</th></tr></thead><tbody>'+''.join(body)+'</tbody></table>'
def main():
    events=load_csv('reconciled_events.csv')
    health=load_csv('source_health_report.csv')
    hub=load_text('results_system_hub.md')
    graphics=load_text('results_graphics_queue.md')
    final_graphics=[r for r in events if r.get('include_in_graphics')=='Yes']
    finals=[r for r in events if r.get('gender_scope')=='women' and r.get('status_norm')=='final' and float(r.get('confidence') or 0)>=0.70]
    review=[r for r in events if r.get('gender_scope')=='women' and r.get('manual_review')=='Yes']
    top=[r for r in events if r.get('gender_scope')=='women' and r.get('include_in_dashboard')=='Yes'][:40]
    doc=f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Her Sports Daily Results Desk v4</title><style>:root{{--bg:#0f1020;--panel:#181a2f;--text:#f7f3ff;--muted:#beb6d4;--accent:#ff4fd8;--border:rgba(255,255,255,.14)}}*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,system-ui,sans-serif;color:var(--text);background:radial-gradient(circle at 20% 0%,rgba(255,79,216,.18),transparent 30%),radial-gradient(circle at 80% 0%,rgba(124,247,255,.12),transparent 30%),var(--bg)}}header{{position:sticky;top:0;z-index:5;background:rgba(15,16,32,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--border);padding:22px}}.wrap,main{{max-width:1280px;margin:0 auto}}.brand{{display:flex;gap:14px;align-items:center}}.bug{{width:54px;height:54px;border-radius:14px;border:2px solid var(--accent);display:grid;place-items:center;font-weight:900;font-size:10px;line-height:.92;text-align:center;background:linear-gradient(135deg,rgba(255,79,216,.25),rgba(124,247,255,.12))}}h1{{margin:0;font-size:clamp(26px,4vw,42px)}}.sub,.small{{color:var(--muted);font-size:13px;line-height:1.45}}main{{padding:22px}}section{{margin-bottom:28px}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}@media(max-width:960px){{.grid{{grid-template-columns:1fr}}}}.card{{background:rgba(24,26,47,.96);border:1px solid var(--border);border-radius:18px;padding:16px;box-shadow:0 12px 32px rgba(0,0,0,.24)}}.card h3{{margin:10px 0;font-size:18px;line-height:1.15}}.meta{{display:flex;flex-wrap:wrap;gap:6px}}.pill{{display:inline-flex;border:1px solid var(--border);color:var(--muted);padding:5px 8px;border-radius:999px;font-size:12px;font-weight:800}}pre{{white-space:pre-wrap;word-wrap:break-word;line-height:1.45;font-size:13px;background:rgba(0,0,0,.28);border:1px solid var(--border);padding:14px;border-radius:14px}}.empty{{padding:16px;border:1px dashed var(--border);border-radius:14px;color:var(--muted)}}table{{width:100%;border-collapse:collapse;background:rgba(24,26,47,.96);border-radius:18px;overflow:hidden}}td,th{{padding:10px;border-bottom:1px solid var(--border);font-size:12px;text-align:left;color:var(--muted)}}th{{color:var(--text)}}</style></head><body><header><div class="wrap brand"><div class="bug">HER<br>SPORTS<br>DAILY</div><div><h1>Results Desk v4</h1><div class="sub">Multi-source women’s sports results, confidence, review, and graphics queue.</div></div></div></header><main><section><h2>System Hub</h2><div class="card"><pre>{esc(hub)}</pre></div></section><section><h2>Graphics Ready</h2>{cards(final_graphics,'No high-confidence graphics-ready finals.')}</section><section><h2>Verified Finals</h2>{cards(finals,'No verified finals.')}</section><section><h2>Manual Review Queue</h2>{cards(review,'No manual review items.')}</section><section><h2>Top Women’s Results</h2>{cards(top,'No women’s results found.')}</section><section><h2>Source Health</h2>{health_table(health)}</section><section><h2>Graphic Packets</h2><div class="card"><pre>{esc(graphics)}</pre></div></section></main></body></html>"""
    Path('results_dashboard').mkdir(exist_ok=True)
    Path('results_dashboard/index.html').write_text(doc, encoding='utf-8')
    print('Created results_dashboard/index.html')
if __name__=='__main__': main()

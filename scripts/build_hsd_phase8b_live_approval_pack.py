from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from PIL import Image, ImageDraw, ImageFont

VERSION = "v1.0-phase8b-live-approval-review-pack"
LIVE_REPORT = Path("live_post_ready_v4_report.json")
OUT_DIR = Path("outputs/latest/HSD_PHASE8B_APPROVAL_REVIEW")
CONTACT_SHEET = OUT_DIR / "phase8b_live_numbered_review_contact_sheet.jpg"
DECISION_CSV = OUT_DIR / "live_visual_approval_decisions_RECOMMENDED.csv"
REVIEW_MD = OUT_DIR / "APPROVAL_REVIEW.md"
REPORT_JSON = Path("phase8b_live_approval_review_report.json")
REPORT_MD = Path("phase8b_live_approval_review_report.md")
GOLD=(223,161,38); BG=(4,6,12); INK=(238,236,226)
FIELDS=["review_number","decision","reason","item_id","platform","template_id","headline","output_path","technical_status","release_ready_recommended","asset_route"]


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def font(size:int,bold=True):
    paths=["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"]
    for p in paths:
        try: return ImageFont.truetype(p,size=size)
        except Exception: pass
    return ImageFont.load_default()


def read_rows() -> List[Dict[str, Any]]:
    if not LIVE_REPORT.exists():
        return []
    payload=json.loads(LIVE_REPORT.read_text(encoding='utf-8'))
    return [r for r in payload.get('rows') or [] if isinstance(r,dict)]


def decision_for(row: Mapping[str,Any]) -> tuple[str,str]:
    tech=clean(row.get('technical_status'))
    if tech != 'live_technical_candidate':
        return 'needs_fix', clean(row.get('technical_reasons')) or 'technical gate blocked'
    template=clean(row.get('template_id'))
    route=clean(row.get('asset_assurance_player_route'))
    headline=clean(row.get('headline'))
    if route == 'downgraded_player_to_non_player_team_spotlight':
        return 'hold', 'TEAM SPOTLIGHT fallback requires human visual approval'
    if 'Dallas Wings beat Seattle Storm' in headline and '42-40' in clean(row.get('rendered_copy')):
        return 'hold', 'manual score sanity check recommended'
    if template.startswith('hsd_game_recap_final_score') and int(row.get('phase8b_result_banned_count') or 0) == 0:
        return 'approve', 'Final Score row passed Phase 8B result language and technical gates'
    if template == 'hsd_tonight_in_the_w_a':
        return 'approve', 'Tonight row passed word-safe Phase 8A/8B language and technical gates'
    return 'approve', 'technical candidate passed gates'


def make_thumb(path: Path, number: int) -> Optional[Image.Image]:
    if not path.exists():
        return None
    try:
        im=Image.open(path).convert('RGB')
    except Exception:
        return None
    im.thumbnail((216,270))
    canvas=Image.new('RGB',(216,270),BG)
    canvas.paste(im,((216-im.width)//2,(270-im.height)//2))
    d=ImageDraw.Draw(canvas)
    d.rectangle((0,0,58,46),fill=(0,0,0))
    d.text((10,6),str(number),font=font(28),fill=GOLD)
    return canvas


def build(mode:str) -> Dict[str,Any]:
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    rows=read_rows()
    decisions=[]; thumbs=[]
    for idx,row in enumerate(rows,1):
        decision, reason=decision_for(row)
        out=clean(row.get('output_path'))
        decisions.append({
            'review_number':idx,
            'decision':decision,
            'reason':reason,
            'item_id':clean(row.get('item_id')),
            'platform':clean(row.get('platform')),
            'template_id':clean(row.get('template_id')),
            'headline':clean(row.get('headline')),
            'output_path':out,
            'technical_status':clean(row.get('technical_status')),
            'release_ready_recommended':str(row.get('release_ready_recommended')),
            'asset_route':clean(row.get('asset_assurance_player_route')),
        })
        thumb=make_thumb(Path(out),idx)
        if thumb: thumbs.append(thumb)
    with DECISION_CSV.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(decisions)
    if thumbs:
        cols=5; rows_count=(len(thumbs)+cols-1)//cols
        sheet=Image.new('RGB',(cols*216,rows_count*270),BG)
        for i,thumb in enumerate(thumbs):
            sheet.paste(thumb,((i%cols)*216,(i//cols)*270))
        sheet.save(CONTACT_SHEET)
    counts={d:sum(x['decision']==d for x in decisions) for d in ['approve','hold','needs_fix']}
    REVIEW_MD.write_text("\n".join([
        "# HSD Phase 8B Live Approval Review",
        "",
        f"Mode: `{mode}`",
        f"Rows reviewed: `{len(decisions)}`",
        f"Approve: `{counts.get('approve',0)}`",
        f"Hold: `{counts.get('hold',0)}`",
        f"Needs fix: `{counts.get('needs_fix',0)}`",
        "",
        "Use this CSV as a recommendation only. Human visual approval remains required before limited handoff.",
    ])+"\n",encoding='utf-8')
    report={'version':VERSION,'mode':mode,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'status':'passed_phase8b_live_approval_review_pack' if decisions else 'blocked_phase8b_live_approval_review_pack','strict_exit_code':0 if decisions else 2,'review_rows':len(decisions),'decision_counts':counts,'decision_csv':DECISION_CSV.as_posix(),'contact_sheet':CONTACT_SHEET.as_posix() if CONTACT_SHEET.exists() else '', 'blockers':[] if decisions else ['no_live_rows_found']}
    REPORT_JSON.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    REPORT_MD.write_text("\n".join(["# HSD Phase 8B Approval Pack Report","",f"Status: `{report['status']}`",f"Rows: `{len(decisions)}`",f"CSV: `{DECISION_CSV.as_posix()}`",f"Contact sheet: `{report['contact_sheet']}`"])+"\n",encoding='utf-8')
    return report


def main(argv: Optional[List[str]]=None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument('--mode',choices=['fixture_audit','live_data'],default='fixture_audit'); parser.add_argument('--strict',action='store_true')
    args=parser.parse_args(argv)
    report=build(args.mode)
    print(json.dumps({k:report[k] for k in ['version','mode','status','review_rows','decision_counts','blockers']},indent=2))
    return report['strict_exit_code'] if args.strict else 0

if __name__=='__main__':
    raise SystemExit(main())

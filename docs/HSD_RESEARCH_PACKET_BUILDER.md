# HSD Research Packet Builder

Status: review-only operating helper.

Use `scripts/build_hsd_external_research_packet_v1.py` when ChatGPT Pro or Gemini Pro would improve a decision and Mike should receive one exact upload bundle plus one exact prompt.

Example:

```powershell
$env:HSD_RUN_OUTPUT_DIR='outputs/local/latest/files'
.\.venv\Scripts\python.exe scripts\build_hsd_external_research_packet_v1.py `
  --tool gemini_pro `
  --lane renderer `
  --short-task "compare latest render to references" `
  --question "Critique the latest HSD render for athlete-first composition, text hierarchy, number placement, background depth, and emotional focal point. Return five PR-sized renderer packets."
```

Outputs:

- `outputs/local/latest/files/external_research_packets/<packet>/README.md`
- `outputs/local/latest/files/external_research_packets/<packet>.zip`
- `outputs/local/latest/files/external_research_packets/<packet>/research_alert_email.md`
- `outputs/local/latest/files/external_research_packets/<packet>/research_alert_gmail_payload.json`
- `outputs/local/latest/files/external_research_packet_latest.json`

The repo does not send email directly. The generated Gmail payload is meant for the conductor/Gmail connector or for manual copy-paste. Default policy is draft-first; send only when time-sensitive.

## Alert Draft Only

Use `scripts/build_hsd_research_alert_draft_v1.py` when the conductor already has a packet path, folder path, or current artifact bundle and only needs an email-ready alert plus a paste prompt.

Example:

```powershell
$env:HSD_RUN_OUTPUT_DIR='outputs/local/latest/files'
.\.venv\Scripts\python.exe scripts\build_hsd_research_alert_draft_v1.py `
  --tool chatgpt_pro `
  --lane workflow `
  --short-task "rank conductor workflow bottlenecks" `
  --packet-path "outputs/local/latest/files/external_research_packets/workflow-packet.zip" `
  --why-now "The conductor needs a ranked outside critique before opening more lanes."
```

Outputs:

- `outputs/local/latest/files/research_alert_drafts/<alert>/research_alert_email.md`
- `outputs/local/latest/files/research_alert_drafts/<alert>/prompt_to_paste.md`
- `outputs/local/latest/files/research_alert_drafts/<alert>/research_alert_gmail_payload.json`
- `outputs/local/latest/files/research_alert_draft_latest.json`

The alert-draft helper does not create a ZIP and does not send email. Use it for quick, review-only operator alerts; use the external research packet builder when Codex needs to assemble the upload bundle too.

Guardrails:

- Review-only packet.
- No paid APIs.
- No automatic downloads.
- No auto-approval.
- No approval-state changes.
- No `headshot.png` writes.
- No `.approved` markers.
- No publish-ready lane.
- No publishing.

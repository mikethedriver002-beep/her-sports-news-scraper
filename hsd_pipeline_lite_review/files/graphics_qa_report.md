# HSD Graphics QA Scorer v1.10 BeBe Ops v2.4 Report

Generated: 2026-06-14T17:01:50.509852+00:00

Bundles scored: 1

## tonight-in-the-w

- Decision: **fail**
- Score: 57
- Render path: `generated_graphics/tonight-in-the-w.png`
- Issues: `[{"code": "UPLOAD_PACK_READY_WITH_REVIEW", "severity": "review", "message": "Upload pack complete, but public player images/crop rules require manual visual review."}, {"code": "PLAYER_IMAGE_FIT_REVIEW", "severity": "review", "message": "Use tight crop rules for: Rhyne Howard, Allisha Gray, Brittney Sykes, Sonia Citron, Breanna Stewart, Sabrina Ionescu"}, {"code": "PROMPT_NOT_SANITIZED", "severity": "critical", "message": "Winner, Loser, Do not alter"}, {"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest/upload-pack QA only."}]`
- Remediation: Visually verify public player images, crop tightly, and avoid wrong-team jersey/context before generation. Generate separate 1080x1350 slide files, upload them to rendered_graphics_input/, and rerun rendered-slide QA. Strip banned/result/internal terms and rerender.

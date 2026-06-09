# HSD Asset Visual QA v1.2 Notes

This build is targeted at three problems:
1. junk entity extraction
2. incomplete WNBA logo coverage
3. unsafe player-feature logic

The system now prefers safety over completeness.
If exact player imagery is not available, it should generate strong editorial prompts that do not require player photos.


## v1.2.2

Fixes fact-warning propagation and creates `chatgpt_review_pack/` plus `hsd_chatgpt_review_packet.md` for fast uploads.


## v1.2.2

Patched stale player-team hint: Jessica Shepard now maps to Dallas Wings.


## v1.3.1

Adds `generate_hsd_graphics_upload_pack_v1.py` to create upload-ready logo/flag asset packs and ZIPs for the graphics chat.


## v1.3.1

Adds a direct graphics handoff file and forces the review packet + run summary to include the graphics upload pack outputs so you can verify the ZIPs actually exist after each run.

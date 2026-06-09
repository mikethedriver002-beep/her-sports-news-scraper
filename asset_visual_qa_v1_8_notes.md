# HSD Asset Visual QA v1.8 Notes

## Based on latest graphic review

The latest generation was much improved. It fixed the robotic `Verified Final` issue and produced a much stronger four-slide carousel.

Remaining issues found:

1. The packet is still about an old Dallas Wings vs. Los Angeles Sparks result.
2. Slide 3 proves the two-team performer format works, but public-source player images can show risky jersey context.
3. Ariel Atkins displayed in an alternate/overseas-looking jersey context, which can confuse the post.
4. We still need a clean way to QA actual exported slides after graphics generation.

## v1.8 response

- Freshness Gate blocks old or undated results before they become "ready" upload packs.
- Player Image Fit Gate does not use face recognition. It detects sourcing/team-context risk and adds crop rules.
- Rendered Slide QA checks actual exported images when you place them in `rendered_graphics_input/`.
- Upload Pack now marks packets as blocked/review when freshness or player-fit gates require it.

## Posting rule

Fresh packets can proceed. Old packets must be relabeled as `Last Night`, `Yesterday`, or `Carryover`, or they should be blocked.

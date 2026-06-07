# Her Sports Daily News Sync v1.2 Notes

The v1.1 run successfully found candidates, sources, and packets, but the final-score field was blank in the output briefs.

v1.2 fixes that by:

- making the Results Desk graphics queue parser more tolerant
- inferring queue section from editorial bucket/content action
- extracting final scores from fallback recommendation text
- inferring winner/loser from headlines
- cleaning WNBA top-performer text
- forcing manual review if a final score is still missing

After running v1.2, check that `news_brief_queue.md` says things like:

`Verified final: Dallas Wings 104 - Los Angeles Sparks 96`

instead of:

`Verified final: .`

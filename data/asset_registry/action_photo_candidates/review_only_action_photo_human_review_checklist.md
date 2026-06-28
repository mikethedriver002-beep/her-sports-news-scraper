# Review-Only Action Photo Human Review Checklist

Generated: `2026-06-28T19:18:57.609143+00:00`

Work each row in this order: identity, event context, rights posture, suitability, then workflow disposition. The output is a review decision on a lead, not asset approval.

## Review Steps

1. Verify the athlete identity against an official roster, player directory, federation page, media guide, or event anchor.
2. Confirm the event name, date, season, team, opponent, and uniform context before trusting the lead.
3. Capture the source URL, source domain, source title/caption, photographer or agency credit, and any visible license or rights clues.
4. Assign the most conservative rights class; official source does not mean publish-ready rights.
5. Reject or escalate restricted-access imagery, credential-only contexts, locker-room/corridor imagery, manipulations, or missing-provenance rows.
6. Avoid video, broadcast, GIF, or footage-derived stills unless an explicit policy allows that source type.
7. Check promo/commercial sensitivity before spending review time on editorial or rights-sensitive imagery.
8. Assess render suitability only after identity and rights posture are credible.
9. Cluster duplicates and near-duplicates so the same moment is not reviewed repeatedly.
10. Record a disposition using `manual_review_status`, `manual_reviewer`, `reviewed_at_utc`, and notes; do not change asset approval state here.

## Red Flags

- discoverability being mistaken for permission
- old uniform, transfer, loan, or national-team context being treated as current club context
- broadcast/video/social-video stills
- restricted-access or behind-the-scenes setting
- all-rights-reserved or purchase-license clues without a rights path
- AI-edited, composited, or suspiciously manipulated imagery
- source URL that lands on search results rather than a stable item page
- repost chain that hides the original source or credit

## Hard Stop

Do not download image files, approve assets, write headshots, create `.approved` markers, move files, publish, or claim render readiness from this checklist.

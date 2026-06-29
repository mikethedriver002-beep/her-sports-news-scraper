# Review-Only Action Photo Candidate Research Packet v1

Generated: `2026-06-28T00:00:00+00:00`

This packet converts the action-photo candidate queue into copy-ready research tasks for Mike, ChatGPT Pro, Gemini Pro, and manual research. It is a bridge toward real candidate-photo URLs and evidence, not a download, approval, or render-ready workflow.

## Local Download Law

`download_approved=yes` remains human-edited only after `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` are filled. Any later download must land in `data/assets/quarantine/review_only_candidates/`. Download approval is not asset approval; approval and render-ready status remain separate.

## What Mike Sends To ChatGPT/Gemini

Send one task prompt at a time. Ask the researcher to return only URL/evidence rows in a CSV code block. They must not download images, save files, claim approval, assert current roster truth without an identity anchor, or mark anything render-ready.

## What Mike Pastes Back

Paste returned rows into a human review worksheet using exactly this schema:

```csv
candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required
```

## Summary

- Research tasks: `10`
- Validation issues: `0`
- Rows with human download approval marked yes: `0`
- Review-only rows: `10`
- Publish-ready rows: `0`

## Task Counts

- chatgpt_pro: `7`
- gemini_pro: `1`
- manual_research: `2`

## Copy-Ready Tasks

### APR001: APQ001 - WNBA

- Researcher lane: `manual_research`
- Source family: `Getty Images Editorial Sports`
- Source macro: `{player_name} WNBA match action site:gettyimages.com`

```text
You are a manual researcher URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ001. Sport/entity: basketball / WNBA. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: Getty Images Editorial Sports / editorial_wire. Search macro or source lead: {player_name} WNBA match action site:gettyimages.com. Look for action-photo candidate page URLs and separate identity/evidence anchors for transition_drive|block|rebound|celebration. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR002: APQ002 - WNBA

- Researcher lane: `chatgpt_pro`
- Source family: `WNBA official league/team galleries`
- Source macro: `{player_name} {team} site:wnba.com OR site:{team}.wnba.com photos OR gallery OR recap`

```text
You are a ChatGPT Pro URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ002. Sport/entity: basketball / WNBA. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: WNBA official league/team galleries / official_league_gallery. Search macro or source lead: {player_name} {team} site:wnba.com OR site:{team}.wnba.com photos OR gallery OR recap. Look for action-photo candidate page URLs and separate identity/evidence anchors for game_action|bench_reaction|celebration. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR003: APQ003 - NWSL

- Researcher lane: `gemini_pro`
- Source family: `ISI Photos Archive`
- Source macro: `{player_name} {club} NWSL isiphotos photoshelter action`

```text
You are a Gemini Pro URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ003. Sport/entity: soccer / NWSL. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: ISI Photos Archive / reputable_newsroom_gallery. Search macro or source lead: {player_name} {club} NWSL isiphotos photoshelter action. Look for action-photo candidate page URLs and separate identity/evidence anchors for dribble|shot|save|celebration. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR004: APQ004 - USWNT / U.S. Soccer

- Researcher lane: `chatgpt_pro`
- Source family: `ISI Photos / U.S. Soccer`
- Source macro: `{player_name} USWNT match action ISI Photos OR ussoccer photos`

```text
You are a ChatGPT Pro URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ004. Sport/entity: soccer / USWNT / U.S. Soccer. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: ISI Photos / U.S. Soccer / official_federation_or_tournament. Search macro or source lead: {player_name} USWNT match action ISI Photos OR ussoccer photos. Look for action-photo candidate page URLs and separate identity/evidence anchors for national_team_action|goal_celebration|defensive_play. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR005: APQ005 - NCAA Women Basketball

- Researcher lane: `chatgpt_pro`
- Source family: `NCAA Photos / Clarkson Creative`
- Source macro: `{player_name} NCAA March Madness basketball ncaaphotos photoshelter`

```text
You are a ChatGPT Pro URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ005. Sport/entity: basketball / NCAA Women Basketball. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: NCAA Photos / Clarkson Creative / official_federation_or_tournament. Search macro or source lead: {player_name} NCAA March Madness basketball ncaaphotos photoshelter. Look for action-photo candidate page URLs and separate identity/evidence anchors for drive|jump_shot|celebration|defense. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR006: APQ006 - NCAA Women Softball

- Researcher lane: `chatgpt_pro`
- Source family: `NCAA Photos / Clarkson Creative`
- Source macro: `{player_name} Women College World Series softball ncaaphotos photoshelter`

```text
You are a ChatGPT Pro URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ006. Sport/entity: softball / NCAA Women Softball. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: NCAA Photos / Clarkson Creative / official_federation_or_tournament. Search macro or source lead: {player_name} Women College World Series softball ncaaphotos photoshelter. Look for action-photo candidate page URLs and separate identity/evidence anchors for swing|pitch|slide|fielding. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR007: APQ007 - PWHL

- Researcher lane: `manual_research`
- Source family: `Getty / Ice Garden / Inside the Rink`
- Source macro: `{player_name} PWHL game action Getty OR Ice Garden OR Inside the Rink gallery`

```text
You are a manual researcher URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ007. Sport/entity: hockey / PWHL. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: Getty / Ice Garden / Inside the Rink / editorial_wire. Search macro or source lead: {player_name} PWHL game action Getty OR Ice Garden OR Inside the Rink gallery. Look for action-photo candidate page URLs and separate identity/evidence anchors for skate|shot|save|celebration. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR008: APQ008 - AUSL / Pro Softball

- Researcher lane: `chatgpt_pro`
- Source family: `Athletes Unlimited / AUSL Media Hub`
- Source macro: `{player_name} AUSL softball action site:theausl.com OR Jade Hewitt`

```text
You are a ChatGPT Pro URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ008. Sport/entity: softball / AUSL / Pro Softball. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: Athletes Unlimited / AUSL Media Hub / official_league_gallery. Search macro or source lead: {player_name} AUSL softball action site:theausl.com OR Jade Hewitt. Look for action-photo candidate page URLs and separate identity/evidence anchors for swing|pitch|fielding|dugout_celebration. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR009: APQ009 - WTA Tennis

- Researcher lane: `chatgpt_pro`
- Source family: `WTA / Getty`
- Source macro: `{player_name} WTA match action site:wtatennis.com OR site:gettyimages.com`

```text
You are a ChatGPT Pro URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ009. Sport/entity: tennis / WTA Tennis. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: WTA / Getty / official_league_gallery. Search macro or source lead: {player_name} WTA match action site:wtatennis.com OR site:gettyimages.com. Look for action-photo candidate page URLs and separate identity/evidence anchors for serve|forehand|backhand|celebration. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

### APR010: APQ010 - LPGA Golf

- Researcher lane: `chatgpt_pro`
- Source family: `LPGA / Getty`
- Source macro: `{player_name} LPGA swing site:lpga.com OR site:gettyimages.com`

```text
You are a ChatGPT Pro URL/evidence researcher for HSD review-only action-photo candidates. Queue ID: APQ010. Sport/entity: golf / LPGA Golf. Target: replace operator_fill_player_or_team with the player or team being researched. Source family/category: LPGA / Getty / official_league_gallery. Search macro or source lead: {player_name} LPGA swing site:lpga.com OR site:gettyimages.com. Look for action-photo candidate page URLs and separate identity/evidence anchors for drive|approach|putt|celebration. Return CSV in a code block with exactly these columns: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required. Use source_url as the candidate page/source page, not a downloaded file. Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved.
```

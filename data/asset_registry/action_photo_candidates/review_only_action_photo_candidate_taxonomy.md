# Review-Only Action Photo Candidate Taxonomy

Generated: `2026-06-28T19:18:57.609143+00:00`

Use these controlled vocabularies for URL-first/evidence-first action photo candidate rows. They classify review leads only; they do not grant download, asset approval, or render readiness.

## Source Categories

- `official_team_gallery`: Official team/club gallery, recap, or photo surface.
- `official_league_gallery`: Official league gallery, recap, or photo surface.
- `official_federation_or_tournament`: Official federation, tournament, NCAA, or championship photo surface.
- `verification_only_player_page`: Roster, player profile, media guide, or stats page used only as an identity anchor.
- `editorial_wire`: Getty, AP, Reuters, Imagn, or similar editorial marketplace lead.
- `reputable_newsroom_gallery`: Reputable newsroom, local beat, regional broadcaster, or public media gallery.
- `official_social`: Official athlete, team, league, federation, or tournament social post.
- `third_party_creator_public`: Independent photographer, portfolio, Flickr, SmugMug, or creator-owned public lead.
- `gray_area_public_lead`: Fan, repost, archive, forum, or weak-provenance public lead for parking only.

## Rights Classes

- `official_review_needed`: Official source found; no publish-ready rights are assumed.
- `official_partner_licensed_manual_review`: Official surface using partner/licensed imagery such as Getty or similar.
- `editorial_wire_rights_sensitive`: Editorial marketplace or wire source; licensing review is mandatory.
- `newsroom_photo_rights_sensitive`: Newsroom or beat outlet image; rights/provenance review is mandatory.
- `social_uncleared`: Social discovery lead; rights remain unclear.
- `third_party_creator_uncleared`: Independent creator lead; provenance and permission remain unclear.
- `gray_area_lead_only`: Weak chain of title; review-only lead, not a download candidate.
- `reject_do_not_pursue`: Restricted, deceptive, missing provenance, or clearly unusable.

## Identity Confidence

- `confirmed_official`: Caption/source identity and official roster/player anchor match cleanly.
- `strong_context`: Jersey, team, event, teammate/opponent context strongly align.
- `probable`: Likely but incomplete identity match.
- `weak`: Low-confidence match due to obstructed, old, low-res, or thin evidence.
- `mismatch_or_unknown`: Conflicting details or insufficient evidence.

## Download-Approval Gate

- Required local-download-law fields: `source_url, entity_id, rights_class, identity_confidence, intended_review_only_use`.
- Additional required human-review fields before `download_approved=yes`: `source_category`, `manual_reviewer`, and `photographer_credit` or `credit_not_visible_manual_review` with rights notes.
- Blocked rights classes for download approval: `gray_area_lead_only, reject_do_not_pursue, social_uncleared, third_party_creator_uncleared`.
- Minimum identity confidence for download approval: `confirmed_official, strong_context`.

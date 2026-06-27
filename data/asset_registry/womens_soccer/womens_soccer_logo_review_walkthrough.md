# Women's Soccer Logo Review Walkthrough

Generated: `2026-06-27T02:34:29.358279+00:00`

Display-only guide for reviewing the 88-row women's soccer logo contact sheet. This file does not approve assets, download files, move files, publish, or create a publish-ready lane.

## Open First

- Contact sheet: `data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md`
- Intake worksheet: `data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv`
- Walkthrough data: `data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.csv`

## Rows That Need Human Review First

Start with P0 because NWSL is the complete current league set. Use `hold_for_more_evidence` when the local logo path is still missing, even if the source candidate looks right.

- `P0_NWSL_FOUNDATION`: `1` row(s)
- `P0_NWSL_TEAM_LOGOS`: `16` row(s)
- `P1_WSL_FOUNDATION`: `1` row(s)
- `P1_WSL_TEAM_LOGOS`: `12` row(s)
- `P2_LIGA_F_FOUNDATION`: `1` row(s)
- `P2_LIGA_F_TEAM_LOGOS`: `16` row(s)
- `P3_FRAUEN_BUNDESLIGA_FOUNDATION`: `1` row(s)
- `P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS`: `14` row(s)
- `P4_SERIE_A_WOMEN_FOUNDATION`: `1` row(s)
- `P4_SERIE_A_WOMEN_TEAM_LOGOS`: `12` row(s)
- `P5_ARKEMA_PREMIERE_LIGUE_FOUNDATION`: `1` row(s)
- `P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS`: `12` row(s)

## P0 Review Order

1. National Women's Soccer League | league | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/about-the-nwsl
2. Angel City FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/9587b8ce40624165903b6bc9fd252634/angel-city-fc/index
3. Bay FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/19674698cec24f53af8866cd21abaf8f/bay-fc/index
4. Boston Legacy FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/d2d8efe548734dfd8bc667b5a52a079a/boston-legacy-fc/index
5. Chicago Stars FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/269e825b853f4b43a9d38390aa92bf6e/chicago-stars-fc/index
6. Denver Summit FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/cbfcacbef5bc4a278442c00926ac9ebc/denver-summit-fc/index
7. Gotham FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/c83f2ca05aa84c738b5373f0d2a31b39/gotham-fc/index
8. Houston Dash | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/ca3f464d6b794a9087d441d75961403f/houston-dash/index
9. Kansas City Current | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/2c1699409ff84c9eb491aeaca3d3edde/kansas-city-current/index
10. North Carolina Courage | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/fb41ef4439dd495098cb6d40415767cc/north-carolina-courage/index
11. Orlando Pride | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/c3e9513e280b41e5bfbb8230076e8c43/orlando-pride/index
12. Portland Thorns FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/96ba7b37bd8544a1a7329183459150ff/portland-thorns-fc/index
13. Racing Louisville FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/ac29701756da44a08457762380c10733/racing-louisville-fc/index
14. San Diego Wave FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/ca719042b34443c4bcfe380ca4850eaf/san-diego-wave-fc/index
15. Seattle Reign | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/1151140adfc24339ba1c93cb0b6b0238/seattle-reign/index
16. Utah Royals FC | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/acffc559cf7d485a9c05fa23ab57054b/utah-royals-fc/index
17. Washington Spirit | team | precondition=local_asset_present_manual_source_identity_review_required | recommended_decision=approve_for_review_only_renderer_use | source=https://www.nwslsoccer.com/teams/c31d72afc09f42ee86418633aa41390a/washington-spirit/index

## How To Fill The Intake CSV

- `operator_decision`: use `approve_for_review_only_renderer_use`, `deny_logo_asset`, `hold_for_more_evidence`, or `revise_source_metadata`.
- `source_reviewed`: enter `yes` only after you open the official/team source candidate yourself.
- `identity_match`: enter `yes` only when the logo/mark clearly matches the listed league or club.
- `source_url_to_record`: paste the exact source page you reviewed.
- `registry_action`: use `hold_no_registry_state_change` unless you are intentionally providing a human approval decision in a follow-up prompt.
- Guardrails stay false: `publish_ready`, `auto_approval`, `auto_publish`, `move_files`, `paid_apis`, and `asset_downloads`.

## Safest Non-WSL Europe Expansion

Expand one league per PR. For each league, add official club source rows first, then proposed logo slots, then not-approved manual review scopes, then regenerate this board. Do not download logos, do not approve rows, and do not render-enable slots.

All configured Europe top-flight league club source rows are now seeded. Next safest step: human-review exact club/logo sources and any local assets from this board before approval or renderer use.

## All Rows

- rank=1 | P0_NWSL_FOUNDATION | National Women's Soccer League | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=2 | P0_NWSL_TEAM_LOGOS | Angel City FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=3 | P0_NWSL_TEAM_LOGOS | Bay FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=4 | P0_NWSL_TEAM_LOGOS | Boston Legacy FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=5 | P0_NWSL_TEAM_LOGOS | Chicago Stars FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=6 | P0_NWSL_TEAM_LOGOS | Denver Summit FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=7 | P0_NWSL_TEAM_LOGOS | Gotham FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=8 | P0_NWSL_TEAM_LOGOS | Houston Dash | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=9 | P0_NWSL_TEAM_LOGOS | Kansas City Current | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=10 | P0_NWSL_TEAM_LOGOS | North Carolina Courage | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=11 | P0_NWSL_TEAM_LOGOS | Orlando Pride | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=12 | P0_NWSL_TEAM_LOGOS | Portland Thorns FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=13 | P0_NWSL_TEAM_LOGOS | Racing Louisville FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=14 | P0_NWSL_TEAM_LOGOS | San Diego Wave FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=15 | P0_NWSL_TEAM_LOGOS | Seattle Reign | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=16 | P0_NWSL_TEAM_LOGOS | Utah Royals FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=17 | P0_NWSL_TEAM_LOGOS | Washington Spirit | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=18 | P1_WSL_FOUNDATION | Barclays Women's Super League | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=19 | P1_WSL_TEAM_LOGOS | Arsenal Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=20 | P1_WSL_TEAM_LOGOS | Aston Villa Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=21 | P1_WSL_TEAM_LOGOS | Brighton & Hove Albion Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=22 | P1_WSL_TEAM_LOGOS | Chelsea Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=23 | P1_WSL_TEAM_LOGOS | Everton Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=24 | P1_WSL_TEAM_LOGOS | Leicester City Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=25 | P1_WSL_TEAM_LOGOS | Liverpool Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=26 | P1_WSL_TEAM_LOGOS | London City Lionesses | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=27 | P1_WSL_TEAM_LOGOS | Manchester City Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=28 | P1_WSL_TEAM_LOGOS | Manchester United Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=29 | P1_WSL_TEAM_LOGOS | Tottenham Hotspur Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=30 | P1_WSL_TEAM_LOGOS | West Ham United Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=31 | P2_LIGA_F_FOUNDATION | Liga F Moeve | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=32 | P2_LIGA_F_TEAM_LOGOS | Alhama CF ElPozo | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=33 | P2_LIGA_F_TEAM_LOGOS | Athletic Club | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=34 | P2_LIGA_F_TEAM_LOGOS | Atlético de Madrid | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=35 | P2_LIGA_F_TEAM_LOGOS | Costa Adeje Tenerife | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=36 | P2_LIGA_F_TEAM_LOGOS | Deportivo Abanca | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=37 | P2_LIGA_F_TEAM_LOGOS | DUX Logroño | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=38 | P2_LIGA_F_TEAM_LOGOS | FC Badalona Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=39 | P2_LIGA_F_TEAM_LOGOS | FC Barcelona | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=40 | P2_LIGA_F_TEAM_LOGOS | Granada CF | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=41 | P2_LIGA_F_TEAM_LOGOS | Levante UD | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=42 | P2_LIGA_F_TEAM_LOGOS | Madrid CFF | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=43 | P2_LIGA_F_TEAM_LOGOS | RCD Espanyol de Barcelona | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=44 | P2_LIGA_F_TEAM_LOGOS | Real Madrid CF | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=45 | P2_LIGA_F_TEAM_LOGOS | Real Sociedad | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=46 | P2_LIGA_F_TEAM_LOGOS | SD Eibar | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=47 | P2_LIGA_F_TEAM_LOGOS | Sevilla FC | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=48 | P3_FRAUEN_BUNDESLIGA_FOUNDATION | Google Pixel Womens Bundesliga | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=49 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | 1. FC Köln Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=50 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | 1. FC Nürnberg Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=51 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | Bayer 04 Leverkusen Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=52 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | Eintracht Frankfurt Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=53 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | FC Bayern Munich Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=54 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | FC Carl Zeiss Jena Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=55 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | Hamburger SV Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=56 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | RB Leipzig Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=57 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | SC Freiburg Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=58 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | SGS Essen | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=59 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | SV Werder Bremen Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=60 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | TSG Hoffenheim Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=61 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | Union Berlin Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=62 | P3_FRAUEN_BUNDESLIGA_TEAM_LOGOS | VfL Wolfsburg Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=63 | P4_SERIE_A_WOMEN_FOUNDATION | Serie A Women Athora | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=64 | P4_SERIE_A_WOMEN_TEAM_LOGOS | AC Milan Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=65 | P4_SERIE_A_WOMEN_TEAM_LOGOS | AS Roma Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=66 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Como Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=67 | P4_SERIE_A_WOMEN_TEAM_LOGOS | FC Internazionale Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=68 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Fiorentina Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=69 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Genoa Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=70 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Juventus Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=71 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Lazio Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=72 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Napoli Femminile | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=73 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Parma Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=74 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Sassuolo Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=75 | P4_SERIE_A_WOMEN_TEAM_LOGOS | Ternana Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=76 | P5_ARKEMA_PREMIERE_LIGUE_FOUNDATION | Arkema Premiere Ligue | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=77 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | AS Saint-Etienne Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=78 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | Dijon FCO Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=79 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | FC Fleury 91 Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=80 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | FC Nantes Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=81 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | Le Havre AC Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=82 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | MHSC Feminines | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=83 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | OL Lyonnes | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=84 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | Olympique Marseille Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=85 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | Paris FC Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=86 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | Paris Saint-Germain Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=87 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | RC Lens Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use
- rank=88 | P5_ARKEMA_PREMIERE_LIGUE_TEAM_LOGOS | RC Strasbourg Alsace Women | status=not_approved | file_exists=true | decision=approve_for_review_only_renderer_use

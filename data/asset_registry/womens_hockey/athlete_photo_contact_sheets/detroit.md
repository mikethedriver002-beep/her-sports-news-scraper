# PWHL Detroit Athlete Candidate Board

Review-only source-candidate board for operator-supplied athlete/photo candidates.

- Candidate rows: `3`
- Source review can confirm the roster/profile/index page was opened and relevant.
- Identity review must stay held until the row names a concrete athlete and points to reviewed evidence.
- Local file review must stay `no` until Mike manually supplies a candidate file.
- Guardrails: no downloads, no auto-approval, no `.approved` markers, no publish-ready movement.

## Candidate Rows

1. `detroit_roster_source_candidate_01` | operator_add_player_from_team_roster
   - Source kind: `roster_or_public_profile_candidate`
   - Source candidate: `https://www.thepwhl.com/en/teams/detroit/roster`
   - Local candidate path: `assets/leagues/womens_hockey/pwhl/athletes/detroit/detroit_roster_source_candidate_01/headshot.png`
   - Approved marker path: `assets/leagues/womens_hockey/pwhl/athletes/detroit/detroit_roster_source_candidate_01/.approved`
   - Hold reason: Operator can mark source_reviewed after opening the roster page; player identity and local file review must remain hold until a concrete athlete and local candidate asset exist.
2. `detroit_team_profile_source_candidate_02` | operator_add_player_from_team_profile_source
   - Source kind: `team_profile_source_candidate`
   - Source candidate: `https://www.thepwhl.com/en/teams/detroit`
   - Local candidate path: `assets/leagues/womens_hockey/pwhl/athletes/detroit/detroit_team_profile_source_candidate_02/headshot.png`
   - Approved marker path: `assets/leagues/womens_hockey/pwhl/athletes/detroit/detroit_team_profile_source_candidate_02/.approved`
   - Hold reason: Operator can use the team page as context/source evidence; approval stays held until a named athlete and reviewed local candidate asset exist.
3. `detroit_league_player_index_candidate_03` | operator_add_player_from_league_player_index
   - Source kind: `league_player_index_candidate`
   - Source candidate: `https://www.thepwhl.com/en/stats/player-stats`
   - Local candidate path: `assets/leagues/womens_hockey/pwhl/athletes/detroit/detroit_league_player_index_candidate_03/headshot.png`
   - Approved marker path: `assets/leagues/womens_hockey/pwhl/athletes/detroit/detroit_league_player_index_candidate_03/.approved`
   - Hold reason: Operator can mark the source as reviewed after opening the league player index; identity and asset approval remain held until a named athlete row has local candidate evidence.

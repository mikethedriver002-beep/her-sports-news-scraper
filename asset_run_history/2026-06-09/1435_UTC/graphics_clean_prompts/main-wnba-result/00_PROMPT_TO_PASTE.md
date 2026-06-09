# HSD Graphics Prompt: Main WNBA Result

Use the attached files only.
Use the attached logo files and attached player/person image files exactly as mapped. Do not fetch, substitute, or invent any logos, player images, bodies, jerseys, or numbers.
Treat the game facts, scores, team names, and player names as locked facts and preserve them exactly.
Render only display-safe editorial language. Never render internal QA or prompt-control language.
Create polished Her Sports Daily graphics with premium editorial sports-media styling.
Output separate slide files.

## Cleaned production brief

# Main WNBA Result

### STRICT HSD SLIDE BLUEPRINT OVERRIDE v1.7

Player images required: YES
Production decision: ready_for_graphics_chat

PROMPT SANITIZER RULES:
- Strip internal QA language before writing the final prompt.
- Prefer display language from graphics_display_copy.csv.
- If both team performer data exists, slide 3 must include both teams.
- If approved player images exist, use them. Do not replace with invented people.

PLAYER IMAGE STATUS: required player images are present in the upload pack. Use the uploaded player image files only.

Slide-by-slide requirements:

SLIDE 1 - Result hero with both teams represented
Layout: Two-player hero, Dallas left/cyan, Sparks right/magenta. Both sides should feel visually full.
Must include: One Dallas player image; One Sparks player image; Dallas Wings logo; Los Angeles Sparks logo; Dallas 104; Los Angeles 96
Forbidden: Final / Final Score; empty side; logos-only cover when player images are available; fake players or fake jerseys

SLIDE 2 - Balanced final score board
Layout: Symmetric split scoreboard. Fill both sides equally with team name, score, and logo.
Must include: Final Score; Dallas Wings 104; Los Angeles Sparks 96; one Dallas logo; one Sparks logo
Forbidden: Dallas gets the win / Dallas beats L.A. label; Los Angeles Sparks / Sparks fall label; Final / Final Score strip; empty side; duplicate logo floating in margin

SLIDE 3 - Two-sided top performers
Layout: Two equal columns or stacked two-team comparison. Use Dallas players only on the Dallas side and Sparks players only on the Sparks side.
Must include: Dallas leaders; Sparks leaders; Jessica Shepard 22 PTS 15 REB 5 AST 2 STL; Arike Ogunbowale 30 PTS 6 REB 6 AST; Paige Bueckers 18 PTS 3 REB 14 AST 1 STL; Kelsey Plum 27 PTS 6 AST; Ariel Atkins 16 PTS; Dearica Hamby 15 PTS
Forbidden: Wings-only performer slide; Sparks side missing; duplicate giant team logo in the margin; mixed-up player identities

SLIDE 4 - CTA with filled composition
Layout: Strong CTA with score echo, both logos, HSD branding, and one community prompt.
Must include: What stood out?; Follow Her Sports Daily; Dallas 104; Los Angeles 96; both logos
Forbidden: dead space; Final / Final Score; generic robotic CTA; same composition as slide 2

Global correction rules from prior runs:
- Never render the phrase Final / Final Score.
- Never label teams as Dallas gets the win / Dallas beats L.A. or Los Angeles Sparks / Sparks fall.
- Slide 2 must feel balanced on both sides.
- Slide 3 must include Sparks performers as well as Dallas performers.
- Do not place a duplicate team logo in an unused margin just to fill space.

HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Main WNBA Result
Template: result_slide_v2
Canvas: 1080x1350 carousel
Source facts:
Caption/context: Dallas Wings beat Los Angeles Sparks. Top performers: Jessica Shepard (Dallas Wings): PTS 22, REB 15, AST 5, STL 2; Arike Ogunbowale (Dallas Wings): PTS 30, REB 6, AST 6; Paige Bueckers (Dallas Wings): PTS 18, REB 3, AST 14, STL 1.

Safe graphics mode: player_images_allowed
Critical instruction: Player photos are allowed only for approved exact player assets listed below. Never invent or substitute.

Approved exact assets:
- Dallas Wings | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg
- Los Angeles Sparks | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg
- Jessica Shepard | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg
- Arike Ogunbowale | primary_player_photo_v1 | https://statico.profootballnetwork.com/wp-content/uploads/2025/05/11030756/arike-ogunbowale-paige-bueckers-impact-dallas-wings-1920x1280.jpg
- Paige Bueckers | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg
- Kelsey Plum | primary_player_photo_v1 | https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Kelsey_Plum_2025_Sparks_%28cropped%29.jpg/1280px-Kelsey_Plum_2025_Sparks_%28cropped%29.jpg
- Ariel Atkins | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg
- Dearica Hamby | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg
- Nneka Ogwumike | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg
- Cameron Brink | primary_player_photo_v1 | https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Cameron_Brink_Sparks_%28cropped%29.jpg/1280px-Cameron_Brink_Sparks_%28cropped%29.jpg

Fact warnings:
No fact warnings.

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.

## Display-safe slide copy

### Slide 1 - cover_result_hero
- Headline: Dallas Wings Beat Los Angeles Sparks
- Subhead: Dallas handles L.A., 104-96
- Kicker: Final in Los Angeles
- Score copy: 104-96
- Notes: Use one hero player from each team when available. Headline should feel editorial, not robotic

### Slide 2 - balanced_scoreboard
- Headline: Final Score
- Subhead: Dallas Wings 104, Los Angeles Sparks 96
- Kicker: Dallas gets the win
- Score copy: Dallas 104 · Sparks 96
- Notes: Do not render Dallas gets the win / Dallas beats L.A./Los Angeles Sparks / Sparks fall or Final / Final Score. Use a balanced two-sided scoreboard with both teams equally present

### Slide 3 - two_team_performers
- Headline: Top Performers
- Subhead: Dallas leaders and Sparks leaders from the same game
- Kicker: The box score story
- Notes: Two equal sides. Dallas performers on one side, Sparks performers on the other. No one-team-only layout

### Slide 4 - cta_wrap
- Headline: What stood out?
- Subhead: Dallas 104, Los Angeles 96
- Kicker: Join the conversation
- Score copy: Final: 104-96
- CTA: Follow Her Sports Daily for more women’s sports coverage
- Notes: Use a filled CTA slide with one prompt and both logos. Avoid empty dead space

## Layout and composition requirements

- Slide 1: Left/Right entities: Dallas Wings | Los Angeles Sparks | Required people count: left 1, right 1 | Must include: Dallas Wings; Los Angeles Sparks; 104; 96 | Composition: Balanced split cover. If player images exist, use one Dallas player and one Sparks player | Notes: No empty side. Do not make this a logos-only cover when approved player photos are present
- Slide 2: Left/Right entities: Dallas Wings | Los Angeles Sparks | Required people count: left 0, right 0 | Must include: Final Score; Dallas Wings; Los Angeles Sparks; 104; 96 | Composition: Scores and team identity should be visually balanced left and right. Do not label teams as Dallas gets the win / Dallas beats L.A. or Los Angeles Sparks / Sparks fall | Notes: Both sides must feel equally full
- Slide 3: Left/Right entities: Dallas Wings | Los Angeles Sparks | Required people count: left 2, right 2 | Must include: Jessica Shepard; Arike Ogunbowale; Paige Bueckers; Kelsey Plum; Ariel Atkins; Dearica Hamby | Composition: Two-column performer comparison. Left column Dallas. Right column Sparks | Notes: No one-team-only layout. No giant duplicate margin logo
- Slide 4: Left/Right entities: Dallas Wings | Los Angeles Sparks | Required people count: left 0, right 0 | Must include: Follow Her Sports Daily; What stood out?; 104; 96 | Composition: CTA should feel filled and purposeful. Include both logos and a conversation prompt | Notes: Avoid dead space and generic filler copy

## Attached asset identity rules

- team_logo: Dallas Wings | Dallas Wings | Use only as the Dallas Wings logo | Never: Do not use as a player image. Do not place duplicate floating logos in unused corners or margins
- team_logo: Los Angeles Sparks | Los Angeles Sparks | Use only as the Los Angeles Sparks logo | Never: Do not use as a player image. Do not place duplicate floating logos in unused corners or margins
- player_photo: Jessica Shepard | Dallas Wings | Use this image only for Jessica Shepard (Dallas Wings) | Never: Never use this image for any player other than Jessica Shepard. Never swap with another player. If unsure, omit the photo rather than substituting
- player_photo: Arike Ogunbowale | Dallas Wings | Use this image only for Arike Ogunbowale (Dallas Wings) | Never: Never use this image for any player other than Arike Ogunbowale. Never swap with another player. If unsure, omit the photo rather than substituting
- player_photo: Paige Bueckers | Dallas Wings | Use this image only for Paige Bueckers (Dallas Wings) | Never: Never use this image for any player other than Paige Bueckers. Never swap with another player. If unsure, omit the photo rather than substituting
- player_photo: Kelsey Plum | Los Angeles Sparks | Use this image only for Kelsey Plum (Los Angeles Sparks) | Never: Never use this image for any player other than Kelsey Plum. Never swap with another player. If unsure, omit the photo rather than substituting
- player_photo: Ariel Atkins | Los Angeles Sparks | Use this image only for Ariel Atkins (Los Angeles Sparks) | Never: Never use this image for any player other than Ariel Atkins. Never swap with another player. If unsure, omit the photo rather than substituting
- player_photo: Dearica Hamby | Los Angeles Sparks | Use this image only for Dearica Hamby (Los Angeles Sparks) | Never: Never use this image for any player other than Dearica Hamby. Never swap with another player. If unsure, omit the photo rather than substituting
- player_photo: Nneka Ogwumike | Los Angeles Sparks | Use this image only for Nneka Ogwumike (Los Angeles Sparks) | Never: Never use this image for any player other than Nneka Ogwumike. Never swap with another player. If unsure, omit the photo rather than substituting
- player_photo: Cameron Brink | Los Angeles Sparks | Use this image only for Cameron Brink (Los Angeles Sparks) | Never: Never use this image for any player other than Cameron Brink. Never swap with another player. If unsure, omit the photo rather than substituting

## Internal-language rule

Never render internal QA or verification labels. If a line sounds like workflow language instead of editorial sports language, rewrite it before rendering.

## Final reminder

Use natural, human sports-editor phrasing. Keep the facts exact and the wording clean.

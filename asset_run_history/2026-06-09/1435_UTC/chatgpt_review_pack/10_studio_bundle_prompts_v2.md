# HSD Bundle Prompts v2.2

Generated: 2026-06-09T14:35:09.825099+00:00

## Main WNBA Result


### STRICT HSD SLIDE BLUEPRINT OVERRIDE v1.7

Player images required: YES
Production decision: ready_for_graphics_chat

PROMPT SANITIZER RULES:
- Strip internal QA language before writing the final prompt.
- Never render: Verified Final, Winner, Loser, BUNDLE LOCKED FACTS, source-safe context, graphics-safe context, or Do not alter.
- Prefer display language from graphics_display_copy.csv.
- If both team performer data exists, slide 3 must include both teams.
- If approved player images exist, use them. Do not replace with invented people.

PLAYER IMAGE STATUS: required player images are present in the upload pack. Use the uploaded player image files only.

Slide-by-slide requirements:

SLIDE 1 - Result hero with both teams represented
Layout: Two-player hero, Dallas left/cyan, Sparks right/magenta. Both sides should feel visually full.
Must include: One Dallas player image; One Sparks player image; Dallas Wings logo; Los Angeles Sparks logo; Dallas 104; Los Angeles 96
Forbidden: Verified Final; empty side; logos-only cover when player images are available; fake players or fake jerseys

SLIDE 2 - Balanced final score board
Layout: Symmetric split scoreboard. Fill both sides equally with team name, score, and logo.
Must include: Final Score; Dallas Wings 104; Los Angeles Sparks 96; one Dallas logo; one Sparks logo
Forbidden: Winner label; Loser label; Verified Final strip; empty side; duplicate logo floating in margin

SLIDE 3 - Two-sided top performers
Layout: Two equal columns or stacked two-team comparison. Use Dallas players only on the Dallas side and Sparks players only on the Sparks side.
Must include: Dallas leaders; Sparks leaders; Jessica Shepard 22 PTS 15 REB 5 AST 2 STL; Arike Ogunbowale 30 PTS 6 REB 6 AST; Paige Bueckers 18 PTS 3 REB 14 AST 1 STL; Kelsey Plum 27 PTS 6 AST; Ariel Atkins 16 PTS; Dearica Hamby 15 PTS
Forbidden: Wings-only performer slide; Sparks side missing; duplicate giant team logo in the margin; mixed-up player identities

SLIDE 4 - CTA with filled composition
Layout: Strong CTA with score echo, both logos, HSD branding, and one community prompt.
Must include: What stood out?; Follow Her Sports Daily; Dallas 104; Los Angeles 96; both logos
Forbidden: dead space; Verified Final; generic robotic CTA; same composition as slide 2

Global correction rules from prior runs:
- Never render the phrase Verified Final.
- Never label teams as Winner or Loser.
- Slide 2 must feel balanced on both sides.
- Slide 3 must include Sparks performers as well as Dallas performers.
- Do not place a duplicate team logo in an unused margin just to fill space.

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Main WNBA Result
Template: result_slide_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Dallas Wings beat Los Angeles Sparks. Top performers: Jessica Shepard (Dallas Wings): PTS 22, REB 15, AST 5, STL 2; Arike Ogunbowale (Dallas Wings): PTS 30, REB 6, AST 6; Paige Bueckers (Dallas Wings): PTS 18, REB 3, AST 14, STL 1.
Accuracy lock: BUNDLE LOCKED FACTS: Dallas Wings beat Los Angeles Sparks: Dallas Wings 104, Los Angeles Sparks 96. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

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
```

## Tonight in the W Mini-Roundup

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Tonight in the W Mini-Roundup
Template: roundup_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Tonight in the W roundup: Las Vegas Aces beat Golden State Valkyries: Las Vegas Aces 84, Golden State Valkyries 79 | Minnesota Lynx beat Seattle Storm: Minnesota Lynx 88, Seattle Storm 68 | Phoenix Mercury beat Portland Fire: Phoenix Mercury 78, Portland Fire 72
Accuracy lock: BUNDLE LOCKED FACTS: Las Vegas Aces beat Golden State Valkyries: Las Vegas Aces 84, Golden State Valkyries 79 | Minnesota Lynx beat Seattle Storm: Minnesota Lynx 88, Seattle Storm 68 | Phoenix Mercury beat Portland Fire: Phoenix Mercury 78, Portland Fire 72. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: logos_and_text_only
Critical instruction: Do not show any player photo. Use team logos, typography, score treatment, textures, and editorial design only.

Approved exact assets:
- Golden State Valkyries | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg
- Las Vegas Aces | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg
- Minnesota Lynx | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg
- Phoenix Mercury | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg
- Portland Fire | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg
- Seattle Storm | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg

Fact warnings:
No fact warnings.

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.
```

## Volleyball Results Roundup

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Volleyball Results Roundup
Template: roundup_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Around Women’s Sports volleyball radar: USA W beat France W: USA W 3 - France W 2 | Belgium W beat Thailand W: Belgium W 3 - Thailand W 2 | Brazil W beat Bulgaria W: Brazil W 3 - Bulgaria W 0 | Canada W beat France W: Canada W 3 - France W 1 | China W beat Serbia W: China W 3 - Serbia W 0 | Italy W beat Turkey W: Italy W 3 - Turkey W 1
Accuracy lock: BUNDLE LOCKED FACTS: USA W beat France W: USA W 3 - France W 2 | Belgium W beat Thailand W: Belgium W 3 - Thailand W 2 | Brazil W beat Bulgaria W: Brazil W 3 - Bulgaria W 0 | Canada W beat France W: Canada W 3 - France W 1 | China W beat Serbia W: China W 3 - Serbia W 0 | Italy W beat Turkey W: Italy W 3 - Turkey W 1. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: logos_and_text_only
Critical instruction: Do not show any player photo. Use team logos, typography, score treatment, textures, and editorial design only.

Approved exact assets:
- Belgium W | primary_flag_v1 | https://flagcdn.com/w320/be.png
- Brazil W | primary_flag_v1 | https://flagcdn.com/w320/br.png
- Bulgaria W | primary_flag_v1 | https://flagcdn.com/w320/bg.png
- Canada W | primary_flag_v1 | https://flagcdn.com/w320/ca.png
- China W | primary_flag_v1 | https://flagcdn.com/w320/cn.png
- France W | primary_flag_v1 | https://flagcdn.com/w320/fr.png
- Italy W | primary_flag_v1 | https://flagcdn.com/w320/it.png
- Serbia W | primary_flag_v1 | https://flagcdn.com/w320/rs.png
- Thailand W | primary_flag_v1 | https://flagcdn.com/w320/th.png
- Turkey W | primary_flag_v1 | https://flagcdn.com/w320/tr.png
- USA W | primary_flag_v1 | https://flagcdn.com/w320/us.png

Fact warnings:
No fact warnings.

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.
```

## Women's Soccer Radar

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Women's Soccer Radar
Template: radar_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Women’s soccer radar: Brazil U20 W beat Korea Republic U20 W: Brazil U20 W 3 - Korea Republic U20 W 0 | Brazil W beat USA W: Brazil W 2 - USA W 1 | Japan W beat South Africa W: Japan W 5 - South Africa W 0 | Mexico W beat Australia W: Mexico W 1 - Australia W 0
Accuracy lock: BUNDLE LOCKED FACTS: Brazil U20 W beat Korea Republic U20 W: Brazil U20 W 3 - Korea Republic U20 W 0 | Brazil W beat USA W: Brazil W 2 - USA W 1 | Japan W beat South Africa W: Japan W 5 - South Africa W 0 | Mexico W beat Australia W: Mexico W 1 - Australia W 0. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: logos_and_text_only
Critical instruction: Do not show any player photo. Use team logos, typography, score treatment, textures, and editorial design only.

Approved exact assets:
- Australia W | primary_flag_v1 | https://flagcdn.com/w320/au.png
- Brazil U20 W | primary_flag_v1 | https://flagcdn.com/w320/br.png
- Brazil W | primary_flag_v1 | https://flagcdn.com/w320/br.png
- Japan W | primary_flag_v1 | https://flagcdn.com/w320/jp.png
- Korea Republic U20 W | primary_flag_v1 | https://flagcdn.com/w320/kr.png
- Mexico W | primary_flag_v1 | https://flagcdn.com/w320/mx.png
- South Africa W | primary_flag_v1 | https://flagcdn.com/w320/za.png
- USA W | primary_flag_v1 | https://flagcdn.com/w320/us.png

Fact warnings:
No fact warnings.

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.
```

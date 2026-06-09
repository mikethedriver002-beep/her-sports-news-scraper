# HSD Bundle Prompts v2.2

Generated: 2026-06-09T03:09:42.056738+00:00

## Main WNBA Result


### STRICT HSD SLIDE BLUEPRINT OVERRIDE

Player images required: YES
Production decision: ready_for_graphics_chat

PLAYER IMAGE STATUS: required player/person images are present in the upload pack. Use the uploaded player image files only. Do not generate or invent people.

Slide-by-slide requirements:

SLIDE 1 - Result hero with people
Layout: Two-player hero, Dallas left/cyan, Los Angeles right/magenta. Headline centered lower third. Logos small near score, not repeated in margins.
Must include: Dallas Wings player/person image; Los Angeles Sparks player/person image; Dallas Wings logo; Los Angeles Sparks logo; Dallas Wings 104; Los Angeles Sparks 96; Verified Final
Forbidden: fake jerseys; fake numbers; logo-only cover if player images are present; empty right or left side

SLIDE 2 - Balanced final score board
Layout: Symmetric split scoreboard. Fill both sides equally with score slab, team label, logo, and small context strip. No extra logo floating on the left margin.
Must include: Dallas Wings 104; Los Angeles Sparks 96; winner label; loser label; one Dallas logo; one Sparks logo
Forbidden: duplicate logo in corner or left rail; empty side; tiny verified final text strip; cropped score

SLIDE 3 - Two-sided top performers
Layout: Two equal columns. Left column Dallas leaders. Right column Sparks leaders. Use small player photos if uploaded. Use logos only as column headers. No giant logo in the margin.
Must include: Dallas leaders; Sparks leaders; Jessica Shepard 22 PTS 15 REB 5 AST 2 STL; Arike Ogunbowale 30 PTS 6 REB 6 AST; Paige Bueckers 18 PTS 3 REB 14 AST 1 STL; Kelsey Plum 27 PTS 6 AST; Ariel Atkins 16 PTS; Dearica Hamby 15 PTS
Forbidden: Wings-only performer slide; Sparks side missing; duplicate logo on left rail; players assigned to wrong team

SLIDE 4 - CTA with filled composition
Layout: Strong CTA, but not empty. Use both logos in footer, basketball texture, score echo, and one comment prompt.
Must include: Your take?; Follow Her Sports Daily; both team logos; HSD lockup
Forbidden: huge empty dark area; logo pair only with no context; same composition as slide 2

Global correction from previous output:
- Do not put a duplicate Dallas Wings logo on the left margin of the top performers slide.
- Do not create a Wings-only top performers slide. Sparks performers are required too.
- Keep slide 2 balanced so neither side feels empty.
- Use uploaded player/person images when present. No fake player bodies or fake jersey numbers.

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
- Arike Ogunbowale | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg
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

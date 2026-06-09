# HSD Graphics Prompt Sanitizer Rules v1.7

Generated: 2026-06-09T21:30:55.752315+00:00

## Purpose

This file defines the last-pass cleanup rules before a graphics-chat prompt is handed off.

## Hard-strip phrases

- Verified Final
- VERIFIED FINAL
- Winner
- Loser
- BUNDLE LOCKED FACTS
- source-safe context
- graphics-safe context
- Do not alter

## Replace with human display copy

- Verified Final -> Final / Final Score
- Winner -> team name or natural result line
- Loser -> opposing team name or natural result line
- Your Take? -> What stood out?
- Biggest takeaway -> What stood out in this one?

## Display copy rule

The graphics chat should render only display language, not internal QA language.

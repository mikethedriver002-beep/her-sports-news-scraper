# HSD Source Confidence Audit

Date: 2026-06-24

## Decision

The daily command center now separates free-source facts into operator-friendly confidence lanes:

- `publish_grade`: official, primary, wire, or Results Desk final-score facts with enough evidence to use in a manual publish workflow.
- `review_before_publish`: promising evidence, but the operator should confirm before using it.
- `discovery_only`: social, community, gray-area, or thin-source leads that can inspire coverage but cannot carry a factual claim alone.
- `blocked`: paid, private, paywalled, login-only, restricted, or otherwise prohibited source paths.

This keeps free as the default while making the operator's next action clearer.

## Coverage Added

The active News Sync source registry now has stronger free coverage for:

- WNBA official league and all current official team pages.
- AP women's sports and Reuters sports public wire context.
- WTA, LPGA, NCAA softball, USWNT, FIFA women's football, UEFA women's football, NWSL, Volleyball World, CEV, and EHF official sources.
- ESPN/public mainstream sources as cross-check context, not as sole primary proof unless paired with stronger confirmation.

## Scoring Rules

News packets now carry:

- `source_confidence_score`
- `source_confidence_tier`
- `source_publish_grade`
- `source_confidence_reason`

The score rewards final scores, official or wire sources, primary/free sources, cross-checks, multiple usable free sources, and sourced player context. It penalizes missing event dates, failed source fetches with no usable context, discovery-only evidence without confirmation, and blocked source signals.

## Operator Behavior

Discovery-only or blocked packets are held for editor review and marked not production-ready. Review-grade packets are also held even if the rest of the packet looks usable. The command center shows publish-grade and discovery-only packet counts plus the grade and score beside each content candidate.

Manual-only operation remains the default. This change does not add paid APIs, auto-runs, auto-publishing, credentialed scraping, paywall bypassing, or social scraping.

# Roadmap

This roadmap is the public plan for `llm-wiki-starter`.

The project is inspired by Andrej Karpathy's original LLM Wiki idea. The goal here is to take that pattern and turn it into a practical, repeatable starter that people can actually use across modern LLM tools.

This file is the planning surface in the repository. GitHub issues and milestones are the execution surface.

## How to read this roadmap

- `v0.1 Foundation` focuses on trust, clarity, and day-one usability
- `v0.2 Durable Memory` focuses on turning summaries into stronger long-term memory
- `v0.3 Privacy and Scale` focuses on safe sharing, wider ingestion, and repeatable releases

Issue links are grouped by phase and kept here as the source of truth for release planning.

## Tracking

- [#11 Roadmap tracker: v0.x plan for LLM Wiki Starter](https://github.com/intergalacticuser/llm-wiki-starter/issues/11)

## v0.1 Foundation

This phase is about making the starter dependable enough that someone can clone it, understand it, and trust the core workflow.

Planned issues:

- [#1 Add parser tests for Codex and Claude chat ingestion](https://github.com/intergalacticuser/llm-wiki-starter/issues/1)
- [#2 Add CI for CLI smoke checks and docs integrity](https://github.com/intergalacticuser/llm-wiki-starter/issues/2)
- [#3 Add sample public demo corpus and guided walkthrough](https://github.com/intergalacticuser/llm-wiki-starter/issues/3)
- [#4 Add wiki lint command for orphan pages, index drift, and stale links](https://github.com/intergalacticuser/llm-wiki-starter/issues/4)

Release-ready definition:

`v0.1` is done when the starter has a tested ingestion baseline, a small public walkthrough, and basic health checks for both the docs and the wiki structure.

## v0.2 Durable Memory

This phase is about moving beyond transcript collection and summary pages. The starter should help users turn repeated work into reusable memory pages.

Planned issues:

- [#5 Promote chat summaries into durable memory pages](https://github.com/intergalacticuser/llm-wiki-starter/issues/5)
- [#6 Add canonical entity normalization for noisy project names](https://github.com/intergalacticuser/llm-wiki-starter/issues/6)
- [#7 Add reusable query filing workflow for durable answers](https://github.com/intergalacticuser/llm-wiki-starter/issues/7)

Release-ready definition:

`v0.2` is done when the starter has a clear, repeatable path from chats and summaries into `entities`, `concepts`, and `queries`.

## v0.3 Privacy and Scale

This phase is about making the system easier to share safely and easier to extend over time.

Planned issues:

- [#8 Add safe public-export workflow for private wikis](https://github.com/intergalacticuser/llm-wiki-starter/issues/8)
- [#9 Expand chat source support beyond Codex and Claude Code](https://github.com/intergalacticuser/llm-wiki-starter/issues/9)
- [#10 Add release checklist and changelog workflow](https://github.com/intergalacticuser/llm-wiki-starter/issues/10)

Release-ready definition:

`v0.3` is done when the project has a safe public-export story, a wider ingestion surface, and a lightweight release process that future versions can follow.

## Notes

This roadmap is intentionally compact. The goal is not to predict every future feature. The goal is to create a clear sequence of improvements that keeps the project useful, safe, and easy to evolve.

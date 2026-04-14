# Roadmap

This roadmap is the public plan for `llm-wiki-starter`.

The project is inspired by Andrej Karpathy's original LLM Wiki idea. The goal here is to take that pattern and turn it into a practical, repeatable starter that people can actually use across modern LLM tools.

This file is the planning surface in the repository. GitHub issues and milestones are the execution surface.

## How to read this roadmap

- `v0.1 Foundation` focuses on trust, clarity, and day-one usability
- `v0.2 Durable Memory` focuses on turning summaries into stronger long-term memory
- `v0.3 Privacy and Scale` focuses on safe sharing, wider ingestion, and repeatable releases

Issue links are grouped by phase and kept here as the source of truth for release planning.

## v0.1 Foundation

This phase is about making the starter dependable enough that someone can clone it, understand it, and trust the core workflow.

Planned issues:

- Roadmap tracker: v0.x plan for LLM Wiki Starter
- Add parser tests for Codex and Claude chat ingestion
- Add CI for CLI smoke checks and docs integrity
- Add sample public demo corpus and guided walkthrough
- Add wiki lint command for orphan pages, index drift, and stale links

Release-ready definition:

`v0.1` is done when the starter has a tested ingestion baseline, a small public walkthrough, and basic health checks for both the docs and the wiki structure.

## v0.2 Durable Memory

This phase is about moving beyond transcript collection and summary pages. The starter should help users turn repeated work into reusable memory pages.

Planned issues:

- Promote chat summaries into durable memory pages
- Add canonical entity normalization for noisy project names
- Add reusable query filing workflow for durable answers

Release-ready definition:

`v0.2` is done when the starter has a clear, repeatable path from chats and summaries into `entities`, `concepts`, and `queries`.

## v0.3 Privacy and Scale

This phase is about making the system easier to share safely and easier to extend over time.

Planned issues:

- Add safe public-export workflow for private wikis
- Expand chat source support beyond Codex and Claude Code
- Add release checklist and changelog workflow

Release-ready definition:

`v0.3` is done when the project has a safe public-export story, a wider ingestion surface, and a lightweight release process that future versions can follow.

## Notes

This roadmap is intentionally compact. The goal is not to predict every future feature. The goal is to create a clear sequence of improvements that keeps the project useful, safe, and easy to evolve.

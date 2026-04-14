# LLM Wiki Starter

LLM Wiki Starter is a practical starter repository for building a persistent wiki-based memory system with modern LLM agents.

The original idea comes from Andrej Karpathy's "LLM Wiki" note. His post explains the pattern clearly: keep raw sources immutable, let the LLM maintain a structured wiki on top, and let knowledge compound over time instead of being rediscovered on every query.

This repository takes that idea and turns it into something you can actually open in an IDE and use right away.

## What this starter adds

The original note is intentionally abstract. That is part of its strength. It gives you the pattern without locking you into one implementation.

This starter focuses on the missing operational layer:

- ready-to-use instruction files for Codex, Claude Code, Cursor, Windsurf, Copilot, and Cline
- a working chat-ingestion tool for Codex and Claude Code histories
- an incremental `./refresh-memory` command for the day-to-day workflow
- a routing model that tells agents to read `entities`, `concepts`, and `queries` before digging into summaries or raw transcripts
- a cleaner repo shape for turning the idea into a repeatable personal or team setup

## What stays the same

The core architecture is still the same three-layer model:

1. `sources/` holds raw documents and chat transcripts
2. `wiki/` holds LLM-maintained knowledge pages
3. `AGENTS.md` / `CLAUDE.md` / `INSTRUCTIONS.md` define the operating rules

The point is still compounding memory, not one-shot retrieval.

## Quick start

1. Open this folder in your preferred IDE.
2. Let the agent read the instruction file for that IDE.
3. Put a few real source files into `sources/`.
4. Ask the agent to ingest them.
5. Run `./refresh-memory` whenever you want to pull in newly-created chat sessions and rebuild the index.
6. Ask questions against the wiki, not against the raw pile of files.

## Main commands

```bash
# incremental refresh
./refresh-memory

# scope refresh to one IDE
./refresh-memory --ide codex
./refresh-memory --ide claude-code

# scope refresh to the current project or one named project
./refresh-memory --current
./refresh-memory --project "my-project"

# inspect chat history directly
python3 tools/ingest-chats.py list
python3 tools/ingest-chats.py ingest --all
python3 tools/ingest-chats.py ingest --current
```

## Optional Codex skill pack

The repository includes an optional Codex skill pack under `skills/`.

The general entrypoint is `skills/llm-wiki/`, and there are also narrower focused skills for common actions:

- `llm-wiki-refresh`
- `llm-wiki-ingest-this`
- `llm-wiki-ingest-all`
- `llm-wiki-read`
- `llm-wiki-lint`

If you copy these folders into `~/.codex/skills/`, they can be invoked from the Codex skill picker or through explicit prompts such as `$llm-wiki-refresh` and `$llm-wiki-ingest-this`.

## Privacy and publishing

This starter repository is intentionally clean.

It does not ship with personal chats, private sources, project-specific wiki pages, server details, or secrets. That is on purpose.

If you use this system for your own work, be careful before making your wiki public. Raw transcripts, summaries, and derived pages can easily contain:

- private conversations
- access tokens
- deployment details
- customer or team context
- internal architecture notes you did not mean to publish

If your wiki contains real personal or company memory, keep the repository private unless you have explicitly reviewed and sanitized it.

## Attribution

This project is inspired by Andrej Karpathy's LLM Wiki idea:

- Original note: [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

The goal here is not to replace the original idea. It is to offer a working starter kit for people who want to try it immediately.

## Where to read more

- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [From Idea To Working System](docs/from-idea-to-working-system.md)
- [Contributing](CONTRIBUTING.md)
- [Security notes](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## Contributing

Suggestions, corrections, and improvements are welcome.

If you try this in a real workflow and find a better way to structure pages, ingest chats, route context, or keep the wiki healthy over time, open an issue or send a pull request. Practical experience is the whole point.

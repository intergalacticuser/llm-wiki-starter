# From Idea To Working System

This repository started with Andrej Karpathy's LLM Wiki idea.

That original note is valuable precisely because it does not over-specify the implementation. It gives the pattern:

- raw sources stay immutable
- the LLM maintains the wiki
- summaries, entities, concepts, and answered questions become a persistent memory layer
- the value compounds with every ingest and every question

That note is the conceptual foundation for this starter.

## What we kept

We kept the central premise untouched:

- the wiki sits between the LLM and the raw sources
- the LLM is responsible for maintenance work
- knowledge should become more useful over time, not be reassembled from scratch each session

## What we added

To make the pattern easier to use in practice, we added the operational layer that many people end up building for themselves anyway:

### 1. Multi-IDE instruction files

The starter includes instruction files for several common agent environments so the same wiki can be used from different tools without rewriting the operating rules every time.

### 2. Chat ingestion

The repo includes a working ingestion tool for IDE chat history, especially Codex and Claude Code. That turns old sessions into source transcripts and summary pages instead of leaving them trapped inside app-specific history folders.

### 3. Incremental refresh

The `./refresh-memory` command gives you a daily maintenance loop:

1. discover sessions
2. ingest only new or updated chats
3. rebuild the wiki index
4. record the refresh in the log

### 4. Context routing

A frequent failure mode in memory systems is that the agent still jumps straight into raw summaries or sources even after you have already built better pages.

This starter makes routing explicit:

- `entities/` first for project and product questions
- `concepts/` first for recurring patterns and architecture
- `queries/` first for previous syntheses and learned lessons
- summaries only when those durable pages are not enough

### 5. Public-safe starting point

The repository is structured as a starter, not as a dump of a real private memory corpus. That makes it safer to publish, fork, and adapt.

## Why that matters

The jump from idea to usable system is usually not about adding more theory. It is about removing friction:

- how does the agent know what to read first
- how do you ingest chat history without copying files by hand
- how do you avoid reprocessing everything every time
- how do you keep the public repo clean while using the system privately

That is the gap this starter is trying to close.

## Attribution

This project is inspired by Andrej Karpathy's LLM Wiki note and should be understood as an implementation-oriented extension of that idea, not as a replacement for it and not as an official Karpathy project.

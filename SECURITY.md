# Security Notes

This project is a starter for building personal or team memory systems.

That means the biggest security risk is usually not in the tooling itself. It is in the content people ingest into the wiki.

## Do not publish these by accident

Before making a wiki public, review whether it contains:

- personal chats
- internal team conversations
- server addresses
- credentials
- API tokens
- customer data
- internal architecture notes
- deployment commands

## Recommended practice

- keep real working wikis private by default
- use this public repo as a starter, not as a place to dump live memory
- review `sources/`, `wiki/`, and `log.md` before every public push
- keep secrets in environment variables or secret managers, never in markdown pages

If you find an actual security issue in the tooling itself, open a private report first if possible.

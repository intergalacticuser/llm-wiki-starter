#!/bin/bash
# LLM Wiki — Quick chat ingestion wrapper
# Usage:
#   ./wiki-ingest-chats.sh list              # List available chats
#   ./wiki-ingest-chats.sh all               # Ingest all chats
#   ./wiki-ingest-chats.sh current           # Ingest current project
#   ./wiki-ingest-chats.sh project NAME      # Ingest specific project
#   ./wiki-ingest-chats.sh refresh           # Refresh new/updated chats + rebuild index
#   ./wiki-ingest-chats.sh families          # Analyze likely cross-folder product families

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/ingest-chats.py"

case "${1:-help}" in
    list)
        python3 "$PYTHON_SCRIPT" list ${2:+--ide "$2"}
        ;;
    all)
        python3 "$PYTHON_SCRIPT" ingest --all ${2:+--ide "$2"}
        ;;
    current)
        python3 "$PYTHON_SCRIPT" ingest --current
        ;;
    refresh)
        python3 "$SCRIPT_DIR/refresh-memory.py" "${@:2}"
        ;;
    families)
        python3 "$SCRIPT_DIR/analyze-product-families.py" "${@:2}"
        ;;
    project)
        if [ -z "$2" ]; then
            echo "Usage: $0 project PROJECT_NAME"
            exit 1
        fi
        python3 "$PYTHON_SCRIPT" ingest --project "$2"
        ;;
    chat)
        if [ -z "$2" ]; then
            echo "Usage: $0 chat PATH_TO_JSONL"
            exit 1
        fi
        python3 "$PYTHON_SCRIPT" ingest --chat "$2"
        ;;
    help|--help|-h)
        echo "LLM Wiki — Chat Ingestion"
        echo ""
        echo "Usage:"
        echo "  $0 list [ide]              List available chat files"
        echo "  $0 all [ide]               Ingest all chats"
        echo "  $0 current                 Ingest current project's chats"
        echo "  $0 refresh [--ide codex]   Ingest only new/updated chats and rebuild index"
        echo "  $0 families                Analyze likely cross-folder product families"
        echo "  $0 project NAME            Ingest specific project"
        echo "  $0 chat PATH               Ingest specific chat file"
        echo ""
        echo "IDE options: codex, claude-code, cursor, windsurf, continue, cline"
        ;;
    *)
        echo "Unknown command: $1. Use --help for usage."
        exit 1
        ;;
esac

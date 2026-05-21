#!/bin/bash
# Launch the Multimaze Recorder GUI using the project's uv-managed venv.
# Run this script from any directory – it resolves the repo root automatically.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use the installed entry point if available, otherwise fall back to uv run
if [ -f ".venv/bin/mmrecorder" ]; then
    .venv/bin/mmrecorder "$@"
else
    uv run mmrecorder "$@"
fi

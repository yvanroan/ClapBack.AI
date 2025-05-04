#!/bin/bash

mkdir -p backend/data/prompts
echo "$PROMPT_BASE64" | base64 -d > backend/data/prompts/prompts.py

mkdir -p backend/data
echo "$ARCHETYPE_BASE64" | base64 -d > backend/data/archetype.py

exec python -m backend.app.main
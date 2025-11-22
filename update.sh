#!/bin/bash
set -e

echo "📌 Updating repo..."
git add -A
git commit -m "auto update $(date +%d%m%y)"
git push

echo "📌 Uninstalling llmcui..."
pip uninstall -y llmcui || true

echo "📌 Removing ~/.llmcui/ai.db..."
rm -f "$HOME/.llmcui/ai.db"

echo "📌 Reinstalling llmcui (editable)..."
pip install -e .

echo "✅ Finished."

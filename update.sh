#!/bin/bash
set -e

echo "📌 Updating repo..."
git add -A
git commit -m "auto update $(date +%d%m%y_%H%M%S)"
git push

echo "📌 Uninstalling llmcui..."
pip uninstall -y llmcui || true

echo "📌 Removing ~/.llmcui/ai.db..."
rm -f "$HOME/.llmcui/ai.db"

echo "📌 Reinstalling llmcui (editable)..."
pip install -e .

echo "📌 Running tests with coverage..."
pytest \
  --cov=cli \
  --cov=core \
  --cov=tests \
  --cov-report=term-missing \
  --cov-report=html

echo "📊 Coverage HTML created at: htmlcov/index.html"
echo "✅ Finished."

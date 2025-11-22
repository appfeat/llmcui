#!/bin/bash
set -e

REPO_DIR="$HOME/proj/llmcui"
DB_FILE="$HOME/.llmcui/ai.db"

echo "📌 Step 1: Uninstalling llmcui (if any)..."
pip uninstall -y llmcui || true

echo "📌 Step 2: Removing local ai.db..."
rm -f "$DB_FILE"
echo "   Removed $DB_FILE"

echo "📌 Step 3: Ensuring pytest + pytest-cov are installed..."
pip install --quiet pytest pytest-cov

echo "📌 Step 4: Setting PYTHONPATH..."
export PYTHONPATH="$REPO_DIR:$PYTHONPATH"
echo "   PYTHONPATH=$PYTHONPATH"

echo "📌 Step 5: Running full test suite with coverage..."
cd "$REPO_DIR"

pytest \
  --strict-markers \
  --strict-config \
  --disable-warnings \
  --cov=cli \
  --cov=core \
  --cov-report=term-missing \
  -q

echo "✅ Tests completed successfully. No warnings or errors."

echo "📌 Step 6: Git commit + push..."
git add -A
git commit -m "auto update $(date +%d%m%y_%H%M%S)"
git push

echo "📌 Step 7: Reinstalling llmcui locally..."
pip install -e .

echo "🎉 COMPLETE: uninstall → db reset → test → commit → push → reinstall."

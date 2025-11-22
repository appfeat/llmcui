#!/bin/bash
set -euo pipefail

REPO_DIR="$(pwd)"
TARGET_DB="$HOME/.llmcui/ai.db"
TIMESTAMP="$(date +'%d%m%y_%H%M%S')"

echo "📌 Step 1: Uninstalling llmcui package (safe)..."
pip uninstall -y llmcui || true
echo ""

echo "📌 Step 2: Removing local ai.db..."
if [ -f "$TARGET_DB" ]; then
    rm -f "$TARGET_DB"
    echo "   Removed $TARGET_DB"
else
    echo "   No ai.db found."
fi
echo ""

echo "📌 Step 3: Ensuring pytest + pytest-cov are installed..."
pip install pytest pytest-cov > /dev/null
echo ""

echo "📌 Step 4: Setting PYTHONPATH for tests..."
export PYTHONPATH="$REPO_DIR"
echo "   PYTHONPATH=$PYTHONPATH"
echo ""

echo "📌 Step 5: Running full test suite with coverage (warnings = errors)..."
pytest \
    -W error \
    --disable-warnings \
    --cov=cli \
    --cov=core \
    --cov=tests \
    --cov-report=term-missing
echo ""

echo "📌 Step 6: Committing changes..."
git add -A
git commit -m "auto update $TIMESTAMP"
git push
echo ""

echo "📌 Step 7: Reinstalling llmcui locally (editable mode)..."
pip install -e .
echo ""

echo "🎉 COMPLETE: uninstall → db reset → test → commit → push → reinstall"

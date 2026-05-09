#!/usr/bin/env bash
set -e

echo "Building ask-gemini standalone executable..."
pyinstaller --onefile \
    --name ask-gemini \
    --hidden-import browser_cookie3 \
    --hidden-import gemini_webapi \
    ask_gemini/main.py

echo ""
echo "Executable built at: dist/ask-gemini"
ls -lh dist/ask-gemini
echo ""
echo "Test it with: ./dist/ask-gemini --help"

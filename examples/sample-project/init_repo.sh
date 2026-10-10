#!/usr/bin/env bash
# Helper script to initialize a standalone Git repository for testing
set -euo pipefail

TARGET_DIR="${1:-.}"
cd "$TARGET_DIR"

if [ -d ".git" ]; then
    echo "Git repository already initialized in $PWD"
    exit 0
fi

git init -q
git config user.name "PayPulse Bot"
git config user.email "bot@paypulse.local"

# Replay commits from git-log.txt or commit current files
git add .
git commit -q -m "feat: initial commit of PayPulse sample project"
git branch -M main

echo "Sample git repository initialized successfully in $PWD"

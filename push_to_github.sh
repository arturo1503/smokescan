#!/bin/bash
# Push SmokeStudio + SmokeScan to GitHub
# Run this from the smokescan-repo directory

echo "Setting up git credentials..."
# Use GitHub CLI if available
if command -v gh &> /dev/null; then
    gh auth setup-git
    echo "✅ Using gh CLI for auth"
else
    echo "❌ GitHub CLI not found. Please install: brew install gh"
    echo "   Then run: gh auth login"
    exit 1
fi

echo ""
echo "Pushing all files to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All files pushed successfully!"
    echo "   Repository: https://github.com/arturo1503/smokescan"
    echo "   Vercel will auto-deploy from this push."
else
    echo ""
    echo "❌ Push failed. Try:"
    echo "   1. Run: gh auth login"
    echo "   2. Choose: GitHub.com > HTTPS > Login with browser"
    echo "   3. Try again: bash push_to_github.sh"
fi

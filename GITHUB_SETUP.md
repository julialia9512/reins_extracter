# GitHub Setup Instructions

After installing Git, follow these steps:

## Step 1: Configure Git (First time only)

Open PowerShell and run:
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 2: Initialize Repository

```powershell
cd "C:\Users\sakai julia\Documents\paste-scraper"
git init
git add .
git commit -m "Initial commit: Real estate data scraper with Streamlit"
```

## Step 3: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `reins_extracter`
3. **DO NOT** initialize with README, .gitignore, or license (we already have these)

## Step 4: Push to GitHub

Run these commands (replace YOUR_USERNAME with your GitHub username):

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/reins_extracter.git
git push -u origin main
```

## Alternative: Use GitHub CLI (if installed)

```powershell
gh repo create reins_extracter --public --source=. --push
```

## Quick Commands Reference

- `git status` - Check current status
- `git add .` - Stage all changes
- `git commit -m "message"` - Commit changes
- `git push` - Upload to GitHub
- `git pull` - Download from GitHub


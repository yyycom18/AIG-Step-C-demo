# Deploy Project03 to GitHub

Push this project to: **https://github.com/yyycom18/AIG-Step-C-demo**

## Prerequisites

- **Git** installed and in your PATH.  
  Download: https://git-scm.com/download/win  
  Or install via: `winget install Git.Git`

## Steps

Run these in **PowerShell** or **Command Prompt** from the **Project03** folder:

```powershell
cd "C:\Users\user\Desktop\Cursor\Project03"

# 1. Initialize repository (if not already)
git init

# 2. Add remote
git remote add origin https://github.com/yyycom18/AIG-Step-C-demo.git

# 3. Stage all files
git add .

# 4. Commit
git commit -m "Add Project03: HY-IG Spread Indicator Analysis dashboard and backtest"

# 5. Use main branch and push
git branch -M main
git push -u origin main
```

## Authentication

- **HTTPS:** On first push, Git will ask for username and password.  
  Use your **GitHub username** and a **Personal Access Token** (not your GitHub password).  
  Create a token: GitHub → Settings → Developer settings → Personal access tokens.

- **SSH:** If you use SSH:
  ```powershell
  git remote set-url origin git@github.com:yyycom18/AIG-Step-C-demo.git
  git push -u origin main
  ```

## If the repo already has content

If the remote already has commits (e.g. README):

```powershell
git pull origin main --allow-unrelated-histories
# Resolve any merge conflicts, then:
git push -u origin main
```

## What gets pushed

- All source: `*.py`, `index03.html`, `run_server.py`, `requirements.txt`, `README.md`, etc.
- `data/` and `outputs/` (for the dashboard to work after clone)
- Excluded via `.gitignore`: `__pycache__/`, `*.pyc`, `.env`, `venv/`, `.venv/`, IDE/OS junk

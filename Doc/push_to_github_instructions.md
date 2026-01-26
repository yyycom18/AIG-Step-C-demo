# How to Push Project03 to GitHub (with GitHub Desktop)

_(Updated: 2026-01-18)_

## Prerequisites
- **GitHub Desktop** installed ([Download here](https://desktop.github.com/))
- A GitHub account (your username: `yyycom`)
- Your repository created on GitHub and cloned locally

---

## Steps

### 1. Open GitHub Desktop
- Launch the GitHub Desktop app

### 2. Select Your Repository
- Top left: choose `AIG-Step-C-demo` (or your project)

### 3. Make Local Changes
- Edit, add, or remove files in your editor (VSCode, Cursor, etc.)

### 4. Commit Your Changes
- See changed files in GitHub Desktop's left panel
- Enter a descriptive commit message at the bottom left
- Click `Commit to main` (or current branch)

### 5. Push to GitHub
- Click `Push origin` at the top
- Wait for successful push

### 6. Verify Online
- Visit https://github.com/yyycom18/AIG-Step-C-demo
- Confirm your commit(s) are present

---

### ⚠️ Token Security Warning
Never commit or place your GitHub token (like `ghp_...`) in any file, code, or documentation.
Always use your credentials securely via the app or CLI authentication.

---

## Advanced: Command Line Alternative
```bash
git add .
git commit -m "Describe your changes"
git push origin main
```
(Authenticate when prompted. SSH setup is recommended for repeat use.)

---

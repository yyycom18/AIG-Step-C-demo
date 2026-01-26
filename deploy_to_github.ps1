# Deploy Project03 to https://github.com/yyycom18/AIG-Step-C-demo
# Run from Project03 folder. Requires Git in PATH.

$ErrorActionPreference = "Stop"
$REPO = "https://github.com/yyycom18/AIG-Step-C-demo.git"
$BRANCH = "main"

Set-Location $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git is not in PATH. Install from https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path .git)) {
    git init
    Write-Host "Initialized git repository." -ForegroundColor Green
}

$rem = git remote get-url origin 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or -not $rem -or $rem -match "error:") {
    git remote add origin $REPO
    Write-Host "Added remote: $REPO" -ForegroundColor Green
} elseif ($rem -ne $REPO) {
    Write-Host "Remote 'origin' already points to: $rem" -ForegroundColor Yellow
    Write-Host "To use AIG-Step-C-demo, run: git remote set-url origin $REPO" -ForegroundColor Yellow
}

git add .
git status

$msg = "Add Project03: HY-IG Spread Indicator Analysis dashboard and backtest"
git commit -m $msg 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing to commit, or commit failed. Continuing." -ForegroundColor Yellow
}

git branch -M $BRANCH
Write-Host "Pushing to $REPO ($BRANCH)..." -ForegroundColor Cyan
git push -u origin $BRANCH

Write-Host "Done. Repo: https://github.com/yyycom18/AIG-Step-C-demo" -ForegroundColor Green

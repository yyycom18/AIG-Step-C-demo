# Quick push script for Project03 to GitHub
# Run this from your own terminal (not in Cursor's sandboxed environment)

Set-Location $PSScriptRoot

Write-Host "Pushing Project03 to GitHub..." -ForegroundColor Cyan
Write-Host "Repository: https://github.com/yyycom18/AIG-Step-C-demo" -ForegroundColor Cyan
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "View your repo: https://github.com/yyycom18/AIG-Step-C-demo" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Check your network connection and try again." -ForegroundColor Red
    Write-Host "You can also try: git push -u origin main" -ForegroundColor Yellow
}

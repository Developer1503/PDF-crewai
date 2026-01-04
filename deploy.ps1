# Quick Deploy Script for PDF-crewai v2.0
# PowerShell script for Windows

Write-Host "🚀 PDF-crewai v2.0 - Quick Deploy" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "📝 Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git initialized" -ForegroundColor Green
}

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "📝 Uncommitted changes detected" -ForegroundColor Yellow
    $commitMsg = Read-Host "Enter commit message"
    
    git add .
    git commit -m "$commitMsg"
    Write-Host "✅ Changes committed" -ForegroundColor Green
}

# Check if remote exists
$remote = git remote -v
if (-not $remote) {
    Write-Host ""
    Write-Host "⚠️  No remote repository configured" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please create a GitHub repository and run:" -ForegroundColor Cyan
    Write-Host "git remote add origin https://github.com/YOUR_USERNAME/PDF-crewai.git" -ForegroundColor White
    Write-Host "git branch -M main" -ForegroundColor White
    Write-Host "git push -u origin main" -ForegroundColor White
    Write-Host ""
    
    $createRepo = Read-Host "Would you like to open GitHub to create a repository? (y/n)"
    if ($createRepo -eq "y") {
        Start-Process "https://github.com/new"
    }
    
    exit
}

# Push to remote
Write-Host ""
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Go to https://share.streamlit.io" -ForegroundColor White
    Write-Host "2. Click 'New app'" -ForegroundColor White
    Write-Host "3. Select your repository" -ForegroundColor White
    Write-Host "4. Set main file: app_v2.py" -ForegroundColor White
    Write-Host "5. Add your API keys in secrets" -ForegroundColor White
    Write-Host "6. Click Deploy!" -ForegroundColor White
    Write-Host ""
    
    $openStreamlit = Read-Host "Would you like to open Streamlit Cloud now? (y/n)"
    if ($openStreamlit -eq "y") {
        Start-Process "https://share.streamlit.io"
    }
} else {
    Write-Host "❌ Push failed. Please check your remote configuration." -ForegroundColor Red
}

Write-Host ""
Write-Host "📚 For detailed instructions, see DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan

@echo off
setlocal enabledelayedexpansion
title Push RESONA to GitHub
echo =========================================================================
echo   RESONA: Push Project to GitHub
echo =========================================================================
echo.

cd /d "%~dp0"

:: Check if git remote origin exists
git remote get-url origin >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Remote 'origin' is not set yet.
    echo Please paste your GitHub repository URL (e.g. https://github.com/ThanushreeP/RESONA.git):
    set /p REPO_URL="Repository URL: "
    if "!REPO_URL!"=="" (
        echo No URL provided. Aborting.
        pause
        exit /b 1
    )
    git remote add origin !REPO_URL!
    echo Set remote origin to: !REPO_URL!
) else (
    for /f "delims=" %%u in ('git remote get-url origin') do set CURRENT_URL=%%u
    echo Current remote origin: !CURRENT_URL!
    echo Press ENTER to use this URL, or paste a new URL:
    set /p NEW_URL="New URL (or press ENTER): "
    if not "!NEW_URL!"=="" (
        git remote set-url origin !NEW_URL!
        echo Updated remote origin to: !NEW_URL!
    )
)

echo.
echo Staging all project files...
git add -A
git commit -m "Complete RESONA Accessible Coding System for Blind Programmers (KSCST 50th Series)" >nul 2>&1

echo.
echo Pushing branch 'main' to GitHub...
git branch -M main
git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo -------------------------------------------------------------------------
    echo If push was rejected because remote repository has an existing README or commits:
    echo -------------------------------------------------------------------------
    set /p CONFIRM="Force push to overwrite remote with this complete project? (Y/N): "
    if /i "!CONFIRM!"=="Y" (
        git push --force -u origin main
    )
)

echo.
echo =========================================================================
echo   Done! Check your GitHub repository in your browser.
echo =========================================================================
pause

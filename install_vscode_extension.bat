@echo off
title Install RESONA VS Code Extension
echo =========================================================================
echo   Installing RESONA Audio Code Assistant into VS Code
echo   JSS Science & Technology University - KSCST 50th Series
echo =========================================================================

set EXT_DIR=%USERPROFILE%\.vscode\extensions\resona-vscode

echo Copying extension files to %EXT_DIR%...
if not exist "%EXT_DIR%" mkdir "%EXT_DIR%"
xcopy /E /I /Y "%~dp0vscode-extension" "%EXT_DIR%"

echo.
echo =========================================================================
echo   RESONA Extension Successfully Installed into VS Code!
echo   Open VS Code and press Ctrl+Alt+S to launch RESONA Studio.
echo =========================================================================
pause

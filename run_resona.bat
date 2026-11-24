@echo off
title RESONA: Accessible Programming System (JSS STU - KSCST)
echo =========================================================================
echo   Launching RESONA: Audio-Augmented Code Comprehension for Blind Programmers
echo   KSCST 50th Series Student Project - JSS Science & Technology University
echo =========================================================================

set PYTHONPATH=%~dp0..;%~dp0;%PYTHONPATH%

python -m pip install -r requirements.txt --quiet --no-warn-script-location
python start.py

pause

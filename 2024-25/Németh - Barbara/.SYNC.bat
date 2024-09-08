@echo off

:: Add all files to the staging area
git add *

for /f "tokens=1-3 delims=:.," %%a in ("%TIME%") do (
    set "COMMIT_MSG=%%a:%%b"
)
set "COMMIT_MSG=%DATE% - %COMMIT_MSG%"

git commit -m "%COMMIT_MSG%"

git commit --amend -m "%COMMIT_MSG%"

echo Pulling changes from the remote repository...
git pull --tags origin main

echo Pushing changes...
git push --force

echo.
echo Upload successful.

TIMEOUT /T 1 > nul

exit

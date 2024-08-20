@echo off

:: Add all files to the staging area
git add --all

set COMMIT_MSG=%DATE% - %TIME%
git commit -m "%COMMIT_MSG%"

git commit --amend -m "%COMMIT_MSG%"

echo Pulling changes from the remote repository...
git pull --tags origin main

echo Pushing changes...
git push --force --quiet

echo.
echo Upload successful.

TIMEOUT /T 1 > nul

exit

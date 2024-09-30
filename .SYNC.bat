@echo off

git checkout main

git add .

for /f "tokens=1-3 delims=:.," %%a in ("%TIME%") do (
    set "COMMIT_MSG=%%a:%%b"
)
set "COMMIT_MSG=%DATE% - %COMMIT_MSG%"

git commit -m "%COMMIT_MSG%"

echo.
echo PULL-ing changes...
git pull

echo.
echo PUSH-ing changes...
git push

echo.
echo Syncing finished.

TIMEOUT /T 1 > nul

exit

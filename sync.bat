@echo off
cd /d "C:\Users\saulo\Desktop\Claude Code"
git add -A
git diff --staged --quiet
if errorlevel 1 (
    git commit -m "sync: alteracao manual"
    git push
    echo Sincronizado com sucesso!
) else (
    echo Nenhuma alteracao para sincronizar.
)
pause

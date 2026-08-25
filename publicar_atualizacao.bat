@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Publicar atualizacao - GM Planning Dashboard

cd /d "%~dp0"

echo ============================================================
echo   Publicar atualizacao no GM Planning Dashboard
echo ============================================================
echo.
echo Pasta: %cd%
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Esta pasta nao e um repositorio git.
    echo Verifique se este arquivo esta em: ...\14. GM Planning\Modelo
    echo.
    pause
    exit /b 1
)

echo Verificando alteracoes...
git add -A

git diff --cached --quiet
if not errorlevel 1 (
    echo.
    echo Nenhuma alteracao encontrada em app.py, theme.py, Input\*.xlsx etc.
    echo Nada para publicar.
    echo.
    pause
    exit /b 0
)

echo.
echo Alteracoes detectadas:
git diff --cached --stat
echo.

set "msg="
set /p msg="Descreva rapidamente o que mudou (Enter para usar data/hora): "
if "!msg!"=="" (
    for /f "tokens=1-4 delims=/ " %%a in ('date /t') do set "hoje=%%a-%%b-%%c"
    set "msg=Atualizacao !date! !time!"
)

echo.
echo Gravando commit...
git commit -m "!msg!"
if errorlevel 1 (
    echo.
    echo [ERRO] O commit falhou. Veja a mensagem acima.
    echo.
    pause
    exit /b 1
)

echo.
echo Enviando para o GitHub (isso atualiza o site automaticamente)...
git push
if errorlevel 1 (
    echo.
    echo [ERRO] O envio para o GitHub falhou. Veja a mensagem acima.
    echo Se pedir login, complete a autenticacao na janela/navegador que abrir.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Pronto! O site vai atualizar sozinho em ate 1 minuto:
echo   https://gm-planning-dashboard.streamlit.app/
echo ============================================================
echo.
pause

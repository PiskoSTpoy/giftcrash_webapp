@echo off
chcp 65001 >nul
title База знаний Аркона — запуск
cd /d "%~dp0"

echo ============================================================
echo   Запуск базы знаний «Аркона» с доступом по интернету
echo ============================================================
echo.

REM 1) Проверяем Python
where python >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Python не найден.
    echo Установите Python с https://www.python.org/downloads/
    echo При установке отметьте галочку "Add Python to PATH".
    pause
    exit /b 1
)

REM 2) Проверяем cloudflared.exe рядом с этим файлом
if not exist "%~dp0cloudflared.exe" (
    echo [ОШИБКА] Не найден cloudflared.exe в этой папке.
    echo Скачайте его: https://github.com/cloudflare/cloudflared/releases/latest
    echo Нужен файл cloudflared-windows-amd64.exe — переименуйте в cloudflared.exe
    echo и положите рядом с этим start-windows.bat
    pause
    exit /b 1
)

REM 3) Запускаем локальный сервер с логином/паролем в отдельном окне
echo Запускаю локальный сервер (окно "KB server")...
start "KB server" python "%~dp0kb-server.py"

REM Небольшая пауза, чтобы сервер успел подняться
timeout /t 3 >nul

echo.
echo Открываю интернет-туннель. Ниже появится ссылка вида
echo   https://что-то.trycloudflare.com
echo Откройте её на телефоне и введите логин/пароль из kb-server.py.
echo (Чтобы остановить — закройте это окно и окно "KB server".)
echo ============================================================
echo.

REM 4) Туннель Cloudflare на локальный сервер
"%~dp0cloudflared.exe" tunnel --url http://localhost:8000

pause

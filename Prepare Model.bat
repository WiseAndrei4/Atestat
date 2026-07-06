@echo off
title Math OCR - Launcher
setlocal

:: CONFIGURARE: Aici spunem unde să stea DOAR modelele
set OLLAMA_MODELS=%CD%\ollama_storage
if not exist "ollama_storage" mkdir "ollama_storage"

echo [1/2] Repornire Server Ollama pe folder local...
taskkill /f /im "ollama app.exe" >nul 2>&1
taskkill /f /im "ollama.exe" >nul 2>&1
start "" "C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama app.exe"
timeout /t 5 /nobreak >nul

echo [2/2] Pornire Aplicatie...
".venv\Scripts\python.exe" UI_Driver.py

pause
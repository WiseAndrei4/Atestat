@echo off
title Math OCR - Launcher
setlocal

:: CONFIGURARE: Aici spunem unde să stea DOAR modelele
set OLLAMA_MODELS=%CD%\ollama_storage
if not exist "ollama_storage" mkdir "ollama_storage"

echo [1/3] Repornire Server Ollama pe folder local...
taskkill /f /im "ollama app.exe" >nul 2>&1
taskkill /f /im "ollama.exe" >nul 2>&1
start "" "C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama app.exe"
timeout /t 5 /nobreak >nul

echo [2/3] Verificare modele in folderul proiectului...
ollama pull ministral-3:3b

echo [3/3] Pornire Aplicatie...
".venv\Scripts\python.exe" UI_Driver.py

pause
@echo off
setlocal enabledelayedexpansion

title Astra-Hunters-2.0 Launch Manager
color 0A

echo ======================================================================
echo           ASTRA-HUNTERS-2.0 - FULL SYSTEM LAUNCH MANAGER
echo   Multimodal AI Public Speaking & Presentation Evaluation Platform
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: 1. Check Python Virtual Environment
echo [1/3] Checking Python Virtual Environment (.venv)...
if not exist "%ROOT_DIR%.venv\Scripts\activate.bat" (
    color 0C
    echo [ERROR] Virtual environment not found at: %ROOT_DIR%.venv
    echo Please ensure the .venv folder exists with required Python dependencies.
    pause
    exit /b 1
)
echo [OK] Virtual environment found.
echo.

:: 2. Launch FastAPI Backend Server
echo [2/3] Launching FastAPI Backend Server (Port 8000)...
start "Astra-Hunters Backend [FastAPI :8000]" cmd /k "cd /d "%ROOT_DIR%" && "%ROOT_DIR%.venv\Scripts\python.exe" -m uvicorn api:app --port 8000"


:: Wait briefly for FastAPI backend to bind to port
timeout /t 3 /nobreak >nul
echo [OK] FastAPI backend launched in a dedicated terminal.
echo.

:: 3. Launch Frontend (Astra-Frontend)
echo [3/3] Preparing React / Vite Frontend...
cd /d "%ROOT_DIR%Astra-Frontend"

if not exist "node_modules\" (
    echo [INFO] node_modules not found. Running npm install...
    call npm install
    if !errorlevel! neq 0 (
        color 0C
        echo [ERROR] npm install failed. Please check your network and node installation.
        pause
        exit /b 1
    )
)

echo [OK] Dependencies ready. Starting Vite development server...
echo.
echo ======================================================================
echo   Astra-Hunters-2.0 is launching!
echo   Backend:  http://127.0.0.1:8000 (API docs: http://127.0.0.1:8000/docs)
echo   Frontend: http://localhost:5173
echo ======================================================================
echo.

call npm run dev

pause

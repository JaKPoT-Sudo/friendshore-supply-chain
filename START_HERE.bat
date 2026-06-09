@echo off
echo === FriendShore Supply Chain De-Risking Engine ===
echo.

:: Check for .env
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Copy .env.example to .env and add your ANTHROPIC_API_KEY.
    pause
    exit /b 1
)

:: Create venv if it doesn't exist
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Install / update dependencies
echo Installing dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt -q

echo.
echo Starting FriendShore...
echo Open http://localhost:8000 in your browser.
echo Press Ctrl+C to stop.
echo.

venv\Scripts\uvicorn.exe main:app --reload --host 0.0.0.0 --port 8000

pause

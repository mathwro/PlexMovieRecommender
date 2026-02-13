@echo off
setlocal

:: -------------------------------------------------------
:: PlexMovieRecommender - NSSM service installer
:: Run as Administrator
:: -------------------------------------------------------

set SERVICE_NAME=PlexRecommenderBot
set SCRIPT_DIR=%~dp0
:: Strip trailing backslash - CreateProcess rejects paths ending with '\'
set APP_DIR=%~dp0
if "%APP_DIR:~-1%"=="\" set APP_DIR=%APP_DIR:~0,-1%

:: Find Python - prefer venv inside the project directory
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    set PYTHON_EXE=%SCRIPT_DIR%venv\Scripts\python.exe
    echo Found venv at: %SCRIPT_DIR%venv
) else if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe
    echo Found venv at: %SCRIPT_DIR%.venv
) else (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        if not defined PYTHON_EXE set PYTHON_EXE=%%i
    )
    if not defined PYTHON_EXE (
        echo ERROR: python.exe not found. Install Python or create a venv first.
        pause
        exit /b 1
    )
    echo WARNING: No venv found, using system Python: %PYTHON_EXE%
    echo          The service may fail if packages are not installed system-wide.
)

if not exist "%SCRIPT_DIR%.env" (
    echo ERROR: .env file not found at %SCRIPT_DIR%.env
    echo        Copy .env.example to .env and fill in your values.
    pause
    exit /b 1
)

echo.
echo Using Python:  %PYTHON_EXE%
echo Script dir:    %SCRIPT_DIR%
echo Service name:  %SERVICE_NAME%
echo.

:: Remove existing service if present
nssm status %SERVICE_NAME% >nul 2>&1
if %errorlevel%==0 (
    echo Removing existing service...
    nssm stop %SERVICE_NAME% >nul 2>&1
    nssm remove %SERVICE_NAME% confirm
)

:: Install service
nssm install %SERVICE_NAME% "%PYTHON_EXE%"
nssm set %SERVICE_NAME% AppParameters "-u \"%SCRIPT_DIR%bot.py\""
nssm set %SERVICE_NAME% AppDirectory "%APP_DIR%"
nssm set %SERVICE_NAME% AppStdout "%SCRIPT_DIR%bot.log"
nssm set %SERVICE_NAME% AppStderr "%SCRIPT_DIR%bot_error.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateSeconds 86400
nssm set %SERVICE_NAME% AppRotateBytes 10485760
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START
nssm set %SERVICE_NAME% DisplayName "Plex Movie Recommender Bot"
nssm set %SERVICE_NAME% Description "Discord bot that recommends Plex movies"

:: Start it
echo.
echo Starting service...
nssm start %SERVICE_NAME%

if %errorlevel%==0 (
    echo.
    echo Service started successfully.
) else (
    echo.
    echo Service failed to start. Check the logs for details:
    echo   %SCRIPT_DIR%bot.log
    echo   %SCRIPT_DIR%bot_error.log
)

echo.
echo Commands to manage the service:
echo   nssm start   %SERVICE_NAME%
echo   nssm stop    %SERVICE_NAME%
echo   nssm restart %SERVICE_NAME%
echo   nssm remove  %SERVICE_NAME% confirm
echo.
echo Logs: %SCRIPT_DIR%bot.log  (stdout)
echo       %SCRIPT_DIR%bot_error.log  (stderr)
pause

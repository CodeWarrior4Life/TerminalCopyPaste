@echo off
echo ============================================
echo   TCP - Terminal Copy Paste Installer
echo ============================================
echo.

:: Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: PowerShell is required but not found.
    echo Please install PowerShell and try again.
    pause
    exit /b 1
)

:: Launch the PowerShell installer with execution policy bypass
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0install.ps1" %*

:: Pause so user can see output if double-clicked from Explorer
if "%1"=="" pause

#Requires -Version 5.1
<#
.SYNOPSIS
    TCP (Terminal Copy Paste) installer for Windows.
    Detects and installs Python 3.12+, AutoHotkey v2, pip dependencies,
    config, and optional startup shortcut.
.DESCRIPTION
    Run directly:   .\install.ps1
    Or via batch:   install.bat
    Or one-liner:   irm https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

# --- Constants ---
$PYTHON_MIN_MAJOR = 3
$PYTHON_MIN_MINOR = 12
$PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
$AHK_DOWNLOAD_URL = "https://www.autohotkey.com/download/ahk-v2.exe"
$REPO_URL = "https://github.com/CodeWarrior4Life/TerminalCopyPaste.git"
$INSTALL_DIR_DEFAULT = "$env:LOCALAPPDATA\tcp"

# --- Helper Functions ---

function Write-Status {
    param([string]$Status, [string]$Message)
    switch ($Status) {
        "OK"      { Write-Host "  [OK] " -ForegroundColor Green -NoNewline; Write-Host $Message }
        "INSTALL" { Write-Host "  [INSTALL] " -ForegroundColor Yellow -NoNewline; Write-Host $Message }
        "SKIP"    { Write-Host "  [SKIP] " -ForegroundColor Cyan -NoNewline; Write-Host $Message }
        "ERROR"   { Write-Host "  [ERROR] " -ForegroundColor Red -NoNewline; Write-Host $Message }
        "INFO"    { Write-Host "  [INFO] " -ForegroundColor White -NoNewline; Write-Host $Message }
    }
}

function Get-PythonVersion {
    try {
        $output = & python --version 2>&1
        if ($output -match "Python (\d+)\.(\d+)") {
            return @{ Major = [int]$Matches[1]; Minor = [int]$Matches[2] }
        }
    } catch {}
    return $null
}

function Test-PythonInstalled {
    $ver = Get-PythonVersion
    if ($null -eq $ver) { return $false }
    if ($ver.Major -gt $PYTHON_MIN_MAJOR) { return $true }
    if ($ver.Major -eq $PYTHON_MIN_MAJOR -and $ver.Minor -ge $PYTHON_MIN_MINOR) { return $true }
    return $false
}

function Test-AHKInstalled {
    # Check for AHK v2 specifically (v1 is not compatible)
    $regPath = "HKLM:\SOFTWARE\AutoHotkey"
    if (Test-Path "$regPath\v2") { return $true }
    # Check version string in base key
    try {
        $ver = (Get-ItemProperty $regPath -ErrorAction SilentlyContinue).Version
        if ($ver -and $ver -like "2.*") { return $true }
    } catch {}
    # Check PATH
    try {
        $result = Get-Command "AutoHotkey64.exe" -ErrorAction SilentlyContinue
        if ($result) { return $true }
    } catch {}
    return $false
}

function Install-Python {
    Write-Status "INSTALL" "Downloading Python $PYTHON_MIN_MAJOR.$PYTHON_MIN_MINOR+..."
    $installer = "$env:TEMP\python-installer.exe"
    try {
        Invoke-WebRequest -Uri $PYTHON_DOWNLOAD_URL -OutFile $installer -UseBasicParsing
        Write-Status "INSTALL" "Installing Python (this may take a minute)..."
        $proc = Start-Process -FilePath $installer -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_launcher=1" -Wait -PassThru
        if ($proc.ExitCode -ne 0) {
            Write-Status "ERROR" "Python installer exited with code $($proc.ExitCode)"
            exit 1
        }
        # Refresh PATH so python is available in this session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        Write-Status "OK" "Python installed successfully"
    } finally {
        if (Test-Path $installer) { Remove-Item $installer -Force }
    }
}

function Install-AHK {
    Write-Status "INSTALL" "Downloading AutoHotkey v2..."
    $installer = "$env:TEMP\ahk-v2-installer.exe"
    try {
        Invoke-WebRequest -Uri $AHK_DOWNLOAD_URL -OutFile $installer -UseBasicParsing
        Write-Status "INSTALL" "Installing AutoHotkey v2..."
        $proc = Start-Process -FilePath $installer -ArgumentList "/silent" -Wait -PassThru
        if ($proc.ExitCode -ne 0) {
            Write-Status "ERROR" "AHK installer exited with code $($proc.ExitCode)"
            exit 1
        }
        Write-Status "OK" "AutoHotkey v2 installed successfully"
    } finally {
        if (Test-Path $installer) { Remove-Item $installer -Force }
    }
}

function Install-PipDeps {
    param([string]$ReqFile)
    Write-Status "INSTALL" "Installing Python dependencies..."
    & python -m pip install --quiet --upgrade pip 2>&1 | Out-Null
    & python -m pip install --quiet -r $ReqFile
    if ($LASTEXITCODE -ne 0) {
        Write-Status "ERROR" "pip install failed"
        exit 1
    }
    Write-Status "OK" "Python dependencies installed"
}

function Copy-DefaultConfig {
    param([string]$ProjectDir)
    $configDir = "$env:APPDATA\tcp"
    $configFile = "$configDir\config.toml"
    $exampleFile = "$ProjectDir\config\config.example.toml"

    if (Test-Path $configFile) {
        Write-Status "SKIP" "Config already exists at $configFile"
        return
    }

    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }

    if (Test-Path $exampleFile) {
        Copy-Item $exampleFile $configFile
        Write-Status "OK" "Config created at $configFile"
    } else {
        Write-Status "SKIP" "No example config found, skipping"
    }
}

function Set-StartupShortcut {
    param([string]$AhkScript)
    $startupDir = [System.Environment]::GetFolderPath("Startup")
    $shortcutPath = "$startupDir\TCP.lnk"

    if (Test-Path $shortcutPath) {
        Write-Status "SKIP" "Startup shortcut already exists"
        return
    }

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $AhkScript
    $shortcut.WorkingDirectory = Split-Path $AhkScript
    $shortcut.Description = "Terminal Copy Paste"
    $shortcut.Save()
    Write-Status "OK" "Startup shortcut created"
}

function Get-ProjectDir {
    # Check if we're running from within the repo
    # Note: $PSScriptRoot is empty when run via irm | iex (remote mode)
    if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "requirements.txt"))) {
        return $PSScriptRoot
    }

    # Remote mode: clone the repo
    Write-Status "INFO" "Remote mode detected. Cloning TCP repository..."
    $installDir = $INSTALL_DIR_DEFAULT

    if (Test-Path "$installDir\requirements.txt") {
        Write-Status "INFO" "Existing installation found, updating..."
        Push-Location $installDir
        & git pull --quiet 2>&1 | Out-Null
        Pop-Location
        return $installDir
    }

    # Check for git
    try {
        Get-Command "git" -ErrorAction Stop | Out-Null
    } catch {
        Write-Status "ERROR" "Git is required for remote installation. Install Git and try again."
        exit 1
    }

    & git clone --quiet $REPO_URL $installDir
    if ($LASTEXITCODE -ne 0) {
        Write-Status "ERROR" "Failed to clone repository"
        exit 1
    }
    Write-Status "OK" "Repository cloned to $installDir"
    return $installDir
}

# --- Main ---

Write-Host ""
Write-Host "  TCP - Terminal Copy Paste Installer" -ForegroundColor Cyan
Write-Host "  ====================================" -ForegroundColor Cyan
Write-Host ""

# Step 0: Determine project directory
$projectDir = Get-ProjectDir

# Step 1: Python
if (Test-PythonInstalled) {
    $ver = Get-PythonVersion
    Write-Status "OK" "Python $($ver.Major).$($ver.Minor) found"
} else {
    Install-Python
    if (-not (Test-PythonInstalled)) {
        Write-Status "ERROR" "Python installation failed. Please install Python $PYTHON_MIN_MAJOR.$PYTHON_MIN_MINOR+ manually."
        exit 1
    }
}

# Step 2: AutoHotkey v2
if (Test-AHKInstalled) {
    Write-Status "OK" "AutoHotkey v2 found"
} else {
    Install-AHK
}

# Step 3: pip dependencies
$reqFile = Join-Path $projectDir "requirements.txt"
Install-PipDeps -ReqFile $reqFile

# Step 4: Config
Copy-DefaultConfig -ProjectDir $projectDir

# Step 5: Startup option
Write-Host ""
$startup = Read-Host "  Start TCP on login? [y/N]"
if ($startup -match "^[Yy]") {
    $ahkScript = Join-Path $projectDir "src\platforms\windows\tcp.ahk"
    Set-StartupShortcut -AhkScript $ahkScript
} else {
    Write-Status "SKIP" "Startup shortcut not created"
}

# Step 6: Launch TCP
Write-Host ""
$ahkScript = Join-Path $projectDir "src\platforms\windows\tcp.ahk"
if (Test-Path $ahkScript) {
    Write-Status "INFO" "Launching TCP..."
    Start-Process $ahkScript
    Write-Status "OK" "TCP is running! Check your system tray."
} else {
    Write-Status "SKIP" "AHK script not found, skipping launch"
}

# Summary
Write-Host ""
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "  TCP project: $projectDir" -ForegroundColor White
Write-Host ""

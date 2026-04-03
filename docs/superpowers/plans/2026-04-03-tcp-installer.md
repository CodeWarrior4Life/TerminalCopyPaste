# TCP Installation Wrapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build cross-platform installation scripts that detect and silently install all TCP dependencies in a single command.

**Architecture:** Three CLI scripts (install.bat, install.ps1, install.sh) handle the per-OS install logic with remote/local mode detection. An Inno Setup .iss script provides a Windows GUI installer. All scripts are idempotent and print status lines for each step.

**Tech Stack:** PowerShell 5.1+, Bash 4+, Inno Setup 6

---

## Task 1: Windows CLI Launcher

**Files:**
- Create: `install.bat`

- [ ] **Step 1: Write install.bat**

Write `install.bat`:

```batch
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
```

- [ ] **Step 2: Commit**

```bash
git add install.bat
git commit -m "feat: Windows CLI installer launcher (install.bat)"
```

---

## Task 2: Windows CLI Installer (PowerShell)

**Files:**
- Create: `install.ps1`

- [ ] **Step 1: Write install.ps1**

Write `install.ps1`:

```powershell
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
    # Check registry
    $regPath = "HKLM:\SOFTWARE\AutoHotkey"
    if (Test-Path $regPath) { return $true }
    # Check PATH
    try {
        $result = Get-Command "AutoHotkey64.exe" -ErrorAction SilentlyContinue
        if ($result) { return $true }
        $result = Get-Command "AutoHotkey32.exe" -ErrorAction SilentlyContinue
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
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
    $reqFile = Join-Path $scriptDir "requirements.txt"

    if (Test-Path $reqFile) {
        return $scriptDir
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
```

- [ ] **Step 2: Test locally (manual)**

Run from the repo directory:
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

Expected: Python and AHK detected as already installed (`[OK]`), pip deps installed, config copied if missing, startup prompt shown.

- [ ] **Step 3: Commit**

```bash
git add install.ps1
git commit -m "feat: Windows PowerShell installer with auto-detection and silent install"
```

---

## Task 3: macOS/Linux Installer (Bash)

**Files:**
- Create: `install.sh`

- [ ] **Step 1: Write install.sh**

Write `install.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# --- Constants ---
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=12
REPO_URL="https://github.com/CodeWarrior4Life/TerminalCopyPaste.git"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Helper Functions ---

status_ok()      { echo -e "  ${GREEN}[OK]${NC} $1"; }
status_install() { echo -e "  ${YELLOW}[INSTALL]${NC} $1"; }
status_skip()    { echo -e "  ${CYAN}[SKIP]${NC} $1"; }
status_error()   { echo -e "  ${RED}[ERROR]${NC} $1"; }
status_info()    { echo -e "  [INFO] $1"; }

get_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        *)       echo "unknown" ;;
    esac
}

get_linux_pkg_manager() {
    if command -v apt-get &>/dev/null; then
        echo "apt"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    else
        echo "unknown"
    fi
}

pkg_install() {
    local pkg="$1"
    local os
    os=$(get_os)

    if [ "$os" = "macos" ]; then
        brew install "$pkg"
    elif [ "$os" = "linux" ]; then
        local mgr
        mgr=$(get_linux_pkg_manager)
        case "$mgr" in
            apt)    sudo apt-get install -y -qq "$pkg" ;;
            dnf)    sudo dnf install -y -q "$pkg" ;;
            pacman) sudo pacman -S --noconfirm --quiet "$pkg" ;;
            *)
                status_error "No supported package manager found. Install '$pkg' manually."
                exit 1
                ;;
        esac
    fi
}

check_python_version() {
    local cmd="${1:-python3}"
    if ! command -v "$cmd" &>/dev/null; then
        return 1
    fi
    local version
    version=$("$cmd" --version 2>&1 | sed -n 's/.*Python \([0-9]*\.[0-9]*\).*/\1/p')
    local major minor
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -gt "$PYTHON_MIN_MAJOR" ] 2>/dev/null; then
        return 0
    fi
    if [ "$major" -eq "$PYTHON_MIN_MAJOR" ] && [ "$minor" -ge "$PYTHON_MIN_MINOR" ] 2>/dev/null; then
        return 0
    fi
    return 1
}

get_project_dir() {
    # Check if we're in the repo
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -f "$script_dir/requirements.txt" ]; then
        echo "$script_dir"
        return
    fi

    # Remote mode: clone the repo
    local os
    os=$(get_os)
    local install_dir

    case "$os" in
        macos) install_dir="$HOME/Library/Application Support/tcp" ;;
        linux) install_dir="$HOME/.local/share/tcp" ;;
        *)     install_dir="$HOME/.tcp" ;;
    esac

    if [ -f "$install_dir/requirements.txt" ]; then
        status_info "Existing installation found, updating..."
        cd "$install_dir" && git pull --quiet 2>/dev/null
        echo "$install_dir"
        return
    fi

    status_info "Remote mode detected. Cloning TCP repository..."
    if ! command -v git &>/dev/null; then
        status_error "Git is required for remote installation. Install git and try again."
        exit 1
    fi

    git clone --quiet "$REPO_URL" "$install_dir"
    status_ok "Repository cloned to $install_dir"
    echo "$install_dir"
}

# --- macOS-specific ---

install_homebrew() {
    if command -v brew &>/dev/null; then
        status_ok "Homebrew found"
        return
    fi
    status_install "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add brew to PATH for this session
    if [ -f /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -f /usr/local/bin/brew ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    status_ok "Homebrew installed"
}

install_python_macos() {
    if check_python_version python3; then
        local ver
        ver=$(python3 --version 2>&1 | sed -n 's/.*Python \([0-9]*\.[0-9]*\).*/\1/p')
        status_ok "Python $ver found"
        return
    fi
    status_install "Installing Python via Homebrew..."
    brew install python@3.13
    status_ok "Python installed"
}

setup_startup_macos() {
    local project_dir="$1"
    local plist_dir="$HOME/Library/LaunchAgents"
    local plist_file="$plist_dir/com.crossroadtech.tcp.plist"

    if [ -f "$plist_file" ]; then
        status_skip "Launch Agent already exists"
        return
    fi

    mkdir -p "$plist_dir"
    cat > "$plist_file" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.crossroadtech.tcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>-m</string>
        <string>src.tcp_core</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$project_dir</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
PLIST
    status_ok "Launch Agent created"
}

# --- Linux-specific ---

install_python_linux() {
    if check_python_version python3; then
        local ver
        ver=$(python3 --version 2>&1 | sed -n 's/.*Python \([0-9]*\.[0-9]*\).*/\1/p')
        status_ok "Python $ver found"
        return
    fi
    status_install "Installing Python..."
    pkg_install python3
    status_ok "Python installed"
}

install_xclip() {
    if command -v xclip &>/dev/null; then
        status_ok "xclip found"
        return
    fi
    status_install "Installing xclip..."
    pkg_install xclip
    status_ok "xclip installed"
}

setup_startup_linux() {
    local project_dir="$1"
    local autostart_dir="$HOME/.config/autostart"
    local desktop_file="$autostart_dir/tcp.desktop"

    if [ -f "$desktop_file" ]; then
        status_skip "Autostart entry already exists"
        return
    fi

    mkdir -p "$autostart_dir"
    cat > "$desktop_file" << DESKTOP
[Desktop Entry]
Type=Application
Name=TCP - Terminal Copy Paste
Comment=Clipboard image path paster for terminals
Exec=python3 -m src.tcp_core
Path=$project_dir
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
DESKTOP
    status_ok "Autostart entry created"
}

# --- Shared ---

install_pip_deps() {
    local req_file="$1"
    status_install "Installing Python dependencies..."
    python3 -m pip install --quiet --upgrade pip 2>/dev/null || true
    python3 -m pip install --quiet -r "$req_file"
    status_ok "Python dependencies installed"
}

copy_default_config() {
    local project_dir="$1"
    local config_dir="$HOME/.config/tcp"
    local config_file="$config_dir/config.toml"
    local example_file="$project_dir/config/config.example.toml"

    if [ -f "$config_file" ]; then
        status_skip "Config already exists at $config_file"
        return
    fi

    if [ ! -f "$example_file" ]; then
        status_skip "No example config found, skipping"
        return
    fi

    mkdir -p "$config_dir"
    cp "$example_file" "$config_file"
    status_ok "Config created at $config_file"
}

# --- Main ---

echo ""
echo -e "  ${CYAN}TCP - Terminal Copy Paste Installer${NC}"
echo -e "  ${CYAN}====================================${NC}"
echo ""

OS=$(get_os)

if [ "$OS" = "unknown" ]; then
    status_error "Unsupported operating system: $(uname -s)"
    exit 1
fi

# Step 0: Determine project directory
PROJECT_DIR=$(get_project_dir)

# OS-specific dependency installation
if [ "$OS" = "macos" ]; then
    # macOS: Homebrew + Python
    install_homebrew
    install_python_macos
elif [ "$OS" = "linux" ]; then
    # Linux: Python + xclip
    install_python_linux
    install_xclip
fi

# Step 3: pip dependencies
install_pip_deps "$PROJECT_DIR/requirements.txt"

# Step 4: Config
copy_default_config "$PROJECT_DIR"

# Step 5: Startup option
echo ""
read -rp "  Start TCP on login? [y/N] " startup_choice
if [[ "$startup_choice" =~ ^[Yy] ]]; then
    if [ "$OS" = "macos" ]; then
        setup_startup_macos "$PROJECT_DIR"
    elif [ "$OS" = "linux" ]; then
        setup_startup_linux "$PROJECT_DIR"
    fi
else
    status_skip "Startup not configured"
fi

# Summary
echo ""
echo -e "  ${GREEN}Installation complete!${NC}"
echo "  TCP project: $PROJECT_DIR"
if [ "$OS" = "macos" ]; then
    echo "  Run TCP:  cd $PROJECT_DIR && python3 -m src.tcp_core"
    echo "  Note: macOS hotkey shim not yet available. Use python3 -m src.tcp_core directly."
elif [ "$OS" = "linux" ]; then
    echo "  Run TCP:  cd $PROJECT_DIR && python3 -m src.tcp_core"
    echo "  Note: Linux hotkey shim not yet available. Use python3 -m src.tcp_core directly."
fi
echo ""
```

- [ ] **Step 2: Make executable**

```bash
chmod +x install.sh
```

- [ ] **Step 3: Commit**

```bash
git add install.sh
git commit -m "feat: macOS/Linux Bash installer with distro detection and auto-install"
```

---

## Task 4: Inno Setup Script (Windows GUI)

**Files:**
- Create: `installer/tcp.iss`

- [ ] **Step 1: Create installer directory**

```bash
mkdir -p installer
```

- [ ] **Step 2: Write tcp.iss**

Write `installer/tcp.iss`:

```iss
; TCP - Terminal Copy Paste
; Inno Setup Script
; Requires Inno Setup 6+

#define MyAppName "Terminal Copy Paste"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Crossroads Technologies, LLC"
#define MyAppURL "https://github.com/CodeWarrior4Life/TerminalCopyPaste"
#define MyAppExeName "tcp.ahk"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={localappdata}\tcp
DefaultGroupName={#MyAppName}
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=TCPSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=compiler:SetupClassicIcon.ico
UninstallDisplayIcon={app}\src\platforms\windows\tcp.ahk

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startup"; Description: "Start TCP on login"; Flags: unchecked

[Files]
; Copy entire project
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\src\platforms\windows\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userstartup}\TCP"; Filename: "{app}\src\platforms\windows\{#MyAppExeName}"; Tasks: startup

[Run]
; Install Python if needed (check done in Code section)
Filename: "{tmp}\python-installer.exe"; Parameters: "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1"; StatusMsg: "Installing Python..."; Flags: waituntilterminated; Check: NeedsPython
; Install AHK if needed
Filename: "{tmp}\ahk-installer.exe"; Parameters: "/silent"; StatusMsg: "Installing AutoHotkey v2..."; Flags: waituntilterminated; Check: NeedsAHK
; Install pip dependencies
Filename: "python"; Parameters: "-m pip install --quiet -r ""{app}\requirements.txt"""; StatusMsg: "Installing Python dependencies..."; Flags: runhidden waituntilterminated
; Copy default config if not present
Filename: "{cmd}"; Parameters: "/c if not exist ""{userappdata}\tcp\config.toml"" ( mkdir ""{userappdata}\tcp"" 2>nul & copy ""{app}\config\config.example.toml"" ""{userappdata}\tcp\config.toml"" )"; Flags: runhidden waituntilterminated
; Launch TCP
Filename: "{app}\src\platforms\windows\{#MyAppExeName}"; Description: "Launch TCP now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
var
  PythonNeeded: Boolean;
  AHKNeeded: Boolean;

function NeedsPython: Boolean;
begin
  Result := PythonNeeded;
end;

function NeedsAHK: Boolean;
begin
  Result := AHKNeeded;
end;

function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function IsAHKInstalled: Boolean;
begin
  Result := RegKeyExists(HKLM, 'SOFTWARE\AutoHotkey') or
            RegKeyExists(HKCU, 'SOFTWARE\AutoHotkey');
end;

procedure InitializeWizard;
begin
  PythonNeeded := not IsPythonInstalled;
  AHKNeeded := not IsAHKInstalled;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  DownloadPage: TDownloadWizardPage;
begin
  Result := '';

  if PythonNeeded or AHKNeeded then
  begin
    DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);
    DownloadPage.Clear;

    if PythonNeeded then
      DownloadPage.Add('https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe', 'python-installer.exe', '');

    if AHKNeeded then
      DownloadPage.Add('https://www.autohotkey.com/download/ahk-v2.exe', 'ahk-installer.exe', '');

    DownloadPage.Show;
    try
      try
        DownloadPage.Download;
      except
        Result := GetExceptionMessage;
      end;
    finally
      DownloadPage.Hide;
    end;
  end;
end;
```

- [ ] **Step 3: Commit**

```bash
git add installer/tcp.iss
git commit -m "feat: Inno Setup script for Windows GUI installer"
```

---

## Task 5: README Update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README install section**

Replace the existing `## Install (Windows)` section in `README.md` with the new multi-OS install section. Keep everything else unchanged.

Replace from `## Install (Windows)` up to (but not including) `## Supported Terminals` with:

```markdown
## Install

### Windows (GUI)

Download [TCPSetup.exe](https://github.com/CodeWarrior4Life/TerminalCopyPaste/releases/latest) and run it. Installs everything automatically.

### Windows (CLI)

```powershell
irm https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.ps1 | iex
```

Or clone and run locally:

```powershell
git clone https://github.com/CodeWarrior4Life/TerminalCopyPaste.git
cd TerminalCopyPaste
.\install.bat
```

### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.sh | bash
```

> Note: macOS hotkey shim is not yet available. The Python core installs and is usable as `python3 -m src.tcp_core`.

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/CodeWarrior4Life/TerminalCopyPaste/main/install.sh | bash
```

Supports Debian/Ubuntu (apt), Fedora/RHEL (dnf), and Arch (pacman). Automatically installs Python, xclip, and pip dependencies.

> Note: Linux hotkey shim is not yet available. The Python core installs and is usable as `python3 -m src.tcp_core`.
```

- [ ] **Step 2: Verify README renders correctly**

Review the file to make sure markdown formatting is correct and no stray backticks.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README with per-OS install commands"
```

- [ ] **Step 4: Push**

```bash
git push
```

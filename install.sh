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
    # Note: BASH_SOURCE[0] is empty/unset when run via curl | bash (remote mode)
    local script_dir=""
    if [ -n "${BASH_SOURCE[0]:-}" ] && [ "${BASH_SOURCE[0]}" != "bash" ]; then
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    fi

    if [ -n "$script_dir" ] && [ -f "$script_dir/requirements.txt" ]; then
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
    # python@3.13 is keg-only for unversioned names (`python3`, `pip`).
    # Prepend its libexec/bin so the rest of the installer uses 3.13
    # instead of the system's Python.
    local py_libexec
    py_libexec="$(brew --prefix python@3.13)/libexec/bin"
    if [ -d "$py_libexec" ]; then
        export PATH="$py_libexec:$PATH"
    fi
    status_ok "Python installed"
}

# NOTE: No setup_startup_macos here. tcp_core is a stateless per-keypress
# CLI (see design spec §3.1), not a daemon. A login agent would run it
# once at login and exit immediately. Startup setup will be reintroduced
# alongside the macOS hotkey shim (Hammerspoon, spec §3.2 / §9.2).

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

# NOTE: No setup_startup_linux here. Same reason as macOS above --
# tcp_core is a stateless per-keypress CLI, not a daemon. Startup setup
# will be reintroduced alongside the Linux hotkey shim (sxhkd + xdotool,
# spec §3.2 / §9.3).

# --- Shared ---

install_pip_deps() {
    local req_file="$1"
    status_install "Installing Python dependencies..."
    python3 -m pip install --quiet --upgrade pip 2>/dev/null || true
    # Try normal install first, fall back to --break-system-packages for PEP 668 distros
    python3 -m pip install --quiet -r "$req_file" 2>/dev/null || \
        python3 -m pip install --quiet --break-system-packages -r "$req_file"
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
    install_homebrew
    install_python_macos
elif [ "$OS" = "linux" ]; then
    install_python_linux
    install_xclip
fi

# Step 3: pip dependencies
install_pip_deps "$PROJECT_DIR/requirements.txt"

# Step 4: Config
copy_default_config "$PROJECT_DIR"

# Step 5: Startup option -- deferred on macOS/Linux until hotkey shim lands
status_skip "Login startup not configured -- waiting on macOS/Linux hotkey shim"

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

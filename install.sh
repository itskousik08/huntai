#!/usr/bin/env bash
# HuntAI Installation Script
# Supports Linux & Termux (Android)

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'
BOLD='\033[1m'

banner() {
  echo -e "${GREEN}"
  echo "  ██╗  ██╗██╗   ██╗███╗   ██╗████████╗ █████╗ ██╗"
  echo "  ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔══██╗██║"
  echo "  ███████║██║   ██║██╔██╗ ██║   ██║   ███████║██║"
  echo "  ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══██║██║"
  echo "  ██║  ██║╚██████╔╝██║ ╚████║   ██║   ██║  ██║██║"
  echo "  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝"
  echo -e "${RESET}"
  echo -e "${CYAN}  [ INSTALLER v1.0 ]${RESET}"
  echo ""
}

step() { echo -e "  ${GREEN}→${RESET} $1"; }
ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET} $1"; }
err()  { echo -e "  ${RED}✗${RESET} $1"; }
info() { echo -e "  ${CYAN}·${RESET} $1"; }

banner

echo -e "${BOLD}  Installing HuntAI dependencies...${RESET}"
echo ""

# ── Detect environment ────────────────────────────────
IS_TERMUX=false
if [ -d "/data/data/com.termux" ]; then
  IS_TERMUX=true
  info "Detected: Termux (Android)"
else
  info "Detected: Linux"
fi

# ── Python check ──────────────────────────────────────
step "Checking Python..."
if command -v python3 &>/dev/null; then
  PYVER=$(python3 --version 2>&1)
  ok "Python found: $PYVER"
  PYTHON=python3
elif command -v python &>/dev/null; then
  PYVER=$(python --version 2>&1)
  ok "Python found: $PYVER"
  PYTHON=python
else
  err "Python not found!"
  if $IS_TERMUX; then
    echo "  Run: pkg install python"
  else
    echo "  Install Python 3.8+ from https://python.org"
  fi
  exit 1
fi

# ── pip check ─────────────────────────────────────────
step "Checking pip..."
if $PYTHON -m pip --version &>/dev/null; then
  ok "pip available"
else
  err "pip not found"
  if $IS_TERMUX; then echo "  Run: pkg install python"; fi
  exit 1
fi

# ── Install Python packages ───────────────────────────
step "Installing Python packages..."
echo ""

PACKAGES=(
  "fastapi>=0.100.0"
  "uvicorn[standard]>=0.23.0"
  "httpx>=0.24.0"
  "colorama>=0.4.6"
  "apify-client>=1.5.0"
  "pydantic>=2.0.0"
  "websockets>=11.0"
  "python-multipart"
)

for pkg in "${PACKAGES[@]}"; do
  step "Installing $pkg..."
  $PYTHON -m pip install "$pkg" --quiet --break-system-packages 2>/dev/null || \
  $PYTHON -m pip install "$pkg" --quiet --user 2>/dev/null || \
  warn "Could not install $pkg — please install manually"
done

echo ""
ok "All Python packages installed"

# ── Create config directory ───────────────────────────
step "Creating ~/.huntai directory..."
mkdir -p "$HOME/.huntai"
ok "Config directory ready: ~/.huntai"

# ── Check Ollama ──────────────────────────────────────
echo ""
step "Checking Ollama..."
if command -v ollama &>/dev/null; then
  ok "Ollama is installed"
  # Check if running
  if curl -s http://localhost:11434/api/tags &>/dev/null; then
    ok "Ollama is running"
    # Check for model
    if ollama list 2>/dev/null | grep -q "glm4\|glm-4"; then
      ok "GLM model found"
    else
      warn "GLM model not found. Run: ollama pull glm4:9b"
    fi
  else
    warn "Ollama is not running. Start with: ollama serve"
  fi
else
  warn "Ollama not found"
  echo ""
  echo -e "  ${YELLOW}Install Ollama:${RESET}"
  if $IS_TERMUX; then
    echo "    pkg install ollama"
    echo "    ollama serve &"
    echo "    ollama pull glm4:9b"
  else
    echo "    curl -fsSL https://ollama.ai/install.sh | sh"
    echo "    ollama serve &"
    echo "    ollama pull glm4:9b"
  fi
fi

# ── Make huntai.py executable ─────────────────────────
if [ -f "huntai.py" ]; then
  chmod +x huntai.py
  ok "huntai.py is executable"
fi

# ── Done ──────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}╔═══════════════════════════════════════════╗${RESET}"
echo -e "  ${GREEN}║${RESET}  ✓  HuntAI Installation Complete!        ${GREEN}║${RESET}"
echo -e "  ${GREEN}╚═══════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}Before running HuntAI, make sure:${RESET}"
echo -e "  ${CYAN}1.${RESET} Ollama is running:    ${YELLOW}ollama serve${RESET}"
echo -e "  ${CYAN}2.${RESET} Model is downloaded:  ${YELLOW}ollama pull glm4:9b${RESET}"
echo ""
echo -e "  ${BOLD}Then launch HuntAI:${RESET}"
echo -e "  ${GREEN}  python huntai.py${RESET}"
echo ""

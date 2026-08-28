#!/usr/bin/env bash
#
# Automated Setup Script for Universal Compressor & MeloTTS Voice Server
# Python 3.12.3 Environment Setup
#
# Usage:
#   bash setup_venv.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="python3.12"
if ! command -v "$PYTHON_BIN" &>/dev/null; then
    if command -v python3 &>/dev/null && python3 -c "import sys; exit(0 if sys.version_info[:2] == (3, 12) else 1)" 2>/dev/null; then
        PYTHON_BIN="python3"
    else
        echo "⚠️  python3.12 was not found directly in PATH. Using system default $(which python3 || echo python3)"
        PYTHON_BIN="python3"
    fi
fi

echo "=========================================================="
echo "  Setting up venv with Python: $($PYTHON_BIN --version 2>&1)"
echo "  Target directory: $SCRIPT_DIR/venv"
echo "=========================================================="

# Create venv if not existing
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "==> Creating virtual environment..."
    "$PYTHON_BIN" -m venv "$SCRIPT_DIR/venv"
fi

VENV_PIP="$SCRIPT_DIR/venv/bin/pip"
VENV_PY="$SCRIPT_DIR/venv/bin/python"

# Ensure execution permissions for venv binaries
chmod +x "$SCRIPT_DIR/venv/bin/"* 2>/dev/null || true

echo "==> Upgrading pip and setuptools..."
"$VENV_PIP" install --upgrade pip
"$VENV_PIP" install "setuptools<81"

echo "==> Installing CPU-only PyTorch..."
"$VENV_PIP" install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

echo "==> Installing Compression & Web Server dependencies..."
"$VENV_PIP" install -r "$SCRIPT_DIR/requirements.txt"

echo "==> Installing MeloTTS engine..."
"$VENV_PIP" install git+https://github.com/myshell-ai/MeloTTS.git

echo "==> Cleaning up conflicting unidic dictionary (enforcing unidic-lite)..."
"$VENV_PIP" uninstall -y unidic 2>/dev/null || true

echo "==> Downloading required NLTK tagger resources..."
"$VENV_PY" -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"

echo "=========================================================="
echo "  Verification check"
echo "=========================================================="
"$VENV_PY" -c "
import fastapi, PIL, fitz, soundfile, torch
print('✓ FastAPI:', fastapi.__version__)
print('✓ PIL (Pillow):', PIL.__version__)
print('✓ PyMuPDF (fitz):', fitz.__version__)
print('✓ PyTorch:', torch.__version__)
try:
    from melo.api import TTS
    print('✓ MeloTTS: successfully imported!')
except Exception as e:
    print('⚠️ MeloTTS import check:', e)
"

echo "=========================================================="
echo "✓ Setup complete! You can now start the server with:"
echo "  $SCRIPT_DIR/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8090"
echo "=========================================================="

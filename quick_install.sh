#!/bin/bash
#
# Quick Install Script - One-command setup for Crawl Video Project
#
# Usage:
#   ./quick_install.sh          # Full setup (install + verify)
#   ./quick_install.sh verify   # Verify only (skip installation)
#

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse mode
MODE="${1:-install}"

if [ "$MODE" = "verify" ]; then
    echo "======================================"
    echo "🔍 Verify Setup - Crawl Video Project"
    echo "======================================"
else
    echo "======================================"
    echo "🚀 Quick Install - Crawl Video Project"
    echo "======================================"
fi
echo ""

# Check Python version
echo "📌 Checking Python version..."
python3 --version
echo ""

# If verify mode, skip installation
if [ "$MODE" = "verify" ]; then
    echo "⏭️  Skipping installation (verify mode)"
    echo ""

    # Activate venv if exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Run verification
    echo "🧪 Running setup verification..."
    echo ""
    python3 verify_setup.py
    EXIT_CODE=$?
    echo ""

    if [ $EXIT_CODE -eq 0 ]; then
        echo "======================================"
        echo "✅ Verification Passed!"
        echo "======================================"
    else
        echo "======================================"
        echo "❌ Verification Failed!"
        echo "======================================"
        echo "Run './quick_install.sh' to install/fix dependencies"
    fi
    exit $EXIT_CODE
fi

# Installation mode
echo "📦 Starting installation..."
echo ""

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q
echo "✅ pip upgraded"
echo ""

# Install Python dependencies
echo "📥 Installing Python dependencies..."
echo "   This may take 2-5 minutes..."
pip install -r requirements.txt -q
echo "✅ Python dependencies installed"
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
echo "   This may take 1-2 minutes..."
playwright install chromium
echo "✅ Playwright Chromium installed"
echo ""

# Check ffmpeg (optional)
echo "🔍 Checking for ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg is installed"
    ffmpeg -version | head -1
else
    echo "⚠️  ffmpeg not found (optional, needed for video downloads)"
    echo "   Install with: sudo apt-get install ffmpeg"
fi
echo ""

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env file created (please configure it)"
    else
        echo "⚠️  .env.example not found, skipping"
    fi
else
    echo "✅ .env file already exists"
fi
echo ""

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p data/downloads data/sessions data/cache data/courses/en data/courses/ja logs downloads downloads/en downloads/ja
echo "✅ Directories created"
echo ""

# Run verification
echo "🧪 Running setup verification..."
echo ""
python3 verify_setup.py
EXIT_CODE=$?
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "======================================"
    echo "✅ Installation Complete!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Activate venv: source venv/bin/activate"
    echo "2. Edit .env file with your configuration"
    echo "3. Run the crawler: python3 run_browser.py <mode>"
    echo ""
    echo "Available modes:"
    echo "  - sites      : Parse initial categories/series"
    echo "  - categories : Crawl category details"
    echo "  - series     : Crawl series details"
    echo "  - courses    : Crawl course details and videos"
    echo "  - content    : Extract course content (overview + transcript)"
    echo "  - downloads  : Download videos"
    echo ""
    echo "Example: python3 run_browser.py content en"
    echo ""
else
    echo "======================================"
    echo "❌ Installation failed!"
    echo "======================================"
    echo "Please check the errors above"
    echo ""
fi

exit $EXIT_CODE

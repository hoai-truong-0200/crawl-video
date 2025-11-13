#!/bin/bash
# Quick Installation Script for Crawl Video Project

set -e  # Exit on error

echo "======================================"
echo "🚀 Quick Install - Crawl Video Project"
echo "======================================"
echo ""

PROJECT_DIR="/home/jesterjz/workspace/work/crawl-video"
cd "$PROJECT_DIR"

# Check Python version
echo "📌 Checking Python version..."
python3 --version
echo ""

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
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
    echo "⚠️  ffmpeg not found (optional, needed for Phase 4)"
    echo "   Install with: sudo apt-get install ffmpeg"
fi
echo ""

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created (please configure it)"
else
    echo "✅ .env file already exists"
fi
echo ""

# Run verification
echo "🧪 Running setup verification..."
echo ""
python3 verify_setup.py
echo ""

echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate venv: source venv/bin/activate"
echo "2. Run tests: python3 test_phase1_phase2.py"
echo "3. See RUN_TESTS.md for detailed testing instructions"
echo ""

# 🚀 Setup Guide

Step-by-step guide to set up the Crawl Video project.

## Prerequisites

### Required Software
- **Python 3.10+** (3.11 or 3.12 recommended)
- **Git**
- **ffmpeg** and **ffprobe**

### Check Prerequisites

```bash
# Check Python version
python3 --version  # Should be >= 3.10

# Check Git
git --version

# Check ffmpeg
ffmpeg -version
ffprobe -version
```

## Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd crawl-video
```

## Step 2: Create Virtual Environment

### Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

## Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

This will install:
- Playwright (browser automation)
- yt-dlp (video downloader)
- Google Drive API
- All supporting libraries

## Step 4: Install Playwright Browsers

```bash
# Install Chromium browser for Playwright
playwright install chromium

# Or install all browsers (optional)
# playwright install
```

## Step 5: Install System Dependencies

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### macOS
```bash
brew install ffmpeg
```

### Windows
Download from: https://ffmpeg.org/download.html

Add to PATH after installation.

## Step 6: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

### Minimum Required Settings

```env
# Browser
BROWSER_HEADLESS=false  # Set to true after testing

# Download
DOWNLOAD_PATH=data/downloads

# Google Drive (configure later)
GOOGLE_CREDENTIALS_PATH=config/credentials.json
```

## Step 7: Setup Google Drive API (Optional - for upload)

### 7.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Name it "Crawl Video" or similar

### 7.2 Enable Drive API

1. Navigate to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click "Enable"

### 7.3 Create Credentials

**Option A: Service Account (Recommended)**

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in details and create
4. Click on the created service account
5. Go to "Keys" tab
6. Click "Add Key" > "Create New Key"
7. Choose JSON format
8. Save the downloaded file as `config/credentials.json`

**Option B: OAuth2 (For personal use)**

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client ID"
3. Configure consent screen if needed
4. Choose "Desktop app"
5. Download the JSON file
6. Save as `config/credentials.json`

### 7.4 Configure Drive Folder (Optional)

If you want to upload to a specific folder:

1. Create a folder in Google Drive
2. Get the folder ID from the URL:
   ```
   https://drive.google.com/drive/folders/FOLDER_ID_HERE
   ```
3. Add to `.env`:
   ```env
   GOOGLE_DRIVE_PARENT_FOLDER_ID=FOLDER_ID_HERE
   ```

For Service Account: Share the folder with the service account email.

## Step 8: Verify Installation

Create a test script to verify everything works:

```bash
python -c "
import playwright
import yt_dlp
from google.oauth2 import service_account
from loguru import logger
from pydantic import BaseModel

print('✅ All imports successful!')
print('✅ Setup complete!')
"
```

## Step 9: Test Playwright

```bash
# Test Playwright browser
python -c "
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://www.google.com')
    print('✅ Playwright working!')
    browser.close()
"
```

## Common Issues & Solutions

### Issue: `playwright: command not found`

**Solution**: Make sure virtual environment is activated
```bash
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### Issue: ffmpeg not found

**Solution**:
```bash
# Verify installation
which ffmpeg  # Linux/macOS
where ffmpeg  # Windows

# If not found, install using package manager
```

### Issue: Google API authentication fails

**Solution**:
- Verify `config/credentials.json` exists and is valid
- Check that Drive API is enabled in Google Cloud Console
- For Service Account: Share drive folder with service account email

### Issue: Import errors

**Solution**:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: Playwright browser not launching

**Solution**:
```bash
# Reinstall browsers
playwright install --force chromium
```

## Next Steps

After successful setup:

1. ✅ Review [README.md](../README.md) for usage
2. ✅ Check [TECH_RESEARCH.md](TECH_RESEARCH.md) for architecture
3. ✅ See [TODO.md](../TODO.md) for development status

## Verification Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] All Python packages installed
- [ ] Playwright browsers installed
- [ ] ffmpeg installed and accessible
- [ ] `.env` file configured
- [ ] Google Drive credentials configured (if using upload)
- [ ] Test imports successful
- [ ] Playwright test successful

## Development Mode

For active development:

```bash
# Install additional dev tools (optional)
pip install ipython black flake8 mypy

# Enable auto-reload in Python scripts
export PYTHONDONTWRITEBYTECODE=1
```

## Production Considerations

For production deployment:

1. Set `BROWSER_HEADLESS=true` in `.env`
2. Configure proper logging levels
3. Set up monitoring
4. Configure rate limiting appropriately
5. Use process managers (systemd, supervisor, pm2)

---

**Last Updated**: 2025-11-13

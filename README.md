# 🎥 GLOBIS Video Crawler & Uploader

Automated system to crawl video courses from GLOBIS Unlimited, download videos, and upload to Google Drive.

## 🚀 Features

- ✅ **Advanced Anti-Detection**: Stealth browser automation with human behavior simulation
- ✅ **Smart Crawling**: Extract courses and videos metadata from multiple categories
- ✅ **Video Download**: Automated download using yt-dlp with Vimeo support
- ✅ **Cloud Upload**: Automatic upload to Google Drive with resumable transfers
- ✅ **Session Management**: Resume operations from interruptions
- ✅ **Rate Limiting**: Avoid detection with intelligent request throttling

## 📁 Project Structure

```
crawl-video/
├── src/
│   ├── browser/          # Anti-detection browser setup
│   ├── crawler/          # Course & video metadata crawling
│   ├── downloader/       # Video download with yt-dlp
│   ├── uploader/         # Google Drive integration
│   └── utils/            # Session, logging, helpers
├── config/               # Configuration files
├── data/
│   ├── courses/          # Course metadata JSON files
│   ├── downloads/        # Downloaded videos
│   ├── sessions/         # Session state files
│   └── cache/            # Temporary cache
├── docs/                 # Documentation
├── logs/                 # Application logs
├── tests/                # Unit tests
└── main.py              # Main entry point
```

## 🛠️ Tech Stack

- **Browser Automation**: Playwright + playwright-stealth
- **Video Download**: yt-dlp + ffmpeg
- **Cloud Storage**: Google Drive API v3
- **HTTP Client**: httpx with HTTP/2
- **Logging**: loguru
- **Configuration**: pydantic + python-dotenv

## 📦 Installation

### Prerequisites

- Python 3.10+
- ffmpeg and ffprobe
- Google Cloud account with Drive API enabled

### Setup

1. **Clone repository**:
```bash
git clone <repo-url>
cd crawl-video
```

2. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Install system dependencies**:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

5. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

6. **Setup Google Drive API**:
   - Create a Google Cloud project
   - Enable Google Drive API
   - Create Service Account or OAuth2 credentials
   - Download credentials to `config/credentials.json`

## 🎯 Usage

### Basic Usage

```bash
# Run full workflow: crawl -> download -> upload
python main.py

# Crawl metadata only
python main.py --crawl-only

# Download videos only
python main.py --download-only

# Upload to Drive only
python main.py --upload-only
```

### Advanced Options

```bash
# Resume from last session
python main.py --resume

# Specify custom config
python main.py --config custom_config.json

# Enable debug logging
python main.py --log-level DEBUG

# Process specific category
python main.py --category "Marketing"
```

## ⚙️ Configuration

Edit `.env` file for configuration:

```env
# Browser Settings
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=45000

# Google Drive
GOOGLE_CREDENTIALS_PATH=config/credentials.json

# Download Settings
DOWNLOAD_PATH=data/downloads
VIDEO_QUALITY_PREFERENCE=720p,1080p,480p

# Anti-Detection
STEALTH_MODE=true
BEHAVIOR_SIMULATION=true
MAX_REQUESTS_PER_MINUTE=10
```

See [.env.example](.env.example) for all available options.

## 📖 Documentation

- [Tech Research](docs/TECH_RESEARCH.md) - Technology selection and analysis
- [TODO List](TODO.md) - Development roadmap and progress

## 🔒 Security & Privacy

- Never commit `.env` file or credentials
- Store Google credentials securely in `config/credentials.json`
- Use anti-detection responsibly and ethically
- Respect website terms of service and rate limits

## 🐛 Troubleshooting

### Browser Detection Issues
- Ensure `STEALTH_MODE=true` in `.env`
- Try using headed mode: `BROWSER_HEADLESS=false`
- Clear browser cache in `data/cache/`

### Download Failures
- Check ffmpeg installation: `ffmpeg -version`
- Verify video URL is accessible
- Check logs in `logs/` directory

### Upload Errors
- Verify Google credentials are valid
- Check Drive API is enabled
- Ensure sufficient Drive storage

## 📝 Development

### Project Status

See [TODO.md](TODO.md) for current development status.

**Progress**: 2/25 tasks (8%)

### Running Tests

```bash
pytest tests/
```

## 📄 License

MIT License

## ⚠️ Disclaimer

This tool is for educational purposes only. Ensure you have proper authorization before crawling any website. Respect robots.txt and website terms of service.

---

**Last Updated**: 2025-11-13

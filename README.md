# 🎥 GLOBIS Video Crawler & Uploader

Automated system to crawl video courses from GLOBIS Unlimited, download videos, and upload to Google Drive.

## 🚀 Features

- ✅ **Advanced Anti-Detection**: Stealth browser automation with human behavior simulation
- ✅ **Multi-Language Support**: Crawl English (en) and Japanese (ja) courses
- ✅ **Smart Crawling**: Hierarchical extraction (sites → categories/series → courses → content)
- ✅ **Incremental Saving**: Auto-save after each item to prevent data loss
- ✅ **Auto-Initialization**: JSON files auto-created with correct structure
- ✅ **Show More Handling**: Automatically clicks "Show More" buttons to load all content
- ✅ **Selective Crawling**: `--only-empty` flag to skip completed items
- ✅ **Learning Points**: Extract and organize videos by learning objectives
- ✅ **Content Extraction**: Extract overview, transcript, and AI summary to text files
- ✅ **Video Download**: Automated Vimeo video downloads with progress tracking
- ✅ **Human Behavior Simulation**: Natural delays, mouse movements, and video pause during downloads
- 🚧 **Cloud Upload**: Google Drive integration (planned)

## 📁 Project Structure

```
crawl-video/
├── src/
│   ├── browser/          # Anti-detection browser setup
│   ├── crawler/          # Course & video metadata crawling
│   │   ├── category_parser.py     # Parse category pages
│   │   ├── category_crawler.py    # Crawl all categories
│   │   ├── series_crawler.py      # Crawl all series
│   │   ├── course_crawler.py      # Crawl course details
│   │   ├── course_parser.py       # Parse course pages
│   │   ├── content_extractor.py   # Extract course content
│   │   ├── vimeo_interceptor.py   # Intercept Vimeo download URLs
│   │   └── content_manager.py     # Manage JSON files
│   ├── uploader/         # Google Drive integration (planned)
│   └── utils/            # Helpers and utilities
│       └── file_downloader.py     # Async file downloader
├── data/
│   ├── courses/          # Course metadata JSON files
│   │   ├── sites.json    # Source URLs for categories/series
│   │   ├── en/           # English content
│   │   │   ├── learn-content.json    # Categories and courses
│   │   │   └── explore-content.json  # Series and courses
│   │   └── ja/           # Japanese content
│   │       ├── learn-content.json
│   │       └── explore-content.json
│   └── chrome_profile_copy/  # Chrome profile for auth
├── downloads/            # Downloaded videos and extracted content
│   ├── en/              # English content
│   │   ├── categories/  # From learn-content
│   │   │   └── [category_title]/
│   │   │       └── [course_title]/
│   │   │           ├── overview.txt
│   │   │           ├── transcript.txt
│   │   │           ├── summary.txt (if available)
│   │   │           └── [learning_point_title]/
│   │   │               └── [video_title].mp4
│   │   └── series/      # From explore-content
│   │       └── [series_title]/
│   │           └── [course_title]/
│   │               ├── overview.txt
│   │               ├── transcript.txt
│   │               ├── summary.txt
│   │               └── [learning_point_title]/
│   │                   └── [video_title].mp4
│   └── ja/              # Japanese content (same structure)
├── docs/                 # Documentation
├── logs/                 # Application logs
├── tests/                # Unit tests
└── main.py              # Main entry point
```

## 🛠️ Tech Stack

- **Browser Automation**: Playwright (async) + stealth techniques
- **Parsing**: BeautifulSoup4 for HTML parsing
- **Logging**: loguru for structured logging
- **Data Management**: JSON-based with auto-initialization
- **Video Download**: Vimeo network interception + aiohttp async downloads
- **Cloud Storage**: Google Drive API v3 (planned)

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

### Crawling Workflow

The crawler follows a hierarchical structure:

```
1. sites     → Parse initial categories/series from sites.json
2. categories → Crawl category details (course lists)
3. series    → Crawl series details (course lists)
4. courses   → Extract course details (duration, learning_points, videos)
5. content   → Extract course content (overview, transcript, summary) to txt files
6. downloads → Download videos (Vimeo) to local storage
```

### Basic Commands

```bash
# Run full workflow: crawl -> download -> upload
python main.py

# Crawl metadata only
python main.py --crawl-only

# Download videos only
python main.py --download-only

# Crawl course details (duration + learning_points + videos)
python3 run_browser.py courses          # All courses
python3 run_browser.py courses en       # English only

# Extract course content (overview, transcript, summary)
python3 run_browser.py content          # All courses
python3 run_browser.py content en       # English only
python3 run_browser.py content ja       # Japanese only

# Download videos
python3 run_browser.py downloads        # All videos
python3 run_browser.py downloads en     # English only
python3 run_browser.py downloads ja     # Japanese only

# Run full workflow
python3 run_browser.py all              # sites → categories → series → courses → content
```

### Advanced Options

```bash
# Resume from last session
python main.py --resume

# Specify custom config
python main.py --config custom_config.json

# Enable debug logging
python main.py --log-level DEBUG

# Only extract Japanese content missing files
python3 run_browser.py content ja --only-empty

# Only download videos not yet downloaded (is_downloaded == false)
python3 run_browser.py downloads --only-empty

# Only download missing English videos
python3 run_browser.py downloads en --only-empty
```

### Examples

```bash
# Initial setup: Parse all categories and series
python3 run_browser.py sites

# Get course lists for English categories
python3 run_browser.py categories en

# Extract course details for all languages
python3 run_browser.py courses

# Extract course content (overview/transcript/summary)
python3 run_browser.py content

# Resume interrupted content extraction (skip existing)
python3 run_browser.py content --only-empty

# Download all videos
python3 run_browser.py downloads

# Resume interrupted downloads (skip already downloaded)
python3 run_browser.py downloads --only-empty
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

### Download Issues
- **No download URL found**: Vimeo interceptor may not have captured the URL
  - Increase wait time after page load (currently 4-6 seconds)
  - Check if video player loaded properly
- **Download timeout**: Large video files may exceed timeout (default: 300s)
  - Modify timeout parameter in FileDownloader if needed
- **Video already downloaded**: Check `is_downloaded` flag in JSON or file existence
  - Use `--only-empty` to skip already downloaded videos
- **Progress not showing**: Progress logs appear at INFO level every 10%

### Data Issues
- **JSON parse errors**: Files are auto-initialized if corrupt
- **Missing data**: Use `--only-empty` to re-crawl incomplete items
- **Duplicate entries**: Each item has unique URL as identifier
- **Invalid filenames**: Special characters in titles are sanitized to underscores

## 📝 Development

### Project Status

**Current Phase**: Video download complete ✅
- ✅ Sites parsing with Show More handling
- ✅ Categories and series crawling
- ✅ Course details extraction (duration + learning_points)
- ✅ Multi-language support (EN/JA)
- ✅ Incremental saving and auto-initialization
- ✅ Selective crawling with `--only-empty`
- ✅ Content extraction (overview, transcript, summary) to text files
- ✅ Video download with Vimeo network interception
- ✅ Human behavior simulation (delays, mouse movements, video pause)
- ✅ Download progress tracking with percentage display
- 🚧 Google Drive upload

### Running Tests

```bash
pytest tests/
```

## 📄 License

MIT License

## ⚠️ Disclaimer

This tool is for educational purposes only. Ensure you have proper authorization before crawling any website. Respect robots.txt and website terms of service.

---

**Last Updated**: 2025-12-12

## 📋 Recent Updates

### Version 1.0 - Video Download Feature (2025-12-12)

**New Features:**
- ✅ **Video Download Command**: New `downloads` option to download Vimeo videos
  - Navigate to each video step URL
  - Intercept Vimeo progressive download URLs (best quality: 1080p → 720p → 540p → 360p)
  - Download videos with async HTTP requests
  - Save to: `downloads/[lang]/[categories|series]/[category]/[course]/[learning_point]/[video].mp4`

- ✅ **Download Tracking**: `is_downloaded` flag in JSON data
  - Automatically set to `true` after successful download
  - Skip already downloaded videos with `--only-empty` flag
  - Check file existence to prevent re-downloads

- ✅ **Progress Display**: Real-time download progress
  - Show percentage at INFO level every 10%
  - Format: `📥 Progress: 50.3% (5,234,567/10,469,134 bytes)`
  - Final confirmation with file size

- ✅ **Human Behavior Simulation**: Anti-detection enhancements
  - Random page load delays (2.5-4.0 seconds)
  - Random mouse movements after page load
  - Random network wait times (4.0-6.0 seconds)
  - Pause Vimeo video before download starts (Vimeo Player API)
  - Random delay after pausing (0.5-1.5 seconds)
  - Random delays between videos (3.0-6.0 seconds)

- ✅ **Robust Downloads**: Retry logic and error handling
  - 3 retry attempts with exponential backoff
  - Timeout: 300 seconds (5 minutes) per video
  - Graceful error handling with statistics tracking
  - Incremental JSON saves after each successful download

**Technical Implementation:**
- `VimeoInterceptor`: Network response monitoring for progressive URLs
- `FileDownloader`: Async file downloads with aiohttp
- Video pause via Vimeo Player postMessage API
- Organized folder structure by learning points

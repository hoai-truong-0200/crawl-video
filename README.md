# 🎥 GLOBIS Video Crawler

Automated system to crawl video courses from GLOBIS Unlimited with advanced anti-detection, multi-language support, and comprehensive content extraction.

**Version**: 2.0 | **Last Updated**: 2025-12-22

---

## 🚀 Features

- ✅ **Advanced Anti-Detection**: Stealth browser automation with human behavior simulation
- ✅ **Multi-Language Support**: Crawl English (en) and Japanese (ja) courses
- ✅ **Smart Crawling**: Hierarchical extraction (sites → categories/series → courses → videos → content + downloads)
- ✅ **Intelligent Skip Logic**: Time-based + data-based skipping to avoid re-crawling
- ✅ **Incremental Saving**: Auto-save after each item to prevent data loss
- ✅ **Learning Points Extraction**: Organize videos by learning objectives
- ✅ **Content Extraction**: Extract overview & transcript to separate .txt files
- ✅ **Video Download**: Automated Vimeo downloads with real-time progress tracking
- ✅ **Resume Support**: Safe interruption with Ctrl+C, resume anytime

---

## 📁 Project Structure

```
crawl-video/
├── src/
│   ├── browser/              # Anti-detection browser setup
│   │   └── stealth_config.py
│   ├── crawler/              # Crawling & parsing modules
│   │   ├── category_parser.py     # Parse category pages
│   │   ├── category_crawler.py    # Crawl all categories
│   │   ├── series_crawler.py      # Crawl all series
│   │   ├── course_crawler.py      # Extract course details
│   │   ├── course_parser.py       # Parse course pages
│   │   ├── video_crawler.py       # Extract video content ⭐NEW
│   │   └── content_manager.py     # JSON data management
│   ├── downloader/           # Video download modules
│   │   ├── vimeo_extractor.py     # Extract Vimeo URLs
│   │   └── video_downloader.py    # Download videos
│   └── utils/                # Utilities
│       └── sites_manager.py        # Manage sites.json
├── data/
│   ├── courses/              # Course metadata
│   │   ├── sites.json        # Source URLs
│   │   ├── en/               # English content
│   │   │   ├── learn-content.json    # Categories
│   │   │   └── explore-content.json  # Series
│   │   └── ja/               # Japanese content
│   └── chrome_profile_copy/  # Chrome profile for auth
├── downloads/                # Downloaded content
│   ├── en/
│   │   ├── categories/
│   │   │   └── [Category]/
│   │   │       └── [Course]/
│   │   │           ├── overview.txt
│   │   │           ├── transcript.txt
│   │   │           └── [Learning Point]/
│   │   │               └── [Video].mp4
│   │   └── series/
│   └── ja/
├── docs/                     # Documentation
│   ├── SUMMARY.md            # Comprehensive system summary ⭐NEW
│   ├── SITES_OPTION.md
│   └── TECH_RESEARCH.md
└── run_browser.py            # Main entry point
```

---

## 🛠️ Tech Stack

- **Browser Automation**: Playwright (async) + stealth techniques
- **Parsing**: BeautifulSoup4
- **Logging**: loguru
- **Video Download**: yt-dlp + ffmpeg
- **Data**: JSON with auto-initialization

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- Google Chrome
- ffmpeg (for video processing)

### Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd crawl-video

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt
playwright install chromium

# 4. Install ffmpeg (system dependency)
# Ubuntu/Debian:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html

# 5. Create data directories
mkdir -p data/courses/{en,ja}
```

---

## 🎯 Usage

### Quick Start

```bash
# 1. Parse initial site structure
python3 run_browser.py sites

# 2. Crawl categories and series
python3 run_browser.py categories
python3 run_browser.py series

# 3. Extract course details
python3 run_browser.py courses

# 4. Extract video content (overview + transcript)
python3 run_browser.py content

# 5. Download videos
python3 run_browser.py downloads

# OR run everything at once:
python3 run_browser.py all
```

### Available Options

| Option | Description | Output |
|--------|-------------|--------|
| `sites` | Parse categories/series lists | `learn-content.json`, `explore-content.json` |
| `categories` | Crawl category details + course lists | Updated `learn-content.json` |
| `series` | Crawl series details + course lists | Updated `explore-content.json` |
| `courses` | Extract learning points + videos | Updated JSON with `learning_points` |
| `content` | Extract overview/transcript to .txt | `downloads/.../overview.txt`, `transcript.txt` |
| `downloads` | Download video files | `downloads/.../*.mp4` |
| `all` | Run full workflow | All of the above |

### Language Selection

```bash
# Crawl specific language
python3 run_browser.py courses en    # English only
python3 run_browser.py content ja    # Japanese only

# Crawl all languages (default)
python3 run_browser.py courses       # Both en and ja
```

### Skip Logic

All options automatically skip recently-updated items to save time:

**Categories/Series**: Skip if updated < 14 days **AND** has courses
```bash
# Will skip categories crawled in last 2 weeks that have course data
python3 run_browser.py categories
```

**Courses**: Skip if updated < 14 days **AND** has learning_points
```bash
# Will skip courses crawled in last 2 weeks that have learning points
python3 run_browser.py courses
```

**Content**: Skip if `is_content == true`
```bash
# Will skip videos that already have overview/transcript extracted
python3 run_browser.py content
```

**Downloads**: Skip if `is_downloaded == true`
```bash
# Will skip videos already downloaded
python3 run_browser.py downloads
```

---

## 📊 Workflow Diagram

```
┌──────────┐
│  sites   │  Parse category/series URLs from sites.json
└────┬─────┘
     │
     ├─────────────┬─────────────┐
     │             │             │
┌────▼─────┐  ┌───▼───────┐    ...
│categories│  │  series   │
└────┬─────┘  └───┬───────┘
     │            │
     └────────┬───┘
              │
         ┌────▼────┐
         │ courses │  Extract learning_points + videos
         └────┬────┘
              │
         ┌────▼────┐
         │ content │  Extract overview + transcript → .txt
         └────┬────┘
              │
         ┌────▼─────┐
         │downloads │  Download video files → .mp4
         └──────────┘
```

---

## 📖 Data Structure

### JSON Structure (learn-content.json / explore-content.json)

```json
{
  "language": "en",
  "last_updated": "2025-12-22T10:00:00",
  "categories": [
    {
      "title": "Critical Thinking",
      "url": "/en/categories/123",
      "last_updated": "2025-12-22T10:00:00",
      "courses": [
        {
          "title": "Adaptive Thinking",
          "url": "/en/courses/456",
          "duration": 50,
          "last_updated": "2025-12-22T11:00:00",
          "learning_points": [
            {
              "title": "Introduction",
              "videos": [
                {
                  "title": "What Is Adaptive Thinking",
                  "url": "/en/courses/456/steps/789",
                  "step_id": "789",
                  "duration": "5:23",
                  "learning_point": "Introduction",
                  "last_updated": "2025-12-22T11:00:00",
                  "is_downloaded": false,
                  "is_content": false
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### File Output Structure

```
downloads/
├── en/
│   ├── categories/
│   │   └── Critical Thinking/
│   │       └── Adaptive Thinking/
│   │           ├── overview.txt          # Course overview
│   │           ├── transcript.txt        # Course transcript
│   │           └── Introduction/
│   │               └── What Is Adaptive Thinking.mp4
│   └── series/
│       └── Business Essentials/
│           └── [Course]/
│               ├── overview.txt
│               ├── transcript.txt
│               └── [Learning Point]/
│                   └── [Video].mp4
```

---

## ⚙️ Configuration

### sites.json

Edit `data/courses/sites.json` to configure source URLs:

```json
{
  "en": [
    "https://unlimited.globis.co.jp/en/explore-content",
    "https://unlimited.globis.co.jp/en/learn-content"
  ],
  "ja": [
    "https://unlimited.globis.co.jp/ja/learn-content",
    "https://unlimited.globis.co.jp/ja/explore-content"
  ]
}
```

### settings.py

Key settings in `config/settings.py`:
- Delays: `MIN_DELAY=1.5s`, `MAX_DELAY=3.0s`
- Retries: `MAX_RETRIES=3`
- Browser arguments (anti-detection)

---

## 🐛 Troubleshooting

### Browser Issues
```bash
# Clear Chrome profile and retry
rm -rf data/chrome_profile_copy/
python3 run_browser.py sites
```

### Empty Results
- Check if "Show More" button was clicked
- Verify page HTML structure
- Check logs for error messages

### Skip Logic Issues
```bash
# Force re-crawl by deleting last_updated from JSON
# Or wait 14 days for automatic re-crawl
```

### Download Failures
```bash
# Verify ffmpeg installed
ffmpeg -version

# Check yt-dlp version
yt-dlp --version

# Update yt-dlp
pip install --upgrade yt-dlp
```

---

## 📚 Documentation

- **[SUMMARY.md](docs/SUMMARY.md)** - Comprehensive system documentation (NEW ⭐)
- **[SITES_OPTION.md](docs/SITES_OPTION.md)** - Sites parsing details
- **[TECH_RESEARCH.md](docs/TECH_RESEARCH.md)** - Technology research
- **[TODO.md](TODO.md)** - Development roadmap

---

## 🚧 Project Status

**Current Version**: 2.0 ✅

### Completed Features
- ✅ Sites parsing with Show More handling
- ✅ Categories and series crawling
- ✅ Course details extraction (duration + learning_points)
- ✅ Video content extraction (overview + transcript to .txt)
- ✅ Video downloads with progress tracking
- ✅ Multi-language support (EN/JA)
- ✅ Incremental saving
- ✅ Smart skip logic (time + data based)

### Planned Features
- [ ] Video quality selection (720p, 1080p)
- [ ] Parallel downloads
- [ ] Google Drive integration
- [ ] Web UI for monitoring
- [ ] Docker containerization

---

## 🔒 Security & Privacy

### Anti-Detection
- Playwright stealth mode
- Human behavior simulation
- Random delays (1.5-5.0s)
- Chrome profile persistence

### Data Privacy
- All data stored locally
- No credential storage
- Manual login required (one-time per session)
- Session persists in Chrome profile

### Best Practices
- Respect rate limits (built-in delays)
- One session at a time per language
- Clean shutdown (Ctrl+C safe)

---

## 📄 License

MIT License - See LICENSE file

---

## ⚠️ Disclaimer

**Educational purposes only**. Ensure you have proper authorization before crawling any website. Respect robots.txt and website terms of service.

**Copyright**: Downloaded content may be copyrighted. Use responsibly and in accordance with GLOBIS Unlimited terms of service.

---

**Quick Links**:
- 📖 [Full Documentation](docs/SUMMARY.md)
- 🐛 [Report Issues](https://github.com/your-repo/issues)
- 💬 [Discussions](https://github.com/your-repo/discussions)

**Last Updated**: 2025-12-22 | **Maintainer**: Development Team

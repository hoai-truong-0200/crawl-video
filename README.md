# 🎥 GLOBIS Video Crawler

Automated system to crawl video courses from GLOBIS Unlimited with advanced anti-detection and multi-language support.

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
- 🚧 **Video Download**: Using yt-dlp with Vimeo support (planned)
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
│   │   ├── content_extractor.py   # Extract course content (NEW!)
│   │   └── content_manager.py     # Manage JSON files
│   ├── downloader/       # Video download (planned)
│   ├── uploader/         # Google Drive integration (planned)
│   └── utils/            # Helpers and utilities
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
├── downloads/            # Extracted course content
│   ├── en/              # English content
│   │   ├── categories/  # From learn-content
│   │   │   └── [category_title]/
│   │   │       └── [course_title]/
│   │   │           ├── overview.txt
│   │   │           ├── transcript.txt
│   │   │           └── summary.txt (if available)
│   │   └── series/      # From explore-content
│   │       └── [series_title]/
│   │           └── [course_title]/
│   │               ├── overview.txt
│   │               ├── transcript.txt
│   │               └── summary.txt
│   └── ja/              # Japanese content (same structure)
├── docs/                 # Documentation
├── logs/                 # Application logs
├── tests/                # Unit tests
└── run_browser.py        # Main entry point
```

## 🛠️ Tech Stack

- **Browser Automation**: Playwright (async) + stealth techniques
- **Parsing**: BeautifulSoup4 for HTML parsing
- **Logging**: loguru for structured logging
- **Data Management**: JSON-based with auto-initialization
- **Video Download**: yt-dlp + ffmpeg (planned)
- **Cloud Storage**: Google Drive API v3 (planned)

## 📦 Installation

### Prerequisites

- Python 3.10+
- Google Chrome browser (for authentication)

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

4. **Prepare data directory**:
```bash
mkdir -p data/courses/{en,ja}
```

5. **Configure sites.json** (optional):
   - Edit `data/courses/sites.json` to add/modify source URLs
   - Default configuration provided for GLOBIS Unlimited

## 🎯 Usage

### Crawling Workflow

The crawler follows a hierarchical structure:

```
1. sites     → Parse initial categories/series from sites.json
2. categories → Crawl category details (course lists)
3. series    → Crawl series details (course lists)
4. courses   → Extract course details (duration, learning_points, videos)
5. content   → Extract course content (overview, transcript, summary) to txt files
6. downloads → Download videos [planned]
```

### Basic Commands

```bash
# Parse initial categories and series from sites.json
python3 run_browser.py sites            # All languages
python3 run_browser.py sites en         # English only
python3 run_browser.py sites ja         # Japanese only

# Crawl category details (course lists)
python3 run_browser.py categories       # All categories
python3 run_browser.py categories en    # English only

# Crawl series details (course lists)
python3 run_browser.py series           # All series
python3 run_browser.py series ja        # Japanese only

# Crawl course details (duration + learning_points + videos)
python3 run_browser.py courses          # All courses
python3 run_browser.py courses en       # English only

# Extract course content (overview, transcript, summary)
python3 run_browser.py content          # All courses
python3 run_browser.py content en       # English only
python3 run_browser.py content ja       # Japanese only

# Run full workflow
python3 run_browser.py all              # sites → categories → series → courses → content
```

### Selective Crawling

Use `--only-empty` flag to skip items that already have data:

```bash
# Only crawl categories with empty courses list
python3 run_browser.py categories --only-empty

# Only crawl courses with empty learning_points
python3 run_browser.py courses --only-empty

# Only extract content from courses without existing txt files
python3 run_browser.py content --only-empty

# Only extract Japanese content missing files
python3 run_browser.py content ja --only-empty
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
```

## ⚙️ Configuration

### sites.json Structure

Configure source URLs in `data/courses/sites.json`:

```json
{
  "en": {
    "learn": "xxx",
    "explore": "xxx"
  },
  "ja": {
    "learn": "xxx",
    "explore": "xxx"
  }
}
```

### Data Structure

**learn-content.json** (Categories):
```json
{
  "language": "en",
  "last_updated": "2025-12-10T12:00:00",
  "categories": [
    {
      "title": "Category Name",
      "url": "https://...",
      "last_updated": "...",
      "courses": [
        {
          "title": "Course Title",
          "url": "https://...",
          "duration": 50,
          "learning_points": [...]
        }
      ]
    }
  ]
}
```

**explore-content.json** (Series):
```json
{
  "series": [
    {
      "title": "Series Name",
      "url": "https://...",
      "last_updated": "...",
      "courses": [...]
    }
  ]
}
```

## 📖 Documentation

- [Sites Option](docs/SITES_OPTION.md) - Details on sites parsing
- [Tech Research](docs/TECH_RESEARCH.md) - Technology selection and analysis
- [TODO List](TODO.md) - Development roadmap and progress

## 🔒 Security & Privacy

- Use anti-detection responsibly and ethically
- Respect website terms of service and rate limits
- Chrome profile is copied to `data/chrome_profile_copy/` for session persistence
- Manual login required only once per session

## 🐛 Troubleshooting

### Browser Issues
- If login fails, try running in headed mode (default)
- Clear Chrome profile: `rm -rf data/chrome_profile_copy/`
- Check browser logs in console

### Crawling Issues
- **Empty results**: Check if "Show More" button was clicked properly
- **Duration not found**: Verify course page HTML structure matches selectors
- **Learning points missing**: Ensure "Content" tab is being clicked
- **Content extraction fails**: Check if tabs (Overview/Transcript) exist on page
- **Summary not extracted**: Summary tab is optional and may not exist for all courses
- Check logs for detailed error messages

### Data Issues
- **JSON parse errors**: Files are auto-initialized if corrupt
- **Missing data**: Use `--only-empty` to re-crawl incomplete items
- **Duplicate entries**: Each item has unique URL as identifier
- **Invalid filenames**: Special characters in titles are sanitized to underscores

## 📝 Development

### Project Status

**Current Phase**: Content extraction complete ✅
- ✅ Sites parsing with Show More handling
- ✅ Categories and series crawling
- ✅ Course details extraction (duration + learning_points)
- ✅ Multi-language support (EN/JA)
- ✅ Incremental saving and auto-initialization
- ✅ Selective crawling with `--only-empty`
- ✅ Content extraction (overview, transcript, summary) to text files
- 🚧 Video download with yt-dlp
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

**Last Updated**: 2025-12-11

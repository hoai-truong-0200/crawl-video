# 🚀 GLOBIS Unlimited Crawler - Quick Start

## ✅ Project Status: 100% Complete

All 30 tasks across 5 phases have been implemented and tested.

## 📋 Prerequisites

1. **Python 3.8+** with packages:
   - playwright
   - loguru
   - aiohttp

2. **Chrome Browser** with a logged-in GLOBIS profile

3. **yt-dlp** for video downloading

## 🎯 Quick Start

### 1. First Time Setup

```bash
# Run test mode - this will copy your Chrome profile and check login
python run_browser.py test
```

This will:
- Copy your Chrome profile (one-time operation)
- Open Chrome with anti-detection
- Check if you're logged in
- Test parsing a single category

### 2. Workflow Commands

```bash
# Crawl categories (learn-content)
python run_browser.py categories

# Crawl series (explore-content)  
python run_browser.py series

# Crawl course details (overview, transcript, duration)
python run_browser.py courses

# Crawl video metadata (URLs, learning points)
python run_browser.py videos

# Download all videos
python run_browser.py downloads

# Full workflow (categories → series → courses → videos)
python run_browser.py all
```

## 📁 Directory Structure

```
crawl-video/
├── data/
│   ├── courses/
│   │   ├── en/
│   │   │   ├── learn-content.json    # EN categories & courses
│   │   │   └── explore-content.json  # EN series & courses
│   │   └── ja/
│   │       ├── learn-content.json    # JA categories & courses
│   │       └── explore-content.json  # JA series & courses
│   └── chrome_profile_copy/          # Persistent Chrome session
├── downloads/
│   └── en/                            # Downloaded videos
│       └── {Category}/
│           └── {Course}/
│               └── {LearnPoint}/
│                   └── {Video}.mp4
└── tests/
    ├── test_categories.py
    ├── test_series.py
    ├── test_courses.py
    ├── test_videos.py
    └── test_downloads.py
```

## 🔧 Current Configuration

- **Language**: English (EN) by default
- **Content files**: `data/courses/en/learn-content.json` and `explore-content.json`
- **Download directory**: `downloads/en/`
- **Chrome profile**: Copied from `~/.config/google-chrome/Profile 1`

### Switching to Japanese

To work with Japanese content, update these lines in `run_browser.py`:

```python
# Change from:
LEARN_CONTENT_FILE = Path("data/courses/en/learn-content.json")
EXPLORE_CONTENT_FILE = Path("data/courses/en/explore-content.json")

# To:
LEARN_CONTENT_FILE = Path("data/courses/ja/learn-content.json")
EXPLORE_CONTENT_FILE = Path("data/courses/ja/explore-content.json")
```

## 📊 Current Data

### English Content
- **Categories**: 13 categories in learn-content
- **Location**: `data/courses/en/`
- **Status**: Ready for crawling

### Japanese Content  
- **Location**: `data/courses/ja/`
- **Status**: Empty (needs initial crawl)

## 🎬 Video Download Features

The download implementation includes:

✅ **Smart Skip Logic** - Checks if video already exists before downloading  
✅ **File Verification** - Ensures downloaded files have size > 0  
✅ **Retry Mechanism** - Up to 3 retry attempts for failed downloads  
✅ **Empty File Handling** - Re-downloads if file exists but is empty  
✅ **LearnPoint Structure** - Maintains hierarchical organization  
✅ **Browser Cookie Auth** - Uses Chrome cookies for authenticated access  

## 📝 Typical Workflow

### Option A: Fresh Start (All Content)

```bash
# 1. Test and login
python run_browser.py test

# 2. Run full workflow
python run_browser.py all
```

### Option B: Download Only (After Crawling)

```bash
# If you already have JSON files with video metadata
python run_browser.py downloads
```

### Option C: Incremental Updates

```bash
# Update categories
python run_browser.py categories

# Update course details
python run_browser.py courses

# Update video metadata
python run_browser.py videos

# Download new videos
python run_browser.py downloads
```

## 🧪 Testing

```bash
# Test individual components
python tests/test_categories.py
python tests/test_series.py
python tests/test_courses.py
python tests/test_videos.py
python tests/test_downloads.py
```

## ⚠️ Important Notes

1. **Login Session**: You only need to login once - the session is saved in the Chrome profile copy

2. **Anti-Detection**: The crawler uses advanced anti-detection techniques:
   - Stealth mode enabled
   - Real Chrome browser (not Chromium)
   - Human-like behavior simulation
   - Random delays between requests

3. **Rate Limiting**: The crawler includes delays (2-5 seconds) between requests to avoid rate limiting

4. **Video Downloads**: 
   - Requires `yt-dlp` to be installed
   - Uses Chrome cookies for authentication
   - Downloads in MP4 format with best quality

## 📖 Documentation

- [TODO_FINAL.md](docs/TODO_FINAL.md) - Complete task list (30/30 complete)
- [TODO_NEW_STRUCTURE.md](docs/TODO_NEW_STRUCTURE.md) - Original requirements
- [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) - Detailed setup instructions

## 🎉 Project Complete!

All features have been implemented and tested. The crawler is production-ready!

# 📋 TODO LIST - Crawl Video Project

> **Mục tiêu**: Crawl video courses từ GLOBIS Unlimited, download và upload lên Google Drive tự động

**Tổng tiến độ**: 18/25 tasks (72%)

---

## 🛠️ Tech Stack

### Core Technologies
- **Browser Automation**: Playwright (Python) + playwright-stealth
- **Anti-Detection**: undetected-playwright, faker, numpy
- **Video Download**: yt-dlp, httpx
- **Cloud Storage**: Google Drive API v3
- **Utilities**: pydantic, loguru, tenacity, tqdm

### Architecture
```
src/
├── browser/          # Anti-detection browser setup ✅
├── crawler/          # Course & video metadata crawling ✅
├── downloader/       # Video download với yt-dlp
├── uploader/         # Google Drive integration
└── utils/            # Session, logging, helpers
```

---

## Phase 1: Setup & Foundation (3/3) ✅

- [x] **Task 1**: Nghiên cứu và lựa chọn công nghệ phù hợp ✅
  - Playwright + stealth plugins
  - yt-dlp cho video download
  - Google Drive API v3
  - Xác định libraries cần thiết
  - **Research Document**: [docs/TECH_RESEARCH.md](docs/TECH_RESEARCH.md)

- [x] **Task 2**: Tạo cấu trúc project mới và xóa file cũ ✅
  - Created folders: `src/`, `logs/`, `tests/` with proper structure
  - Removed old JavaScript files: `crawler.js`, `downloader.js`, etc.
  - Created `.env.example` with comprehensive settings
  - Updated `.gitignore` for Python project
  - Created `.gitkeep` files for empty directories
  - Updated README.md with project documentation

- [x] **Task 3**: Setup dependencies và requirements.txt ✅
  - Created comprehensive `requirements.txt` with all dependencies
  - Organized by categories (Browser, Video, Google Drive, Utils)
  - Created [docs/SETUP.md](docs/SETUP.md) with detailed setup guide
  - Created `verify_setup.py` script for installation verification
  - Documented all installation steps and troubleshooting

---

## Phase 2: Anti-Detection & Browser (5/5) ✅

- [x] **Task 4**: Cấu hình browser fingerprinting protection ✅
  - User agent rotation with realistic Chrome UAs
  - Viewport randomization (1920x1080, 1366x768, etc.)
  - Timezone và language settings
  - Canvas/WebGL fingerprint spoofing
  - Consistent fingerprints with seed support
  - File: [src/browser/fingerprint.py](src/browser/fingerprint.py)

- [x] **Task 5**: Implement stealth mode để bypass anti-bot ✅
  - Remove navigator.webdriver property
  - Patch chrome.runtime và automation flags
  - Add realistic plugins and permissions
  - 40+ browser launch arguments for stealth
  - JavaScript injection for all pages
  - File: [src/browser/stealth_config.py](src/browser/stealth_config.py)

- [x] **Task 6**: Xây dựng human behavior simulator ✅
  - Bezier curve mouse movements
  - Natural scrolling with random pauses
  - Realistic hover and click behaviors
  - Form typing with typos and corrections
  - Reading simulation with eye tracking patterns
  - File: [src/browser/human_behavior.py](src/browser/human_behavior.py)

- [x] **Task 7**: Implement random delays giữa actions ✅
  - Configurable timing for 8 action types
  - Thinking time, reading time, navigation delays
  - Random variance and jitter
  - Rate limiting (per minute/hour)
  - Statistics tracking
  - File: [src/browser/timing.py](src/browser/timing.py)

- [x] **Task 8**: Thiết lập browser automation với đăng nhập thủ công ✅
  - Complete BrowserManager class
  - Context manager support (async with)
  - Manual login with headed mode
  - Session save/load functionality
  - Integration of all anti-detection features
  - Example usage with multiple scenarios
  - Files: [src/browser/browser_manager.py](src/browser/browser_manager.py), [src/browser/example_usage.py](src/browser/example_usage.py)

---

## Phase 3: Crawling Categories & Series (6/6) ✅

- [x] **Task 9**: Module quản lý content (categories, courses, videos) ✅
  - ContentManager class với load/save JSON
  - Dataclasses: Category, Course, Video
  - Statistics tracking
  - File: [src/crawler/content_manager.py](src/crawler/content_manager.py)

- [x] **Task 10**: CategoryParser để extract course info từ category pages ✅
  - Parse course cards từ category pages
  - Extract: title, URL, duration, last_updated
  - Filter by duration
  - File: [src/crawler/category_parser.py](src/crawler/category_parser.py)

- [x] **Task 11**: CategoryCrawler để crawl tất cả categories ✅
  - Navigate to each category page
  - Extract courses using CategoryParser
  - Human-like behavior với delays
  - Retry logic và error handling
  - Save to learn-content.json
  - File: [src/crawler/category_crawler.py](src/crawler/category_crawler.py)

- [x] **Task 12**: SeriesCrawler để crawl series pages ✅
  - Crawl từ explore page (series/playlists)
  - Extract courses từ series
  - Similar structure to CategoryCrawler
  - Save to explore-content.json
  - File: [src/crawler/series_crawler.py](src/crawler/series_crawler.py)

- [x] **Task 13**: run_browser.py - Main automation script ✅
  - Integrated workflow script
  - Chrome profile management
  - Manual login detection
  - Multiple modes: test, crawl, series, all
  - Anti-bot protection
  - File: [run_browser.py](run_browser.py)

- [x] **Task 14**: Test và verify category/series crawling ✅
  - Tested CategoryCrawler successfully
  - Tested SeriesCrawler successfully
  - learn-content.json populated with courses
  - explore-content.json populated with series

---

## Phase 4: Crawling Videos (2/2) ✅

- [x] **Task 15**: CourseParser để extract video info từ course pages ✅
  - Parse step list từ course sidebar
  - Extract step info: title, URL, duration, step_id
  - Extract Vimeo URL từ iframe
  - Extract Vimeo video ID
  - File: [src/crawler/course_parser.py](src/crawler/course_parser.py)

- [x] **Task 16**: CourseCrawler để crawl videos từ tất cả courses ✅
  - Load courses từ learn-content.json / explore-content.json
  - Navigate to each course page
  - Extract all steps (video lessons)
  - Navigate to each step to extract Vimeo URL
  - Update JSON with video information (title, url, vimeo_url)
  - Human-like delays and retry logic
  - Statistics tracking
  - Integration vào run_browser.py (mode: videos, all)
  - Files: [src/crawler/course_crawler.py](src/crawler/course_crawler.py), [test_course_parser.py](test_course_parser.py), [test_single_course_crawl.py](test_single_course_crawl.py)

---

## Phase 5: Video Download (2/2) ✅

- [x] **Task 17**: DOM-based video URL extraction ✅
  - Extract URLs from `window.playerConfig` in Vimeo iframe
  - Support progressive MP4, HLS, and DASH formats
  - Automatic quality selection (best available)
  - Parse all available video formats
  - VimeoExtractor class with robust error handling
  - File: [src/downloader/vimeo_extractor.py](src/downloader/vimeo_extractor.py)

- [x] **Task 18**: Video downloader với auto-download (progressive + HLS/DASH) ✅
  - Progressive MP4: Direct download với aiohttp
  - HLS/DASH: yt-dlp automatic download
  - Retry mechanism (3 attempts với exponential backoff)
  - Proper temp file handling (.mp4.part)
  - Quality selection (best quality first)
  - Update JSON với download status
  - Integration với CourseCrawler
  - Files: [src/downloader/video_downloader.py](src/downloader/video_downloader.py), [test_single_video_download.py](test_single_video_download.py)
  - Documentation: [PHASE5_COMPLETE.md](PHASE5_COMPLETE.md)

---

## Phase 6: Google Drive Upload (0/3)

- [ ] **Task 19**: Setup Google Drive API authentication
  - Create Google Cloud project
  - Enable Drive API
  - Setup Service Account hoặc OAuth2
  - Download credentials.json
  - File: `src/uploader/auth.py`

- [ ] **Task 20**: Drive uploader với resumable upload
  - MediaFileUpload với resumable=True
  - Chunk size: 10MB
  - Progress tracking
  - Error handling và retry
  - Update JSON với drive_file_id
  - File: `src/uploader/drive_uploader.py`

- [ ] **Task 21**: Folder organization theo category/course structure
  - Create folders hierarchy
  - Organize: Category > Course > Videos
  - Check existing files (skip duplicates)
  - File: `src/uploader/folder_manager.py`

---

## Phase 7: Production Ready (0/4)

- [ ] **Task 22**: Session & state management
  - Save progress to JSON/SQLite
  - Resume from last checkpoint
  - Track: downloaded videos, uploaded videos, failed items
  - File: `src/utils/session_manager.py`

- [ ] **Task 23**: Enhanced error handling & logging
  - Structured logging với loguru
  - Error recovery strategies
  - Retry với exponential backoff
  - File: `src/utils/error_handler.py`

- [ ] **Task 24**: Main orchestrator script improvements
  - CLI interface với argparse
  - Full workflow: Crawl > Download > Upload
  - Resume capability
  - Progress summary
  - Statistics dashboard
  - File: `main.py`

- [ ] **Task 25**: Testing & Documentation
  - Test end-to-end workflow
  - Optimize concurrent operations
  - Memory usage optimization
  - Complete usage documentation
  - Troubleshooting guide
  - File: `docs/USAGE.md`

---

## 📊 Progress Tracking

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| Phase 1: Setup & Foundation | 3 | 3 | 100% ✅ |
| Phase 2: Anti-Detection & Browser | 5 | 5 | 100% ✅ |
| Phase 3: Crawling Categories & Series | 6 | 6 | 100% ✅ |
| Phase 4: Crawling Videos | 2 | 2 | 100% ✅ |
| Phase 5: Video Download | 2 | 2 | 100% ✅ |
| Phase 6: Google Drive Upload | 3 | 0 | 0% |
| Phase 7: Production Ready | 4 | 0 | 0% |
| **TOTAL** | **25** | **18** | **72%** |

---

## 🎯 Current Status & Next Steps

### ✅ Completed (Phases 1-5)
1. ✅ **Phase 1**: Setup & Foundation - COMPLETED (100%)
2. ✅ **Phase 2**: Anti-Detection & Browser - COMPLETED (100%)
3. ✅ **Phase 3**: Crawling Categories & Series - COMPLETED (100%)
4. ✅ **Phase 4**: Crawling Videos - COMPLETED (100%)
5. ✅ **Phase 5**: Video Download (DOM extraction + Auto-download) - COMPLETED (100%)

### 📹 Available Commands
```bash
# Test single category parsing
python3 run_browser.py test

# Crawl all categories (learn-content.json)
python3 run_browser.py crawl

# Crawl all series (explore-content.json)
python3 run_browser.py series

# Crawl videos from all courses (NEW!)
python3 run_browser.py videos

# Full crawl: categories + series + videos (NEW!)
python3 run_browser.py all

# Test single course video crawl (quick test)
python3 test_single_course_crawl.py

# Test course parser only
python3 test_course_parser.py
```

### 🔄 Phase 6: Google Drive Upload (NEXT)
- Task 19: Google Drive API authentication
- Task 20: Drive uploader with resumable upload
- Task 21: Folder organization by category/course structure

**Ready to proceed with Google Drive integration!**

---

**Last Updated**: 2025-11-18
**Current Phase**: 5 Complete, Moving to Phase 6

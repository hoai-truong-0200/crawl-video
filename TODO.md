# 📋 TODO LIST - Crawl Video Project

> **Mục tiêu**: Crawl video courses từ GLOBIS Unlimited, download và upload lên Google Drive tự động

**Tổng tiến độ**: 8/25 tasks (32%)

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
├── browser/          # Anti-detection browser setup
├── crawler/          # Course & video metadata crawling
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

## Phase 3: Crawling Metadata (0/6)

- [ ] **Task 9**: Module đọc danh sách categories từ learn-content.json
  - Load JSON file
  - Validate structure
  - Parse categories list
  - File: `src/crawler/data_loader.py`

- [ ] **Task 10**: Crawler truy cập từng category URL với human-like behavior
  - Navigate với delays
  - Scroll và hover
  - Wait for dynamic content
  - File: `src/crawler/category_crawler.py`

- [ ] **Task 11**: Parser extract thông tin course
  - Extract: title, URL, last_updated
  - Handle multiple courses per category
  - Validate extracted data
  - File: `src/crawler/course_parser.py`

- [ ] **Task 12**: Crawler truy cập từng course với scrolling/hovering
  - Navigate to course detail page
  - Simulate human reading behavior
  - Extract video list section
  - File: `src/crawler/course_detail_crawler.py`

- [ ] **Task 13**: Parser extract thông tin video
  - Extract: video title, URL
  - Handle video player embeds
  - Parse video metadata
  - File: `src/crawler/video_parser.py`

- [ ] **Task 14**: Lưu dữ liệu vào learn-content.json
  - Update JSON structure
  - Preserve existing data
  - Validate final output
  - File: `src/crawler/data_saver.py`

---

## Phase 4: Video Download (0/2)

- [ ] **Task 15**: Module network interception để bắt video URLs
  - Playwright network monitoring
  - Intercept Vimeo requests
  - Extract m3u8/mpd manifests
  - Parse quality options
  - File: `src/downloader/video_detector.py`

- [ ] **Task 16**: Video downloader với yt-dlp + progress tracking
  - yt-dlp integration
  - Progress bar với tqdm
  - Retry mechanism (3 attempts)
  - Resume incomplete downloads
  - Quality selection (720p > 1080p > 480p)
  - File: `src/downloader/video_downloader.py`

---

## Phase 5: Google Drive Upload (0/3)

- [ ] **Task 17**: Setup Google Drive API authentication
  - Create Google Cloud project
  - Enable Drive API
  - Setup Service Account hoặc OAuth2
  - Download credentials.json
  - File: `src/uploader/auth.py`

- [ ] **Task 18**: Drive uploader với resumable upload
  - MediaFileUpload với resumable=True
  - Chunk size: 10MB
  - Progress tracking
  - Error handling và retry
  - File: `src/uploader/drive_uploader.py`

- [ ] **Task 19**: Folder organization theo category/course structure
  - Create folders hierarchy
  - Organize: Category > Course > Videos
  - Check existing files (skip duplicates)
  - File: `src/uploader/folder_manager.py`

---

## Phase 6: Production Ready (0/6)

- [ ] **Task 20**: Session & state management
  - Save progress to JSON/SQLite
  - Resume from last checkpoint
  - Track: downloaded videos, uploaded videos, failed items
  - File: `src/utils/session_manager.py`

- [ ] **Task 21**: Rate limiting & request throttling
  - Max requests per minute
  - Exponential backoff
  - Respect site's rate limits
  - File: `src/utils/rate_limiter.py`

- [ ] **Task 22**: Error handling & logging
  - Setup loguru logger
  - Log levels: DEBUG, INFO, WARNING, ERROR
  - Rotating file handler
  - Structured logging
  - File: `src/utils/logger.py`

- [ ] **Task 23**: Main orchestrator script
  - CLI interface với argparse
  - Workflow: Crawl > Download > Upload
  - Resume capability
  - Progress summary
  - File: `main.py`

- [ ] **Task 24**: Testing & optimization
  - Test anti-detection effectiveness
  - Test resumable downloads
  - Test Drive upload
  - Optimize concurrent operations
  - Memory usage optimization

- [ ] **Task 25**: Documentation
  - README.md với setup instructions
  - Usage examples
  - Configuration guide
  - Troubleshooting section
  - File: `docs/USAGE.md`

---

## 📊 Progress Tracking

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| Phase 1: Setup & Foundation | 3 | 3 | 100% ✅ |
| Phase 2: Anti-Detection & Browser | 5 | 5 | 100% ✅ |
| Phase 3: Crawling Metadata | 6 | 0 | 0% |
| Phase 4: Video Download | 2 | 0 | 0% |
| Phase 5: Google Drive Upload | 3 | 0 | 0% |
| Phase 6: Production Ready | 6 | 0 | 0% |
| **TOTAL** | **25** | **8** | **32%** |

---

## 🎯 Next Steps

1. ✅ Phase 1: Setup & Foundation - COMPLETED (100%)
2. ✅ Phase 2: Anti-Detection & Browser - COMPLETED (100%)
3. 🔄 Phase 3: Crawling Metadata (NEXT)
   - Task 9: Data loader for categories
   - Task 10: Category crawler
   - Task 11: Course parser
   - Task 12: Course detail crawler
   - Task 13: Video parser
   - Task 14: Data saver

---

**Last Updated**: 2025-11-13

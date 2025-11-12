# 📋 TODO LIST - Crawl Video Project

> **Mục tiêu**: Crawl video courses từ GLOBIS Unlimited, download và upload lên Google Drive tự động

**Tổng tiến độ**: 0/25 tasks (0%)

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

## Phase 1: Setup & Foundation (0/3)

- [ ] **Task 1**: Nghiên cứu và lựa chọn công nghệ phù hợp
  - Playwright + stealth plugins
  - yt-dlp cho video download
  - Google Drive API v3
  - Xác định libraries cần thiết

- [ ] **Task 2**: Tạo cấu trúc project mới và xóa file cũ
  - Tạo folders: `src/`, `config/`, `data/`, `logs/`
  - Xóa các file JavaScript cũ không cần thiết
  - Setup `.gitignore` và `.env.example`

- [ ] **Task 3**: Setup dependencies và requirements.txt
  - Tạo `requirements.txt` với đầy đủ dependencies
  - Setup virtual environment
  - Install Playwright browsers
  - Test basic imports

---

## Phase 2: Anti-Detection & Browser (0/5)

- [ ] **Task 4**: Cấu hình browser fingerprinting protection
  - User agent rotation
  - Viewport randomization
  - Timezone và language settings
  - Canvas/WebGL fingerprint spoofing
  - File: `src/browser/fingerprint.py`

- [ ] **Task 5**: Implement stealth mode để bypass anti-bot
  - Ẩn WebDriver flags
  - Patch navigator.webdriver
  - Remove automation indicators
  - File: `src/browser/stealth_config.py`

- [ ] **Task 6**: Xây dựng human behavior simulator
  - Random mouse movements (bezier curves)
  - Natural scrolling patterns
  - Hover effects
  - File: `src/browser/human_behavior.py`

- [ ] **Task 7**: Implement random delays giữa actions
  - Thinking time (2-5s)
  - Reading time (1-3s)
  - Random jitter
  - File: `src/browser/timing.py`

- [ ] **Task 8**: Thiết lập browser automation với đăng nhập thủ công
  - Playwright context manager
  - Headed mode support
  - Cookie persistence
  - File: `src/browser/browser_manager.py`

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
| Phase 1: Setup & Foundation | 3 | 0 | 0% |
| Phase 2: Anti-Detection & Browser | 5 | 0 | 0% |
| Phase 3: Crawling Metadata | 6 | 0 | 0% |
| Phase 4: Video Download | 2 | 0 | 0% |
| Phase 5: Google Drive Upload | 3 | 0 | 0% |
| Phase 6: Production Ready | 6 | 0 | 0% |
| **TOTAL** | **25** | **0** | **0%** |

---

## 🎯 Next Steps

1. ✅ Review và approve todo list
2. 🔄 Bắt đầu từ Task 1: Research công nghệ
3. 🔄 Implement từng phase tuần tự
4. 🔄 Update progress sau mỗi task hoàn thành

---

**Last Updated**: 2025-11-12

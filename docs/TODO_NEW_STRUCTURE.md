# 📋 TODO LIST - GLOBIS Unlimited Crawler (Restructured)

> **Mục tiêu**: Crawl video courses từ GLOBIS Unlimited (EN + JA), download video tự động và lưu trữ local

**Tổng tiến độ**: 5/30 tasks (17%)

---

## 🛠️ Tech Stack

### Core Technologies
- **Browser Automation**: Playwright (Python) + playwright-stealth
- **Anti-Detection**: Human behavior simulation, faker, numpy
- **Video Download**: yt-dlp, aiohttp
- **Utilities**: pydantic, loguru, asyncio

### Project Structure
```
crawl-video/
├── src/               # Source code
│   ├── browser/       # Anti-detection browser setup
│   ├── crawler/       # Crawling logic
│   ├── downloader/    # Video download
│   └── utils/         # Helpers & utilities
├── data/              # Data storage
│   └── courses/       # Course JSON data
│       ├── en/        # English content
│       │   ├── learn-content.json
│       │   └── explore-content.json
│       └── ja/        # Japanese content
│           ├── learn-content.json
│           └── explore-content.json
├── downloads/         # Downloaded videos
│   ├── en/            # English videos
│   │   ├── {Category}/
│   │   │   └── {Course}/
│   │   │       └── {LearnPoint}/
│   │   │           └── {Video}.mp4
│   │   └── {Series}/
│   │       └── {Course}/
│   │           └── {LearnPoint}/
│   │               └── {Video}.mp4
│   └── ja/            # Japanese videos (same structure)
├── logs/              # Log files (by date)
│   ├── 2025-11-19.log
│   └── 2025-11-20.log
├── tests/             # Test files
│   ├── test_categories.py
│   ├── test_series.py
│   ├── test_courses.py
│   ├── test_videos.py
│   └── test_downloads.py
├── docs/              # Documentation
│   ├── README.md
│   ├── TODO.md
│   ├── SETUP.md
│   └── ...
├── run_browser.py     # Main CLI script
└── requirements.txt   # Dependencies
```

---

## Phase 1: Project Restructure (5/5) ✅

- [x] **Task 1**: Create new folder structure ✅
  - Created `tests/`, `logs/`, `downloads/`, `docs/`
  - Moved test files to `tests/`
  - Moved documentation to `docs/`
  - Clean root directory

- [x] **Task 2**: Setup language support (EN/JA) ✅
  - Read from `sites.json` (en + ja URLs)
  - Create `data/courses/en/` and `data/courses/ja/`
  - Separate JSON files per language

- [x] **Task 3**: Update logging to file (by date) ✅
  - Log to `logs/{YYYY-MM-DD}.log`
  - Console output + file logging
  - Rotation policy (keep last 30 days)

- [x] **Task 4**: Update download directory structure ✅
  - Pattern: `downloads/{lang}/{Category|Series}/{Course}/{LearnPoint}/{Video}.mp4`
  - Auto-create directories
  - Sanitize filenames

- [x] **Task 5**: Remove Google Drive upload code ✅
  - Remove `src/uploader/` module
  - Remove Drive-related fields from JSON
  - Update requirements.txt

---

## Phase 2: Data Models & Schema (0/5)

- [ ] **Task 6**: Update JSON schema with new fields
  - Add `last_updated` to categories, series, courses, videos
  - Add `overview`, `transcript`, `duration` to courses
  - Add `learning_point` to videos
  - Add `language` field (en/ja)
  - File: `src/crawler/content_manager.py`

- [ ] **Task 7**: Create LearnPoint dataclass
  - LearnPoint name extraction
  - Videos grouped by LearnPoint
  - Support nested structure
  - File: `src/crawler/content_manager.py`

- [ ] **Task 8**: Update Course dataclass
  - Add overview field
  - Add transcript field
  - Add duration field (in minutes)
  - Add last_updated field

- [ ] **Task 9**: Add language parameter to all crawlers
  - CategoryCrawler with language
  - SeriesCrawler with language
  - CourseCrawler with language
  - Save to language-specific JSON

- [ ] **Task 10**: Create SitesManager to read sites.json
  - Load EN/JA URLs
  - Get base URL by language
  - Get learn-content/explore-content URLs
  - File: `src/utils/sites_manager.py`

---

## Phase 3: Updated Crawling Options (0/10)

### Option: categories (0/2)

- [ ] **Task 11**: Update CategoryCrawler
  - Crawl all categories from `/learn-content`
  - Extract: title, URL, last_updated
  - Save to `data/courses/{lang}/learn-content.json`
  - Single test: `tests/test_categories.py`

- [ ] **Task 12**: Add last_updated timestamp
  - Extract from page or use current datetime
  - Format: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)

### Option: series (0/2)

- [ ] **Task 13**: Update SeriesCrawler
  - Crawl all series from `/explore-content`
  - Extract: title, URL, last_updated
  - Save to `data/courses/{lang}/explore-content.json`
  - Single test: `tests/test_series.py`

- [ ] **Task 14**: Add last_updated timestamp
  - Same format as categories

### Option: courses (0/3)

- [ ] **Task 15**: Update CourseCrawler - Extract additional fields
  - Extract `overview` (course description)
  - Extract `transcript` (if available)
  - Extract `duration` (total course duration)
  - Extract `last_updated`
  - Single test: `tests/test_courses.py`

- [ ] **Task 16**: Create CourseParser methods
  - `extract_overview()` - from course page
  - `extract_transcript()` - from transcript tab
  - `extract_duration()` - from course metadata
  - File: `src/crawler/course_parser.py`

- [ ] **Task 17**: Update course JSON structure
  - Save new fields to JSON
  - Validate all fields present

### Option: videos (0/3)

- [ ] **Task 18**: Extract LearnPoint structure
  - Find elements with class `*__learningPointName`
  - Group videos by LearnPoint
  - Extract LearnPoint title
  - Create hierarchy: Course > LearnPoint > Videos

- [ ] **Task 19**: Update video extraction
  - Extract video within LearnPoint context
  - Save LearnPoint name to video object
  - Maintain order within LearnPoint
  - **Set `downloaded: false` by default** when creating video object
  - Single test: `tests/test_videos.py`

- [ ] **Task 20**: Update video JSON structure
  - Add `learning_point` field
  - Add `last_updated` field
  - Add `downloaded` status (default: false)
  - Group videos by LearnPoint in JSON

---

## Phase 4: Download Implementation (0/5)

### Option: downloads (0/5)

- [ ] **Task 21**: Update download directory structure
  - Pattern: `downloads/{lang}/{Category|Series}/{Course}/{LearnPoint}/{Video}.mp4`
  - Create nested directories automatically
  - Sanitize all folder/file names

- [ ] **Task 22**: Sequential download with status check
  - **IMPORTANT**: Check `downloaded` status in JSON BEFORE opening video link
  - If `downloaded: true` → **Skip** (don't open link, move to next)
  - If `downloaded: false` → Open link and proceed with download
  - Check if file exists on disk before download
  - Update JSON with `downloaded: true` after successful download
  - Add file size check (>0 bytes)

- [ ] **Task 23**: Download with LearnPoint grouping
  - Download videos grouped by LearnPoint
  - Maintain folder structure
  - Progress tracking per LearnPoint

- [ ] **Task 24**: Add download verification
  - Check file exists after download
  - Verify file size > 0
  - Update JSON `downloaded: true` only if valid
  - Retry failed downloads

- [ ] **Task 25**: Single test for downloads
  - Test download single video
  - Test LearnPoint folder creation
  - Test file verification
  - File: `tests/test_downloads.py`

---

## Phase 5: CLI & Integration (0/5)

- [ ] **Task 26**: Update run_browser.py with new options
  - `--language` or `-l` flag (en/ja/all)
  - `categories` - Crawl categories
  - `series` - Crawl series
  - `courses` - Crawl courses (with overview, transcript, duration)
  - `videos` - Crawl videos (with LearnPoint)
  - `downloads` - Download videos
  - `all` - Run full workflow

- [ ] **Task 27**: Add language selection
  - Default: both EN and JA
  - Option to select single language
  - Process each language separately

- [ ] **Task 28**: Integrate human behavior for all options
  - Apply to categories crawling
  - Apply to series crawling
  - Apply to courses crawling
  - Apply to videos crawling
  - Apply to downloads

- [ ] **Task 29**: Add progress tracking & logging
  - Console progress bars (tqdm)
  - Detailed file logging
  - Summary statistics per option
  - Error logging with traceback

- [ ] **Task 30**: Update all test files
  - Create `tests/test_categories.py`
  - Create `tests/test_series.py`
  - Create `tests/test_courses.py`
  - Create `tests/test_videos.py`
  - Create `tests/test_downloads.py`
  - Test each option independently before integration

---

## 📊 Progress Tracking

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| Phase 1: Project Restructure | 5 | 5 | 100% ✅ |
| Phase 2: Data Models & Schema | 5 | 0 | 0% |
| Phase 3: Updated Crawling Options | 10 | 0 | 0% |
| Phase 4: Download Implementation | 5 | 0 | 0% |
| Phase 5: CLI & Integration | 5 | 0 | 0% |
| **TOTAL** | **30** | **5** | **17%** |

---

## 🎯 Current Status

### ✅ Completed
1. ✅ **Phase 1**: Project Restructure - COMPLETED (100%)
   - Folder structure reorganized
   - Test files moved to `tests/`
   - Documentation moved to `docs/`
   - Language support prepared

### 🔄 Next Steps (Phase 2)

**Priority**: Update data models and schema

1. Update JSON schema with new fields (overview, transcript, duration, learning_point, last_updated)
2. Create LearnPoint dataclass
3. Update Course/Video dataclasses
4. Add language parameter support
5. Create SitesManager utility

---

## 📋 New JSON Schema

### learn-content.json / explore-content.json
```json
{
  "language": "en",
  "last_updated": "2025-11-20T00:00:00Z",
  "categories": [
    {
      "title": "Critical Thinking",
      "url": "/en/categories/critical-thinking",
      "last_updated": "2025-11-20T00:00:00Z",
      "courses": [
        {
          "title": "Business Proposals",
          "url": "/en/courses/abc123/learn/steps",
          "overview": "Learn how to structure proposals...",
          "transcript": "Full transcript here...",
          "duration": 45,
          "last_updated": "2025-11-20T00:00:00Z",
          "learning_points": [
            {
              "title": "Introduction",
              "videos": [
                {
                  "title": "What is a Proposal?",
                  "url": "/en/courses/abc123/learn/steps/60784",
                  "vimeo_url": "https://player.vimeo.com/video/123",
                  "downloaded": true,
                  "download_path": "downloads/en/Critical Thinking/Business Proposals/Introduction/What is a Proposal.mp4",
                  "last_updated": "2025-11-20T00:00:00Z"
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

---

## 🚀 Usage (After Completion)

### Run Options
```bash
# Crawl categories (EN only)
python run_browser.py -l en categories

# Crawl series (JA only)
python run_browser.py -l ja series

# Crawl courses with full details (both languages)
python run_browser.py courses

# Crawl videos with LearnPoint grouping
python run_browser.py -l en videos

# Download all videos
python run_browser.py downloads

# Full workflow (all options, all languages)
python run_browser.py -l all all
```

### Test Individual Options
```bash
# Test categories crawling
python tests/test_categories.py

# Test series crawling
python tests/test_series.py

# Test courses crawling (with new fields)
python tests/test_courses.py

# Test videos crawling (with LearnPoint)
python tests/test_videos.py

# Test download workflow
python tests/test_downloads.py
```

---

**Last Updated**: 2025-11-20
**Current Phase**: 1 Complete, Moving to Phase 2
**Next Task**: Update JSON schema and data models

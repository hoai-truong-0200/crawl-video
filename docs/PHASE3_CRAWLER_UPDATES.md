# Phase 3 - Crawler Updates

## ✅ Completed Updates (In Progress)

### Updated Crawlers

#### 1. CategoryCrawler (Updated)
**File:** `src/crawler/category_crawler.py`

**Changes:**
- ✅ Added `language` parameter (default: "en")
- ✅ Updated ContentManager initialization with language support
- ✅ Updated Course object creation with new fields:
  - `overview` (empty, filled later)
  - `transcript` (empty, filled later)
  - `duration` (0, filled later)
  - `last_updated` (ISO 8601 timestamp)
  - `learning_points` (empty list, filled when crawling videos)
- ✅ Added `last_updated` timestamp to categories
- ✅ Updated default content_file path to `data/courses/en/learn-content.json`

**Usage:**
```python
from pathlib import Path
from src.crawler.category_crawler import CategoryCrawler

# English categories
crawler = CategoryCrawler(
    content_file=Path("data/courses/en/learn-content.json"),
    language="en"
)

# Japanese categories
crawler = CategoryCrawler(
    content_file=Path("data/courses/ja/learn-content.json"),
    language="ja"
)
```

---

#### 2. SeriesCrawler (Updated)
**File:** `src/crawler/series_crawler.py`

**Changes:**
- ✅ Added `language` parameter (default: "en")
- ✅ Added ContentManager for proper data model handling
- ✅ Replaced manual JSON loading/saving with ContentManager
- ✅ Updated Course object creation with new fields:
  - `overview`, `transcript`, `duration`, `last_updated`, `learning_points`
- ✅ Added `last_updated` timestamp to series
- ✅ Updated default content_file path to `data/courses/en/explore-content.json`
- ✅ Now uses `self.content_manager.series` instead of manual dict parsing

**Usage:**
```python
from pathlib import Path
from src.crawler.series_crawler import SeriesCrawler

# English series
crawler = SeriesCrawler(
    content_file=Path("data/courses/en/explore-content.json"),
    language="en"
)

# Japanese series
crawler = SeriesCrawler(
    content_file=Path("data/courses/ja/explore-content.json"),
    language="ja"
)
```

---

#### 3. CourseCrawler (Updated)
**File:** `src/crawler/course_crawler.py`

**Changes:**
- ✅ Added `language` parameter (default: "en")
- ✅ Updated ContentManager initialization with language support
- ✅ Removed Google Drive fields from Video objects:
  - ❌ Removed `uploaded_to_drive`
  - ❌ Removed `drive_file_id`
- ✅ Added new Video fields:
  - `learning_point` (empty for now, will be filled when extracting LearnPoint structure)
  - `downloaded` (default: False)
  - `download_path` (empty string)
  - `last_updated` (ISO 8601 timestamp)
- ✅ Updated video grouping:
  - Videos now grouped in LearnPoint structure
  - Currently using single "Default" LearnPoint (TODO: extract actual structure)
- ✅ Updated download path to include language: `downloads/{lang}/...`
- ✅ Changed `enable_download` default to `False` (downloads done in separate phase)
- ✅ Added `last_updated` timestamp to courses after crawling

**Usage:**
```python
from pathlib import Path
from src.crawler.course_crawler import CourseCrawler

# English courses (no download)
crawler = CourseCrawler(
    content_file=Path("data/courses/en/learn-content.json"),
    language="en",
    enable_download=False
)

# Japanese courses with download enabled
crawler = CourseCrawler(
    content_file=Path("data/courses/ja/learn-content.json"),
    language="ja",
    enable_download=True
)
```

---

## 📋 Data Schema Changes

### Old Video Object
```python
Video(
    title="...",
    url="...",
    vimeo_url="...",
    downloaded=False,
    uploaded_to_drive=False,  # ❌ REMOVED
    drive_file_id=""          # ❌ REMOVED
)
```

### New Video Object
```python
Video(
    title="...",
    url="...",
    vimeo_url="...",
    learning_point="",         # ✅ NEW
    downloaded=False,          # ✅ NEW (explicit default)
    download_path="",          # ✅ NEW
    last_updated="2025-11-20T..." # ✅ NEW
)
```

### Course Object Updates
```python
Course(
    title="...",
    url="...",
    overview="",               # ✅ NEW (TODO: extract from page)
    transcript="",             # ✅ NEW (TODO: extract from page)
    duration=0,                # ✅ NEW (TODO: extract from page)
    last_updated="2025-11-20T...",  # ✅ NEW
    learning_points=[          # ✅ NEW (replaces videos list)
        LearnPoint(
            title="Default",   # TODO: extract actual names
            videos=[...]
        )
    ]
)
```

---

## 🔄 Migration Notes

### Backward Compatibility
- ✅ ContentManager handles old format → new format conversion
- ✅ Old `videos` array automatically converted to single "Default" LearnPoint
- ✅ Missing fields filled with defaults

### Language Support
All crawlers now accept `language` parameter:
- `"en"` → saves to `data/courses/en/`
- `"ja"` → saves to `data/courses/ja/`

### Google Drive Removal
- All references to `uploaded_to_drive` removed
- All references to `drive_file_id` removed
- No need to migrate old data (ContentManager ignores unknown fields)

---

## ✅ COMPLETED - Phase 3 Tasks

### Task 15-17: Extract Course Details (3/3) ✅
- [x] Extract `overview` from course page - Multiple selectors (meta tags, description divs)
- [x] Extract `transcript` from transcript tab/section - Handles click triggers, multiple formats
- [x] Extract `duration` from course metadata - Sum of step durations or direct indicator
- [x] Create CourseParser methods for extraction - All methods implemented

**Implementation:** [src/crawler/course_parser.py](src/crawler/course_parser.py)
- `extract_overview(page)` - Tries multiple selectors (meta, description, about sections)
- `extract_transcript(page)` - Clicks transcript tabs, extracts from various formats
- `extract_duration(page)` - Calculates from step durations or finds duration indicator

### Task 18-20: Extract LearnPoint Structure (3/3) ✅
- [x] Find elements with class `*__learningPointName` - Multiple selector patterns
- [x] Extract LearnPoint titles from DOM - Parent/sibling hierarchy traversal
- [x] Group videos by their LearnPoint - Dict mapping to organize videos
- [x] Update CourseCrawler to use actual LearnPoint structure - Replaced "Default" placeholder
- [x] Set `learning_point` field on Video objects - Set from extracted structure

**Implementation:** [src/crawler/course_parser.py](src/crawler/course_parser.py)
- `extract_learning_points(page)` - Returns `Dict[str, List[StepInfo]]`
- Searches for: `__learningPointName`, `learningPoint`, `sectionTitle`, `chapterTitle`
- Fallback to "Default" group if structure not found

**CourseCrawler Updates:** [src/crawler/course_crawler.py](src/crawler/course_crawler.py)
- Returns `List[LearnPoint]` instead of `List[Video]`
- Organizes videos by LearnPoint during extraction
- Each video has `learning_point` field set correctly

---

## 🧪 Testing

### Test Files to Create
1. **tests/test_categories.py** - Test CategoryCrawler with language support
2. **tests/test_series.py** - Test SeriesCrawler with language support
3. **tests/test_courses.py** - Test CourseCrawler with new schema
4. **tests/test_videos.py** - Test video extraction with LearnPoint structure

### Manual Testing
```bash
# Test categories crawler (EN)
python -c "
from pathlib import Path
from src.crawler.category_crawler import CategoryCrawler
# ... test code
"

# Test series crawler (JA)
python -c "
from pathlib import Path
from src.crawler.series_crawler import SeriesCrawler
# ... test code
"
```

---

## 📊 Progress Summary

### Phase 3 Progress: 10/10 tasks (100%) ✅

| Task | Status | Notes |
|------|--------|-------|
| Task 11: Update CategoryCrawler | ✅ | Language support, last_updated added |
| Task 12: Add last_updated to categories | ✅ | ISO 8601 format |
| Task 13: Update SeriesCrawler | ✅ | ContentManager integration |
| Task 14: Add last_updated to series | ✅ | ISO 8601 format |
| Task 15: Extract course overview | ✅ | Multiple selector strategies |
| Task 16: Extract course transcript | ✅ | Tab clicks & content extraction |
| Task 17: Extract course duration | ✅ | Sum durations or find indicator |
| Task 18: Extract LearnPoint structure | ✅ | DOM traversal with fallback |
| Task 19: Update video extraction | ✅ | New Video fields added |
| Task 20: Update video JSON structure | ✅ | Grouped by LearnPoint |

**Phase 3 Status:** COMPLETE ✅

All tests passed (6/6) in [tests/test_phase3_crawlers.py](tests/test_phase3_crawlers.py)

---

## 🎯 Next Steps - Phase 4

Phase 3 is now complete! Ready to move to Phase 4:

**Phase 4: Download Implementation (0/5 tasks)**

1. **Task 21**: Update download directory structure
   - Pattern: `downloads/{lang}/{Category|Series}/{Course}/{LearnPoint}/{Video}.mp4`
   - Create nested directories automatically
   - Sanitize all folder/file names

2. **Task 22**: Sequential download with status check
   - **IMPORTANT**: Check `downloaded` status in JSON BEFORE opening video link
   - If `downloaded: true` → **Skip** (don't open link, move to next)
   - If `downloaded: false` → Open link and proceed with download
   - Update JSON with `downloaded: true` after successful download

3. **Task 23**: Download with LearnPoint grouping
   - Download videos grouped by LearnPoint
   - Maintain folder structure
   - Progress tracking per LearnPoint

4. **Task 24**: Add download verification
   - Check file exists after download
   - Verify file size > 0
   - Update JSON `downloaded: true` only if valid
   - Retry failed downloads

5. **Task 25**: Single test for downloads
   - Test download single video
   - Test LearnPoint folder creation
   - Test file verification
   - File: `tests/test_downloads.py`

---

**Updated:** 2025-11-21
**Phase:** 3 - Crawler Updates ✅ COMPLETE (100%)
**Next:** Phase 4 - Download Implementation

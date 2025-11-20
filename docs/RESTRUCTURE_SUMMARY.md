# Project Restructure Summary

## ✅ Completed Tasks

### 1. Folder Structure Reorganization
```
✅ tests/          - All test files
✅ logs/           - Date-based log files
✅ downloads/      - Downloaded videos
✅ docs/           - All documentation
✅ data/courses/
   ├── en/         - English content JSONs
   └── ja/         - Japanese content JSONs
```

### 2. Created Documentation
- ✅ [TODO_NEW_STRUCTURE.md](TODO_NEW_STRUCTURE.md) - Complete TODO with 30 tasks across 5 phases
- ✅ [PROJECT_RESTRUCTURE.md](PROJECT_RESTRUCTURE.md) - Detailed restructure explanation
- ✅ [RESTRUCTURE_SUMMARY.md](RESTRUCTURE_SUMMARY.md) - This file

### 3. Created SitesManager Utility
- ✅ File: [../src/utils/sites_manager.py](../src/utils/sites_manager.py)
- ✅ Tested and working
- ✅ Manages EN/JA URLs from sites.json

**Features:**
- `get_languages()` - Get available languages
- `get_learn_content_url(lang)` - Get learn-content URL
- `get_explore_content_url(lang)` - Get explore-content URL
- `get_base_url(lang)` - Get base URL
- `get_content_file_path(lang, type)` - Get JSON file path
- `ensure_language_dirs()` - Create language directories

---

## 📋 New Workflow Structure

### 5 Separate Options

**1. categories**
- Crawl categories from `/learn-content`
- Extract: title, URL, last_updated
- Save to: `data/courses/{lang}/learn-content.json`

**2. series**
- Crawl series from `/explore-content`
- Extract: title, URL, last_updated
- Save to: `data/courses/{lang}/explore-content.json`

**3. courses**
- Crawl course details
- Extract: title, **overview**, **transcript**, **duration**, URL, last_updated
- Save full course metadata

**4. videos**
- Crawl videos with **LearnPoint grouping**
- Extract: title, URL, learning_point, last_updated
- Group videos by LearnPoint in JSON

**5. downloads**
- Sequential download with verification
- Path: `downloads/{lang}/{Category|Series}/{Course}/{LearnPoint}/{Video}.mp4`
- Check file exists before/after download
- Update JSON with download status

---

## 🌍 Language Support

### sites.json Structure
```json
{
  "en": [
    "https://unlimited.globis.co.jp/en/learn-content",
    "https://unlimited.globis.co.jp/en/explore-content"
  ],
  "ja": [
    "https://unlimited.globis.co.jp/ja/learn-content",
    "https://unlimited.globis.co.jp/ja/explore-content"
  ]
}
```

### Usage
```bash
# English only
python run_browser.py -l en categories

# Japanese only
python run_browser.py -l ja series

# Both languages (default)
python run_browser.py courses
```

---

## 📦 LearnPoint Structure

### What is LearnPoint?

Videos are grouped by **Learning Points** (learning objectives).

### Example Structure
```
Course: Business Proposals
├── LearnPoint: Introduction
│   ├── Video 1: What is a Proposal?
│   └── Video 2: Why Proposals Matter
├── LearnPoint: Main Content
│   ├── Video 3: Proposal Structure
│   └── Video 4: Key Elements
└── LearnPoint: Conclusion
    └── Video 5: Final Tips
```

### Download Path
```
downloads/
└── en/
    └── Critical Thinking/
        └── Business Proposals/
            ├── Introduction/
            │   ├── What is a Proposal.mp4
            │   └── Why Proposals Matter.mp4
            ├── Main Content/
            │   ├── Proposal Structure.mp4
            │   └── Key Elements.mp4
            └── Conclusion/
                └── Final Tips.mp4
```

---

## 📊 New Data Schema

### Category
```json
{
  "title": "Critical Thinking",
  "url": "/en/categories/critical-thinking",
  "last_updated": "2025-11-20T00:00:00Z",
  "courses": [...]
}
```

### Course (Enhanced)
```json
{
  "title": "Business Proposals",
  "url": "/en/courses/abc123/learn/steps",
  "overview": "Learn how to structure proposals...",
  "transcript": "Full course transcript...",
  "duration": 45,
  "last_updated": "2025-11-20T00:00:00Z",
  "learning_points": [...]
}
```

### LearnPoint (New)
```json
{
  "title": "Introduction",
  "videos": [...]
}
```

### Video (Enhanced)
```json
{
  "title": "What is a Proposal?",
  "url": "/en/courses/abc123/steps/60784",
  "vimeo_url": "https://player.vimeo.com/video/123",
  "learning_point": "Introduction",
  "downloaded": true,
  "download_path": "downloads/en/.../Introduction/What is a Proposal.mp4",
  "last_updated": "2025-11-20T00:00:00Z"
}
```

**Removed fields:**
- ❌ `uploaded_to_drive`
- ❌ `drive_file_id`

---

## 🚧 Next Steps (Phase 2)

### Priority Tasks

1. **Update Data Models**
   - Create LearnPoint dataclass
   - Add overview, transcript, duration to Course
   - Add learning_point, download_path to Video
   - Add last_updated to all objects

2. **Update Crawlers**
   - Add language parameter
   - Extract new fields (overview, transcript, duration)
   - Extract LearnPoint structure
   - Add last_updated timestamps

3. **Create Test Files**
   - tests/test_categories.py
   - tests/test_series.py
   - tests/test_courses.py
   - tests/test_videos.py
   - tests/test_downloads.py

4. **Update CLI**
   - Update run_browser.py with 5 options
   - Add --language flag
   - Integrate human behavior for all options

5. **Remove Google Drive**
   - Delete src/uploader/ module
   - Update requirements.txt
   - Clean up Drive-related code

---

## 📈 Progress Tracking

**Phase 1: Project Restructure** - ✅ **100% Complete**
- [x] Folder structure
- [x] Documentation
- [x] SitesManager utility

**Phase 2: Data Models** - ⏳ **0% Complete**
- [ ] LearnPoint dataclass
- [ ] Course enhancements
- [ ] Video enhancements
- [ ] last_updated fields

**Phase 3: Crawling Options** - ⏳ **0% Complete**
- [ ] categories option
- [ ] series option
- [ ] courses option (with new fields)
- [ ] videos option (with LearnPoint)

**Phase 4: Downloads** - ⏳ **0% Complete**
- [ ] LearnPoint-based paths
- [ ] File verification
- [ ] Sequential downloads
- [ ] JSON status updates

**Phase 5: Integration** - ⏳ **0% Complete**
- [ ] CLI with 5 options
- [ ] Language selection
- [ ] Test files
- [ ] Human behavior integration

**Overall**: 5/30 tasks (17%)

---

## 🎯 Testing Strategy

### Step 1: Individual Tests
Test each option independently before integration:

```bash
# Test each option separately
python tests/test_categories.py
python tests/test_series.py
python tests/test_courses.py
python tests/test_videos.py
python tests/test_downloads.py
```

### Step 2: Integration
Only after all tests pass, integrate into main CLI:

```bash
# Run full workflow
python run_browser.py -l en all
```

---

## 📝 Notes

### Key Changes from Original
1. ✅ **No Google Drive** upload
2. ✅ **Multi-language** support (EN/JA)
3. ✅ **LearnPoint** grouping for videos
4. ✅ **Enhanced course data** (overview, transcript, duration)
5. ✅ **5 separate options** instead of single workflow
6. ✅ **Organized folders** (tests/, logs/, downloads/, docs/)
7. ✅ **Individual testing** before integration

### Development Approach
- Build incrementally (one phase at a time)
- Test each component independently
- Document as we go
- Keep existing working code until new code is tested

---

**Status**: Phase 1 Complete ✅
**Next**: Begin Phase 2 (Data Models & Schema)
**Updated**: 2025-11-20

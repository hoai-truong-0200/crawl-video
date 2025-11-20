# Project Restructure - GLOBIS Unlimited Crawler

## Overview
Complete restructure of the GLOBIS Unlimited crawler project with new requirements:

### Key Changes
1. **Multi-language support** (EN + JA)
2. **Updated workflow** with 5 separate options
3. **LearnPoint grouping** for videos
4. **Enhanced course data** (overview, transcript, duration)
5. **Removed Google Drive** upload features
6. **Organized folder structure**

---

## New Folder Structure

```
crawl-video/
├── src/                    # Source code
│   ├── browser/            # ✅ Anti-detection (existing)
│   ├── crawler/            # ⚠️ Update needed
│   ├── downloader/         # ⚠️ Update needed
│   └── utils/              # ⚠️ Add new utilities
│
├── data/                   # Data storage
│   └── courses/
│       ├── sites.json      # ✅ EN/JA URLs
│       ├── en/             # ⚠️ NEW - English content
│       │   ├── learn-content.json
│       │   └── explore-content.json
│       └── ja/             # ⚠️ NEW - Japanese content
│           ├── learn-content.json
│           └── explore-content.json
│
├── downloads/              # ✅ Video downloads
│   ├── en/
│   │   ├── {Category}/
│   │   │   └── {Course}/
│   │   │       └── {LearnPoint}/
│   │   │           └── {Video}.mp4
│   │   └── {Series}/
│   │       └── ...
│   └── ja/                 # Same structure
│
├── logs/                   # ✅ Date-based logs
│   ├── 2025-11-19.log
│   └── 2025-11-20.log
│
├── tests/                  # ✅ Test files
│   ├── test_categories.py
│   ├── test_series.py
│   ├── test_courses.py
│   ├── test_videos.py
│   └── test_downloads.py
│
├── docs/                   # ✅ Documentation
│   ├── README.md
│   ├── TODO_NEW_STRUCTURE.md
│   ├── PROJECT_RESTRUCTURE.md
│   └── ...
│
├── run_browser.py          # ⚠️ Update with new options
└── requirements.txt        # ⚠️ Update dependencies
```

---

## Workflow Changes

### Old Workflow
```
1. Crawl categories
2. Crawl videos
3. Download videos
4. Upload to Google Drive
```

### New Workflow (5 Options)

**Option 1: `categories`**
- Crawl all categories from `/learn-content`
- Extract: title, URL, last_updated
- Save to: `data/courses/{lang}/learn-content.json`

**Option 2: `series`**
- Crawl all series from `/explore-content`
- Extract: title, URL, last_updated
- Save to: `data/courses/{lang}/explore-content.json`

**Option 3: `courses`**
- Crawl all courses in categories/series
- Extract: title, **overview**, **transcript**, **duration**, URL, last_updated
- Save course details to JSON

**Option 4: `videos`**
- Crawl all videos in courses
- **Group by LearnPoint** (new requirement)
- Extract: title, URL, learning_point, last_updated
- Save video list with LearnPoint structure

**Option 5: `downloads`**
- Sequential download of videos
- Check if file exists (skip if already downloaded)
- Save to: `downloads/{lang}/{Category|Series}/{Course}/{LearnPoint}/{Video}.mp4`
- Update JSON with download status after verification

---

## Data Model Changes

### Old Schema (Video object)
```json
{
  "title": "Video 1",
  "url": "/courses/abc/steps/123",
  "vimeo_url": "https://player.vimeo.com/video/123",
  "downloaded": false,
  "uploaded_to_drive": false,
  "drive_file_id": ""
}
```

### New Schema (Video with LearnPoint)
```json
{
  "title": "What is a Proposal?",
  "url": "/courses/abc/steps/123",
  "vimeo_url": "https://player.vimeo.com/video/123",
  "learning_point": "Introduction",
  "downloaded": true,
  "download_path": "downloads/en/Category/Course/Introduction/Video.mp4",
  "last_updated": "2025-11-20T00:00:00Z"
}
```

### New Fields Added

**All objects:**
- `last_updated` (ISO 8601 timestamp)

**Course object:**
- `overview` (string) - Course description
- `transcript` (string) - Full course transcript
- `duration` (int) - Total duration in minutes

**Video object:**
- `learning_point` (string) - LearnPoint group name
- `download_path` (string) - Actual file path after download
- Removed: `uploaded_to_drive`, `drive_file_id`

---

## LearnPoint Structure

### What is LearnPoint?

Videos in a course are grouped into **LearnPoints** (learning objectives).

### HTML Structure
```html
<div class="...">
  <div class="*__learningPointName">Introduction</div>
  <div class="video-item">Video 1</div>
  <div class="video-item">Video 2</div>
</div>

<div class="...">
  <div class="*__learningPointName">Main Content</div>
  <div class="video-item">Video 3</div>
  <div class="video-item">Video 4</div>
</div>
```

### JSON Representation
```json
{
  "learning_points": [
    {
      "title": "Introduction",
      "videos": [
        {"title": "Video 1", "url": "..."},
        {"title": "Video 2", "url": "..."}
      ]
    },
    {
      "title": "Main Content",
      "videos": [
        {"title": "Video 3", "url": "..."},
        {"title": "Video 4", "url": "..."}
      ]
    }
  ]
}
```

### Download Path with LearnPoint
```
downloads/
└── en/
    └── Critical Thinking/
        └── Business Proposals/
            ├── Introduction/           ← LearnPoint
            │   ├── Video 1.mp4
            │   └── Video 2.mp4
            └── Main Content/           ← LearnPoint
                ├── Video 3.mp4
                └── Video 4.mp4
```

---

## Language Support

### sites.json
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

### Language Selection
```bash
# English only
python run_browser.py -l en categories

# Japanese only
python run_browser.py -l ja categories

# Both languages (default)
python run_browser.py categories
```

### Data Storage
- EN content: `data/courses/en/learn-content.json`
- JA content: `data/courses/ja/learn-content.json`
- Separate JSON files per language

---

## Implementation Plan

### Phase 1: Restructure ✅
- [x] Create folder structure
- [x] Move files to correct locations
- [x] Setup language directories

### Phase 2: Data Models (In Progress)
- [ ] Create LearnPoint dataclass
- [ ] Update Course dataclass (overview, transcript, duration)
- [ ] Update Video dataclass (learning_point, download_path)
- [ ] Add last_updated to all objects
- [ ] Create SitesManager utility

### Phase 3: Update Crawlers
- [ ] Add language parameter to all crawlers
- [ ] Extract overview, transcript, duration from courses
- [ ] Extract LearnPoint structure from videos
- [ ] Add last_updated timestamps

### Phase 4: Update Download
- [ ] Update path structure with LearnPoint
- [ ] Add file existence check
- [ ] Sequential download with verification
- [ ] Update JSON after successful download

### Phase 5: CLI & Testing
- [ ] Update run_browser.py with 5 options
- [ ] Add language selection
- [ ] Create test files for each option
- [ ] Integrate human behavior
- [ ] Add logging to files

---

## Testing Strategy

### Individual Test Files

**tests/test_categories.py**
- Test category crawling for single language
- Verify title, URL, last_updated extracted
- Check JSON saved correctly

**tests/test_series.py**
- Test series crawling for single language
- Verify all series found
- Check JSON format

**tests/test_courses.py**
- Test single course extraction
- Verify overview, transcript, duration extracted
- Check all new fields present

**tests/test_videos.py**
- Test video extraction with LearnPoint
- Verify videos grouped correctly
- Check LearnPoint names extracted

**tests/test_downloads.py**
- Test single video download
- Verify LearnPoint folder created
- Check file verification works
- Test JSON update after download

### Integration Testing

Only integrate into `run_browser.py` after all individual tests pass.

---

## Removed Features

### Google Drive Upload
- Removed `src/uploader/` module completely
- Removed from requirements.txt:
  - google-api-python-client
  - google-auth-httplib2
  - google-auth-oauthlib
- Removed fields from JSON:
  - `uploaded_to_drive`
  - `drive_file_id`

---

## Summary

This restructure transforms the project from a simple crawler to a **comprehensive multi-language course data extraction and download system** with:

✅ **Better organization** - Clear folder structure
✅ **Language support** - EN + JA
✅ **Enhanced data** - overview, transcript, duration, learning_point
✅ **Structured downloads** - LearnPoint-based folders
✅ **Modular workflow** - 5 separate options
✅ **Better testing** - Individual test files per option
✅ **Simplified scope** - No cloud upload

Next: Begin Phase 2 (Data Models & Schema)

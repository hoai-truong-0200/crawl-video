# Phase 2 Complete - Data Models & Schema

## ✅ Completed Updates

### 1. Updated Dataclasses

#### Video (Enhanced)
```python
@dataclass
class Video:
    title: str = ""
    url: str = ""
    vimeo_url: str = ""
    learning_point: str = ""      # NEW
    downloaded: bool = False       # NEW (default: False)
    download_path: str = ""        # NEW
    last_updated: str = ""         # NEW
```

**Changes:**
- ✅ Added `learning_point` - LearnPoint group name
- ✅ Added `downloaded` - Download status (default: False)
- ✅ Added `download_path` - Local file path after download
- ✅ Added `last_updated` - ISO 8601 timestamp
- ❌ Removed `uploaded_to_drive`, `drive_file_id`

#### LearnPoint (NEW)
```python
@dataclass
class LearnPoint:
    title: str = ""
    videos: List[Video] = field(default_factory=list)
```

**Purpose:** Group videos by learning objectives

#### Course (Enhanced)
```python
@dataclass
class Course:
    title: str = ""
    url: str = ""
    overview: str = ""             # NEW
    transcript: str = ""           # NEW
    duration: int = 0              # NEW (minutes)
    last_updated: str = ""         # NEW
    learning_points: List[LearnPoint] = field(default_factory=list)  # NEW
```

**Changes:**
- ✅ Added `overview` - Course description
- ✅ Added `transcript` - Full course transcript
- ✅ Added `duration` - Total duration in minutes
- ✅ Added `last_updated` - ISO 8601 timestamp
- ✅ Changed `videos: List[Video]` → `learning_points: List[LearnPoint]`

#### Category (Enhanced)
```python
@dataclass
class Category:
    title: str = ""
    url: str = ""
    last_updated: str = ""         # NEW
    courses: List[Course] = field(default_factory=list)
```

**Changes:**
- ✅ Added `last_updated` - ISO 8601 timestamp

#### Series (NEW)
```python
@dataclass
class Series:
    title: str = ""
    url: str = ""
    last_updated: str = ""
    courses: List[Course] = field(default_factory=list)
```

**Purpose:** Same as Category but for explore-content

---

## 📋 New JSON Schema

### Complete Structure
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
          "overview": "Learn how to structure strong proposals...",
          "transcript": "Full course transcript content here...",
          "duration": 45,
          "last_updated": "2025-11-20T00:00:00Z",
          "learning_points": [
            {
              "title": "Introduction",
              "videos": [
                {
                  "title": "What is a Proposal?",
                  "url": "/en/courses/abc123/learn/steps/60784",
                  "vimeo_url": "https://player.vimeo.com/video/123456",
                  "learning_point": "Introduction",
                  "downloaded": false,
                  "download_path": "",
                  "last_updated": "2025-11-20T00:00:00Z"
                },
                {
                  "title": "Why Proposals Matter",
                  "url": "/en/courses/abc123/learn/steps/60785",
                  "vimeo_url": "https://player.vimeo.com/video/123457",
                  "learning_point": "Introduction",
                  "downloaded": true,
                  "download_path": "downloads/en/Critical Thinking/Business Proposals/Introduction/Why Proposals Matter.mp4",
                  "last_updated": "2025-11-20T00:48:30Z"
                }
              ]
            },
            {
              "title": "Main Content",
              "videos": [
                {
                  "title": "Proposal Structure",
                  "url": "/en/courses/abc123/learn/steps/60786",
                  "vimeo_url": "https://player.vimeo.com/video/123458",
                  "learning_point": "Main Content",
                  "downloaded": false,
                  "download_path": "",
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

## 🔄 Migration Path

### Old Format (Before)
```json
{
  "categories": [
    {
      "title": "Category",
      "url": "/category",
      "courses": [
        {
          "title": "Course",
          "url": "/course",
          "last_updated": "",
          "videos": [
            {
              "title": "Video",
              "url": "/video",
              "vimeo_url": "",
              "downloaded": false,
              "uploaded_to_drive": false,
              "drive_file_id": ""
            }
          ]
        }
      ]
    }
  ]
}
```

### New Format (After)
```json
{
  "language": "en",
  "last_updated": "2025-11-20T00:00:00Z",
  "categories": [
    {
      "title": "Category",
      "url": "/category",
      "last_updated": "2025-11-20T00:00:00Z",
      "courses": [
        {
          "title": "Course",
          "url": "/course",
          "overview": "",
          "transcript": "",
          "duration": 0,
          "last_updated": "2025-11-20T00:00:00Z",
          "learning_points": [
            {
              "title": "Introduction",
              "videos": [
                {
                  "title": "Video",
                  "url": "/video",
                  "vimeo_url": "",
                  "learning_point": "Introduction",
                  "downloaded": false,
                  "download_path": "",
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

**Key Differences:**
1. ✅ Added `language` at root level
2. ✅ Added `last_updated` at all levels
3. ✅ Added `overview`, `transcript`, `duration` to courses
4. ✅ Changed `videos[]` → `learning_points[{title, videos[]}]`
5. ✅ Added `learning_point`, `download_path` to videos
6. ❌ Removed `uploaded_to_drive`, `drive_file_id`

---

## 📁 File Updates

### src/crawler/content_manager.py

**Status:** ✅ Dataclasses updated, ContentManager needs load/save methods update

**Next Steps:**
1. Update `load()` method to parse LearnPoint structure
2. Update `save()` method to serialize with new fields
3. Add support for `language` field at root
4. Remove Drive-related fields

---

## 🧪 Testing

### Test Data Model Creation
```python
from src.crawler.content_manager import Video, LearnPoint, Course, Category
from datetime import datetime

# Create video
video = Video(
    title="What is a Proposal?",
    url="/en/courses/abc/steps/123",
    vimeo_url="https://player.vimeo.com/video/123",
    learning_point="Introduction",
    downloaded=False,
    download_path="",
    last_updated=datetime.now().isoformat()
)

# Create LearnPoint
learn_point = LearnPoint(
    title="Introduction",
    videos=[video]
)

# Create Course
course = Course(
    title="Business Proposals",
    url="/en/courses/abc/learn/steps",
    overview="Learn to write proposals...",
    transcript="Full transcript...",
    duration=45,
    last_updated=datetime.now().isoformat(),
    learning_points=[learn_point]
)

# Create Category
category = Category(
    title="Critical Thinking",
    url="/en/categories/critical-thinking",
    last_updated=datetime.now().isoformat(),
    courses=[course]
)
```

---

## 📊 Progress Update

### Phase 2: Data Models & Schema

- [x] **Task 6**: Update JSON schema with new fields ✅
- [x] **Task 7**: Create LearnPoint dataclass ✅
- [x] **Task 8**: Update Course dataclass ✅
- [ ] **Task 9**: Add language parameter to all crawlers
- [x] **Task 10**: Create SitesManager utility ✅

**Phase 2 Progress**: 4/5 tasks (80%)

---

## 🎯 Next Steps

### Phase 2 Remaining
- [ ] Update ContentManager `load()` and `save()` methods for new structure

### Phase 3 Preview
- [ ] Update crawlers to extract new fields
- [ ] Extract LearnPoint structure from pages
- [ ] Add last_updated timestamps

---

## Summary

✅ **Completed:**
- New dataclasses: Video, LearnPoint, Course, Category, Series
- All new fields added (overview, transcript, duration, learning_point, downloaded, download_path, last_updated)
- Google Drive fields removed
- Documentation created

⏳ **Next:**
- Update ContentManager load/save methods
- Begin Phase 3 (Crawler updates)

**Updated**: 2025-11-20
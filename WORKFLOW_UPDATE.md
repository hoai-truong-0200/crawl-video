# Workflow Update - Sequential Download with Incremental Save

## Overview
Updated `run_browser.py videos` workflow to download videos sequentially with incremental JSON saves.

## New Workflow

### Sequential Process (Per Video)
1. **Navigate to video page** → Wait for page load
2. **Extract video info** (title + url) → **Save to JSON immediately**
3. **Extract download URL** from DOM (`window.playerConfig`)
4. **Download video** → Wait for completion
5. **Update JSON** with download status
6. **Move to next video** → Repeat

### Key Changes

**Before:**
- Crawled all video URLs first
- Downloaded all videos in batch
- Saved JSON once at the end

**After:**
- Process videos **one by one**
- **Save JSON after each video** (incremental progress)
- Download immediately after extracting URL
- **Wait for download completion** before next video

## Updated Files

### 1. VideoDownloader ([src/downloader/video_downloader.py](src/downloader/video_downloader.py))

**Changes:**
- Updated download directory structure: `downloads/` → `data/downloads/`
- Added `content_type` parameter (`learn-content` or `explore-content`)
- New path format: `data/downloads/{content_type}/{Category}/{Course}/{Video Title}.mp4`

```python
# Before
downloads/Category Name/Course Name/video.mp4

# After
data/downloads/learn-content/Category Name/Course Name/video.mp4
data/downloads/explore-content/Series Name/Course Name/video.mp4
```

### 2. CourseCrawler ([src/crawler/course_crawler.py](src/crawler/course_crawler.py))

**Changes:**
- Auto-detect content type from file path
- **Incremental JSON save** after each video
- Sequential workflow:

```python
# Step 1: Create video object with basic info
video = Video(title=step.title, url=step.url, vimeo_url="", downloaded=False)

# Step 2: Add to list and save JSON immediately
videos.append(video)
course.videos = videos
self.content_manager.save()  # ✅ Save progress

# Step 3: Extract download URL from DOM
video_urls = await VimeoExtractor.extract_video_urls(page)
best_download_url = video_urls.get('best_download_url')

# Step 4: Download video (wait for completion)
download_success = await self.downloader.download_from_extracted_url(
    download_url=best_download_url,
    category_or_series=category.title,
    course_name=course.title,
    video_title=step.title,
)

# Step 5: Update JSON with download status
video.downloaded = download_success
self.content_manager.save()  # ✅ Save download status

# Move to next video...
```

## Directory Structure

### Download Folders
```
data/downloads/
├── learn-content/
│   ├── Critical Thinking and Communication/
│   │   ├── Business Proposals/
│   │   │   ├── Introduction.mp4
│   │   │   ├── Proposal Structure.mp4
│   │   │   └── Final Tips.mp4
│   │   └── Writing Effective Emails/
│   │       ├── Video 1.mp4
│   │       ├── Video 2.mp4
│   │       └── Video 3.mp4
│   └── Leadership/
│       └── ...
└── explore-content/
    ├── Series Name/
    │   └── Course Name/
    │       ├── Video 1.mp4
    │       └── Video 2.mp4
    └── ...
```

### JSON Structure (learn-content.json)
```json
{
  "categories": [
    {
      "title": "Critical Thinking and Communication",
      "courses": [
        {
          "title": "Business Proposals",
          "url": "https://unlimited.globis.co.jp/en/courses/d8501fa9/learn/steps",
          "videos": [
            {
              "title": "Introduction",
              "url": "/en/courses/d8501fa9/learn/steps/60784",
              "vimeo_url": "https://player.vimeo.com/video/1117632958",
              "downloaded": true,
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

## Benefits

### 1. Incremental Progress Saving
- JSON saved after each video
- Can resume if script crashes
- Progress visible in real-time

### 2. Sequential Downloads
- One video at a time
- Easier to track progress
- Less memory usage

### 3. Better Error Handling
- Failed downloads don't block entire course
- Each video's status tracked independently
- Easy to retry failed videos

### 4. Organized File Structure
- Clear separation: `learn-content` vs `explore-content`
- Hierarchical folders: `{Category}/{Course}/{Video}`
- Easy to navigate and manage

## Testing

### Test Script
New test file: [test_download_workflow.py](test_download_workflow.py)

```bash
source venv/bin/activate
python test_download_workflow.py
```

**What it tests:**
- Single course crawl
- Sequential video processing
- Incremental JSON saves
- Download completion
- JSON status updates

### Expected Behavior

**Console Output:**
```
19:45:12 | INFO     | 📂 Category: Critical Thinking and Communication
19:45:12 | INFO     | 📚 Course: Business Proposals
19:45:15 | INFO     |    🎬 Step [1/3]: Introduction
19:45:15 | DEBUG    |       💾 Saved video info to JSON: Introduction
19:45:18 | INFO     |       📥 Starting download: Introduction
19:45:18 | INFO     |       📥 Downloading (HLS/DASH): Introduction
19:45:24 | INFO     |       ✅ Downloaded: Introduction.mp4 (6.2 MB)
19:45:24 | INFO     |       ✅ Download complete & JSON updated
19:45:26 | INFO     |    🎬 Step [2/3]: Proposal Structure
...
```

**File System:**
```
data/downloads/learn-content/
└── Critical Thinking and Communication/
    └── Business Proposals/
        ├── Introduction.mp4        (✅ Downloaded)
        ├── Proposal Structure.mp4  (⏳ Downloading...)
        └── Final Tips.mp4          (⏸️ Pending)
```

**JSON Updates:**
- After step 1: `Introduction` → saved with `downloaded: false`
- After download: `Introduction` → updated to `downloaded: true`
- After step 2: `Proposal Structure` → saved with `downloaded: false`
- ...continues sequentially

## Usage

### Run Full Workflow
```bash
source venv/bin/activate
python run_browser.py videos
```

**Process:**
1. Loads `data/courses/learn-content.json`
2. For each category → For each course:
   - Navigate to course page
   - Extract all video steps
   - For each video:
     - Extract title + url
     - Save to JSON
     - Extract download URL
     - Download video
     - Update JSON with status
3. Videos saved to: `data/downloads/learn-content/{Category}/{Course}/{Video}.mp4`

### Resume Failed Downloads
Since JSON is saved incrementally, you can:
1. Check JSON for videos with `downloaded: false`
2. Re-run crawler (it will skip already downloaded videos)
3. Only failed/pending videos will be downloaded

## Summary

**New workflow advantages:**
- ✅ Incremental progress saving
- ✅ Sequential downloads (one at a time)
- ✅ Wait for completion before next video
- ✅ Better organized file structure
- ✅ Easier to resume/retry
- ✅ Real-time progress tracking

**Perfect for:**
- Large course libraries
- Unreliable network conditions
- Long-running crawls
- Easy progress monitoring

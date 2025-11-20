# Download Workflow - Status Check Logic

## Overview

Download workflow với logic kiểm tra `downloaded` status để tối ưu performance và tránh download lại video đã có.

---

## Two-Phase Approach

### Phase 1: Option `videos`
**Mục đích**: Crawl video metadata

**Actions**:
1. Navigate to course page
2. Extract LearnPoint structure
3. For each video in LearnPoint:
   - Extract title, URL, vimeo_url
   - **Set `downloaded: false`** (default)
   - Save to JSON immediately

**Output**: JSON with all videos marked as `downloaded: false`

### Phase 2: Option `downloads`
**Mục đích**: Download videos sequentially

**Actions**:
1. Load JSON file
2. For each video:
   - **CHECK `downloaded` status FIRST**
   - If `downloaded: true` → **SKIP** (don't open browser link)
   - If `downloaded: false` → Process download
3. After successful download:
   - Update `downloaded: true`
   - Update `download_path`
   - Save JSON

---

## Detailed Download Logic

### Flowchart

```
Start Download Option
    ↓
Load JSON file
    ↓
For each Category/Series:
    ↓
  For each Course:
      ↓
    For each LearnPoint:
        ↓
      For each Video:
          ↓
        ┌─────────────────────────┐
        │ Check `downloaded`      │
        │ status in JSON          │
        └──────────┬──────────────┘
                   │
          ┌────────┴────────┐
          │                 │
       TRUE              FALSE
          │                 │
          ↓                 ↓
    ┌─────────┐      ┌──────────────┐
    │ SKIP    │      │ Open browser │
    │ (log)   │      │ Navigate URL │
    └─────────┘      └──────┬───────┘
          │                 │
          │                 ↓
          │         ┌──────────────┐
          │         │ Extract DOM  │
          │         │ Get download │
          │         │ URL          │
          │         └──────┬───────┘
          │                │
          │                ↓
          │         ┌──────────────┐
          │         │ Download     │
          │         │ video file   │
          │         └──────┬───────┘
          │                │
          │                ↓
          │         ┌──────────────┐
          │         │ Verify file  │
          │         │ exists &     │
          │         │ size > 0     │
          │         └──────┬───────┘
          │                │
          │         ┌──────┴───────┐
          │         │              │
          │      SUCCESS         FAIL
          │         │              │
          │         ↓              ↓
          │    ┌─────────┐   ┌─────────┐
          │    │ Update  │   │ Keep    │
          │    │ JSON:   │   │ JSON:   │
          │    │ true    │   │ false   │
          │    └────┬────┘   └─────────┘
          │         │              │
          └─────────┴──────────────┘
                    │
                    ↓
              Next Video
```

---

## Code Implementation

### Option videos: Set default status

```python
# In video extraction (option: videos)
async def extract_videos(page, learning_point_name):
    """Extract videos and set downloaded: false"""

    videos = []
    for video_element in video_elements:
        title = extract_title(video_element)
        url = extract_url(video_element)

        video = Video(
            title=title,
            url=url,
            learning_point=learning_point_name,
            downloaded=False,  # ← DEFAULT STATUS
            download_path="",
            last_updated=datetime.now().isoformat()
        )

        videos.append(video)

        # Save to JSON immediately
        save_json()

    return videos
```

### Option downloads: Check status before opening

```python
# In download option
async def download_videos(page, language):
    """Download videos with status check"""

    # Load JSON
    data = load_json(language)

    for category in data.categories:
        for course in category.courses:
            for learning_point in course.learning_points:
                for video in learning_point.videos:

                    # ====================================
                    # CRITICAL: Check status BEFORE opening link
                    # ====================================
                    if video.downloaded:
                        logger.info(f"⏭️  SKIP (already downloaded): {video.title}")
                        continue  # Don't open browser, move to next

                    # Status is False → Proceed with download
                    logger.info(f"📥 Downloading: {video.title}")

                    # Open browser and navigate
                    await page.goto(f"https://unlimited.globis.co.jp{video.url}")

                    # Extract download URL from DOM
                    download_url = await extract_download_url(page)

                    # Download video
                    file_path = build_download_path(
                        language, category.title,
                        course.title, learning_point.title,
                        video.title
                    )

                    success = await download_video_file(download_url, file_path)

                    # Update status only if successful
                    if success and file_exists(file_path) and file_size(file_path) > 0:
                        video.downloaded = True
                        video.download_path = str(file_path)
                        video.last_updated = datetime.now().isoformat()

                        # Save JSON after each video
                        save_json(data)

                        logger.info(f"✅ Downloaded & JSON updated: {video.title}")
                    else:
                        logger.error(f"❌ Download failed: {video.title}")
                        # Keep downloaded: False for retry later
```

---

## Benefits of Status Check

### 1. **Performance Optimization**
- ✅ Skip already downloaded videos
- ✅ Don't open browser for completed videos
- ✅ Faster execution on retry/resume

### 2. **Resume Capability**
- ✅ Can stop and resume anytime
- ✅ Only download pending videos
- ✅ Progress saved incrementally

### 3. **Error Recovery**
- ✅ Failed downloads keep `downloaded: false`
- ✅ Easy to identify failed videos
- ✅ Re-run downloads only for failed items

### 4. **Bandwidth Saving**
- ✅ Never re-download same video
- ✅ Skip network requests for completed videos
- ✅ Efficient use of resources

---

## Example Scenario

### Initial State (After option: videos)
```json
{
  "learning_points": [
    {
      "title": "Introduction",
      "videos": [
        {"title": "Video 1", "downloaded": false},
        {"title": "Video 2", "downloaded": false},
        {"title": "Video 3", "downloaded": false}
      ]
    }
  ]
}
```

### After Partial Download (2/3 videos)
```json
{
  "learning_points": [
    {
      "title": "Introduction",
      "videos": [
        {
          "title": "Video 1",
          "downloaded": true,
          "download_path": "downloads/en/.../Video 1.mp4"
        },
        {
          "title": "Video 2",
          "downloaded": true,
          "download_path": "downloads/en/.../Video 2.mp4"
        },
        {
          "title": "Video 3",
          "downloaded": false  // ← FAILED or PENDING
        }
      ]
    }
  ]
}
```

### Re-run Download Option

**Behavior:**
- Video 1: `downloaded: true` → **SKIP** ⏭️
- Video 2: `downloaded: true` → **SKIP** ⏭️
- Video 3: `downloaded: false` → **DOWNLOAD** 📥

**Output:**
```
⏭️  SKIP (already downloaded): Video 1
⏭️  SKIP (already downloaded): Video 2
📥 Downloading: Video 3
✅ Downloaded & JSON updated: Video 3
```

---

## Status Transition Diagram

```
┌─────────────────┐
│ Video Created   │
│ (option: videos)│
└────────┬────────┘
         │
         ↓
    downloaded: false
         │
         ↓
┌────────┴─────────┐
│ Download Attempt │
│ (option:downloads)
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
 SUCCESS    FAIL
    │         │
    ↓         ↓
  true      false
    │         │
    ↓         ↓
 [END]    [RETRY]
```

---

## Implementation Checklist

### Option: videos
- [ ] Extract video metadata
- [ ] Set `downloaded: false` by default
- [ ] Save to JSON immediately after extraction
- [ ] Add `last_updated` timestamp

### Option: downloads
- [ ] Load JSON file
- [ ] **Check `downloaded` status BEFORE opening link**
- [ ] Skip if `true`, download if `false`
- [ ] Download video file
- [ ] Verify file exists and size > 0
- [ ] Update `downloaded: true` only on success
- [ ] Update `download_path` and `last_updated`
- [ ] Save JSON after each video

---

## Error Handling

### Scenario 1: Download fails
```python
if download_failed:
    # Keep downloaded: false
    video.downloaded = False
    logger.error(f"❌ Download failed: {video.title}")
    # Do NOT update download_path
    # Video will be retried on next run
```

### Scenario 2: File corrupted (size = 0)
```python
if file_size(file_path) == 0:
    # Remove corrupted file
    file_path.unlink()

    # Keep downloaded: false
    video.downloaded = False
    logger.error(f"❌ Corrupted file (0 bytes): {video.title}")
```

### Scenario 3: Network timeout
```python
try:
    await download_video_file(url, path)
except TimeoutError:
    video.downloaded = False
    logger.error(f"⏱️ Timeout: {video.title}")
    # Will retry on next run
```

---

## Summary

### Key Points

1. **Option videos**: Always set `downloaded: false` when creating video objects
2. **Option downloads**: ALWAYS check status BEFORE opening browser link
3. **Skip logic**: `downloaded: true` → Don't waste time opening link
4. **Update logic**: Only set `downloaded: true` after verification
5. **Resume capability**: Can stop/resume anytime, progress saved

### Workflow

```
videos option → downloaded: false (all videos)
    ↓
downloads option → check status
    ↓
├─ true  → SKIP ⏭️
└─ false → DOWNLOAD 📥
    ↓
  verify
    ↓
├─ success → downloaded: true ✅
└─ fail    → downloaded: false (retry) ❌
```

**Result**: Efficient, resumable, error-tolerant download system.
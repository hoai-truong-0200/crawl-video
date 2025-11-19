# Phase 5 Complete: DOM-Based Video Extraction & Auto-Download

## Overview
Successfully implemented DOM-based video URL extraction and automatic download for both HLS/DASH and progressive MP4 videos.

## What Was Accomplished

### 1. Switched from Network Interception to DOM Extraction
**Problem**: Network interception approach required videos to actually play, which was unreliable.

**Solution**: Extract video URLs directly from `window.playerConfig` object in Vimeo iframe DOM.

### 2. Created VimeoExtractor Class
**File**: [src/downloader/vimeo_extractor.py](src/downloader/vimeo_extractor.py)

**Features**:
- Accesses Vimeo iframe and extracts `window.playerConfig` from DOM
- Parses all available video formats:
  - Progressive MP4 (direct download URLs with quality levels)
  - HLS (adaptive streaming with m3u8 playlists)
  - DASH (adaptive streaming with JSON manifests)
- Selects best quality URL automatically
- Returns structured video URL data

**Key Method**:
```python
async def extract_video_urls(page: Page, timeout: int = 10000) -> Optional[Dict]:
    """
    Returns:
    {
        'video_id': str,
        'vimeo_player_url': str,
        'progressive': [{'quality': str, 'url': str, 'width': int, 'height': int}],
        'hls': {'cdn': str, 'url': str} or None,
        'dash': {'cdn': str, 'url': str} or None,
        'best_download_url': str
    }
    """
```

### 3. Enhanced VideoDownloader with Auto-Download Support
**File**: [src/downloader/video_downloader.py](src/downloader/video_downloader.py)

**New Method**: `download_from_extracted_url()`

**Features**:
- Automatically detects URL type (progressive, HLS, or DASH)
- Downloads progressive MP4s directly with aiohttp
- Downloads HLS/DASH streams with yt-dlp
- Retry logic with exponential backoff
- Proper error handling and cleanup

**Supported Formats**:
- Progressive MP4: Direct download with aiohttp
- HLS (.m3u8): Downloaded with yt-dlp
- DASH (.mpd, playlist.json): Downloaded with yt-dlp

### 4. Updated CourseCrawler
**File**: [src/crawler/course_crawler.py](src/crawler/course_crawler.py)

**Changes**:
- Removed `VimeoInterceptor` (network-based approach)
- Added `VimeoExtractor` (DOM-based approach)
- Updated step extraction to use `extract_video_urls()`
- Changed download call to use `download_from_extracted_url()`

**Workflow**:
1. Navigate to step page
2. Wait for video player to load
3. Extract video URLs from DOM using VimeoExtractor
4. Download using best quality URL
5. Continue to next step

### 5. Test Script Updated
**File**: [test_single_video_download.py](test_single_video_download.py)

**Features**:
- Extracts playerConfig from Vimeo iframe
- Saves all URLs to `video_urls.json`
- Automatically downloads first video (HLS/DASH or progressive)
- Shows download progress and file size

**Test Results**:
```
✅ playerConfig extracted successfully
📺 HLS URL found
📥 Downloading HLS/DASH stream with yt-dlp...
✅ Download complete!
   File: downloaded_video.mp4
   Size: 6.2 MB
```

## Key Improvements

### 1. Reliability
- **Before**: Depended on video playback triggering network requests
- **After**: Extracts URLs directly from DOM, always available

### 2. Video Format Support
- **Before**: Only attempted to capture progressive URLs from network
- **After**: Supports all formats (progressive, HLS, DASH)

### 3. Download Methods
- **Before**: Only yt-dlp with Vimeo player URL
- **After**:
  - Progressive: Direct download with aiohttp (faster)
  - HLS/DASH: yt-dlp with extracted stream URL

### 4. Quality Selection
- **Before**: Relied on yt-dlp's automatic selection
- **After**: Extracts all qualities, selects best automatically

## Technical Details

### playerConfig Structure
```json
{
  "request": {
    "files": {
      "progressive": [
        {
          "quality": "720p",
          "width": 1280,
          "height": 720,
          "url": "https://vod-progressive-ak.vimeocdn.com/..."
        }
      ],
      "hls": {
        "default_cdn": "akfire_interconnect_quic",
        "cdns": {
          "akfire_interconnect_quic": {
            "url": "https://vod-adaptive-ak.vimeocdn.com/.../playlist.m3u8"
          }
        }
      },
      "dash": {
        "default_cdn": "akfire_interconnect_quic",
        "cdns": {
          "akfire_interconnect_quic": {
            "url": "https://vod-adaptive-ak.vimeocdn.com/.../playlist.json"
          }
        }
      }
    }
  }
}
```

### URL Type Detection
```python
is_progressive = 'progressive' in url or '.mp4' in url
is_hls = '.m3u8' in url or 'playlist' in url
is_dash = '.mpd' in url or 'playlist.json' in url
```

### Download Methods by Type

**Progressive MP4**:
```python
async with aiohttp.ClientSession() as session:
    async with session.get(download_url) as resp:
        # Download chunks
        async for chunk in resp.content.iter_chunked(1024 * 1024):
            f.write(chunk)
```

**HLS/DASH**:
```python
cmd = ['yt-dlp', download_url, '-o', str(temp_path), '--no-playlist']
process = await asyncio.create_subprocess_exec(*cmd, ...)
```

## Files Modified

1. **New Files**:
   - [src/downloader/vimeo_extractor.py](src/downloader/vimeo_extractor.py) - VimeoExtractor class

2. **Modified Files**:
   - [src/downloader/video_downloader.py](src/downloader/video_downloader.py) - Added `download_from_extracted_url()`
   - [src/downloader/__init__.py](src/downloader/__init__.py) - Export VimeoExtractor
   - [src/crawler/course_crawler.py](src/crawler/course_crawler.py) - Use VimeoExtractor instead of VimeoInterceptor
   - [test_single_video_download.py](test_single_video_download.py) - Auto-download HLS/DASH videos

3. **Test Output**:
   - `video_urls.json` - Extracted URLs
   - `playerConfig.json` - Full playerConfig dump
   - `downloaded_video.mp4` - Downloaded video file

## Next Steps

### Phase 6: Google Drive Uploader
- Implement Google Drive API integration
- Upload downloaded videos to Drive
- Track uploaded files (drive_file_id)
- Handle quota limits and retries

### Phase 7: Main Orchestration Script
- Combine all components into main workflow
- Run full crawl + download + upload pipeline
- Progress tracking and resumability
- Error recovery and logging

## Testing

To test the DOM extraction and auto-download:

```bash
source venv/bin/activate
python test_single_video_download.py
```

This will:
1. Open video page in browser
2. Extract all video URLs from DOM
3. Save URLs to `video_urls.json`
4. Automatically download the video
5. Show download progress and result

## Summary

Phase 5 successfully implemented a robust video extraction and download system that:
- Works with all video formats (progressive, HLS, DASH)
- Extracts URLs directly from DOM (more reliable)
- Automatically downloads using the best method for each format
- Handles errors and retries gracefully
- Maintains human-like behavior throughout

The system is now ready for Phase 6 (Google Drive upload) and Phase 7 (full orchestration).

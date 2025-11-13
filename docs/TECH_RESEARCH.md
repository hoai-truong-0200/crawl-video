# 🔬 Technology Research - Task 1

**Date**: 2025-11-13
**Status**: ✅ Completed

---

## 1. Browser Automation & Anti-Detection

### Selected: Playwright + Stealth Plugin

#### **playwright-stealth**
- **Package**: `playwright-stealth` (PyPI)
- **Latest Version**: June 2025 release
- **Python Support**: 3.9 - 3.12
- **Repository**: Port of puppeteer-extra-plugin-stealth

#### **Key Features**:
- Removes `navigator.webdriver` property
- Patches "HeadlessChrome" from User-Agent
- Multiple evasion modules for bot detection bypass
- Modifies browser properties automatically

#### **Limitations** (Important!):
⚠️ **Won't bypass advanced bot detection**
- Only works for simple bot detection methods
- Should be considered a proof-of-concept starting point
- Advanced anti-bot systems (Cloudflare, PerimeterX) may still detect
- Requires additional custom patches for production use

#### **Recommended Approach**:
```python
# Layered anti-detection strategy
1. playwright-stealth (base layer)
2. Custom fingerprint spoofing
3. Human behavior simulation
4. Real browser profiles with cookies
5. Residential proxies (if needed)
```

#### **Alternative Considered**:
- `undetected-playwright` - More aggressive patching
- `nodriver` - Newer framework avoiding automation protocols entirely
- **Decision**: Use playwright-stealth + custom enhancements

---

## 2. Video Download

### Selected: yt-dlp

#### **Package Details**:
- **Package**: `yt-dlp[default]` (PyPI)
- **Python Support**: 3.10+ (CPython), 3.11+ (PyPy)
- **Status**: Actively maintained (October 2025 release)
- **Repository**: https://github.com/yt-dlp/yt-dlp

#### **Vimeo Support**:
✅ **Native Vimeo support**
- Downloads from Vimeo and 1000+ other platforms
- Handles HLS (m3u8) and DASH streams
- Automatic quality selection
- Format merging with ffmpeg

#### **Best Practices for Vimeo**:
```python
# Recommended format selection
yt-dlp -f "bestvideo+bestaudio" <vimeo_url>

# With cookies for authenticated content
yt-dlp --cookies cookies.txt <url>

# Custom quality preference
yt-dlp -f "bestvideo[height<=720]+bestaudio" <url>
```

#### **Known Issues**:
⚠️ Password-protected Vimeo videos may fail (API changes)
✅ Public and authenticated videos work well

#### **Dependencies Required**:
- **ffmpeg** + **ffprobe** - CRITICAL for merging streams
- **aria2c** (optional) - Faster downloads

#### **Python API Usage**:
```python
import yt_dlp

ydl_opts = {
    'format': 'bestvideo+bestaudio',
    'outtmpl': '%(title)s.%(ext)s',
    'progress_hooks': [progress_callback],
    'cookiefile': 'cookies.txt'
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
```

---

## 3. Google Drive Upload

### Selected: Google Drive API v3 with Resumable Upload

#### **Package Details**:
- **Core Package**: `google-api-python-client>=2.100.0`
- **Auth**: `google-auth>=2.23.0`
- **OAuth2**: `google-auth-oauthlib>=1.1.0`

#### **Resumable Upload Process**:

**Step 1: Initiate Session**
```python
POST https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable

Headers:
- Authorization: Bearer <token>
- Content-Type: application/json

Body: {
  "name": "video.mp4",
  "parents": ["folder_id"]
}

Response: Location header contains session URI
```

**Step 2: Upload File**
```python
PUT <session_uri>

Headers:
- Content-Length: <file_size>
- Content-Range: bytes 0-<chunk_size>/<total_size>

Body: <file_chunk>
```

#### **Best Practices**:

✅ **Chunk Size**:
- Use chunks of 5-10 MB
- Must be multiples of 256 KB (256*1024)
- Larger chunks = faster, less overhead

✅ **Error Handling**:
- Save session URI (expires after 1 week)
- Implement retry logic with exponential backoff
- Resume from last uploaded chunk on failure

✅ **Progress Tracking**:
```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(
    filename,
    mimetype='video/mp4',
    resumable=True,
    chunksize=10*1024*1024  # 10MB
)

request = service.files().create(
    body=file_metadata,
    media_body=media
)

response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"Uploaded {int(status.progress() * 100)}%")
```

#### **For Shared Drives**:
Add `supportsAllDrives=true` query parameter

---

## 4. Supporting Libraries

### Core Dependencies:
```txt
# Browser Automation
playwright>=1.40.0
playwright-stealth>=1.0.0

# Video Download
yt-dlp>=2024.10.0

# Google Drive
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0

# HTTP Client
httpx[http2]>=0.25.0

# Human Behavior
faker>=20.0.0
numpy>=1.24.0

# Configuration
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# Logging & Progress
loguru>=0.7.0
tqdm>=4.66.0

# Retry Logic
tenacity>=8.2.0

# File Operations
aiofiles>=23.0.0
```

### System Dependencies:
```bash
# Required
ffmpeg  # Video processing
ffprobe # Stream analysis

# Optional
aria2c  # Faster downloads
```

---

## 5. Architecture Decisions

### **Browser Strategy**:
- **Headed mode** for initial login (manual authentication)
- **Save session** (cookies, localStorage) to disk
- **Reuse session** for automated crawling
- **Human behavior** simulation throughout

### **Video Detection Strategy**:
```
Option 1 (Preferred): Network Interception
├── Monitor all network requests
├── Filter Vimeo CDN URLs
├── Extract m3u8/mpd manifests
└── Pass to yt-dlp for download

Option 2 (Fallback): DOM Analysis
├── Extract video_id from page
├── Call Vimeo API/endpoints
└── Download via yt-dlp
```

### **Upload Strategy**:
```
For each video:
├── Check if already exists on Drive (skip duplicate)
├── Start resumable upload
├── Upload in 10MB chunks
├── Track progress
├── Organize into folder structure
└── Log success/failure
```

---

## 6. Risk Mitigation

### **Anti-Bot Detection**:
- ⚠️ GLOBIS may have Cloudflare or similar protection
- 🛡️ Mitigation: Stealth + human behavior + real browser session
- 🛡️ Backup: Manual CAPTCHA solving if needed

### **Rate Limiting**:
- ⚠️ Too many requests = IP ban
- 🛡️ Mitigation: Random delays (2-5s between actions)
- 🛡️ Max 10-20 requests per minute

### **Vimeo Protection**:
- ⚠️ Vimeo may use signed URLs with expiration
- 🛡️ Mitigation: Download immediately after extraction
- 🛡️ Reuse authenticated cookies

### **Google Drive Quotas**:
- ⚠️ 750 GB/day upload limit per user
- ⚠️ 10 TB total storage limit (free accounts: 15 GB)
- 🛡️ Mitigation: Track daily usage, pause if needed

---

## 7. Final Tech Stack

```yaml
Language: Python 3.10+

Core Stack:
  - Browser: Playwright + playwright-stealth
  - Video: yt-dlp + ffmpeg
  - Cloud: Google Drive API v3
  - HTTP: httpx with HTTP/2

Anti-Detection:
  - Fingerprint spoofing
  - Human behavior simulation
  - Session persistence
  - Rate limiting

Architecture:
  - Modular design (browser, crawler, downloader, uploader)
  - State management (resume capability)
  - Comprehensive logging
  - Error handling with retries
```

---

## 8. Next Steps

✅ Task 1 Complete - Technology selected and validated

**Ready for Task 2**: Create project structure
- Create folder hierarchy
- Remove old files
- Setup .gitignore

**Ready for Task 3**: Setup dependencies
- Create requirements.txt
- Setup virtual environment
- Install Playwright browsers

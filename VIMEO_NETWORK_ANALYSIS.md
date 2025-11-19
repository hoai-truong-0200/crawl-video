# Vimeo Network Analysis

## Summary

GLOBIS Unlimited uses Vimeo embedded players for video hosting. Through network request inspection, I've identified the video download URL patterns.

## Key Findings

### 1. Vimeo Player URL (Already Captured)
```
https://player.vimeo.com/video/{video_id}
```
Example: `https://player.vimeo.com/video/1117632958`

This is an iframe embed URL - NOT downloadable.

### 2. Progressive MP4 Redirect URL (NEW - Target for Interception)
```
https://player.vimeo.com/progressive_redirect/playback/{playback_id}/rendition/{quality}/file.mp4
```

Example:
```
https://player.vimeo.com/progressive_redirect/playback/954202754/rendition/720p/file.mp4?loc=external&oauth2_token_id=1612052367&signature=a7efd93117a2a094e569f45192f64aad22bbe21929df79fe921fd8ee72c7486e
```

**Response**: HTTP 302 redirect

### 3. Actual CDN Download URL (Final Target)
```
https://download-video-ak.vimeocdn.com/v3-1/playback/{uuid}/{file_id}?__token__=...
```

Example:
```
https://download-video-ak.vimeocdn.com/v3-1/playback/89d2f664-455f-4e55-ac5c-cfc961e3a166/eac4e4d2-79ce5672?__token__=st=1763402961~exp=1763406561~acl=%2Fv3-1%2Fplayback%2F89d2f664-455f-4e55-ac5c-cfc961e3a166%2Feac4e4d2-79ce5672%2A~hmac=22bc103bf22c07d6133f371953fcced3a23194259e6bf68f774006c224d96133&r=dXMtY2VudHJhbDE%3D
```

**Response**: HTTP 206 Partial Content (video chunks)

**Token Expiration**: ~1 hour (3600 seconds)

## Video Quality Options

Multiple quality renditions are available:
- `1080p` - Full HD
- `720p` - HD (seen in test)
- `540p` - SD
- `360p` - Low quality

## Interception Strategy

### Option 1: Monitor Network Requests (Recommended)
Use Playwright's network monitoring to capture:
1. Listen for requests to `progressive_redirect`
2. Extract the redirect URL from the response
3. Follow the 302 redirect to get final CDN URL

### Option 2: Direct API Call
After getting Vimeo player URL, we could potentially:
1. Extract video ID from `player.vimeo.com/video/{id}`
2. Make API call to Vimeo to get progressive URLs
3. But this may require authentication tokens

**Recommended**: Option 1 - network monitoring is simpler and more reliable.

## Implementation Plan

### VimeoInterceptor Class

```python
class VimeoInterceptor:
    def __init__(self, page: Page):
        self.page = page
        self.captured_urls = []

    async def start_interception(self):
        # Monitor network requests for progressive_redirect
        self.page.on("response", self._capture_video_url)

    async def _capture_video_url(self, response):
        # Check if URL contains progressive_redirect
        # Extract download URL
        # Store in captured_urls

    async def get_download_urls(self, vimeo_player_url: str) -> Dict[str, str]:
        # Return dict of quality -> download_url
        # { '720p': 'https://...', '1080p': 'https://...' }
```

### Integration into CourseCrawler

When visiting each video step:
1. Create VimeoInterceptor instance
2. Start network monitoring
3. Load video page (triggers Vimeo player load)
4. Wait for network requests to complete
5. Extract download URLs from interceptor
6. Save to Video object

### Enhanced Video Data Model

Add new field to Video dataclass:
```python
@dataclass
class Video:
    title: str
    url: str
    vimeo_url: str  # Player URL
    download_urls: Dict[str, str] = field(default_factory=dict)  # NEW: quality -> URL mapping
    downloaded: bool = False
    uploaded_to_drive: bool = False
    drive_file_id: str = ""
```

## Notes

- Download URLs include authentication tokens that expire
- Tokens valid for ~1 hour (may need to re-extract before downloading)
- For video downloading (Phase 6), we can use yt-dlp with the player URL directly
- yt-dlp will handle the network interception and quality selection automatically
- **Decision**: Store player URL is enough for yt-dlp, but storing download URLs provides backup option

## Conclusion

We have two paths forward:

**Path A (Simpler)**:
- Keep current implementation (just store player URL)
- Use yt-dlp to download directly from player URL
- yt-dlp handles all the complexity

**Path B (More Control)**:
- Implement VimeoInterceptor to capture direct download URLs
- Store download URLs in JSON
- Provides backup if yt-dlp fails
- More complex implementation

**Recommendation**: Start with Path A (yt-dlp), implement Path B if needed.

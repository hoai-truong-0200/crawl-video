# Phase 4 Complete: Course Video Crawler

## ✅ Đã hoàn thành

### 1. CourseParser ([src/crawler/course_parser.py](src/crawler/course_parser.py))
Class để parse course pages và extract video information:
- `parse_course_page()` - Extract tất cả steps từ sidebar
- `extract_vimeo_url()` - Extract Vimeo player URL từ iframe
- `extract_vimeo_id()` - Extract Vimeo video ID từ URL

**StepInfo dataclass** với fields:
- `title` - Step title (e.g., "Introduction")
- `url` - Step URL (e.g., "/en/courses/xxx/learn/steps/123")
- `duration` - Video duration (e.g., "01:23")
- `vimeo_url` - Vimeo player URL
- `step_id` - Step ID

### 2. CourseCrawler ([src/crawler/course_crawler.py](src/crawler/course_crawler.py))
Class để crawl tất cả courses và extract video URLs:
- Load courses từ `learn-content.json` hoặc `explore-content.json`
- Navigate đến từng course page
- Extract tất cả steps (video lessons)
- Navigate đến từng step để extract Vimeo URL
- Update JSON với video information
- Human-like behavior với random delays
- Retry logic cho failed requests
- Detailed statistics tracking

**Features:**
- ✅ Crawl tất cả courses từ JSON file
- ✅ Extract video information (title, URL, Vimeo URL)
- ✅ Save đầy đủ thông tin vào JSON
- ✅ **Human-like behavior** (scrolling, mouse movements)
- ✅ Human-like delays (1.5-3.0s)
- ✅ Retry logic (max 3 attempts)
- ✅ Detailed logging và statistics

**Human Behaviors:**
- 🖱️ **Scrolling**: Natural scroll patterns on course pages (down 300-600px, up 100-200px)
- 🖱️ **Mouse Movement**: Bezier curve movements to video players
- 🖱️ **Engagement**: Pauses to simulate reading/viewing (0.5-1.5s)
- 🖱️ **Randomization**: Variable timing to avoid detection patterns

### 3. Integration vào run_browser.py
Đã thêm mode "videos" vào [run_browser.py](run_browser.py):

**New mode: `videos`**
```bash
python3 run_browser.py videos
```
Crawl videos từ cả `learn-content.json` và `explore-content.json`

**Updated mode: `all`**
```bash
python3 run_browser.py all
```
Bây giờ crawl: Categories → Series → Videos (tất cả!)

## 📋 Video Data Structure

Mỗi video trong JSON có format:
```json
{
    "title": "Introduction",
    "url": "/en/courses/d8501fa9/learn/steps/60784",
    "vimeo_url": "https://player.vimeo.com/video/1117632958",
    "downloaded": false,
    "uploaded_to_drive": false,
    "drive_file_id": ""
}
```

## 🚀 Cách sử dụng

### Test Human Behavior (Visual Demo)
```bash
python3 test_human_behavior.py
```
**WATCH THE BROWSER!** Bạn sẽ thấy:
- ✅ Smooth scrolling (không nhảy cóc)
- ✅ Mouse di chuyển theo đường cong Bezier
- ✅ Pauses tự nhiên giữa các actions
- ✅ Timing variations realistic

### Test CourseParser
```bash
python3 test_course_parser.py
```
- Load course đầu tiên từ learn-content.json
- Extract tất cả steps
- Navigate đến step đầu tiên
- Extract Vimeo URL

### Crawl videos từ tất cả courses
```bash
python3 run_browser.py videos
```
Sẽ crawl:
1. Videos từ tất cả courses trong `learn-content.json`
2. Videos từ tất cả series trong `explore-content.json`

### Full workflow (tất cả)
```bash
python3 run_browser.py all
```
Sẽ thực hiện:
1. Crawl categories → `learn-content.json`
2. Crawl series → `explore-content.json`
3. Crawl videos từ learn-content
4. Crawl videos từ explore-content

## 📊 Statistics

CourseCrawler tracking:
- Courses crawled successfully
- Courses failed
- Total videos found
- Videos with Vimeo URL
- Videos without Vimeo URL
- Average videos per course
- Vimeo extraction success rate
- Errors encountered

## ⏭️ Next Steps

Bây giờ bạn có thể chạy:

### Option 1: Chỉ crawl videos (giả sử đã có courses)
```bash
python3 run_browser.py videos
```

### Option 2: Full crawl từ đầu
```bash
python3 run_browser.py all
```

Sau khi crawl xong, JSON files sẽ có đầy đủ:
- ✅ Categories
- ✅ Courses
- ✅ Videos với title, URL, và Vimeo URL

## 🎯 Ready for Phase 5

Phase 4 hoàn thành! Bây giờ có đầy đủ video URLs.

**Phase 5 - Network Interception** sẽ:
- Intercept network requests để bắt actual video download URLs
- Extract m3u8/mp4 URLs từ Vimeo
- Prepare cho video download

Nhưng trước tiên, hãy test video crawling!

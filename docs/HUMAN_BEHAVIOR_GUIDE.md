# 🖱️ Human Behavior Implementation Guide

## Overview

CourseCrawler đã được tích hợp với **HumanBehavior** để simulate hành vi người dùng thật khi duyệt courses và videos, giúp tránh bị phát hiện bởi anti-bot systems.

## 🎯 Behaviors Implemented

### 1. Course Page Behavior

Khi navigate đến course page, crawler sẽ:

**a) Scroll Down (300-600px)**
- Mô phỏng việc xem course overview
- Random scroll amount để tự nhiên hơn
- Sử dụng natural scrolling với pauses

**b) Reading Pause (0.8-1.5s)**
- Pause như đang đọc course description
- Random duration để không bị detect pattern

**c) Scroll Up (100-200px)**
- Mô phỏng việc đọc lại thông tin
- Natural reading pattern
- Tạo realistic user flow

### 2. Step/Video Page Behavior

Khi navigate đến từng video step:

**a) Mouse Movement to Video Player**
- Tự động detect Vimeo iframe player
- Calculate center position của player
- Move mouse đến player với Bezier curve
- Smooth, human-like cursor movement

**b) Viewing Pause (0.5-1.0s)**
- Pause như đang xem video preview
- Simulate hover trên player
- Random duration

**c) Engagement Scroll (100-200px)**
- Small scroll để simulate engagement
- Shows interest in content
- Natural exploration behavior

## 🔧 Configuration

### Enable/Disable Human Behavior

```python
from src.crawler.course_crawler import CourseCrawler

# With human behavior (default)
crawler = CourseCrawler(
    content_file="data/courses/learn-content.json",
    enable_human_behavior=True  # Default
)

# Without human behavior (faster, but riskier)
crawler = CourseCrawler(
    content_file="data/courses/learn-content.json",
    enable_human_behavior=False
)
```

### Custom HumanBehavior Instance

```python
from src.browser.human_behavior import HumanBehavior
from src.crawler.course_crawler import CourseCrawler

# Create custom human behavior
human = HumanBehavior()

# Pass to crawler
crawler = CourseCrawler(
    content_file="data/courses/learn-content.json",
    human_behavior=human
)
```

## 📊 Timing Breakdown

### Per Course (without videos)
- Navigation: ~2-3s
- Page settle: 1.5-2.5s
- Human behavior: 2-4s
  - Scroll down: ~1s
  - Reading pause: 0.8-1.5s
  - Scroll up: ~0.5s
- **Total: ~6-10s per course page**

### Per Video Step
- Navigation: ~1-2s
- Player load: 1.0-2.0s
- Human behavior: 1.5-3s
  - Mouse movement: ~0.5-1s
  - Viewing pause: 0.5-1.0s
  - Engagement scroll: ~0.5-1s
- **Total: ~4-7s per video step**

### Example: Course with 10 videos
- Course page: ~8s
- 10 video steps: 10 × 5.5s = 55s
- Delays between steps: 10 × 1.2s = 12s
- **Total: ~75s (~1.25 minutes) per course**

## 🎭 Behavior Patterns

### Natural Reading Pattern
```
1. Arrive at page
2. Wait for page load (1.5-2.5s)
3. Scroll down to read content (300-600px)
4. Pause to read (0.8-1.5s)
5. Scroll up slightly (100-200px) - rereading
6. Start interacting with elements
```

### Video Engagement Pattern
```
1. Navigate to video step
2. Wait for player load (1-2s)
3. Move mouse to video player (Bezier curve)
4. Pause on player (0.5-1s) - preview/hover
5. Small scroll for engagement (100-200px)
6. Extract video information
```

## 🛡️ Anti-Detection Benefits

### Why This Works

1. **Variable Timing**
   - No fixed delays → Hard to detect patterns
   - Random ranges mimic human variability
   - Natural pauses between actions

2. **Realistic Mouse Movement**
   - Bezier curves (not straight lines)
   - Speed variations
   - Human-like acceleration/deceleration

3. **Natural Scrolling**
   - Multiple small scrolls (not instant)
   - Random pause intervals
   - Bidirectional (up/down) patterns

4. **Engagement Signals**
   - Mouse hovers on interactive elements
   - Scrolling shows content consumption
   - Pauses indicate reading/viewing

## 🧪 Testing

### Test với 1 course
```bash
python3 test_single_course_crawl.py
```
Watch the browser to see human-like behaviors in action:
- Smooth scrolling
- Mouse movements to video players
- Natural pauses

### Full crawl với behavior
```bash
python3 run_browser.py videos
```

## 📝 Logging

Human behavior actions are logged at DEBUG level:

```
🖱️  Simulating human behavior on course page...
      Could not move mouse to video player: ...
```

Set log level to DEBUG to see detailed behavior:
```python
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="DEBUG")
```

## ⚙️ Advanced Customization

### Adjust Scroll Amounts
Edit [src/crawler/course_crawler.py](src/crawler/course_crawler.py:199-213):
```python
# Course page - increase for more scrolling
await self.human_behavior.natural_scroll(
    page,
    scroll_amount=random.randint(300, 600),  # Increase range
    direction="down"
)

# Step page - decrease for subtle movement
await self.human_behavior.natural_scroll(
    page,
    scroll_amount=random.randint(50, 100),  # Decrease range
    direction="down"
)
```

### Adjust Mouse Movement Speed
Edit [src/browser/human_behavior.py](src/browser/human_behavior.py):
```python
# Slower, more cautious movement
duration = random.uniform(1000, 2000)  # ms

# Faster, confident movement
duration = random.uniform(300, 600)  # ms
```

## 🎬 Visual Demo

When running with `headless=False`, you'll see:
- ✅ Page scrolls smoothly (not instant jumps)
- ✅ Mouse cursor moves in curves (not teleporting)
- ✅ Natural pauses between actions
- ✅ Realistic timing variations

## 🔍 Troubleshooting

### Behavior Too Slow?
```python
# Reduce delays
crawler = CourseCrawler(
    min_delay=0.5,
    max_delay=1.0,
    enable_human_behavior=True  # Still safe with shorter delays
)
```

### Want Faster Crawling?
```python
# Disable human behavior (not recommended)
crawler = CourseCrawler(
    enable_human_behavior=False
)
```

### Mouse Movement Errors?
Check logs for:
```
Could not move mouse to video player: ...
```
This is normal - crawler continues without movement if player not found.

## 📚 Related Files

- [src/browser/human_behavior.py](src/browser/human_behavior.py) - HumanBehavior class
- [src/crawler/course_crawler.py](src/crawler/course_crawler.py) - CourseCrawler with behaviors
- [src/browser/timing.py](src/browser/timing.py) - Timing configurations

## 🎯 Best Practices

1. **Always enable human behavior** for production crawling
2. **Use headless=False** during testing to verify behaviors
3. **Monitor logs** for behavior execution
4. **Adjust timing** based on website responsiveness
5. **Don't disable** behaviors unless absolutely necessary

---

**Last Updated**: 2025-11-17
**Status**: Active and tested

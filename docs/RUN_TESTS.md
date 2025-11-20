# 🧪 Hướng dẫn Test Phase 1 & Phase 2

## Mục tiêu

Test thực tế các module đã implement trong Phase 1 và Phase 2:
- Phase 1: Kiểm tra dependencies
- Phase 2: Test browser automation với anti-detection

## Bước 1: Cài đặt Dependencies

### 1.1. Tạo Virtual Environment

```bash
cd /home/jesterjz/workspace/work/crawl-video

# Tạo virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate
```

### 1.2. Cài đặt Python Packages

```bash
# Upgrade pip
pip install --upgrade pip

# Cài tất cả dependencies
pip install -r requirements.txt
```

**Thời gian ước tính**: 2-5 phút

### 1.3. Cài đặt Playwright Browsers

```bash
# Cài Chromium browser
playwright install chromium
```

**Thời gian ước tính**: 1-2 phút

### 1.4. Cài ffmpeg (Optional - cho Phase 4)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg

# Hoặc kiểm tra nếu đã cài
ffmpeg -version
```

## Bước 2: Verify Setup

Chạy script verification:

```bash
python3 verify_setup.py
```

**Expected Output**:
```
✅ All checks PASSED!
```

Nếu có lỗi, xem [docs/SETUP.md](docs/SETUP.md) để troubleshoot.

## Bước 3: Run Tests

### Test Level 1: Dependencies Only (Nhanh)

```bash
# Test imports only (không cần browser)
python3 test_phase1_phase2.py
```

Script sẽ test:
- ✅ Phase 1: Import tất cả dependencies
- ✅ Phase 2.1: Fingerprinting module
- ✅ Phase 2.2: Timing & Delays module
- ✅ Phase 2.3: Browser Manager initialization
- ✅ Phase 2.4: Live browser test với example.com

### Test Level 2: Individual Modules

#### Test Fingerprinting:

```python
python3 -c "
import asyncio
from src.browser.fingerprint import FingerprintGenerator

gen = FingerprintGenerator()
fp = gen.generate()

print('Generated Fingerprint:')
print(f'  User Agent: {fp.user_agent[:60]}...')
print(f'  Viewport: {fp.viewport_width}x{fp.viewport_height}')
print(f'  Timezone: {fp.timezone}')
print(f'  Language: {fp.language}')
"
```

#### Test Timing:

```python
python3 -c "
import asyncio
from src.browser.timing import DelayManager, ActionType

async def test():
    manager = DelayManager()
    print('Testing delays...')

    delay = await manager.wait(ActionType.CLICK)
    print(f'Click delay: {delay:.3f}s')

    delay = await manager.wait(ActionType.READING)
    print(f'Reading delay: {delay:.3f}s')

asyncio.run(test())
"
```

### Test Level 3: Browser Automation (Đầy đủ)

Chạy example usage:

```bash
cd /home/jesterjz/workspace/work/crawl-video
python3 -m src.browser.example_usage
```

Hoặc tạo test script riêng:

```python
# test_browser.py
import asyncio
from src.browser.browser_manager import BrowserManager

async def main():
    async with BrowserManager(headless=False) as browser:
        # Navigate to test page
        await browser.navigate_to("https://www.google.com")

        # Simulate reading
        await browser.read_page(min_duration=2, max_duration=3)

        # Scroll
        await browser.scroll_page("down", distance=500)

        print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

```bash
python3 test_browser.py
```

## Bước 4: Kiểm tra Anti-Detection

### Test 1: Check WebDriver Flag

```python
python3 -c "
import asyncio
from src.browser.browser_manager import BrowserManager

async def check_webdriver():
    async with BrowserManager(headless=True) as browser:
        page = browser.get_page()
        await page.goto('https://www.example.com')

        # Check navigator.webdriver
        webdriver = await page.evaluate('navigator.webdriver')
        print(f'navigator.webdriver = {webdriver}')

        if webdriver is None or webdriver is False:
            print('✅ WebDriver flag properly hidden')
        else:
            print('❌ WebDriver flag detected!')

asyncio.run(check_webdriver())
"
```

### Test 2: Bot Detection Sites

Truy cập các trang test bot detection:

```python
import asyncio
from src.browser.browser_manager import BrowserManager

async def test_bot_detection():
    async with BrowserManager(headless=False) as browser:
        # Test sites (chọn 1)
        test_urls = [
            "https://bot.sannysoft.com/",
            "https://arh.antoinevastel.com/bots/areyouheadless",
            "https://pixelscan.net/",
        ]

        await browser.navigate_to(test_urls[0])

        # Wait để xem kết quả
        import time
        time.sleep(10)

        print("Check the browser window for detection results")

asyncio.run(test_bot_detection())
```

## Expected Results

### ✅ Successful Output:

```
============================================================
TEST SUMMARY
============================================================
Phase 1: Dependencies: ✅ PASSED
Phase 2.1: Fingerprinting: ✅ PASSED
Phase 2.2: Timing: ✅ PASSED
Phase 2.3: Browser Init: ✅ PASSED
Phase 2.4: Live Browser: ✅ PASSED

Total: 5/5 tests passed (100.0%)

🎉 ALL TESTS PASSED!
```

### Browser Window Should Show:

- No "Chrome is being controlled by automated software" banner
- Normal website rendering
- Smooth scrolling and mouse movements
- Human-like timing

### Anti-Detection Should Show:

On bot detection sites:
- ✅ `navigator.webdriver` = undefined/false
- ✅ No automation indicators
- ✅ Realistic browser fingerprint
- ✅ Human-like behavior patterns

## Troubleshooting

### Issue: "playwright: command not found"

```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall
pip install playwright
playwright install chromium
```

### Issue: "ImportError: No module named 'src'"

```bash
# Make sure you're in project root
cd /home/jesterjz/workspace/work/crawl-video

# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run with python -m
python3 -m test_phase1_phase2
```

### Issue: Browser fails to start

```bash
# Install system dependencies
playwright install-deps chromium

# Or use system Chrome
# (modify browser_manager.py to use channel='chrome')
```

### Issue: Timeouts

```bash
# Increase timeouts in .env
BROWSER_TIMEOUT=60000
PAGE_TIMEOUT=30000
```

## Performance Benchmarks

Expected timing for test suite:

- Dependencies test: < 1s
- Fingerprinting test: < 0.1s
- Timing test: 2-5s (includes delays)
- Browser init test: 1-2s
- Live browser test: 5-10s

**Total**: ~10-20 seconds

## Next Steps

Sau khi tất cả tests pass:

1. ✅ Verify anti-detection effectiveness
2. ✅ Test manual login flow (if needed)
3. ✅ Save session for reuse
4. 🔄 Ready for Phase 3: Crawling implementation

## Logs

Test logs được lưu tại:
- `logs/test_phase1_phase2.log` - Detailed debug logs
- Console output - Summary results

Xem logs để debug:
```bash
tail -f logs/test_phase1_phase2.log
```

---

**Created**: 2025-11-13
**Last Updated**: 2025-11-13

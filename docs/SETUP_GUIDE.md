# Setup Guide - GLOBIS Unlimited Crawler

**Last Updated:** 2025-11-24

---

## 📋 Prerequisites

1. **Python 3.8+**
2. **Chrome browser** installed
3. **Playwright** installed
4. **GLOBIS Unlimited account** (for login)

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 2: Copy Chrome Profile (QUAN TRỌNG!)

**Mục đích**: Giữ session đăng nhập giữa các lần chạy

**Cách thực hiện:**

1. Đóng TẤT CẢ cửa sổ Chrome đang mở
2. Chạy lệnh:

```bash
python run_browser.py test
```

**Script sẽ tự động:**
- Copy Chrome profile từ `~/.config/google-chrome/Profile 1`
- Đến `data/chrome_profile_copy/`
- Hiển thị size của profile

**Output mẫu:**
```
📋 Copying Chrome profile...
   From: /home/user/.config/google-chrome/Profile 1
   To:   data/chrome_profile_copy
   Size: 245M
✅ Chrome profile copied successfully
```

**Lưu ý:**
- Chỉ cần copy **1 LẦN DUY NHẤT**
- Nếu đã tồn tại, script sẽ skip bước này
- Profile size thường ~200-300MB

### Step 3: Login Lần Đầu

Sau khi copy profile, Chrome sẽ mở tự động:

1. Trình duyệt sẽ mở trang GLOBIS
2. **Đăng nhập thủ công** với tài khoản của bạn
3. Chờ đến khi thấy trang chủ GLOBIS
4. Session sẽ được lưu tự động

**Session được lưu tại:**
- Browser cookies: trong `data/chrome_profile_copy/`
- Session JSON: `data/sessions/globis_session.json`

### Step 4: Verify Setup

```bash
# Test single category
python run_browser.py test
```

**Kết quả mong đợi:**
```
✅ Chrome profile already exists
✅ Chrome launched with persistent context
✅ Stealth mode applied
✅ Already logged in (session found)
✅ Test complete
```

### Step 5: Run Production Crawl

```bash
# Crawl everything
python run_browser.py all
```

---

## 📁 Directory Structure

Sau khi setup, cấu trúc thư mục:

```
crawl-video/
├── data/
│   ├── chrome_profile_copy/    # Chrome profile (copied once)
│   │   ├── Default/
│   │   ├── Local State
│   │   └── ...
│   ├── sessions/
│   │   └── globis_session.json # Login session
│   └── courses/
│       ├── en/
│       │   ├── learn-content.json
│       │   └── explore-content.json
│       └── ja/
│           ├── learn-content.json
│           └── explore-content.json
├── downloads/
│   ├── en/
│   │   └── {Category}/
│   │       └── {Course}/
│   │           ├── overview.txt
│   │           ├── transcript.txt
│   │           └── {LearnPoint}/
│   │               └── {Video}.mp4
│   └── ja/
│       └── ... (same structure)
└── logs/
    └── {YYYY-MM-DD}.log
```

---

## 🔧 Chrome Profile Details

### Tại sao cần copy Chrome profile?

1. **Giữ session đăng nhập**: Không cần login lại mỗi lần chạy
2. **Cookies persistence**: Cookies được lưu giữa các lần chạy
3. **Anti-bot**: Profile thực giúp bypass anti-bot tốt hơn
4. **Extensions**: Giữ các extensions nếu có

### Source Profile Location

**Linux:**
```
~/.config/google-chrome/Profile 1
```

**macOS:**
```
~/Library/Application Support/Google/Chrome/Profile 1
```

**Windows:**
```
C:\Users\{YourName}\AppData\Local\Google\Chrome\User Data\Profile 1
```

### Destination Profile

```
data/chrome_profile_copy/
```

### Nếu Source Profile không tồn tại

Script sẽ liệt kê tất cả profiles có sẵn:

```
❌ Source Chrome profile not found
Available Chrome profiles:
  - Default
  - Profile 1
  - Profile 2
```

**Cách fix:**
1. Mở file `run_browser.py`
2. Tìm dòng: `SOURCE_PROFILE = Path.home() / ".config/google-chrome/Profile 1"`
3. Đổi `Profile 1` thành profile bạn muốn (ví dụ: `Default`)

---

## 🔐 Login Process

### Lần đầu tiên (Manual Login)

```bash
python run_browser.py test
```

1. Chrome mở → Trang login GLOBIS
2. **Bạn đăng nhập thủ công**
3. Script detect login thành công
4. Session được lưu

**Console output:**
```
🔐 STEP 3: Check/Handle Login
⏳ Waiting for login...
   Please login manually in the browser
   Checking every 5 seconds...
✅ Login successful!
📝 Session saved to: data/sessions/globis_session.json
```

### Lần sau (Auto Login)

```bash
python run_browser.py categories
```

Script tự động:
1. Load Chrome profile (có cookies)
2. Mở GLOBIS
3. **Tự động đăng nhập** (session còn hạn)
4. Bắt đầu crawl

**Console output:**
```
🔐 STEP 3: Check/Handle Login
✅ Already logged in (session found)
```

### Session Expiration

Nếu session hết hạn (sau ~24-48h):

```
⚠️  Session may have expired
⏳ Waiting for manual login...
```

**Cách fix:**
1. Đăng nhập lại thủ công trong browser
2. Script sẽ lưu session mới
3. Tiếp tục crawl

Hoặc xóa session cũ:
```bash
rm data/sessions/globis_session.json
python run_browser.py test  # Login lại
```

---

## 🛡️ Anti-Bot Protection

### 5 Layers Protection

1. **Persistent Chrome Profile**
   - Sử dụng profile thực của Chrome
   - Cookies và history tự nhiên

2. **Browser Launch Arguments (30+ flags)**
   ```
   --disable-blink-features=AutomationControlled
   --exclude-switches=enable-automation
   --disable-dev-shm-usage
   ... (27 more)
   ```

3. **JavaScript Patches**
   ```javascript
   delete navigator.webdriver
   window.chrome = { runtime: {} }
   navigator.plugins = [1, 2, 3, 4, 5]
   ```

4. **Stealth Mode (playwright-stealth)**
   - Remove automation indicators
   - Realistic browser fingerprint

5. **Fingerprint Randomization**
   - User agent rotation
   - Viewport randomization
   - Timezone settings

### Verification

Trong browser console (F12):
```javascript
console.log(navigator.webdriver)  // undefined (not false!)
console.log(window.chrome)        // { runtime: {} }
console.log(navigator.plugins)    // [1, 2, 3, 4, 5]
```

**Kết quả mong đợi:**
```
✅ navigator.webdriver: undefined
✅ window.chrome: exists
✅ No CAPTCHA
✅ No bot detection
```

---

## 🚀 Usage Commands

### Test & Setup

```bash
# First time setup + test
python run_browser.py test

# Test with existing session
python run_browser.py test
```

### Individual Options

```bash
# Crawl categories only
python run_browser.py categories

# Crawl series only
python run_browser.py series

# Crawl course details (overview, transcript, duration)
python run_browser.py courses

# Crawl videos (with LearnPoint structure)
python run_browser.py videos

# Download videos (Phase 4 - TODO)
python run_browser.py downloads
```

### Full Workflow

```bash
# Crawl everything: categories → series → courses → videos
python run_browser.py all
```

**Workflow steps:**
1. Crawl categories → `data/courses/en/learn-content.json`
2. Wait 10 seconds
3. Crawl series → `data/courses/en/explore-content.json`
4. Wait 10 seconds
5. Crawl course details (overview, transcript, duration)
6. Wait 10 seconds
7. Crawl videos (with LearnPoint structure)

**Estimated time:**
- Categories: ~5-10 minutes
- Series: ~5-10 minutes
- Course details: ~30-60 minutes (depending on # of courses)
- Videos: ~30-60 minutes

**Total:** ~1-2 hours for full workflow

### Test Scripts

```bash
# Test categories
python tests/test_categories.py

# Test series
python tests/test_series.py

# Test course details
python tests/test_courses.py

# Test videos
python tests/test_videos.py
```

---

## 🔍 Troubleshooting

### Problem 1: Chrome profile not found

**Error:**
```
❌ Source Chrome profile not found: ~/.config/google-chrome/Profile 1
```

**Solution:**
```bash
# List available profiles
ls ~/.config/google-chrome/

# Update SOURCE_PROFILE in run_browser.py
# Change to: "Default" or "Profile 2", etc.
```

### Problem 2: Session expired

**Error:**
```
⚠️  Session may have expired
Page redirected to: /error
```

**Solution:**
```bash
# Delete old session
rm data/sessions/globis_session.json

# Re-run and login again
python run_browser.py test
```

### Problem 3: Browser not opening

**Error:**
```
Playwright not installed
```

**Solution:**
```bash
# Install Playwright
pip install playwright

# Install browsers
playwright install chromium
```

### Problem 4: Permission denied

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Close all Chrome windows
killall chrome

# Re-run
python run_browser.py test
```

### Problem 5: CORS errors in console

**These are NORMAL!**
```
Access to font at 'https://fonts.gstatic.com/...' blocked by CORS
Access to fetch at 'https://api.unlimited.globis.co.jp/...' blocked
```

**Explanation:**
- Browser security restrictions
- Do NOT affect scraping
- Can be safely ignored

---

## 📊 Output Files

### JSON Files

**learn-content.json:**
```json
{
  "language": "en",
  "last_updated": "2025-11-24T10:30:00",
  "categories": [
    {
      "title": "Critical Thinking",
      "url": "/en/categories/critical-thinking",
      "last_updated": "2025-11-24T10:30:00",
      "courses": [
        {
          "title": "Business Proposals",
          "url": "/en/courses/d8501fa9/learn/steps",
          "overview": "en/Critical Thinking/Business Proposals/overview.txt",
          "transcript": "en/Critical Thinking/Business Proposals/transcript.txt",
          "duration": 7,
          "last_updated": "2025-11-24T10:35:00",
          "learning_points": [
            {
              "title": "Default",
              "videos": [
                {
                  "title": "Introduction",
                  "url": "/en/courses/d8501fa9/learn/steps/60784",
                  "vimeo_url": "https://player.vimeo.com/video/123456",
                  "learning_point": "Default",
                  "downloaded": false,
                  "download_path": "",
                  "last_updated": "2025-11-24T10:36:00"
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

### Text Files

**overview.txt:**
```
Business proposals are more than just formal documents...
```

**transcript.txt:**
```
Business Proposals
Introduction
Ken, do you have five minutes? I need a miracle...
```

---

## 💡 Best Practices

### 1. First Time Setup
- Run `python run_browser.py test` first
- Login manually when browser opens
- Wait for "Login successful" message
- Session will be saved automatically

### 2. Regular Usage
- Use specific options when possible (not always `all`)
- Check logs for warnings/errors
- Monitor disk space for text files

### 3. Session Management
- Session lasts ~24-48 hours
- Delete old session if login fails
- Re-login when needed

### 4. Anti-Bot
- Don't run too frequently (wait 10+ seconds between requests)
- Use human-like delays (already implemented)
- Monitor for CAPTCHA (should never appear)

### 5. Data Management
- Backup JSON files regularly
- Check output files for accuracy
- Review logs for any issues

---

## 📚 Additional Documentation

- [TODO_NEW_STRUCTURE.md](TODO_NEW_STRUCTURE.md) - Full task list
- [TODO_FINAL.md](TODO_FINAL.md) - Consolidated requirements
- [QUICK_START.md](../QUICK_START.md) - Quick commands reference
- [BROWSER_ANTI_BOT_PROTECTION.md](BROWSER_ANTI_BOT_PROTECTION.md) - Anti-bot details
- [PHASE3_COMPLETION_REPORT.md](PHASE3_COMPLETION_REPORT.md) - Phase 3 report

---

**Setup Complete!** 🎉

Now you can run:
```bash
python run_browser.py all
```

Happy crawling! 🚀

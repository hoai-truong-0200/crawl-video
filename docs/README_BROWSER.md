# GLOBIS Browser Automation

## Quick Start

**Single command to run:**
```bash
python3 run_browser.py
```

## What It Does

### First Run (One-Time Setup):
1. ✅ Copies your Chrome profile (`~/.config/google-chrome/Profile 1` → `data/chrome_profile_copy`)
2. ✅ Launches Chrome with anti-bot protection
3. ✅ Opens login page - **You login manually**
4. ✅ Saves session permanently
5. ✅ Tests browsing first category from `learn-content.json`

### Subsequent Runs:
1. ✅ Uses existing profile copy (no re-copy needed)
2. ✅ Launches Chrome with anti-bot protection
3. ✅ **No login needed** - session persists!
4. ✅ Browses category page

## Features

### ✅ Anti-Bot Protection
- Removes `--enable-automation` flag
- Overrides `navigator.webdriver` → `undefined`
- Injects stealth scripts for:
  - Chrome runtime
  - Permissions API
  - Navigator plugins
  - Languages
- 30+ stealth launch arguments

### ✅ Chrome Profile Integration
- Uses your real Chrome profile (copied)
- Session persists across runs
- Cookies, extensions, history preserved
- No conflict with your running Chrome

### ✅ Simple & Clean
- **One file**: `run_browser.py`
- No complex setup
- Self-contained workflow
- Easy to modify

## Workflow

```
┌──────────────────────────────┐
│ 1. Copy Chrome Profile       │ (Only first time)
│    (513MB, takes ~35 seconds) │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│ 2. Launch Chrome             │
│    + Anti-bot protection     │
│    + Stealth scripts         │
│    + 30 launch arguments     │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│ 3. Check Login Status        │
└─────────┬────────────────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
 Logged In   Not Logged In
    │           │
    │           ├─→ Navigate to login page
    │           ├─→ Wait for manual login (10 min timeout)
    │           └─→ Save session
    │
    └─────┬─────┘
          │
          ▼
┌──────────────────────────────┐
│ 4. Test Category Browsing    │
│    - Load first category URL │
│    - Navigate & check status │
│    - Find course elements    │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│ 5. Keep Browser Open         │
│    - Manual inspection       │
│    - Press Ctrl+C to exit    │
└──────────────────────────────┘
```

## Configuration

Edit these variables in `run_browser.py`:

```python
# Chrome profile paths
SOURCE_PROFILE = Path.home() / ".config/google-chrome/Profile 1"  # Change if different
DEST_PROFILE = Path("data/chrome_profile_copy")

# GLOBIS URLs
LOGIN_URL = "https://unlimited.globis.co.jp/signin?locale=en"
SUCCESS_INDICATOR = "a[href*='signout']"  # Selector for logged-in state

# Content file
CONTENT_FILE = Path("data/courses/learn-content.json")
```

## Troubleshooting

### "Source Chrome profile not found"
- Check which Chrome profile you use: `ls ~/.config/google-chrome/`
- Update `SOURCE_PROFILE` in `run_browser.py`

### "Login timeout"
- Login within 10 minutes
- Check console for errors
- Verify selector `a[href*='signout']` is correct

### Chrome warnings about flags
- These are normal and don't affect functionality
- Warnings like "unsupported flag" can be ignored

### Anti-detection not working
- Open DevTools (F12) in the browser
- Run in console: `console.log(navigator.webdriver)`
- Should show: `undefined` (not `true`)

## File Structure

```
.
├── run_browser.py              # Main file - run this!
├── data/
│   ├── chrome_profile_copy/    # Chrome profile (gitignored)
│   └── courses/
│       └── learn-content.json  # Category/course data
└── src/
    └── browser/
        └── stealth_config.py   # Anti-bot configurations
```

## Future Updates

All future changes should be made in `run_browser.py` only:
- Add new features
- Modify workflow steps
- Update configuration
- Change selectors

**No need for multiple test files!**

## Anti-Detection Techniques Applied

1. **Launch Arguments**:
   - `--disable-blink-features=AutomationControlled`
   - `--exclude-switches=enable-automation`
   - 28 other stealth flags

2. **Ignored Default Args**:
   - `--enable-automation` (removed)
   - `--no-sandbox` (removed - unsupported)
   - `--disable-setuid-sandbox` (removed - unsupported)

3. **JavaScript Injection**:
   ```javascript
   navigator.webdriver → undefined
   window.chrome.runtime → {}
   navigator.plugins → [1,2,3,4,5]
   navigator.languages → ['en-US', 'en']
   ```

4. **User Agent**:
   - Chrome 131.0.0.0 on Windows 10

5. **Chrome Profile**:
   - Real user profile with history
   - Realistic browsing patterns
   - Persistent cookies & sessions

## Success Indicators

✅ **Browser launches without errors**
✅ **Console shows: `navigator.webdriver: undefined`**
✅ **No "controlled by automated software" message**
✅ **Login session persists across runs**
✅ **Can browse categories without re-login**

---

**Last Updated**: 2025-11-16
**Version**: 1.0

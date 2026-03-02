#!/usr/bin/env python3
"""
GLOBIS Browser Automation with Chrome Profile

WORKFLOW:
1. Launch Chrome with anti-bot protection (stealth mode)
2. Manual login (if needed) - ONLY ONCE, session persists in Chrome profile
3. Choose mode to crawl different levels of content

AVAILABLE MODES:
┌─────────────┬──────────────────────────────────────────────────────────────┐
│ sites       │ Parse initial categories/series lists from sites.json URLs   │
│             │ - Auto-clicks "Show More" buttons to load all items           │
│             │ - Saves to learn-content.json & explore-content.json          │
│             │ - Supports multi-language (en/ja)                             │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ categories  │ Crawl detailed info for each category (learn-content)        │
│             │ - Gets course count, description, image                       │
│             │ - Auto-clicks "Show More" to load all courses                 │
│             │ - Saves incrementally after each category                     │
│             │ - Skip if updated < 14 days AND has courses                   │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ series      │ Crawl detailed info for each series (explore-content)        │
│             │ - Gets course count, description, image                       │
│             │ - Auto-clicks "Show More" to load all courses                 │
│             │ - Saves incrementally after each series                       │
│             │ - Skip if updated < 14 days AND has courses                   │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ courses     │ Crawl course details (learning_points + videos)              │
│             │ - Extracts: duration + learning_points + videos               │
│             │ - Clicks "Content" tab to parse learning point structure      │
│             │ - Groups videos by learning objectives                        │
│             │ - Saves incrementally after each course                       │
│             │ - Skip if updated < 14 days AND has learning_points           │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ content     │ Extract video content (overview + transcript)                │
│             │ - Navigate to individual video step pages                     │
│             │ - Extract overview and transcript text                        │
│             │ - Save to downloads/[lang]/[categories|series]/[title]/      │
│             │ - Files: overview.txt, transcript.txt                         │
│             │ - Skip if is_content = true                                   │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ downloads   │ Download videos using Vimeo URLs                             │
│             │ - Progressive MP4 with progress tracking                      │
│             │ - HLS/DASH with yt-dlp                                        │
│             │ - Save to downloads/[lang]/[categories|series]/[title]/[lp]/ │
│             │ - Skip if is_downloaded = true                                │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ all         │ Run full workflow: sites → categories → series → courses     │
│             │ → content → downloads                                         │
└─────────────┴──────────────────────────────────────────────────────────────┘

USAGE:
    python3 run_browser.py sites            # Parse initial lists (all languages)
    python3 run_browser.py sites en         # Parse English only
    python3 run_browser.py sites ja         # Parse Japanese only

    python3 run_browser.py categories       # Crawl all categories (learn-content)
    python3 run_browser.py categories en    # Crawl English categories only
    python3 run_browser.py categories ja    # Crawl Japanese categories only

    python3 run_browser.py series           # Crawl all series (explore-content)
    python3 run_browser.py series en        # Crawl English series only
    python3 run_browser.py series ja        # Crawl Japanese series only

    python3 run_browser.py courses          # Crawl all courses (all languages)
    python3 run_browser.py courses en       # Crawl English courses only
    python3 run_browser.py courses ja       # Crawl Japanese courses only

    python3 run_browser.py content          # Extract video content (all languages)
    python3 run_browser.py content en       # Extract English video content
    python3 run_browser.py content ja       # Extract Japanese video content
    python3 run_browser.py downloads        # Download videos
    python3 run_browser.py downloads en     # Download English videos only
    python3 run_browser.py all              # Full workflow

FEATURES:
- Auto-initialization: JSON files auto-created with correct structure if empty
- Incremental saving: Data saved after each item to prevent loss on errors
- Show More handling: Automatically clicks "Show More" buttons to load all content
- Multi-language: Supports English (en) and Japanese (ja) with ISO 639-1 codes
- Stealth mode: Anti-bot detection with human-like behavior simulation

DATA FILES:
- data/courses/sites.json: Source URLs for categories and series
- data/courses/en/learn-content.json: English categories and courses
- data/courses/en/explore-content.json: English series and courses
- data/courses/ja/learn-content.json: Japanese categories and courses
- data/courses/ja/explore-content.json: Japanese series and courses

PROFILE MANAGEMENT:
- Use 'init' mode to copy Chrome profile with cookies and sessions
- Supports interactive profile selection
- Preserves authentication state for future runs
"""

import asyncio
import shutil
import json
import sys
import random
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from src.browser.stealth_config import (
    get_browser_launch_args,
    apply_stealth_to_page
)
from src.crawler.category_parser import CategoryParser
from src.crawler.category_crawler import CategoryCrawler
from src.crawler.series_crawler import SeriesCrawler
from src.crawler.course_crawler import CourseCrawler
from src.crawler.content_manager import ContentManager, Category, Series
from src.utils.sites_manager import SitesManager
from src.utils.logger_config import setup_logger
from src.downloader.vimeo_extractor import VimeoExtractor
from src.downloader.video_downloader import VideoDownloader

# Setup logger
logger = setup_logger(
    log_dir="logs",
    app_name="crawl",
    console_level="INFO",
    file_level="DEBUG"
)


# ============================================================
# CONFIGURATION
# ============================================================

# Chrome profile path (destination for copied profile)
DEST_PROFILE = Path("data/chrome_profile")

# GLOBIS URLs
LOGIN_URL = "https://unlimited.globis.co.jp/signin?locale=en"
SUCCESS_INDICATOR = "a[href*='signout']"  # Element visible when logged in

# Content files (default to English)
LEARN_CONTENT_FILE = Path("data/courses/en/learn-content.json")
EXPLORE_CONTENT_FILE = Path("data/courses/en/explore-content.json")


# ============================================================
# STEP 1: COPY CHROME PROFILE
# ============================================================

def copy_chrome_profile() -> bool:
    """
    Copy Chrome profile using ChromeProfileManager

    If profile already exists, skip.
    Otherwise, prompt user to select a profile interactively.

    Returns:
        True if profile exists or copied successfully, False otherwise
    """
    from src.browser.profile_manager import ChromeProfileManager

    # Check if profile already exists
    if DEST_PROFILE.exists():
        logger.info(f"✅ Chrome profile already exists: {DEST_PROFILE}")
        return True

    # Profile doesn't exist, need to copy
    logger.info("📋 Chrome profile not found, need to copy from existing profile")
    logger.info("")

    # Create profile manager
    profile_manager = ChromeProfileManager(dest_profile=DEST_PROFILE)

    # Interactive profile selection
    source_profile = profile_manager.select_profile_interactive()

    if not source_profile:
        logger.error("❌ No profile selected")
        logger.info("\nTo copy a profile later, run: python3 run_browser.py init")
        return False

    # Copy profile
    success = profile_manager.copy_profile(source_profile, force=False)

    if success:
        logger.info("✅ Chrome profile copied successfully")
        logger.info(f"   Saved to: {DEST_PROFILE}")
        return True
    else:
        logger.error("❌ Failed to copy profile")
        return False


# ============================================================
# STEP 2: LAUNCH CHROME WITH ANTI-BOT
# ============================================================

async def launch_chrome():
    """Launch Chrome with persistent context and anti-bot protection"""

    logger.info("=" * 60)
    logger.info("🚀 LAUNCHING CHROME")
    logger.info("=" * 60)

    # Get stealth args
    base_args = get_browser_launch_args()

    # Add critical anti-detection args (avoid duplicates)
    additional_args = [
        '--exclude-switches=enable-automation',
    ]

    # Merge args - set() removes duplicates automatically
    all_args = list(set(base_args + additional_args))

    logger.info(f"🔧 Launch arguments: {len(all_args)} anti-detection flags")

    # Create Playwright instance
    playwright = await async_playwright().start()

    # Launch persistent context
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=str(DEST_PROFILE.absolute()),
        channel='chrome',  # Use real Chrome
        args=all_args,
        ignore_default_args=[
            '--enable-automation',  # Remove automation flag
            '--no-sandbox',  # Remove unsupported flags on Linux
            '--disable-setuid-sandbox',
        ],
        headless=False,
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
        java_script_enabled=True,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        chromium_sandbox=True,  # Use system sandbox
    )

    logger.info("✅ Chrome launched with persistent context")

    # Get or create page
    if len(context.pages) > 0:
        page = context.pages[0]
        logger.info(f"✅ Using existing page: {page.url}")
    else:
        page = await context.new_page()
        logger.info("✅ Created new page")

    # Apply stealth scripts
    await apply_stealth_to_page(page)
    logger.info("🥷 Basic stealth mode applied")

    # Apply advanced anti-detection
    await page.add_init_script("""
        // Delete webdriver property completely
        delete Object.getPrototypeOf(navigator).webdriver;

        // Override navigator.webdriver to return undefined (not false!)
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });

        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // Ensure chrome.runtime exists
        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {};
        }

        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        console.log('🥷 Advanced anti-detection active');
        console.log('   navigator.webdriver:', navigator.webdriver);
        console.log('   window.chrome:', !!window.chrome);
    """)

    logger.info("🥷 Advanced anti-detection scripts injected")

    return playwright, context, page


# ============================================================
# STEP 3: HANDLE LOGIN
# ============================================================

async def ensure_logged_in(page):
    """Check if logged in, if not wait for manual login"""

    logger.info("\n" + "=" * 60)
    logger.info("🔐 CHECKING LOGIN STATUS")
    logger.info("=" * 60)

    # Navigate to home page to check login
    await page.goto("https://unlimited.globis.co.jp/ja", wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(3)

    # Check if logged in - try multiple selectors
    login_indicators = [
        # Profile image (most reliable indicator)
        "[class*='_ProfileImage']",
        "._ProfileImage",
        # Signout links
        "a[href*='signout']",
        "a[href*='/signout']",
        "[href*='signout']",
        "button:has-text('Sign Out')",
        "button:has-text('サインアウト')",
        "a:has-text('Sign Out')",
        "a:has-text('サインアウト')",
        # User menu/profile indicators
        "[data-testid='user-menu']",
        "[class*='user-menu']",
        "[class*='UserMenu']",
        "button[aria-label*='user']",
        "button[aria-label*='account']",
        # Avatar/profile icon
        "[class*='avatar']",
        "[class*='Avatar']",
        "img[alt*='profile']",
    ]

    is_logged_in = False
    found_selector = None

    for selector in login_indicators:
        try:
            elem = await page.query_selector(selector)
            if elem:
                is_logged_in = True
                found_selector = selector
                break
        except Exception:
            continue

    # If found login indicator, return success
    if is_logged_in:
        logger.info(f"✅ Already logged in! (found: {found_selector})")
        logger.info("✅ Login verified successfully")
        return True

    # Not logged in - check URL and page title for debugging
    current_url = page.url
    try:
        page_title = await page.title()
    except:
        page_title = "Unknown"

    logger.warning(f"⚠️  No login indicators found")
    logger.debug(f"   URL: {current_url}")
    logger.debug(f"   Title: {page_title}")

    # Not logged in - need manual login or re-copy profile
    logger.warning("⚠️  Not logged in yet")
    logger.warning("Profile may not contain valid cookies/sessions")

    print("\n" + "=" * 70)
    print("❌ LOGIN REQUIRED")
    print("=" * 70)
    print("\nChoose an option:")
    print("[1] Login manually in browser (then cookies will be saved)")
    print("[2] Re-copy profile from Chrome (to get fresh cookies/sessions)")
    print("[0] Cancel and exit")
    print("=" * 70)

    while True:
        try:
            choice = input("\nSelect option [1/2/0]: ").strip()

            if choice == "0":
                logger.info("❌ User cancelled")
                return False

            elif choice == "1":
                # Option 1: Manual login
                logger.info("🔑 Selected: Manual login")
                logger.info(f"🔗 Navigating to login page: {LOGIN_URL}")

                await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

                print("\n" + "=" * 60)
                print("👉 PLEASE LOGIN MANUALLY")
                print("=" * 60)
                print("Steps:")
                print("  1. Enter your GLOBIS credentials in the browser")
                print("  2. Click 'Sign In'")
                print("  3. Wait for redirect to home page")
                print("  4. Press ENTER when login complete")
                print("=" * 60)

                # Wait for Enter key
                input("\n⏎ Press ENTER after you've logged in...")

                # Re-check login status
                logger.info("\n🔍 Re-checking login status...")

                # Navigate to home page to verify login
                await page.goto("https://unlimited.globis.co.jp/ja", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)

                # Check login indicators again
                is_logged_in_now = False
                found_selector_now = None

                for selector in login_indicators:
                    try:
                        elem = await page.query_selector(selector)
                        if elem:
                            is_logged_in_now = True
                            found_selector_now = selector
                            break
                    except Exception:
                        continue

                if is_logged_in_now:
                    logger.info(f"✅ LOGIN SUCCESSFUL! (found: {found_selector_now})")
                    logger.info("🎉 Session saved - you won't need to login again!")
                    return True
                else:
                    logger.warning("⚠️  Still not logged in")
                    logger.warning("Please try again or choose a different option")
                    # Loop back to menu
                    continue

            elif choice == "2":
                # Option 2: Re-copy profile
                logger.info("📋 Selected: Re-copy profile")

                from src.browser.profile_manager import ChromeProfileManager

                # Create profile manager
                profile_manager = ChromeProfileManager(dest_profile=DEST_PROFILE)

                # Interactive profile selection
                source_profile = profile_manager.select_profile_interactive()

                if not source_profile:
                    logger.error("❌ No profile selected")
                    return False

                # Copy profile with force=True to overwrite
                success = profile_manager.copy_profile(source_profile, force=True)

                if not success:
                    logger.error("❌ Failed to copy profile")
                    return False

                logger.info("\n✅ Profile re-copied successfully")
                logger.info("⚠️  Please RESTART the script to use new profile")
                logger.info("   (Browser needs to reload with fresh cookies)")
                return False

            else:
                print("❌ Invalid choice. Please enter 1, 2, or 0")
                continue

        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            return False


# ============================================================
# HELPER: PAUSE VIDEO
# ============================================================

async def pause_video(page):
    """
    Pause Vimeo video before download to save bandwidth

    Strategy:
    1. Wait for video to ACTUALLY start playing (currentTime > 0, !paused, readyState >= 2)
    2. Pause the video
    3. Verify pause was successful (check paused state after pause)
    4. Retry if pause failed

    Args:
        page: Playwright page object

    Returns:
        bool: True if paused successfully, False otherwise
    """
    try:
        # Get iframe
        iframe_element = await page.query_selector('iframe[src*="player.vimeo.com"]')
        if not iframe_element:
            logger.debug("   No Vimeo iframe found, skipping pause")
            return False

        vimeo_iframe = await iframe_element.content_frame()
        if not vimeo_iframe:
            logger.debug("   Could not get iframe content frame")
            return False

        # STEP 1: Wait for video to ACTUALLY start playing
        # Increased timeout and better detection
        logger.debug("   Waiting for video to start playing...")

        video_is_playing = False
        playing_time = 0

        # Wait up to 12 seconds for video to start
        for i in range(24):  # 24 x 0.5s = 12 seconds max
            state = await vimeo_iframe.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (!video) {
                        return { error: 'No video element' };
                    }

                    // Video is ACTUALLY playing when ALL conditions are true:
                    const isPlaying = (
                        video.currentTime > 0 &&       // Has started
                        !video.paused &&               // Not paused
                        video.readyState >= 2          // Has data to play
                    );

                    return {
                        isPlaying: isPlaying,
                        paused: video.paused,
                        currentTime: video.currentTime,
                        readyState: video.readyState
                    };
                }
            """)

            if state.get('error'):
                logger.debug(f"   {state.get('error')}")
                await asyncio.sleep(0.5)
                continue

            # Video is ACTUALLY playing - wait a bit more to ensure it's stable
            if state.get('isPlaying'):
                current_time = state.get('currentTime', 0)

                # Wait until video has played for at least 0.5 seconds
                # This ensures video is truly playing, not just started
                if current_time >= 0.5:
                    video_is_playing = True
                    playing_time = current_time
                    logger.debug(f"   ✅ Video is playing (time: {current_time:.2f}s, readyState: {state.get('readyState')})")
                    break
                else:
                    # Video just started, wait more
                    logger.debug(f"   Video starting... (time: {current_time:.2f}s)")

            # Not playing yet, wait more
            await asyncio.sleep(0.5)

        if not video_is_playing:
            # Video didn't play after 12 seconds - force play
            logger.debug("   Video didn't auto-play after 12s, forcing play...")
            try:
                await vimeo_iframe.evaluate("() => { const v = document.querySelector('video'); if(v) v.play(); }")
                # Wait longer for forced play to take effect
                await asyncio.sleep(2.0)
            except:
                pass

        # STEP 1.5: Random delay to simulate human watching video (1-5 seconds)
        watch_delay = random.uniform(1.0, 5.0)
        logger.debug(f"   Watching video for {watch_delay:.1f}s (human behavior)...")
        await asyncio.sleep(watch_delay)

        # STEP 2: Pause the video and VERIFY it's paused
        logger.debug("   Attempting to pause video...")

        for attempt in range(3):  # Try up to 3 times
            pause_result = await vimeo_iframe.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (!video) {
                        return { error: 'No video element' };
                    }

                    // Pause the video
                    video.pause();

                    // Return state after pause
                    return {
                        paused: video.paused,
                        currentTime: video.currentTime
                    };
                }
            """)

            if pause_result.get('error'):
                logger.debug(f"   {pause_result.get('error')}")
                return False

            # VERIFY: Check if video is actually paused
            if pause_result.get('paused'):
                logger.debug(f"   ⏸️  Video successfully paused at {pause_result.get('currentTime', 0):.2f}s")

                # Double-check after 0.2s to ensure it stays paused
                await asyncio.sleep(0.2)
                verify = await vimeo_iframe.evaluate("() => { const v = document.querySelector('video'); return v ? v.paused : false; }")

                if verify:
                    logger.debug(f"   ✅ Pause verified")
                    return True
                else:
                    logger.debug(f"   ⚠️  Video started playing again after pause attempt {attempt + 1}/3")
                    await asyncio.sleep(0.2)
                    continue
            else:
                logger.debug(f"   ⚠️  Pause attempt {attempt + 1}/3 failed (paused={pause_result.get('paused')})")
                await asyncio.sleep(0.2)
                continue

        # Failed to pause after 3 attempts
        logger.warning(f"   ⚠️  Could not pause video after 3 attempts")
        return False

    except Exception as e:
        logger.debug(f"   ⚠️  Error pausing video: {e}")
        return False


# ============================================================
# STEP 4A: TEST SINGLE CATEGORY PARSING
# ============================================================

async def test_category_parsing(page, save_html=True):
    """Load first category from JSON and browse it"""

    logger.info("\n" + "=" * 60)
    logger.info("🧪 TEST CATEGORY PARSING")
    logger.info("=" * 60)

    # Load content file
    if not LEARN_CONTENT_FILE.exists():
        logger.error(f"❌ Content file not found: {LEARN_CONTENT_FILE}")
        return False

    with open(LEARN_CONTENT_FILE, 'r', encoding='utf-8') as f:
        content = json.load(f)

    categories = content.get('categories', [])
    if not categories:
        logger.error("❌ No categories found in JSON file")
        return False

    # Get first category
    category = categories[0]
    category_title = category.get('title', 'Unknown')
    category_url = category.get('url', '')

    if not category_url:
        logger.error("❌ Category URL is empty")
        return False

    logger.info(f"📚 Testing category: {category_title}")
    logger.info(f"🔗 URL: {category_url}")

    # Navigate to category page
    await page.goto(category_url, wait_until="domcontentloaded", timeout=60000)
    logger.info("✅ Navigation complete")

    await asyncio.sleep(3)

    # Get page info
    try:
        title = await page.title()
        logger.info(f"📄 Page title: {title}")
    except Exception as e:
        logger.warning(f"⚠️  Could not get page title: {e}")

    # Check if still logged in
    try:
        signout_elem = await page.query_selector(SUCCESS_INDICATOR)
        if signout_elem:
            logger.info("✅ Still logged in on category page")
        else:
            logger.warning("⚠️  Sign out link not found - may not be logged in")
    except Exception as e:
        logger.warning(f"⚠️  Could not check login status: {e}")

    # Save HTML if requested
    if save_html:
        try:
            html_content = await page.content()
            html_file = Path("data/category_page_sample.html")
            html_file.parent.mkdir(parents=True, exist_ok=True)
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"💾 HTML saved to: {html_file}")
        except Exception as e:
            logger.warning(f"⚠️  Could not save HTML: {e}")

    # Test CategoryParser
    logger.info("\n" + "=" * 60)
    logger.info("🔍 TESTING CATEGORY PARSER")
    logger.info("=" * 60)

    try:
        parser = CategoryParser()
        courses = await parser.parse_category_page(page)

        if courses:
            logger.info(f"\n✅ Successfully parsed {len(courses)} courses!")
            logger.info("\n📋 Sample courses (first 5):")
            for idx, course in enumerate(courses[:5], 1):
                logger.info(f"\n  [{idx}] {course.title}")
                logger.info(f"      URL: {course.url}")
                logger.info(f"      Duration: {course.duration or 'N/A'}")

            # Show statistics
            courses_with_duration = [c for c in courses if c.duration]
            logger.info(f"\n📊 Statistics:")
            logger.info(f"   Total courses: {len(courses)}")
            logger.info(f"   With duration: {len(courses_with_duration)}")
            logger.info(f"   Without duration: {len(courses) - len(courses_with_duration)}")

            # Test duration filtering
            logger.info(f"\n🔍 Testing duration filter (courses > 10 minutes):")
            long_courses = parser.filter_by_duration(courses, min_duration="00:10:00")
            logger.info(f"   Found {len(long_courses)} courses longer than 10 minutes")
            if long_courses:
                logger.info(f"   Example: {long_courses[0].title} ({long_courses[0].duration})")

        else:
            logger.warning("⚠️  No courses extracted by parser")

    except Exception as e:
        logger.error(f"❌ Parser error: {e}")
        import traceback
        traceback.print_exc()

    return True


# ============================================================
# STEP 4B: CRAWL ALL CATEGORIES
# ============================================================

async def crawl_all_categories(page, only_empty: bool = False):
    """Crawl all categories and save courses to JSON"""

    logger.info("\n" + "=" * 60)
    logger.info("🚀 CRAWL ALL CATEGORIES (LEARN CONTENT)")
    logger.info("=" * 60)

    try:
        # Create crawler
        crawler = CategoryCrawler(
            content_file=LEARN_CONTENT_FILE,
            min_delay=2.0,
            max_delay=5.0,
            max_retries=3,
        )

        # Crawl all categories
        stats = await crawler.crawl_all_categories(page, only_empty=only_empty)

        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ CATEGORY CRAWLING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Results saved to: {LEARN_CONTENT_FILE}")

        return True

    except Exception as e:
        logger.error(f"❌ Crawler error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# STEP 4C: CRAWL ALL SERIES
# ============================================================

async def crawl_all_series(page, only_empty: bool = False):
    """Crawl all series and save courses to JSON"""

    logger.info("\n" + "=" * 60)
    logger.info("🎬 CRAWL ALL SERIES (EXPLORE CONTENT)")
    logger.info("=" * 60)

    try:
        # Create crawler
        crawler = SeriesCrawler(
            content_file=EXPLORE_CONTENT_FILE,
            min_delay=2.0,
            max_delay=5.0,
            max_retries=3,
        )

        # Crawl all series
        stats = await crawler.crawl_all_series(page, only_empty=only_empty)

        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ SERIES CRAWLING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Results saved to: {EXPLORE_CONTENT_FILE}")

        return True

    except Exception as e:
        logger.error(f"❌ Crawler error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# STEP 4D: CRAWL COURSE DETAILS (OVERVIEW, TRANSCRIPT, DURATION)
# ============================================================

async def crawl_all_courses(page, content_file=None, only_empty: bool = False):
    """
    Crawl course details (overview, transcript, duration) from all courses

    Args:
        page: Playwright page object
        content_file: Path to learn-content.json or explore-content.json

    Returns:
        bool: True if successful, False otherwise
    """

    if content_file is None:
        content_file = LEARN_CONTENT_FILE

    logger.info("\n" + "=" * 60)
    logger.info(f"📚 CRAWL COURSE DETAILS FROM: {content_file.name}")
    logger.info("=" * 60)

    try:
        # Create course crawler
        language = "en" if "en" in str(content_file) else "ja"

        crawler = CourseCrawler(
            content_file=content_file,
            language=language,
            min_delay=2.0,
            max_delay=5.0,
            max_retries=3
        )

        # Crawl all courses for details
        stats = await crawler.crawl_all_courses(page, only_empty=only_empty)

        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ COURSE DETAILS CRAWLING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Courses crawled: {stats.get('courses_crawled', 0)}")
        logger.info(f"📊 Courses failed: {stats.get('courses_failed', 0)}")
        logger.info(f"📊 Results saved to: {content_file}")

        return True

    except Exception as e:
        logger.error(f"❌ Course crawler error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# STEP 4E: CRAWL VIDEOS FROM ALL COURSES
# ============================================================

async def crawl_all_videos(page, content_file=None, only_empty: bool = False):
    """
    Extract overview, transcript and summary from all videos in content file
    Saves content to .txt files instead of storing in JSON

    Args:
        page: Playwright Page object
        content_file: Path to content file (defaults to LEARN_CONTENT_FILE)
        only_empty: If True, only crawl videos that haven't been extracted yet
    """

    if content_file is None:
        content_file = LEARN_CONTENT_FILE

    logger.info("\n" + "=" * 60)
    logger.info(f"📹 EXTRACT VIDEO CONTENT (Overview + Transcript + Summary)")
    logger.info(f"   Content file: {content_file}")
    logger.info("=" * 60)

    try:
        # Import required modules
        from src.crawler.content_manager import ContentManager
        from src.crawler.content_extractor import ContentExtractor

        # Get base URL from content file path
        sites_manager = SitesManager()
        language = "en" if "/en/" in str(content_file) else "ja"
        base_url = sites_manager.get_base_url(language)

        # Initialize ContentManager and ContentExtractor
        content_manager = ContentManager(content_file, language=language)
        content_extractor = ContentExtractor(base_dir=Path("downloads"))

        # Load content
        content_manager.load()

        # Get items (categories or series)
        items = content_manager.categories if content_manager.categories else content_manager.series
        item_type = "categories" if content_manager.categories else "series"

        if not items:
            logger.error(f"❌ No {item_type} found in content file")
            return False

        logger.info(f"📊 Found {len(items)} {item_type}")

        # Statistics
        stats = {
            'total_videos': 0,
            'processed': 0,
            'skipped': 0,
            'failed': 0
        }

        # Iterate through items
        for item_idx, item in enumerate(items, 1):
            item_name = item.title
            logger.info(f"\n{'='*70}")
            logger.info(f"📁 [{item_idx}/{len(items)}] {item_type.rstrip('s').upper()}: {item_name}")
            logger.info(f"{'='*70}")

            # Iterate through courses
            for course_idx, course in enumerate(item.courses, 1):
                stats['total_videos'] += 1

                logger.info(f"\n📘 [{course_idx}/{len(item.courses)}] Course: {course.title}")

                # Check if files already exist on disk
                content_type = "series" if content_manager.is_explore_content else "categories"
                output_dir = content_extractor._get_output_dir(
                    language=language,
                    content_type=content_type,
                    category_title=item_name,
                    course_title=course.title
                )
                overview_file = output_dir / "overview.txt"
                transcript_file = output_dir / "transcript.txt"

                files_exist = overview_file.exists() and transcript_file.exists()

                # Check if any video in this course has is_content flag
                has_content_flag = any(
                    video.is_content
                    for lp in course.learning_points
                    for video in lp.videos
                )

                # Skip if BOTH files exist AND flag is set
                if files_exist and has_content_flag:
                    logger.info(f"   ⏭️  Both files exist and is_content=true - Skipping")
                    stats['skipped'] += 1
                    continue

                # Show what needs to be extracted
                if not files_exist:
                    missing = []
                    if not overview_file.exists():
                        missing.append("overview.txt")
                    if not transcript_file.exists():
                        missing.append("transcript.txt")
                    logger.info(f"   📝 Missing files: {', '.join(missing)} - Will extract")

                # Build full course URL
                course_url = course.url
                if not course_url.startswith('http'):
                    domain = '/'.join(base_url.split('/')[:3])
                    course_url = f"{domain}{course_url}"

                # Try to extract content with retries
                max_retries = 3
                success = False

                for attempt in range(1, max_retries + 1):
                    try:
                        if attempt > 1:
                            logger.info(f"      🔄 Retry {attempt}/{max_retries}")

                        # Navigate to course page
                        logger.debug(f"      🌐 Navigating to: {course_url}")
                        await page.goto(course_url, wait_until="domcontentloaded", timeout=30000)

                        # Extract and save content using ContentExtractor
                        content_type = "series" if content_manager.is_explore_content else "categories"
                        results = await content_extractor.extract_and_save(
                            page=page,
                            language=language,
                            content_type=content_type,
                            category_title=item_name,
                            course_title=course.title
                        )

                        # Check if we got any content
                        if any(results.values()):
                            success = True
                            break
                        else:
                            logger.warning(f"      ⚠️  No content extracted")
                            if attempt < max_retries:
                                continue

                    except Exception as e:
                        logger.error(f"      ❌ Error: {e}")
                        if attempt < max_retries:
                            await asyncio.sleep(2 * attempt)
                            continue

                if success:
                    # Mark ALL videos in this course as extracted
                    for lp in course.learning_points:
                        for video in lp.videos:
                            video.is_content = True
                            video.last_updated = datetime.now().isoformat()

                    stats['processed'] += 1

                    # Save progress incrementally
                    content_manager.save()
                    logger.info(f"      ✅ Content extracted and saved")
                else:
                    stats['failed'] += 1
                    logger.warning(f"      ❌ Failed to extract content")

                # Random delay
                delay = 1.5 + (3.0 - 1.5) * (hash(course.url) % 100) / 100
                logger.debug(f"      ⏳ Waiting {delay:.1f}s...")
                await asyncio.sleep(delay)

        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ COURSE CONTENT EXTRACTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Results:")
        logger.info(f"   Total courses: {stats['total_videos']}")
        logger.info(f"   Processed:     {stats['processed']}")
        logger.info(f"   Skipped:       {stats['skipped']}")
        logger.info(f"   Failed:        {stats['failed']}")
        logger.info(f"💾 Content files saved to: downloads/")

        return True

    except Exception as e:
        logger.error(f"❌ Video content crawler error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# STEP 4F: CRAWL SITES - Parse initial categories/series from sites.json URLs
# ============================================================

async def crawl_sites_initial(page, target_language=None):
    """
    Crawl initial categories and series lists from sites.json URLs

    This function:
    1. Reads sites.json to get URLs for each language
    2. For each language (or specific language if provided):
       - Navigates to learn-content URL → Parses LIST of categories → Saves to JSON
       - Navigates to explore-content URL → Parses LIST of series → Saves to JSON
    3. Creates files/folders automatically if they don't exist

    Args:
        page: Playwright Page object
        target_language: Specific language to crawl (e.g., 'en', 'ja'). If None, crawl all languages.

    Returns:
        bool: True if successful, False otherwise
    """

    logger.info("\n" + "=" * 70)
    if target_language:
        logger.info(f"🌍 CRAWLING SITES FOR {target_language.upper()}")
    else:
        logger.info("🌍 CRAWLING SITES FOR ALL LANGUAGES")
    logger.info("=" * 70)

    try:
        # Load sites manager
        sites_manager = SitesManager()
        all_languages = sites_manager.get_languages()

        # Filter languages if target specified
        if target_language:
            if target_language not in all_languages:
                logger.error(f"❌ Language '{target_language}' not found in sites.json")
                logger.info(f"Available languages: {', '.join(all_languages)}")
                return False
            languages = [target_language]
        else:
            languages = all_languages

        logger.info(f"\n📋 Found {len(languages)} languages: {', '.join([lang.upper() for lang in languages])}")

        # Ensure language directories exist
        sites_manager.ensure_language_dirs()

        # Import parser
        from src.crawler.category_parser import CategoryParser

        parser = CategoryParser()
        total_success = 0
        total_failed = 0

        # Process each language
        for idx, lang in enumerate(languages, 1):
            logger.info("\n" + "=" * 70)
            logger.info(f"🌐 LANGUAGE {idx}/{len(languages)}: {lang.upper()}")
            logger.info("=" * 70)

            # Get URLs and file paths for this language
            learn_url = sites_manager.get_learn_content_url(lang)
            explore_url = sites_manager.get_explore_content_url(lang)
            learn_file = sites_manager.get_content_file_path(lang, "learn-content")
            explore_file = sites_manager.get_content_file_path(lang, "explore-content")

            logger.info(f"\n📁 Output files:")
            logger.info(f"   Learn:   {learn_file}")
            logger.info(f"   Explore: {explore_file}")

            # Part 1: Parse categories from learn-content page
            logger.info(f"\n📚 Part 1: Parsing categories from learn-content...")
            logger.info(f"   URL: {learn_url}")

            try:
                # Navigate to learn-content page
                await page.goto(learn_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)  # Wait for page to settle

                # Parse categories
                categories = await parser.parse_initial_categories(page)

                if categories:
                    logger.info(f"✅ Found {len(categories)} categories")

                    # Save to JSON using ContentManager
                    content_mgr = ContentManager(learn_file, language=lang)
                    content_mgr.load()  # Load existing or initialize

                    # Update categories
                    from datetime import datetime

                    content_mgr.categories = [
                        Category(
                            title=cat.title,
                            url=cat.url,
                            last_updated=datetime.now().isoformat(),
                            courses=[]
                        )
                        for cat in categories
                    ]

                    content_mgr.save()
                    logger.info(f"💾 Saved {len(categories)} categories to {learn_file}")
                    total_success += 1
                else:
                    logger.warning(f"⚠️  No categories found for {lang.upper()}")
                    total_failed += 1

            except Exception as e:
                logger.error(f"❌ Failed to parse categories for {lang.upper()}: {e}")
                total_failed += 1

            # Wait between learn and explore
            logger.info("\n⏳ Waiting 5 seconds...")
            await asyncio.sleep(5)

            # Part 2: Parse series from explore-content page
            logger.info(f"\n🎬 Part 2: Parsing series from explore-content...")
            logger.info(f"   URL: {explore_url}")

            try:
                # Navigate to explore-content page
                await page.goto(explore_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)  # Wait for page to settle

                # Parse series
                series_list = await parser.parse_initial_series(page)

                if series_list:
                    logger.info(f"✅ Found {len(series_list)} series")

                    # Save to JSON using ContentManager
                    content_mgr = ContentManager(explore_file, language=lang)
                    content_mgr.load()  # Load existing or initialize

                    # Update series
                    from datetime import datetime

                    content_mgr.series = [
                        Series(
                            title=s.title,
                            url=s.url,
                            last_updated=datetime.now().isoformat(),
                            courses=[]
                        )
                        for s in series_list
                    ]

                    content_mgr.save()
                    logger.info(f"💾 Saved {len(series_list)} series to {explore_file}")
                    total_success += 1
                else:
                    logger.warning(f"⚠️  No series found for {lang.upper()}")
                    total_failed += 1

            except Exception as e:
                logger.error(f"❌ Failed to parse series for {lang.upper()}: {e}")
                total_failed += 1

            # Wait before next language
            if idx < len(languages):
                logger.info("\n⏳ Waiting 10 seconds before next language...")
                await asyncio.sleep(10)

        # Final summary
        logger.info("\n" + "=" * 70)
        if total_failed == 0:
            logger.info("✅ SITES CRAWLING COMPLETE - ALL SUCCESS")
        elif total_success > 0:
            logger.info("⚠️  SITES CRAWLING COMPLETE - PARTIAL SUCCESS")
        else:
            logger.info("❌ SITES CRAWLING FAILED")
        logger.info("=" * 70)
        logger.info(f"📊 Languages processed: {len(languages)}")
        logger.info(f"📊 Successful operations: {total_success}")
        logger.info(f"📊 Failed operations: {total_failed}")

        for lang in languages:
            learn_file = sites_manager.get_content_file_path(lang, "learn-content")
            explore_file = sites_manager.get_content_file_path(lang, "explore-content")
            logger.info(f"\n📁 {lang.upper()}:")
            logger.info(f"   ✅ {learn_file}")
            logger.info(f"   ✅ {explore_file}")

        return total_success > 0

    except Exception as e:
        logger.error(f"❌ Sites crawling error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# STEP 4G: OLD INIT FUNCTION (kept for backward compatibility)
# ============================================================

async def init_all_languages(page, target_language=None):
    """
    OLD FUNCTION - Initialize and crawl categories + series for all languages

    NOTE: This will be replaced by simpler Chrome profile copy functionality.
    Use crawl_sites_initial() instead for parsing initial categories/series.

    Args:
        page: Playwright Page object
        target_language: Specific language to crawl (e.g., 'en', 'ja'). If None, crawl all languages.

    Returns:
        bool: True if successful, False otherwise
    """

    logger.info("\n" + "=" * 70)
    if target_language:
        logger.info(f"🌍 INITIALIZE {target_language.upper()} FROM SITES.JSON")
    else:
        logger.info("🌍 INITIALIZE ALL LANGUAGES FROM SITES.JSON")
    logger.info("=" * 70)

    try:
        # Load sites manager
        sites_manager = SitesManager()
        all_languages = sites_manager.get_languages()

        # Filter languages if target specified
        if target_language:
            if target_language not in all_languages:
                logger.error(f"❌ Language '{target_language}' not found in sites.json")
                logger.info(f"Available languages: {', '.join(all_languages)}")
                return False
            languages = [target_language]
        else:
            languages = all_languages

        logger.info(f"\n📋 Found {len(languages)} languages: {', '.join([lang.upper() for lang in languages])}")

        # Ensure language directories exist
        sites_manager.ensure_language_dirs()

        total_success = 0
        total_failed = 0

        # Process each language
        for idx, lang in enumerate(languages, 1):
            logger.info("\n" + "=" * 70)
            logger.info(f"🌐 LANGUAGE {idx}/{len(languages)}: {lang.upper()}")
            logger.info("=" * 70)

            # Get content files for this language
            learn_content_file = sites_manager.get_content_file_path(lang, "learn-content")
            explore_content_file = sites_manager.get_content_file_path(lang, "explore-content")

            logger.info(f"\n📁 Output files:")
            logger.info(f"   Learn:   {learn_content_file}")
            logger.info(f"   Explore: {explore_content_file}")

            # Part 1: Crawl categories (learn-content)
            logger.info(f"\n📚 Part 1: Crawling categories for {lang.upper()}...")
            logger.info(f"   URL: {sites_manager.get_learn_content_url(lang)}")

            try:
                category_crawler = CategoryCrawler(
                    content_file=learn_content_file,
                    min_delay=2.0,
                    max_delay=5.0,
                    max_retries=3,
                )

                cat_stats = await category_crawler.crawl_all_categories(page)
                logger.info(f"✅ Categories done for {lang.upper()}: {cat_stats.get('categories_crawled', 0)} categories")
                total_success += 1

            except Exception as e:
                logger.error(f"❌ Category crawling failed for {lang.upper()}: {e}")
                total_failed += 1

            # Wait between categories and series (always)
            logger.info("\n⏳ Waiting 10 seconds before series...")
            await asyncio.sleep(10)

            # Part 2: Crawl series (explore-content)
            logger.info(f"\n🎬 Part 2: Crawling series for {lang.upper()}...")
            logger.info(f"   URL: {sites_manager.get_explore_content_url(lang)}")

            try:
                series_crawler = SeriesCrawler(
                    content_file=explore_content_file,
                    min_delay=2.0,
                    max_delay=5.0,
                    max_retries=3,
                )

                series_stats = await series_crawler.crawl_all_series(page)
                logger.info(f"✅ Series done for {lang.upper()}: {series_stats.get('series_crawled', 0)} series")
                total_success += 1

            except Exception as e:
                logger.error(f"❌ Series crawling failed for {lang.upper()}: {e}")
                total_failed += 1

            # Wait before next language (if not last)
            if idx < len(languages):
                logger.info(f"\n⏳ Waiting 15 seconds before next language...")
                await asyncio.sleep(15)

        # Final summary
        logger.info("\n" + "=" * 70)
        if total_failed == 0:
            logger.info("✅ INITIALIZATION COMPLETE - ALL SUCCESS")
        elif total_success > 0:
            logger.info("⚠️  INITIALIZATION COMPLETE - PARTIAL SUCCESS")
        else:
            logger.info("❌ INITIALIZATION FAILED")
        logger.info("=" * 70)
        logger.info(f"📊 Languages processed: {len(languages)}")
        logger.info(f"📊 Successful operations: {total_success}")
        logger.info(f"📊 Failed operations: {total_failed}")

        for lang in languages:
            learn_file = sites_manager.get_content_file_path(lang, "learn-content")
            explore_file = sites_manager.get_content_file_path(lang, "explore-content")
            logger.info(f"\n📁 {lang.upper()}:")
            logger.info(f"   ✅ {learn_file}")
            logger.info(f"   ✅ {explore_file}")

        # Return True if at least some operations succeeded
        # Only return False if ALL operations failed
        return total_success > 0

    except Exception as e:
        logger.error(f"❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# STEP 4G: DOWNLOAD ALL VIDEOS
# ============================================================

async def download_all_videos(page, content_file=None, only_empty: bool = False):
    """
    Download all videos from courses

    Downloads to: downloads/[lang]/[categories|series]/[category_title]/[course_title]/[learning_point_title]/[video_title].mp4
    Updates is_downloaded flag in JSON after successful download

    Args:
        page: Playwright Page object
        content_file: Path to content file (defaults to LEARN_CONTENT_FILE)
        only_empty: If True, only download videos where is_downloaded == False

    Returns:
        bool: True if successful, False otherwise
    """
    from src.crawler.content_manager import ContentManager
    from src.crawler.vimeo_interceptor import VimeoInterceptor
    import random

    if content_file is None:
        content_file = LEARN_CONTENT_FILE

    # Determine language and content type from file path
    language = "en" if "/en/" in str(content_file) else "ja"
    content_type = "categories" if "learn-content" in str(content_file) else "series"

    logger.info("\n" + "=" * 60)
    logger.info(f"📥 DOWNLOAD VIDEOS")
    logger.info(f"   Content file: {content_file}")
    logger.info(f"   Language: {language}")
    logger.info(f"   Type: {content_type}")
    if only_empty:
        logger.info(f"   Mode: Only download videos with is_downloaded=False")
    logger.info("=" * 60)

    try:
        # Load content
        content_manager = ContentManager(content_file, language=language)
        content_manager.load()

        # Get categories or series
        if content_type == "categories":
            containers = content_manager.categories
        else:
            containers = content_manager.series

        if not containers:
            logger.error(f"❌ No {content_type} found in {content_file}")
            return False

        # Initialize downloader and interceptor
        downloader = VideoDownloader(
            download_dir=Path("downloads"),
            language=language,
            cookies_from_browser="chrome"
        )
        interceptor = VimeoInterceptor(page)

        # Statistics
        total_videos = 0
        downloaded_count = 0
        skipped_count = 0
        failed_count = 0

        # Count total videos
        for container in containers:
            for course in container.courses:
                for lp in course.learning_points:
                    total_videos += len(lp.videos)

        logger.info(f"📚 Found {len(containers)} {content_type}")
        logger.info(f"📚 Total videos: {total_videos}")

        video_counter = 0

        # Download videos for each course
        for container in containers:
            container_title = container.title
            logger.info(f"\n{'=' * 70}")
            logger.info(f"📂 {content_type.title()[:-1]}: {container_title}")
            logger.info(f"{'=' * 70}")

            for course in container.courses:
                course_title = course.title
                logger.info(f"\n🎓 Course: {course_title}")

                for lp in course.learning_points:
                    lp_title = lp.title
                    logger.info(f"\n📖 Learning Point: {lp_title}")

                    for video in lp.videos:
                        video_counter += 1
                        video_title = video.title
                        video_url = video.url

                        logger.info(f"\n🎬 Video [{video_counter}/{total_videos}]: {video_title}")

                        # Build output path (sanitize all folder names same as ContentExtractor)
                        safe_container = downloader.sanitize_filename(container_title)
                        safe_course    = downloader.sanitize_filename(course_title)
                        safe_lp        = downloader.sanitize_filename(lp_title)
                        output_dir = Path("downloads") / language / content_type / safe_container / safe_course / safe_lp
                        output_dir.mkdir(parents=True, exist_ok=True)

                        # Sanitize video filename (same logic as folder names)
                        safe_filename = downloader.sanitize_filename(video_title)
                        output_file = output_dir / f"{safe_filename}.mp4"

                        # Skip only if BOTH is_downloaded=true AND file exists
                        if video.is_downloaded and output_file.exists():
                            logger.info(f"⏭️  Skipping (already downloaded and file exists): {output_file.name}")
                            skipped_count += 1
                            continue

                        # If is_downloaded=true but file missing, reset flag and download
                        if video.is_downloaded and not output_file.exists():
                            logger.warning(f"⚠️  File missing despite is_downloaded=true, re-downloading: {output_file.name}")
                            video.is_downloaded = False

                        # If file exists but is_downloaded=false, verify and update flag
                        if not video.is_downloaded and output_file.exists():
                            file_size = output_file.stat().st_size
                            if file_size > 0:
                                logger.info(f"⏭️  File exists ({file_size / 1024 / 1024:.1f} MB), updating is_downloaded flag")
                                video.is_downloaded = True
                                content_manager.save()
                                skipped_count += 1
                                continue
                            else:
                                logger.warning(f"⚠️  File exists but empty (0 bytes), re-downloading")
                                output_file.unlink()

                        # Navigate to video page
                        try:
                            # Convert relative URL to absolute URL
                            if video_url.startswith('/'):
                                base_url = "https://unlimited.globis.co.jp"
                                video_url = base_url + video_url

                            logger.info(f"🔗 URL: {video_url}")

                            # Start intercepting Vimeo URLs
                            await interceptor.start()
                            interceptor.clear()

                            # Navigate to video page
                            await page.goto(video_url, wait_until="domcontentloaded", timeout=30000)

                            # Human-like behavior: Random delay after page load
                            page_load_delay = random.uniform(2.5, 4.0)
                            await asyncio.sleep(page_load_delay)  # Wait for video player to load

                            # Human-like behavior: Small random mouse movement
                            try:
                                await page.mouse.move(
                                    random.randint(100, 500),
                                    random.randint(100, 400)
                                )
                            except:
                                pass

                            # Extract download URL using VimeoExtractor
                            try:
                                logger.info("🔍 Extracting video URLs with VimeoExtractor...")

                                video_data = await VimeoExtractor.extract_video_urls(page, timeout=10000)

                                if video_data and video_data.get('best_download_url'):
                                    download_url = video_data['best_download_url']
                                    logger.debug(f"✅ Extracted download URL: {download_url[:100]}...")
                                else:
                                    logger.debug("⚠️  No download URL from VimeoExtractor, trying network interceptor...")
                                    download_url = interceptor.get_best_quality_url()

                            except Exception as e:
                                logger.debug(f"Error extracting with VimeoExtractor: {e}")
                                # Fallback to network interceptor method
                                download_url = interceptor.get_best_quality_url()

                            if not download_url:
                                logger.warning("❌ No download URL found")
                                failed_count += 1
                                continue

                            # Pause video to save bandwidth
                            logger.info("⏸️  Attempting to pause video...")
                            await pause_video(page)

                            # Download video using VideoDownloader (with built-in validation)
                            is_series = content_type == "series"
                            success = await downloader.download_from_extracted_url(
                                download_url=download_url,
                                category_or_series=container_title,
                                course_name=course_title,
                                learning_point=lp_title,
                                video_title=video_title,
                                max_retries=3,
                                skip_if_exists=False,  # Already checked above
                                is_series=is_series
                            )

                            if success:
                                # Mark as downloaded and save progress
                                video.is_downloaded = True
                                downloaded_count += 1
                                content_manager.save()
                                logger.debug("💾 Progress saved")
                            else:
                                failed_count += 1
                                logger.warning(f"❌ Download failed: {video_title}")

                        except Exception as e:
                            logger.error(f"❌ Error downloading {video_title}: {e}")
                            failed_count += 1
                            continue

                        finally:
                            await interceptor.stop()

                        # Human-like delay between videos with more variation
                        if video_counter < total_videos:
                            delay = random.uniform(3.0, 6.0)
                            logger.info(f"⏳ Waiting {delay:.1f}s before next video...")
                            await asyncio.sleep(delay)

        # Final save
        content_manager.save()
#         # Crawl all courses and download videos
#         stats = await crawler.crawl_all_courses(page, only_empty=only_empty)

        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ VIDEO DOWNLOAD COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Total videos: {total_videos}")
        logger.info(f"📊 Downloaded: {downloaded_count}")
        logger.info(f"📊 Skipped: {skipped_count}")
        logger.info(f"📊 Failed: {failed_count}")

        return True

    except Exception as e:
        logger.error(f"❌ Video download error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# MAIN WORKFLOW
# ============================================================

async def main(mode: str = "test", language: str = None, only_empty: bool = False):
    """
    Main workflow

    Args:
        mode: "init", "test", "categories", "series", "courses", "content", "downloads", or "all"
        language: Target language (e.g., "en", "ja"). If None, uses default or all languages.
    """

    logger.info("\n" + "=" * 70)
    logger.info("🎯 GLOBIS BROWSER AUTOMATION")
    logger.info(f"   Mode: {mode.upper()}")
    if language:
        logger.info(f"   Language: {language.upper()}")
    logger.info("=" * 70)

    # Step 1: Copy profile
    logger.info("\n📋 STEP 1: Copy Chrome Profile")
    if not copy_chrome_profile():
        logger.error("❌ Failed to copy Chrome profile")
        return

    # Step 2: Launch Chrome
    logger.info("\n🚀 STEP 2: Launch Chrome with Anti-Bot Protection")
    playwright, context, page = await launch_chrome()

    try:
        # Step 3: Ensure logged in
        logger.info("\n🔐 STEP 3: Check/Handle Login")
        if not await ensure_logged_in(page):
            logger.error("❌ Login failed or timed out")
            return

        # Step 4: Execute based on mode
        if mode == "sites":
            # NEW: Crawl initial categories/series from sites.json URLs
            if language:
                logger.info(f"\n🌍 STEP 4: Crawl Sites for {language.upper()}")
            else:
                logger.info("\n🌍 STEP 4: Crawl Sites for All Languages")
            success = await crawl_sites_initial(page, language)

            if success:
                logger.info("\n" + "=" * 70)
                logger.info("✅ SITES CRAWLING COMPLETE")
                logger.info("=" * 70)
                logger.info("All categories and series have been parsed successfully!")
            else:
                logger.error("\n❌ Sites crawling had some failures")

            # Close browser automatically
            logger.info("\n👋 Closing browser...")

        elif mode == "init":
            # Init mode: Setup is already done in STEP 1-3
            # If we reached here, login was successful
            logger.info("\n" + "=" * 70)
            logger.info("✅ INITIALIZATION COMPLETE")
            logger.info("=" * 70)
            logger.info("\n📋 Setup Summary:")
            logger.info(f"  ✅ Chrome profile: {DEST_PROFILE}")
            logger.info("  ✅ Browser launched successfully")
            logger.info("  ✅ Login verified")
            logger.info("\nYou can now use other modes to crawl:")
            logger.info("  - sites      : Parse initial categories/series")
            logger.info("  - categories : Crawl category details")
            logger.info("  - series     : Crawl series details")
            logger.info("  - courses    : Crawl course details and videos")
            logger.info("  - content    : Extract course content (overview + transcript)")
            logger.info("  - downloads  : Download videos")

            # Close browser automatically
            logger.info("\n👋 Closing browser...")

        elif mode == "test":
            logger.info("\n🧪 STEP 4: Test Category Parsing (Single Category)")
            await test_category_parsing(page)

            # Keep browser open for inspection
            logger.info("\n" + "=" * 70)
            logger.info("✅ TEST COMPLETE")
            logger.info("=" * 70)
            logger.info("\n📌 Browser will stay open for manual inspection")
            logger.info("   - Check console (F12) for anti-detection logs")
            logger.info("   - Verify navigator.webdriver is undefined")
            logger.info("\n⌨️  Press Ctrl+C to close browser and exit")

            # Wait indefinitely
            try:
                while True:
                    await asyncio.sleep(10)
            except KeyboardInterrupt:
                logger.info("\n👋 Shutting down...")

        elif mode == "categories":
            # Determine which language(s) to crawl
            sites_manager = SitesManager()

            if language:
                # Single language
                logger.info(f"\n🚀 STEP 4: Crawl Categories ({language.upper()})")
                target_file = sites_manager.get_content_file_path(language, "learn-content")

                crawler = CategoryCrawler(
                    content_file=target_file,
                    min_delay=2.0,
                    max_delay=5.0,
                    max_retries=3,
                )

                stats = await crawler.crawl_all_categories(page)

                logger.info("\n" + "=" * 70)
                logger.info(f"✅ CATEGORIES CRAWLING COMPLETE ({language.upper()})")
                logger.info("=" * 70)
                logger.info(f"📊 Results saved to: {target_file}")
            else:
                # Crawl all languages
                logger.info("\n🚀 STEP 4: Crawl Categories (All Languages)")
                languages = sites_manager.get_languages()

                for idx, lang in enumerate(languages, 1):
                    logger.info(f"\n📚 Part {idx}/{len(languages)}: {lang.upper()} categories...")
                    target_file = sites_manager.get_content_file_path(lang, "learn-content")

                    crawler = CategoryCrawler(
                        content_file=target_file,
                        min_delay=2.0,
                        max_delay=5.0,
                        max_retries=3,
                    )

                    stats = await crawler.crawl_all_categories(page)
                    logger.info(f"✅ {lang.upper()} done: {target_file}")

                    if idx < len(languages):
                        logger.info("\n⏳ Waiting 10 seconds before next language...")
                        await asyncio.sleep(10)

                logger.info("\n" + "=" * 70)
                logger.info("✅ CATEGORIES CRAWLING COMPLETE (ALL LANGUAGES)")
                logger.info("=" * 70)

            # Close browser automatically after crawling
            logger.info("\n👋 Closing browser...")

        elif mode == "series":
            # Determine which language(s) to crawl
            sites_manager = SitesManager()

            if language:
                # Single language
                logger.info(f"\n🎬 STEP 4: Crawl Series ({language.upper()})")
                target_file = sites_manager.get_content_file_path(language, "explore-content")

                crawler = SeriesCrawler(
                    content_file=target_file,
                    min_delay=2.0,
                    max_delay=5.0,
                    max_retries=3,
                )

                stats = await crawler.crawl_all_series(page, only_empty=only_empty)

                logger.info("\n" + "=" * 70)
                logger.info(f"✅ SERIES CRAWLING COMPLETE ({language.upper()})")
                logger.info("=" * 70)
                logger.info(f"📊 Results saved to: {target_file}")
            else:
                # Crawl all languages
                logger.info("\n🎬 STEP 4: Crawl Series (All Languages)")
                languages = sites_manager.get_languages()

                for idx, lang in enumerate(languages, 1):
                    logger.info(f"\n🎬 Part {idx}/{len(languages)}: {lang.upper()} series...")
                    target_file = sites_manager.get_content_file_path(lang, "explore-content")

                    crawler = SeriesCrawler(
                        content_file=target_file,
                        min_delay=2.0,
                        max_delay=5.0,
                        max_retries=3,
                    )

                    stats = await crawler.crawl_all_series(page, only_empty=only_empty)
                    logger.info(f"✅ {lang.upper()} done: {target_file}")

                    if idx < len(languages):
                        logger.info("\n⏳ Waiting 10 seconds before next language...")
                        await asyncio.sleep(10)

                logger.info("\n" + "=" * 70)
                logger.info("✅ SERIES CRAWLING COMPLETE (ALL LANGUAGES)")
                logger.info("=" * 70)

            # Close browser automatically
            logger.info("\n👋 Closing browser...")

        elif mode == "courses":
            # Determine which language(s) to crawl
            sites_manager = SitesManager()

            if language:
                # Single language
                logger.info(f"\n📚 STEP 4: Crawl Courses ({language.upper()})")
                logger.info("\nCrawling courses from both learn-content and explore-content...")

                # Learn content
                learn_file = sites_manager.get_content_file_path(language, "learn-content")
                logger.info(f"\n📚 Part 1: Crawling courses from {learn_file}...")
                await crawl_all_courses(page, learn_file, only_empty=only_empty)

                logger.info("\n⏳ Waiting 10 seconds...")
                await asyncio.sleep(10)

                # Explore content
                explore_file = sites_manager.get_content_file_path(language, "explore-content")
                logger.info(f"\n📚 Part 2: Crawling courses from {explore_file}...")
                await crawl_all_courses(page, explore_file, only_empty=only_empty)

                logger.info("\n" + "=" * 70)
                logger.info(f"✅ COURSES CRAWLING COMPLETE ({language.upper()})")
                logger.info("=" * 70)
            else:
                # Crawl all languages
                logger.info("\n📚 STEP 4: Crawl Courses (All Languages)")
                languages = sites_manager.get_languages()

                for idx, lang in enumerate(languages, 1):
                    logger.info(f"\n{'=' * 70}")
                    logger.info(f"🌐 LANGUAGE {idx}/{len(languages)}: {lang.upper()}")
                    logger.info(f"{'=' * 70}")

                    # Learn content
                    learn_file = sites_manager.get_content_file_path(lang, "learn-content")
                    logger.info(f"\n📚 Part 1: {lang.upper()} learn-content...")
                    await crawl_all_courses(page, learn_file, only_empty=only_empty)

                    logger.info("\n⏳ Waiting 10 seconds...")
                    await asyncio.sleep(10)

                    # Explore content
                    explore_file = sites_manager.get_content_file_path(lang, "explore-content")
                    logger.info(f"\n📚 Part 2: {lang.upper()} explore-content...")
                    await crawl_all_courses(page, explore_file, only_empty=only_empty)

                    if idx < len(languages):
                        logger.info("\n⏳ Waiting 15 seconds before next language...")
                        await asyncio.sleep(15)

                logger.info("\n" + "=" * 70)
                logger.info("✅ COURSES CRAWLING COMPLETE (ALL LANGUAGES)")
                logger.info("=" * 70)

            # Close browser
            logger.info("\n👋 Closing browser...")

        elif mode == "content":
            # Determine which language(s) to crawl
            sites_manager = SitesManager()

            if language:
                # Single language
                logger.info(f"\n🎬 STEP 4: Crawl Videos ({language.upper()})")
                logger.info("\nCrawling videos from both learn-content and explore-content...")

                # Learn content
                learn_file = sites_manager.get_content_file_path(language, "learn-content")
                logger.info(f"\n📚 Part 1: Crawling videos from {learn_file}...")
                await crawl_all_videos(page, learn_file, only_empty=only_empty)

                logger.info("\n⏳ Waiting 10 seconds...")
                await asyncio.sleep(10)

                # Explore content
                explore_file = sites_manager.get_content_file_path(language, "explore-content")
                logger.info(f"\n🎬 Part 2: Crawling videos from {explore_file}...")
                await crawl_all_videos(page, explore_file, only_empty=only_empty)

                logger.info("\n" + "=" * 70)
                logger.info(f"✅ VIDEOS CRAWLING COMPLETE ({language.upper()})")
                logger.info("=" * 70)
            else:
                # Crawl all languages
                logger.info("\n🎬 STEP 4: Crawl Videos (All Languages)")
                languages = sites_manager.get_languages()

                for idx, lang in enumerate(languages, 1):
                    logger.info(f"\n{'=' * 70}")
                    logger.info(f"🌐 LANGUAGE {idx}/{len(languages)}: {lang.upper()}")
                    logger.info(f"{'=' * 70}")

                    # Learn content
                    learn_file = sites_manager.get_content_file_path(lang, "learn-content")
                    logger.info(f"\n📚 Part 1: {lang.upper()} learn-content videos...")
                    await crawl_all_videos(page, learn_file, only_empty=only_empty)

                    logger.info("\n⏳ Waiting 10 seconds...")
                    await asyncio.sleep(10)

                    # Explore content
                    explore_file = sites_manager.get_content_file_path(lang, "explore-content")
                    logger.info(f"\n📚 Part 2: {lang.upper()} explore-content...")
                    await crawl_all_videos(page, explore_file, only_empty=only_empty)

                    if idx < len(languages):
                        logger.info("\n⏳ Waiting 15 seconds before next language...")
                        await asyncio.sleep(15)

                logger.info("\n" + "=" * 70)
                logger.info("✅ VIDEOS CRAWLING COMPLETE (ALL LANGUAGES)")
                logger.info("=" * 70)

            # Close browser
            logger.info("\n👋 Closing browser...")

        elif mode == "downloads":
            # Determine which language(s) to download
            sites_manager = SitesManager()

            if language:
                # Single language
                logger.info(f"\n📥 STEP 4: Download Videos ({language.upper()})")
                logger.info("\nDownloading videos from both learn-content and explore-content...")

                # Learn content
                learn_file = sites_manager.get_content_file_path(language, "learn-content")
                logger.info(f"\n📥 Part 1: Downloading from {learn_file}...")
                await download_all_videos(page, learn_file, only_empty=only_empty)

                logger.info("\n⏳ Waiting 10 seconds...")
                await asyncio.sleep(10)

                # Explore content
                explore_file = sites_manager.get_content_file_path(language, "explore-content")
                logger.info(f"\n📥 Part 2: Downloading from {explore_file}...")
                await download_all_videos(page, explore_file, only_empty=only_empty)

                logger.info("\n" + "=" * 70)
                logger.info(f"✅ VIDEO DOWNLOAD COMPLETE ({language.upper()})")
                logger.info("=" * 70)
            else:
                # Download all languages
                logger.info("\n📥 STEP 4: Download Videos (All Languages)")
                languages = sites_manager.get_languages()

                for idx, lang in enumerate(languages, 1):
                    logger.info(f"\n{'=' * 70}")
                    logger.info(f"🌐 LANGUAGE {idx}/{len(languages)}: {lang.upper()}")
                    logger.info(f"{'=' * 70}")

                    # Learn content
                    learn_file = sites_manager.get_content_file_path(lang, "learn-content")
                    logger.info(f"\n📥 Part 1: {lang.upper()} learn-content...")
                    await download_all_videos(page, learn_file, only_empty=only_empty)

                    logger.info("\n⏳ Waiting 10 seconds...")
                    await asyncio.sleep(10)

                    # Explore content
                    explore_file = sites_manager.get_content_file_path(lang, "explore-content")
                    logger.info(f"\n📥 Part 2: {lang.upper()} explore-content...")
                    await download_all_videos(page, explore_file, only_empty=only_empty)

                    if idx < len(languages):
                        logger.info("\n⏳ Waiting 15 seconds before next language...")
                        await asyncio.sleep(15)

                logger.info("\n" + "=" * 70)
                logger.info("✅ VIDEO DOWNLOAD COMPLETE (ALL LANGUAGES)")
                logger.info("=" * 70)

            # Close browser
            logger.info("\n👋 Closing browser...")

        elif mode == "all":
            logger.info("\n🚀 STEP 4: Crawl Everything (Categories + Series + Courses + Content)")

            # Part 1: Crawl categories
            logger.info("\n📚 Part 1: Crawling Categories...")
            cat_success = await crawl_all_categories(page, only_empty=only_empty)

            if cat_success:
                logger.info(f"✅ Categories done: {LEARN_CONTENT_FILE}")
            else:
                logger.error("❌ Category crawling failed")

            # Wait between crawls
            logger.info("\n⏳ Waiting 10 seconds before series...")
            await asyncio.sleep(10)

            # Part 2: Crawl series
            logger.info("\n🎬 Part 2: Crawling Series...")
            series_success = await crawl_all_series(page, only_empty=only_empty)

            if series_success:
                logger.info(f"✅ Series done: {EXPLORE_CONTENT_FILE}")
            else:
                logger.error("❌ Series crawling failed")

            # Wait before course details
            logger.info("\n⏳ Waiting 10 seconds before course details...")
            await asyncio.sleep(10)

            # Part 3: Crawl course details from learn-content
            logger.info("\n📚 Part 3a: Crawling course details from learn-content...")
            learn_courses_success = await crawl_all_courses(page, LEARN_CONTENT_FILE, only_empty=only_empty)

            if learn_courses_success:
                logger.info(f"✅ Learn content course details done: {LEARN_CONTENT_FILE}")
            else:
                logger.error("❌ Learn content course crawling failed")

            # Wait between course crawls
            logger.info("\n⏳ Waiting 10 seconds...")
            await asyncio.sleep(10)

            # Part 3b: Crawl course details from explore-content
            logger.info("\n📚 Part 3b: Crawling course details from explore-content...")
            explore_courses_success = await crawl_all_courses(page, EXPLORE_CONTENT_FILE, only_empty=only_empty)

            if explore_courses_success:
                logger.info(f"✅ Explore content course details done: {EXPLORE_CONTENT_FILE}")
            else:
                logger.error("❌ Explore content course crawling failed")

            # Wait before content extraction
            logger.info("\n⏳ Waiting 10 seconds before content extraction...")
            await asyncio.sleep(10)

            # Part 4a: Extract content from learn-content
            logger.info("\n📄 Part 4a: Extracting content from learn-content...")
            learn_content_success = await crawl_all_videos(page, LEARN_CONTENT_FILE, only_empty=only_empty)

            if learn_content_success:
                logger.info(f"✅ Learn content extraction done")
            else:
                logger.error("❌ Learn content extraction failed")

            # Wait between content extractions
            logger.info("\n⏳ Waiting 10 seconds...")
            await asyncio.sleep(10)

            # Part 4b: Extract content from explore-content
            logger.info("\n📄 Part 4b: Extracting content from explore-content...")
            explore_content_success = await crawl_all_videos(page, EXPLORE_CONTENT_FILE, only_empty=only_empty)

            if explore_content_success:
                logger.info(f"✅ Explore content extraction done")
            else:
                logger.error("❌ Explore content extraction failed")

            # Final summary
            logger.info("\n" + "=" * 70)
            logger.info("✅ ALL CRAWLING COMPLETE")
            logger.info("=" * 70)
            logger.info(f"📊 Categories: {LEARN_CONTENT_FILE}")
            logger.info(f"📊 Series: {EXPLORE_CONTENT_FILE}")
            logger.info(f"📊 Content: Extracted to downloads/ directory")

            # Close browser
            logger.info("\n👋 Closing browser...")

        else:
            logger.error(f"❌ Invalid mode: {mode}")
            logger.info("Valid modes: 'test', 'categories', 'series', 'courses', 'content', 'downloads', 'all'")

    finally:
        # Cleanup
        await context.close()
        await playwright.stop()
        logger.info("✅ Browser closed cleanly")


if __name__ == "__main__":
    # Parse command line arguments
    mode = "test"  # Default mode
    language = None  # Default: all languages or EN
    only_empty = False  # Default: crawl all items

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    # Check for language and --only-empty flag
    for i in range(2, len(sys.argv)):
        arg = sys.argv[i].lower()
        if arg == "--only-empty":
            only_empty = True
        elif arg in ["en", "ja"]:
            language = arg

    # Validate mode
    if mode not in ["sites", "init", "test", "categories", "series", "courses", "content", "downloads", "all"]:
        logger.error(f"❌ Invalid mode: {mode}")
        logger.info("Usage: python3 run_browser.py [mode] [language]")
        logger.info("")
        logger.info("Modes:")
        logger.info("  init       - Copy Chrome profile (cookies + sessions) for authentication")
        logger.info("  sites      - Crawl initial categories/series from sites.json URLs")
        logger.info("  categories - Crawl all categories (learn-content)")
        logger.info("  series     - Crawl all series (explore-content)")
        logger.info("  courses    - Crawl course details (overview, transcript, duration)")
        logger.info("  content    - Extract course content (overview/transcript/summary) to txt files")
        logger.info("  downloads  - Download all videos")
        logger.info("  test       - Test single category parsing (debug mode)")
        logger.info("  all        - Crawl categories + series + courses + content")
        logger.info("")
        logger.info("Language (optional):")
        logger.info("  en         - English only")
        logger.info("  ja         - Japanese only")
        logger.info("  (none)     - All languages (for sites) or default EN (for other modes)")
        logger.info("")
        logger.info("Flags:")
        logger.info("  --only-empty  - Only crawl items with empty data (skip completed)")
        logger.info("")
        logger.info("Examples:")
        logger.info("  python3 run_browser.py sites          # Parse all languages from sites.json")
        logger.info("  python3 run_browser.py sites en       # Parse English categories/series")
        logger.info("  python3 run_browser.py sites ja       # Parse Japanese categories/series")
        logger.info("  python3 run_browser.py categories en  # Crawl English category details")
        logger.info("  python3 run_browser.py courses --only-empty      # Only crawl courses with empty learning_points")
        logger.info("  python3 run_browser.py categories ja --only-empty  # Only crawl Japanese categories with empty courses")
        sys.exit(1)

    asyncio.run(main(mode, language, only_empty))

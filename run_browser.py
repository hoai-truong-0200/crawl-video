#!/usr/bin/env python3
"""
GLOBIS Browser Automation with Chrome Profile

WORKFLOW:
1. Copy Chrome user profile (if not exists) - ONLY ONCE
2. Launch Chrome with copied profile + anti-bot protection
3. Manual login (if needed) - ONLY ONCE, session persists
4. Choose mode:
   - test: Test single category parsing
   - crawl: Crawl all categories and save to JSON

Usage:
    python3 run_browser.py test     # Test single category parsing
    python3 run_browser.py crawl    # Crawl all categories (learn-content)
    python3 run_browser.py series   # Crawl all series (explore-content)
    python3 run_browser.py all      # Crawl both categories and series

Future updates: Just modify this single file
"""

import asyncio
import shutil
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from src.browser.stealth_config import (
    get_browser_launch_args,
    apply_stealth_to_page
)
from src.crawler.category_parser import CategoryParser
from src.crawler.category_crawler import CategoryCrawler
from src.crawler.series_crawler import SeriesCrawler
from src.crawler.course_crawler import CourseCrawler
from loguru import logger


# ============================================================
# CONFIGURATION
# ============================================================

# Chrome profile paths
SOURCE_PROFILE = Path.home() / ".config/google-chrome/Profile 1"
DEST_PROFILE = Path("data/chrome_profile_copy")

# GLOBIS URLs
LOGIN_URL = "https://unlimited.globis.co.jp/signin?locale=en"
SUCCESS_INDICATOR = "a[href*='signout']"  # Element visible when logged in

# Content files
LEARN_CONTENT_FILE = Path("data/courses/learn-content.json")
EXPLORE_CONTENT_FILE = Path("data/courses/explore-content.json")


# ============================================================
# STEP 1: COPY CHROME PROFILE
# ============================================================

def copy_chrome_profile() -> bool:
    """Copy Chrome profile if not exists"""

    if DEST_PROFILE.exists():
        logger.info(f"✅ Chrome profile already exists: {DEST_PROFILE}")
        return True

    if not SOURCE_PROFILE.exists():
        logger.error(f"❌ Source Chrome profile not found: {SOURCE_PROFILE}")
        logger.info("Available Chrome profiles:")
        chrome_dir = Path.home() / ".config/google-chrome"
        if chrome_dir.exists():
            for item in chrome_dir.iterdir():
                if item.is_dir() and ("Profile" in item.name or item.name == "Default"):
                    logger.info(f"  - {item.name}")
        return False

    logger.info(f"📋 Copying Chrome profile...")
    logger.info(f"   From: {SOURCE_PROFILE}")
    logger.info(f"   To:   {DEST_PROFILE}")

    try:
        # Get profile size
        import subprocess
        result = subprocess.run(
            ["du", "-sh", str(SOURCE_PROFILE)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            size = result.stdout.split()[0]
            logger.info(f"   Size: {size}")

        # Copy profile
        shutil.copytree(SOURCE_PROFILE, DEST_PROFILE, dirs_exist_ok=True)
        logger.info("✅ Chrome profile copied successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to copy profile: {e}")
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
        "a[href*='signout']",
        "a[href*='/signout']",
        "[href*='signout']",
        "text=Sign Out",
        "text=サインアウト",
    ]

    is_logged_in = False
    for selector in login_indicators:
        try:
            elem = await page.query_selector(selector)
            if elem:
                logger.info(f"✅ Already logged in! (found: {selector})")
                is_logged_in = True
                break
        except Exception:
            continue

    # Also check if we're NOT on login page
    current_url = page.url
    if "/signin" not in current_url.lower() and not is_logged_in:
        # Might be logged in, just can't find selector
        logger.info(f"✅ On home page (not login page): {current_url}")
        logger.info("Assuming logged in (not on signin page)")
        is_logged_in = True

    if is_logged_in:
        return True

    # Not logged in - need manual login
    logger.warning("⚠️  Not logged in yet")
    logger.info(f"🔗 Navigating to login page: {LOGIN_URL}")

    await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

    logger.info("\n" + "=" * 60)
    logger.info("👉 PLEASE LOGIN MANUALLY")
    logger.info("=" * 60)
    logger.info("Steps:")
    logger.info("  1. Enter your GLOBIS credentials in the browser")
    logger.info("  2. Click 'Sign In'")
    logger.info("  3. Wait for redirect to home page")
    logger.info("\n⏳ Waiting for login... (timeout: 10 minutes)")
    logger.info("Looking for these indicators:")
    for indicator in login_indicators:
        logger.info(f"  - {indicator}")

    # Wait for login success - check multiple conditions
    start_time = asyncio.get_event_loop().time()
    timeout_seconds = 600  # 10 minutes

    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout_seconds:
            logger.error("❌ Login timeout (10 minutes)")
            return False

        # Check if URL changed away from login page
        current_url = page.url
        if "/signin" not in current_url.lower():
            logger.info(f"\n✅ URL changed from login page: {current_url}")
            await asyncio.sleep(2)  # Wait for page to settle

            # Double-check with selectors
            for selector in login_indicators:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        logger.info(f"✅ LOGIN SUCCESSFUL! (found: {selector})")
                        logger.info("🎉 Session saved - you won't need to login again!")
                        await asyncio.sleep(2)
                        return True
                except Exception:
                    continue

            # If URL changed but no selector found, assume success anyway
            logger.info("✅ LOGIN SUCCESSFUL! (URL redirected)")
            logger.info("🎉 Session saved - you won't need to login again!")
            await asyncio.sleep(2)
            return True

        # Wait a bit before next check
        await asyncio.sleep(1)


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

async def crawl_all_categories(page):
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
        stats = await crawler.crawl_all_categories(page)

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

async def crawl_all_series(page):
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
        stats = await crawler.crawl_all_series(page)

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
# MAIN WORKFLOW
# ============================================================

async def main(mode: str = "test"):
    """
    Main workflow

    Args:
        mode: "test", "crawl", "series", or "all"
    """

    logger.info("\n" + "=" * 70)
    logger.info("🎯 GLOBIS BROWSER AUTOMATION")
    logger.info(f"   Mode: {mode.upper()}")
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
        if mode == "test":
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

        elif mode == "crawl":
            logger.info("\n🚀 STEP 4: Crawl All Categories (Learn Content)")
            success = await crawl_all_categories(page)

            if success:
                logger.info("\n" + "=" * 70)
                logger.info("✅ CRAWLING COMPLETE")
                logger.info("=" * 70)
                logger.info(f"📊 Results saved to: {LEARN_CONTENT_FILE}")
            else:
                logger.error("\n❌ Crawling failed")

            # Close browser automatically after crawling
            logger.info("\n👋 Closing browser...")

        elif mode == "series":
            logger.info("\n🎬 STEP 4: Crawl All Series (Explore Content)")
            success = await crawl_all_series(page)

            if success:
                logger.info("\n" + "=" * 70)
                logger.info("✅ SERIES CRAWLING COMPLETE")
                logger.info("=" * 70)
                logger.info(f"📊 Results saved to: {EXPLORE_CONTENT_FILE}")
            else:
                logger.error("\n❌ Crawling failed")

            # Close browser automatically
            logger.info("\n👋 Closing browser...")

        elif mode == "all":
            logger.info("\n🚀 STEP 4: Crawl Everything (Categories + Series)")

            # Crawl categories first
            logger.info("\n📚 Part 1: Crawling Categories...")
            cat_success = await crawl_all_categories(page)

            if cat_success:
                logger.info(f"✅ Categories done: {LEARN_CONTENT_FILE}")
            else:
                logger.error("❌ Category crawling failed")

            # Wait a bit between crawls
            logger.info("\n⏳ Waiting 10 seconds before series...")
            await asyncio.sleep(10)

            # Crawl series
            logger.info("\n🎬 Part 2: Crawling Series...")
            series_success = await crawl_all_series(page)

            if series_success:
                logger.info(f"✅ Series done: {EXPLORE_CONTENT_FILE}")
            else:
                logger.error("❌ Series crawling failed")

            # Final summary
            logger.info("\n" + "=" * 70)
            logger.info("✅ ALL CRAWLING COMPLETE")
            logger.info("=" * 70)
            logger.info(f"📊 Categories: {LEARN_CONTENT_FILE}")
            logger.info(f"📊 Series: {EXPLORE_CONTENT_FILE}")

            # Close browser
            logger.info("\n👋 Closing browser...")

        else:
            logger.error(f"❌ Invalid mode: {mode}")
            logger.info("Valid modes: 'test', 'crawl', 'series', 'all'")

    finally:
        # Cleanup
        await context.close()
        await playwright.stop()
        logger.info("✅ Browser closed cleanly")


if __name__ == "__main__":
    # Parse command line arguments
    mode = "test"  # Default mode
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    # Validate mode
    if mode not in ["test", "crawl", "series", "all"]:
        logger.error(f"❌ Invalid mode: {mode}")
        logger.info("Usage: python3 run_browser.py [test|crawl|series|all]")
        logger.info("  test   - Test single category parsing (default)")
        logger.info("  crawl  - Crawl all categories (learn-content)")
        logger.info("  series - Crawl all series (explore-content)")
        logger.info("  all    - Crawl both categories and series")
        sys.exit(1)

    asyncio.run(main(mode))

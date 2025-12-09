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
├─────────────┼──────────────────────────────────────────────────────────────┤
│ series      │ Crawl detailed info for each series (explore-content)        │
│             │ - Gets course count, description, image                       │
│             │ - Auto-clicks "Show More" to load all courses                 │
│             │ - Saves incrementally after each series                       │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ courses     │ Crawl course details from categories/series                  │
│             │ - Extracts: duration + learning_points + videos + vimeo_urls │
│             │ - Clicks "Content" tab to parse learning point structure      │
│             │ - Groups videos by learning objectives                        │
│             │ - Saves incrementally after each course                       │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ videos      │ Extract video details (overview + transcript)                │
│             │ - For each video in all courses                               │
│             │ - NOT YET IMPLEMENTED                                         │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ downloads   │ Download videos using vimeo_url from courses                 │
│             │ - NOT YET IMPLEMENTED                                         │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ all         │ Run full workflow: sites → categories → series → courses     │
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

    python3 run_browser.py videos           # Extract video details (NOT IMPLEMENTED)
    python3 run_browser.py downloads        # Download videos (NOT IMPLEMENTED)
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

NOTE: 'init' option reserved for future Chrome profile copying feature
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
from src.crawler.content_manager import ContentManager, Category, Series
from src.utils.sites_manager import SitesManager
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

# Content files (default to English)
LEARN_CONTENT_FILE = Path("data/courses/en/learn-content.json")
EXPLORE_CONTENT_FILE = Path("data/courses/en/explore-content.json")


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
# STEP 4D: CRAWL COURSE DETAILS (OVERVIEW, TRANSCRIPT, DURATION)
# ============================================================

async def crawl_all_courses(page, content_file=None):
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
        stats = await crawler.crawl_all_courses(page)

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

async def crawl_all_videos(page, content_file=None):
    """
    Crawl videos from all courses in learn-content.json or explore-content.json

    Args:
        page: Playwright Page object
        content_file: Path to content file (defaults to LEARN_CONTENT_FILE)
    """

    if content_file is None:
        content_file = LEARN_CONTENT_FILE

    logger.info("\n" + "=" * 60)
    logger.info(f"🎬 CRAWL VIDEOS FROM ALL COURSES")
    logger.info(f"   Content file: {content_file}")
    logger.info("=" * 60)

    try:
        # Create crawler
        crawler = CourseCrawler(
            content_file=content_file,
            min_delay=1.5,
            max_delay=3.0,
            max_retries=3,
        )

        # Crawl all courses to extract videos
        stats = await crawler.crawl_all_courses(page)

        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ VIDEO CRAWLING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Results saved to: {content_file}")

        return True

    except Exception as e:
        logger.error(f"❌ Video crawler error: {e}")
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

async def download_all_videos(page, content_file=None):
    """
    Download all videos from courses in learn-content.json or explore-content.json

    Args:
        page: Playwright Page object
        content_file: Path to content file (defaults to LEARN_CONTENT_FILE)

    Returns:
        bool: True if successful, False otherwise
    """

    if content_file is None:
        content_file = LEARN_CONTENT_FILE

    logger.info("\n" + "=" * 60)
    logger.info(f"📥 DOWNLOAD VIDEOS FROM ALL COURSES")
    logger.info(f"   Content file: {content_file}")
    logger.info("=" * 60)

    try:
        # Create crawler with download enabled
        language = "en" if "en" in str(content_file) else "ja"

        crawler = CourseCrawler(
            content_file=content_file,
            language=language,
            min_delay=2.0,
            max_delay=4.0,
            max_retries=3,
            enable_download=True,  # Enable video downloading
        )

        # Crawl all courses and download videos
        stats = await crawler.crawl_all_courses(page)

        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ VIDEO DOWNLOAD COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Videos downloaded: {stats.get('videos_downloaded', 0)}")
        logger.info(f"📊 Videos failed: {stats.get('videos_download_failed', 0)}")
        logger.info(f"📊 Total videos found: {stats.get('total_videos_found', 0)}")

        return True

    except Exception as e:
        logger.error(f"❌ Video download error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# MAIN WORKFLOW
# ============================================================

async def main(mode: str = "test", language: str = None):
    """
    Main workflow

    Args:
        mode: "init", "test", "categories", "series", "courses", "videos", "downloads", or "all"
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
            # NEW: Simple Chrome profile copy functionality
            logger.info("\n📋 STEP 4: Copy Chrome Profile")
            logger.info("\nThis feature will copy Chrome profile for authentication.")
            logger.info("Currently under development - use 'sites' option instead.")
            logger.info("\nUsage:")
            logger.info("  python3 run_browser.py sites [language]")

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

                stats = await crawler.crawl_all_series(page)

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

                    stats = await crawler.crawl_all_series(page)
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
                await crawl_all_courses(page, learn_file)

                logger.info("\n⏳ Waiting 10 seconds...")
                await asyncio.sleep(10)

                # Explore content
                explore_file = sites_manager.get_content_file_path(language, "explore-content")
                logger.info(f"\n📚 Part 2: Crawling courses from {explore_file}...")
                await crawl_all_courses(page, explore_file)

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
                    await crawl_all_courses(page, learn_file)

                    logger.info("\n⏳ Waiting 10 seconds...")
                    await asyncio.sleep(10)

                    # Explore content
                    explore_file = sites_manager.get_content_file_path(lang, "explore-content")
                    logger.info(f"\n📚 Part 2: {lang.upper()} explore-content...")
                    await crawl_all_courses(page, explore_file)

                    if idx < len(languages):
                        logger.info("\n⏳ Waiting 15 seconds before next language...")
                        await asyncio.sleep(15)

                logger.info("\n" + "=" * 70)
                logger.info("✅ COURSES CRAWLING COMPLETE (ALL LANGUAGES)")
                logger.info("=" * 70)

            # Close browser
            logger.info("\n👋 Closing browser...")

        elif mode == "videos":
            # Determine which language(s) to crawl
            sites_manager = SitesManager()

            if language:
                # Single language
                logger.info(f"\n🎬 STEP 4: Crawl Videos ({language.upper()})")
                logger.info("\nCrawling videos from both learn-content and explore-content...")

                # Learn content
                learn_file = sites_manager.get_content_file_path(language, "learn-content")
                logger.info(f"\n📚 Part 1: Crawling videos from {learn_file}...")
                await crawl_all_videos(page, learn_file)

                logger.info("\n⏳ Waiting 10 seconds...")
                await asyncio.sleep(10)

                # Explore content
                explore_file = sites_manager.get_content_file_path(language, "explore-content")
                logger.info(f"\n🎬 Part 2: Crawling videos from {explore_file}...")
                await crawl_all_videos(page, explore_file)

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
                    await crawl_all_videos(page, learn_file)

                    logger.info("\n⏳ Waiting 10 seconds...")
                    await asyncio.sleep(10)

                    # Explore content
                    explore_file = sites_manager.get_content_file_path(lang, "explore-content")
                    logger.info(f"\n🎬 Part 2: {lang.upper()} explore-content videos...")
                    await crawl_all_videos(page, explore_file)

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
                await download_all_videos(page, learn_file)

                logger.info("\n⏳ Waiting 10 seconds...")
                await asyncio.sleep(10)

                # Explore content
                explore_file = sites_manager.get_content_file_path(language, "explore-content")
                logger.info(f"\n📥 Part 2: Downloading from {explore_file}...")
                await download_all_videos(page, explore_file)

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
                    await download_all_videos(page, learn_file)

                    logger.info("\n⏳ Waiting 10 seconds...")
                    await asyncio.sleep(10)

                    # Explore content
                    explore_file = sites_manager.get_content_file_path(lang, "explore-content")
                    logger.info(f"\n📥 Part 2: {lang.upper()} explore-content...")
                    await download_all_videos(page, explore_file)

                    if idx < len(languages):
                        logger.info("\n⏳ Waiting 15 seconds before next language...")
                        await asyncio.sleep(15)

                logger.info("\n" + "=" * 70)
                logger.info("✅ VIDEO DOWNLOAD COMPLETE (ALL LANGUAGES)")
                logger.info("=" * 70)

            # Close browser
            logger.info("\n👋 Closing browser...")

        elif mode == "all":
            logger.info("\n🚀 STEP 4: Crawl Everything (Categories + Series + Courses + Videos)")

            # Part 1: Crawl categories
            logger.info("\n📚 Part 1: Crawling Categories...")
            cat_success = await crawl_all_categories(page)

            if cat_success:
                logger.info(f"✅ Categories done: {LEARN_CONTENT_FILE}")
            else:
                logger.error("❌ Category crawling failed")

            # Wait between crawls
            logger.info("\n⏳ Waiting 10 seconds before series...")
            await asyncio.sleep(10)

            # Part 2: Crawl series
            logger.info("\n🎬 Part 2: Crawling Series...")
            series_success = await crawl_all_series(page)

            if series_success:
                logger.info(f"✅ Series done: {EXPLORE_CONTENT_FILE}")
            else:
                logger.error("❌ Series crawling failed")

            # Wait before course details
            logger.info("\n⏳ Waiting 10 seconds before course details...")
            await asyncio.sleep(10)

            # Part 3: Crawl course details from learn-content
            logger.info("\n📚 Part 3a: Crawling course details from learn-content...")
            learn_courses_success = await crawl_all_courses(page, LEARN_CONTENT_FILE)

            if learn_courses_success:
                logger.info(f"✅ Learn content course details done: {LEARN_CONTENT_FILE}")
            else:
                logger.error("❌ Learn content course crawling failed")

            # Wait between course crawls
            logger.info("\n⏳ Waiting 10 seconds...")
            await asyncio.sleep(10)

            # Part 3b: Crawl course details from explore-content
            logger.info("\n📚 Part 3b: Crawling course details from explore-content...")
            explore_courses_success = await crawl_all_courses(page, EXPLORE_CONTENT_FILE)

            if explore_courses_success:
                logger.info(f"✅ Explore content course details done: {EXPLORE_CONTENT_FILE}")
            else:
                logger.error("❌ Explore content course crawling failed")

            # Wait before video crawling
            logger.info("\n⏳ Waiting 10 seconds before video crawling...")
            await asyncio.sleep(10)

            # Part 4a: Crawl videos from learn-content
            logger.info("\n📹 Part 4a: Crawling videos from learn-content...")
            learn_videos_success = await crawl_all_videos(page, LEARN_CONTENT_FILE)

            if learn_videos_success:
                logger.info(f"✅ Learn content videos done: {LEARN_CONTENT_FILE}")
            else:
                logger.error("❌ Learn content video crawling failed")

            # Wait between video crawls
            logger.info("\n⏳ Waiting 10 seconds...")
            await asyncio.sleep(10)

            # Part 4b: Crawl videos from explore-content
            logger.info("\n📹 Part 4b: Crawling videos from explore-content...")
            explore_videos_success = await crawl_all_videos(page, EXPLORE_CONTENT_FILE)

            if explore_videos_success:
                logger.info(f"✅ Explore content videos done: {EXPLORE_CONTENT_FILE}")
            else:
                logger.error("❌ Explore content video crawling failed")

            # Final summary
            logger.info("\n" + "=" * 70)
            logger.info("✅ ALL CRAWLING COMPLETE")
            logger.info("=" * 70)
            logger.info(f"📊 Categories: {LEARN_CONTENT_FILE}")
            logger.info(f"📊 Series: {EXPLORE_CONTENT_FILE}")
            logger.info(f"📊 Videos: Both files updated with video information")

            # Close browser
            logger.info("\n👋 Closing browser...")

        else:
            logger.error(f"❌ Invalid mode: {mode}")
            logger.info("Valid modes: 'test', 'categories', 'series', 'courses', 'videos', 'downloads', 'all'")

    finally:
        # Cleanup
        await context.close()
        await playwright.stop()
        logger.info("✅ Browser closed cleanly")


if __name__ == "__main__":
    # Parse command line arguments
    mode = "test"  # Default mode
    language = None  # Default: all languages or EN

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    if len(sys.argv) > 2:
        language = sys.argv[2].lower()

    # Validate mode
    if mode not in ["sites", "init", "test", "categories", "series", "courses", "videos", "downloads", "all"]:
        logger.error(f"❌ Invalid mode: {mode}")
        logger.info("Usage: python3 run_browser.py [mode] [language]")
        logger.info("")
        logger.info("Modes:")
        logger.info("  sites      - Crawl initial categories/series from sites.json URLs (NEW!)")
        logger.info("  init       - Copy Chrome profile for authentication (under development)")
        logger.info("  test       - Test single category parsing (default)")
        logger.info("  categories - Crawl all categories (learn-content)")
        logger.info("  series     - Crawl all series (explore-content)")
        logger.info("  courses    - Crawl course details (overview, transcript, duration)")
        logger.info("  videos     - Crawl videos from all courses")
        logger.info("  downloads  - Download all videos (Phase 4)")
        logger.info("  all        - Crawl categories + series + courses + videos")
        logger.info("")
        logger.info("Language (optional):")
        logger.info("  en         - English only")
        logger.info("  ja         - Japanese only")
        logger.info("  (none)     - All languages (for sites) or default EN (for other modes)")
        logger.info("")
        logger.info("Examples:")
        logger.info("  python3 run_browser.py sites          # Parse all languages from sites.json")
        logger.info("  python3 run_browser.py sites en       # Parse English categories/series")
        logger.info("  python3 run_browser.py sites ja       # Parse Japanese categories/series")
        logger.info("  python3 run_browser.py categories en  # Crawl English category details")
        sys.exit(1)

    asyncio.run(main(mode, language))

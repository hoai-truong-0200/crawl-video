"""
Extract DOM from Real GLOBIS Course

Direct navigation to a specific course URL to save DOM for analysis.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser.browser_manager import BrowserManager

# Configure logger
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    colorize=True,
)


# Real course URL
COURSE_URL = "https://unlimited.globis.co.jp/en/courses/d8501fa9/learn/steps"


async def extract_course_dom():
    """Extract DOM from real course page"""
    logger.info("\n" + "="*70)
    logger.info("🌐 EXTRACT REAL COURSE DOM")
    logger.info("="*70)
    logger.info(f"Course URL: {COURSE_URL}")

    browser_manager = None
    session_file = Path("data/sessions/globis_session.json")

    try:
        # Start browser with session support
        logger.info("\n📱 Starting browser...")

        # Check if session exists
        if session_file.exists():
            logger.info(f"📂 Loading session: {session_file}")
            browser_manager = BrowserManager(session_file=session_file)
        else:
            logger.info("🆕 No session found")
            browser_manager = BrowserManager()

        page = await browser_manager.start()

        # Enable console logging from browser
        page.on("console", lambda msg: logger.debug(f"🖥️  Browser: {msg.text}"))
        page.on("pageerror", lambda err: logger.error(f"🔴 Page Error: {err}"))

        # Navigate directly to course URL
        logger.info(f"\n🚀 Navigating to course page...")
        await page.goto(COURSE_URL, wait_until="domcontentloaded", timeout=60000)

        # Wait for page to fully load
        logger.info("⏳ Waiting for page to load...")
        await page.wait_for_timeout(5000)

        # Check current URL
        current_url = page.url
        logger.info(f"📍 Current URL: {current_url}")

        # Check if redirected
        if current_url != COURSE_URL:
            logger.warning(f"⚠️  Redirected to: {current_url}")

            if "/error" in current_url:
                logger.error("❌ Redirected to error page!")
                logger.error("   Possible reasons:")
                logger.error("   - Not logged in")
                logger.error("   - Session expired")
                logger.error("   - No access to this course")
                logger.error("   - Region restricted")

                logger.info("\n🔐 Trying to login...")
                await page.goto("https://unlimited.globis.co.jp/en/signin", wait_until="domcontentloaded")

                logger.info("\n" + "="*70)
                logger.info("PLEASE LOGIN:")
                logger.info("1. Login in the browser window")
                logger.info("2. Press ENTER after logging in")
                logger.info("="*70)
                input("\n👉 Press ENTER after login...")

                # Save session
                logger.info("💾 Saving session...")
                await browser_manager.save_session(session_file)
                logger.info(f"✅ Session saved")

                # Try navigating to course again
                logger.info(f"\n🔄 Retrying course page...")
                await page.goto(COURSE_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(5000)

                current_url = page.url
                logger.info(f"�� New URL: {current_url}")

                if "/error" in current_url:
                    logger.error("❌ Still redirecting to error page!")
                    return False

        logger.info("✅ Successfully loaded course page!")

        # Wait a bit more for dynamic content
        logger.info("⏳ Waiting for dynamic content to load...")
        await page.wait_for_timeout(3000)

        # Try to scroll to load lazy content
        logger.info("📜 Scrolling to load content...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)

        # Get page content
        html_content = await page.content()

        # Create output directory
        output_dir = Path("tests/dom_samples")
        output_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"real_course_{timestamp}.html"

        # Save HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"\n✅ DOM saved to: {output_file}")
        logger.info(f"   File size: {len(html_content):,} bytes")

        # Save URL for reference
        url_file = output_dir / f"real_course_{timestamp}_url.txt"
        with open(url_file, 'w', encoding='utf-8') as f:
            f.write(f"Original URL: {COURSE_URL}\n")
            f.write(f"Final URL: {current_url}\n")

        logger.info(f"✅ URL saved to: {url_file}")

        # Take screenshot
        screenshot_file = output_dir / f"real_course_{timestamp}.png"
        await page.screenshot(path=str(screenshot_file), full_page=True)
        logger.info(f"✅ Screenshot saved to: {screenshot_file}")

        # Extract some basic info
        logger.info("\n📊 Quick analysis:")

        # Count step links
        step_links = await page.query_selector_all('a[href*="/learn/steps/"]')
        logger.info(f"   - Found {len(step_links)} step links")

        # Look for LearnPoint headers
        lp_elements = await page.query_selector_all('[class*="learningPointName"]')
        logger.info(f"   - Found {len(lp_elements)} LearnPoint headers")

        # Look for overview
        overview_elem = await page.query_selector('meta[name="description"]')
        if overview_elem:
            desc = await overview_elem.get_attribute('content')
            logger.info(f"   - Overview (meta): {desc[:80]}..." if desc and len(desc) > 80 else f"   - Overview: {desc}")

        logger.info("\n" + "="*70)
        logger.info("✅ EXTRACTION COMPLETE")
        logger.info("="*70)
        logger.info(f"\nFiles saved:")
        logger.info(f"  - HTML: {output_file}")
        logger.info(f"  - URL: {url_file}")
        logger.info(f"  - Screenshot: {screenshot_file}")
        logger.info("\nNext: Analyze HTML to update selectors in course_parser.py")

        return True

    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        # Keep browser open for inspection
        if browser_manager:
            logger.info("\n⏸️  Keeping browser open for 30 seconds...")
            logger.info("   You can inspect the page now")
            await asyncio.sleep(30)

            logger.info("\n🔄 Closing browser...")
            await browser_manager.close()


def main():
    """Run the extraction"""
    try:
        result = asyncio.run(extract_course_dom())
        if result:
            logger.info("\n✅ Success!")
        else:
            logger.error("\n❌ Failed")
    except KeyboardInterrupt:
        logger.info("\n⚠️  Cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

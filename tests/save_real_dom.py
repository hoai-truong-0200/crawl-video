"""
Save Real DOM from GLOBIS Course Page

This script will:
1. Open browser and navigate to login page
2. Wait for user to manually login
3. Wait for user to navigate to a course page
4. Save the full page HTML for analysis
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


async def save_dom():
    """Save DOM from real course page"""
    logger.info("\n" + "="*70)
    logger.info("🌐 SAVE REAL DOM FOR ANALYSIS")
    logger.info("="*70)

    browser_manager = None
    session_file = Path("data/sessions/globis_session.json")

    try:
        # Start browser with session support
        logger.info("\n📱 Starting browser...")

        # Check if session exists
        if session_file.exists():
            logger.info(f"📂 Found existing session: {session_file}")
            browser_manager = BrowserManager(session_file=session_file)
        else:
            logger.info("🆕 No session found, will create new one")
            browser_manager = BrowserManager()

        page = await browser_manager.start()

        # Enable console logging from browser
        page.on("console", lambda msg: logger.debug(f"🖥️  Browser: {msg.text}"))
        page.on("pageerror", lambda err: logger.error(f"🔴 Page Error: {err}"))

        # Navigate to Japanese site (more stable)
        logger.info("\n🏠 Navigating to GLOBIS home page...")
        await page.goto("https://unlimited.globis.co.jp/ja", wait_until="domcontentloaded", timeout=30000)

        # Wait a bit for any redirects
        await page.wait_for_timeout(2000)

        current_url = page.url
        logger.info(f"📍 After redirect: {current_url}")

        # Check if redirected to error page
        if "/error" in current_url:
            logger.warning("⚠️  Redirected to error page")
            logger.info("🔐 Trying login page instead...")
            await page.goto("https://unlimited.globis.co.jp/ja/signin", wait_until="domcontentloaded", timeout=30000)
        elif "/signin" in current_url or "/login" in current_url:
            logger.info("📍 Already on login page")
        else:
            logger.info("✅ Successfully loaded main page!")

        logger.info("\n" + "="*70)
        logger.info("INSTRUCTIONS:")
        logger.info("1. Login to GLOBIS Unlimited in the browser window")
        logger.info("2. Navigate to ANY course page")
        logger.info("   Example: https://unlimited.globis.co.jp/ja/courses/xxx/learn/steps")
        logger.info("3. Make sure URL contains '/learn/steps'")
        logger.info("4. Come back here and press ENTER")
        logger.info("="*70)

        # Wait for user confirmation
        input("\n👉 Press ENTER after navigating to a course page...")

        # Get current URL
        current_url = page.url
        logger.info(f"\n📍 Current URL: {current_url}")

        # Validate URL
        if "/error" in current_url:
            logger.error("❌ Page redirected to error page!")
            logger.error("   This usually means:")
            logger.error("   - Not logged in properly")
            logger.error("   - Session expired")
            logger.error("   - Access denied from your region")
            logger.info("\n💡 Try: Navigate manually in browser to course page first")
            return False

        if "/learn/steps" not in current_url and "/courses/" not in current_url:
            logger.warning("⚠️  This doesn't look like a course page")
            logger.warning(f"   Current URL: {current_url}")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False

        # Save full HTML
        html_content = await page.content()

        # Create output directory
        output_dir = Path("tests/dom_samples")
        output_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"course_page_{timestamp}.html"

        # Save HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"\n✅ DOM saved to: {output_file}")
        logger.info(f"   File size: {len(html_content):,} bytes")

        # Also save URL for reference
        url_file = output_dir / f"course_page_{timestamp}_url.txt"
        with open(url_file, 'w', encoding='utf-8') as f:
            f.write(current_url)

        logger.info(f"✅ URL saved to: {url_file}")

        # Take screenshot for reference
        screenshot_file = output_dir / f"course_page_{timestamp}.png"
        await page.screenshot(path=str(screenshot_file), full_page=True)
        logger.info(f"✅ Screenshot saved to: {screenshot_file}")

        logger.info("\n" + "="*70)
        logger.info("✅ DOM EXTRACTION COMPLETE")
        logger.info("="*70)
        logger.info(f"\nFiles saved:")
        logger.info(f"  - HTML: {output_file}")
        logger.info(f"  - URL: {url_file}")
        logger.info(f"  - Screenshot: {screenshot_file}")
        logger.info("\nYou can now analyze the DOM structure to update selectors.")

        return True

    except KeyboardInterrupt:
        logger.info("\n⚠️  Cancelled by user")
        return False

    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        # Cleanup
        if browser_manager:
            logger.info("\n🔄 Closing browser...")
            await browser_manager.close()


def main():
    """Run the DOM saver"""
    try:
        result = asyncio.run(save_dom())
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

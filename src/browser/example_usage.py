"""
Example Usage of Browser Manager

Demonstrates how to use the browser automation with anti-detection.
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.browser.browser_manager import BrowserManager


async def example_basic_navigation():
    """Basic example: Navigate and interact with a page"""

    # Create browser manager
    browser = BrowserManager(
        headless=False,  # Set True for production
        randomness_factor=1.0
    )

    try:
        # Start browser
        page = await browser.start()

        # Navigate to a website
        await browser.navigate_to("https://www.google.com")

        # Simulate reading
        await browser.read_page(min_duration=2, max_duration=4)

        # Scroll down
        await browser.scroll_page("down", distance=500)

        # Click an element (example)
        # await browser.click_element(selector="button#search")

        # Keep browser open for manual inspection
        await asyncio.sleep(5)

    finally:
        await browser.close()


async def example_with_manual_login():
    """Example: Manual login with session saving - GLOBIS"""

    session_file = Path("../../data/sessions/globis_session.json")
    session_file.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("🔐 GLOBIS Smart Login Test")
    print("="*60)

    browser = BrowserManager(
        headless=False,  # Must be False for manual login
        fingerprint_seed="globis-test-session",
        randomness_factor=1.0,
        session_file=session_file  # Auto-load if exists
    )

    try:
        page = await browser.start()
        print("✅ Browser started\n")

        # Check if session is valid by navigating to protected page
        test_url = "https://unlimited.globis.co.jp/ja"
        is_valid = await browser.check_session_valid(
            test_url=test_url,
            login_indicator="signin",
            success_indicator="a[href*='signout'], div.user-menu, .user-name"
        )

        if is_valid:
            print("\n" + "="*60)
            print("✅ EXISTING SESSION IS VALID!")
            print("="*60)
            print("No manual login needed\n")

        else:
            print("\n" + "="*60)
            print("⚠️  SESSION EXPIRED OR NOT FOUND")
            print("="*60)
            print("\nBrowser window will open...")
            print("Please login manually when redirected to login page")
            print("="*60 + "\n")

            # Navigate to GLOBIS login page
            login_url = "https://unlimited.globis.co.jp/signin?locale=en"
            print(f"🔗 Navigating to: {login_url}\n")

            await browser.navigate_to(login_url)

            print("="*60)
            print("👤 PLEASE LOGIN IN THE BROWSER WINDOW")
            print("="*60)
            print("\nWaiting for login (timeout: 10 minutes)...")
            print("After login, page will redirect to /ja")
            print("="*60 + "\n")

            # Wait for manual login with multiple possible success indicators
            # After successful login, GLOBIS redirects to /ja
            success = await browser.wait_for_manual_login(
                success_indicator="a[href*='signout'], div.user-menu, .user-name",
                timeout=600000  # 10 minutes
            )

            if success:
                print("\n✅ Login successful!")

                # Save session for future use
                print(f"💾 Saving session to: {session_file}")
                await browser.save_session(session_file)
                print("✅ Session saved!\n")

            else:
                print("\n❌ Login timeout or failed\n")
                return

        # Test post-login navigation
        print("🧪 Testing post-login navigation...")
        await browser.navigate_to("https://unlimited.globis.co.jp/en/categories/critical-thinking-communication")

        title = await page.title()
        print(f"📄 Page: {title}\n")

        # Simulate reading
        await browser.read_page(min_duration=2, max_duration=3)

        print("="*60)
        print("✅ TEST COMPLETED!")
        print("="*60)
        print(f"\nSession saved to: {session_file}")
        print("Next time you run this, it will auto-login!")
        print("\nBrowser will close in 10 seconds...")
        print("="*60 + "\n")

        await asyncio.sleep(10)

    finally:
        await browser.close()
        print("\n✅ Browser closed\n")


async def example_load_existing_session():
    """Example: Load saved session and continue"""

    session_file = Path("../../data/sessions/globis_session.json")

    browser = BrowserManager(
        headless=True,
        session_file=session_file  # Auto-loads session
    )

    try:
        page = await browser.start()

        # Session already loaded, navigate directly (already authenticated)
        await browser.navigate_to("https://unlimited.globis.co.jp/en/dashboard")

        # Your crawling logic here...

    finally:
        await browser.close()


async def example_context_manager():
    """Example: Using context manager (recommended)"""

    async with BrowserManager(headless=False) as browser:
        # Browser automatically started
        page = browser.get_page()

        # Your automation code
        await browser.navigate_to("https://example.com")
        await browser.read_page()

        # Browser automatically closed after this block


async def example_advanced_interaction():
    """Example: Advanced interaction with behavior simulation"""

    async with BrowserManager(headless=False, randomness_factor=1.5) as browser:
        page = browser.get_page()
        behavior = browser.get_behavior_sim()

        # Navigate
        await browser.navigate_to("https://example.com")

        # Simulate reading with scrolling
        await behavior.simulate_reading(min_duration=3, max_duration=6)

        # Random mouse movements
        await behavior.random_mouse_movement()

        # Human-like form filling
        await behavior.simulate_form_typing(
            selector="input#search",
            text="machine learning",
            typing_speed="human"
        )

        # Thinking time before submit
        await behavior.simulate_idle_time(min_seconds=1, max_seconds=2)

        # Click submit with human-like movement
        await browser.click_element(selector="button#submit")


if __name__ == "__main__":
    # Configure logging
    logger.add(
        "../../logs/browser_example.log",
        rotation="1 MB",
        level="DEBUG"
    )

    # Run manual login example
    print("\n🚀 Starting GLOBIS Manual Login Test...")
    asyncio.run(example_with_manual_login())
    print("✅ Test completed!\n")

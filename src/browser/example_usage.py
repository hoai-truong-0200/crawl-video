"""
Example Usage of Browser Manager

Demonstrates how to use the browser automation with anti-detection.
"""

import asyncio
from pathlib import Path
from loguru import logger

from browser_manager import BrowserManager


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
    """Example: Manual login with session saving"""

    session_file = Path("data/sessions/globis_session.json")

    browser = BrowserManager(
        headless=False,  # Must be False for manual login
        user_data_dir=Path("data/cache/browser_profile"),
        fingerprint_seed="my-unique-id",  # Consistent fingerprint
    )

    try:
        page = await browser.start()

        # Wait for manual login
        success = await browser.wait_for_manual_login(
            login_url="https://unlimited.globis.co.jp/en/login",
            success_indicator="div.user-menu",  # Adjust to actual selector
            timeout=300000  # 5 minutes
        )

        if success:
            # Save session for future use
            await browser.save_session(session_file)

            # Continue with authenticated actions
            await browser.navigate_to("https://unlimited.globis.co.jp/en/dashboard")
            await browser.read_page()

    finally:
        await browser.close()


async def example_load_existing_session():
    """Example: Load saved session and continue"""

    session_file = Path("data/sessions/globis_session.json")

    browser = BrowserManager(headless=True)

    try:
        page = await browser.start()

        # Load saved session
        await browser.load_session(session_file)

        # Navigate (already authenticated)
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
        "logs/browser_example.log",
        rotation="1 MB",
        level="DEBUG"
    )

    # Run example
    logger.info("Starting browser automation example...")

    # Choose which example to run:
    # asyncio.run(example_basic_navigation())
    # asyncio.run(example_with_manual_login())
    # asyncio.run(example_load_existing_session())
    # asyncio.run(example_context_manager())
    asyncio.run(example_advanced_interaction())

    logger.info("Example completed!")

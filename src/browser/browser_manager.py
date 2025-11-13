"""
Browser Manager

Main interface for browser automation with anti-detection.
Combines fingerprinting, stealth, and human behavior simulation.
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from .fingerprint import FingerprintGenerator, BrowserFingerprint, get_fingerprint_override_script
from .stealth_config import (
    apply_stealth_to_context,
    apply_stealth_to_page,
    get_browser_launch_args,
    get_context_options
)
from .human_behavior import HumanBehaviorSimulator
from .timing import DelayManager, ActionType, TimingConfig


class BrowserManager:
    """Manage browser instance with anti-detection features"""

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[Path] = None,
        fingerprint_seed: Optional[str] = None,
        randomness_factor: float = 1.0
    ):
        """
        Initialize browser manager

        Args:
            headless: Run in headless mode
            user_data_dir: Directory for persistent browser data
            fingerprint_seed: Seed for consistent fingerprint
            randomness_factor: How random behavior should be (0.5-2.0)
        """
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.randomness_factor = randomness_factor

        # Generate fingerprint
        self.fingerprint_gen = FingerprintGenerator()
        if fingerprint_seed:
            self.fingerprint = self.fingerprint_gen.generate_consistent(fingerprint_seed)
        else:
            self.fingerprint = self.fingerprint_gen.generate()

        # Playwright instances
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Behavior managers
        self.delay_manager = DelayManager(TimingConfig(randomness_factor))
        self.behavior_sim: Optional[HumanBehaviorSimulator] = None

        logger.info("🌐 Browser Manager initialized")
        logger.debug(f"Fingerprint: {self.fingerprint.user_agent[:50]}...")

    async def start(self) -> Page:
        """
        Start browser and create page with anti-detection

        Returns:
            Playwright Page instance
        """
        logger.info("🚀 Starting browser...")

        # Start Playwright
        self.playwright = await async_playwright().start()

        # Launch browser
        launch_options = {
            "headless": self.headless,
            "args": get_browser_launch_args(),
        }

        if self.user_data_dir:
            launch_options["user_data_dir"] = str(self.user_data_dir)

        self.browser = await self.playwright.chromium.launch(**launch_options)
        logger.info("✅ Browser launched")

        # Create context
        context_options = get_context_options(self.headless)

        # Apply fingerprint to context options
        context_options.update({
            "user_agent": self.fingerprint.user_agent,
            "viewport": {
                "width": self.fingerprint.viewport_width,
                "height": self.fingerprint.viewport_height
            },
            "locale": self.fingerprint.language.split(',')[0],
            "timezone_id": self.fingerprint.timezone,
        })

        self.context = await self.browser.new_context(**context_options)
        logger.info("✅ Browser context created")

        # Apply stealth to context
        apply_stealth_to_context(self.context)
        logger.info("🥷 Stealth mode applied to context")

        # Add fingerprint override script
        await self.context.add_init_script(
            get_fingerprint_override_script(self.fingerprint)
        )
        logger.info("🔒 Fingerprint protection applied")

        # Create page
        self.page = await self.context.new_page()

        # Apply stealth to page
        apply_stealth_to_page(self.page)

        # Initialize behavior simulator
        self.behavior_sim = HumanBehaviorSimulator(
            self.page,
            self.randomness_factor
        )

        logger.info("✅ Page created with full anti-detection")

        return self.page

    async def navigate_to(self, url: str, wait_for: str = "networkidle") -> None:
        """
        Navigate to URL with human-like behavior

        Args:
            url: URL to navigate to
            wait_for: Wait condition ('load', 'domcontentloaded', 'networkidle')
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        logger.info(f"🔗 Navigating to: {url}")

        # Navigate
        await self.page.goto(url, wait_until=wait_for, timeout=60000)

        # Wait after page load (human behavior)
        await self.delay_manager.wait(ActionType.PAGE_LOAD)

        # Random small scroll to trigger lazy loading
        if self.behavior_sim:
            await self.behavior_sim.human_scroll("down", distance=200)

        logger.info("✅ Navigation complete")

    async def click_element(
        self,
        selector: Optional[str] = None,
        locator: Optional[Any] = None
    ) -> None:
        """
        Click element with human-like behavior

        Args:
            selector: CSS selector
            locator: Playwright Locator
        """
        if not self.behavior_sim:
            raise RuntimeError("Behavior simulator not initialized")

        # Pre-click delay
        await self.delay_manager.wait(ActionType.CLICK)

        # Human-like click
        await self.behavior_sim.human_click(selector=selector, locator=locator)

        # Post-click delay
        await self.delay_manager.wait(ActionType.CLICK)

    async def scroll_page(
        self,
        direction: str = "down",
        distance: Optional[int] = None
    ) -> None:
        """
        Scroll page with human-like behavior

        Args:
            direction: 'down', 'up', 'to_bottom', 'to_top'
            distance: Pixels to scroll
        """
        if not self.behavior_sim:
            raise RuntimeError("Behavior simulator not initialized")

        await self.behavior_sim.human_scroll(direction, distance)
        await self.delay_manager.wait(ActionType.SCROLLING)

    async def read_page(
        self,
        min_duration: float = 2.0,
        max_duration: float = 5.0
    ) -> None:
        """
        Simulate reading page content

        Args:
            min_duration: Minimum reading time (seconds)
            max_duration: Maximum reading time (seconds)
        """
        if not self.behavior_sim:
            raise RuntimeError("Behavior simulator not initialized")

        logger.debug(f"📖 Simulating reading for {min_duration}-{max_duration}s")
        await self.behavior_sim.simulate_reading(min_duration, max_duration)

    async def wait_for_manual_login(
        self,
        login_url: str,
        success_indicator: str,
        timeout: int = 300000  # 5 minutes
    ) -> bool:
        """
        Wait for user to manually login in headed mode

        Args:
            login_url: URL of login page
            success_indicator: Selector that appears after successful login
            timeout: Maximum wait time in milliseconds

        Returns:
            True if login successful, False if timeout
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        if self.headless:
            logger.warning("⚠️  Manual login requires headed mode!")
            return False

        logger.info("🔐 Waiting for manual login...")
        logger.info(f"Please login at: {login_url}")

        # Navigate to login page
        await self.navigate_to(login_url)

        try:
            # Wait for success indicator
            await self.page.wait_for_selector(
                success_indicator,
                timeout=timeout
            )
            logger.info("✅ Login successful!")
            return True

        except Exception as e:
            logger.error(f"❌ Login timeout or failed: {e}")
            return False

    async def save_session(self, session_file: Path) -> None:
        """
        Save browser session (cookies, localStorage, etc.)

        Args:
            session_file: Path to save session data
        """
        if not self.context:
            raise RuntimeError("Browser context not available")

        # Save cookies
        cookies = await self.context.cookies()

        # Save storage state
        await self.context.storage_state(path=str(session_file))

        logger.info(f"💾 Session saved to {session_file}")

    async def load_session(self, session_file: Path) -> None:
        """
        Load browser session from file

        Args:
            session_file: Path to session data file
        """
        if not session_file.exists():
            logger.warning(f"⚠️  Session file not found: {session_file}")
            return

        if not self.context:
            raise RuntimeError("Browser context not available")

        # Load storage state
        await self.context.add_cookies(
            await self.context.storage_state(path=str(session_file))
        )

        logger.info(f"📂 Session loaded from {session_file}")

    async def close(self) -> None:
        """Clean up and close browser"""
        logger.info("🛑 Closing browser...")

        if self.page:
            await self.page.close()

        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        logger.info("✅ Browser closed")

    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()

    def get_page(self) -> Page:
        """
        Get current page instance

        Returns:
            Playwright Page
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self.page

    def get_behavior_sim(self) -> HumanBehaviorSimulator:
        """
        Get behavior simulator instance

        Returns:
            HumanBehaviorSimulator
        """
        if not self.behavior_sim:
            raise RuntimeError("Behavior simulator not initialized")
        return self.behavior_sim

    def get_delay_manager(self) -> DelayManager:
        """
        Get delay manager instance

        Returns:
            DelayManager
        """
        return self.delay_manager

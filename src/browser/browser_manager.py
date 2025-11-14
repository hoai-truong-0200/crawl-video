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
        randomness_factor: float = 1.0,
        session_file: Optional[Path] = None
    ):
        """
        Initialize browser manager

        Args:
            headless: Run in headless mode
            user_data_dir: Directory for persistent browser data
            fingerprint_seed: Seed for consistent fingerprint
            randomness_factor: How random behavior should be (0.5-2.0)
            session_file: Path to session file for auto-loading
        """
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.randomness_factor = randomness_factor
        self.session_file = session_file

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
        Auto-loads session if session_file exists

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

        # Load session if exists
        if self.session_file and self.session_file.exists():
            logger.info(f"📂 Loading session from {self.session_file}")
            context_options["storage_state"] = str(self.session_file)

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

        if self.session_file and self.session_file.exists():
            logger.info("✅ Page created with session restored")
        else:
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
        success_indicator: str,
        login_url_pattern: str = "signin",
        timeout: int = 300000  # 5 minutes
    ) -> bool:
        """
        Wait for user to manually login in headed mode
        NOTE: Caller should navigate to login page before calling this

        Args:
            success_indicator: Selector that appears after successful login
            login_url_pattern: Pattern in URL that indicates still on login page
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

        start_time = asyncio.get_event_loop().time()

        try:
            while True:
                # Check if timed out
                if (asyncio.get_event_loop().time() - start_time) * 1000 > timeout:
                    raise TimeoutError("Login timeout exceeded")

                # Wait a bit
                await asyncio.sleep(2)

                # Check if URL changed (no longer on login page)
                current_url = self.page.url
                if login_url_pattern not in current_url.lower():
                    logger.info(f"✅ URL changed from login page: {current_url}")

                    # Wait for page to stabilize
                    await asyncio.sleep(3)

                    # Try to find success indicator
                    try:
                        await self.page.wait_for_selector(
                            success_indicator,
                            timeout=10000,
                            state="attached"
                        )
                        logger.info("✅ Login successful (success indicator found)!")
                        return True
                    except:
                        # Even if indicator not found, if URL changed, consider it success
                        logger.info("✅ Login successful (URL changed from login page)!")
                        return True

        except Exception as e:
            logger.error(f"❌ Login timeout or failed: {e}")
            return False

    async def check_session_valid(
        self,
        test_url: str,
        login_indicator: str = "signin",
        success_indicator: Optional[str] = None,
        timeout: int = 15000
    ) -> bool:
        """
        Check if current session is still valid by navigating to protected page

        Args:
            test_url: A protected URL to test with
            login_indicator: String in URL that indicates redirect to login
            success_indicator: Optional selector that appears when logged in (more reliable)
            timeout: Navigation timeout in milliseconds

        Returns:
            True if session valid, False if redirected to login
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        logger.info(f"🔍 Checking session validity at: {test_url}")

        try:
            # Navigate to protected page
            await self.page.goto(test_url, wait_until="domcontentloaded", timeout=timeout)

            # Wait a bit for any redirects to happen
            await asyncio.sleep(2)

            # Check if redirected to login page by URL
            current_url = self.page.url
            if login_indicator in current_url.lower():
                logger.warning("⚠️  Session expired - redirected to login")
                return False

            # If success_indicator provided, check if logged-in element exists
            if success_indicator:
                try:
                    await self.page.wait_for_selector(
                        success_indicator,
                        timeout=5000,
                        state="visible"
                    )
                    logger.info("✅ Session is valid (success indicator found)")
                    return True
                except Exception:
                    logger.warning("⚠️  Session expired - success indicator not found")
                    return False

            logger.info("✅ Session is valid (no redirect detected)")
            return True

        except Exception as e:
            logger.warning(f"⚠️  Session check failed: {e}")
            return False

    async def save_session(self, session_file: Path) -> None:
        """
        Save browser session (cookies, localStorage, etc.)

        Args:
            session_file: Path to save session data
        """
        if not self.context:
            raise RuntimeError("Browser context not available")

        # Ensure parent directory exists
        session_file.parent.mkdir(parents=True, exist_ok=True)

        # Save storage state (includes cookies and localStorage)
        await self.context.storage_state(path=str(session_file))

        logger.info(f"💾 Session saved to {session_file}")


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

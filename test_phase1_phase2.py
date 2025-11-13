#!/usr/bin/env python3
"""
Test Script for Phase 1 & Phase 2

Tests:
1. Phase 1: Dependencies installation verification
2. Phase 2: Browser automation with anti-detection
"""

import sys
import asyncio
from pathlib import Path
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/test_phase1_phase2.log",
    rotation="10 MB",
    level="DEBUG"
)


def test_phase1_imports():
    """Test Phase 1: Verify all dependencies can be imported"""
    logger.info("=" * 60)
    logger.info("PHASE 1: Testing Dependencies")
    logger.info("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test core dependencies
    dependencies = {
        "playwright": "playwright",
        "playwright-stealth": "playwright_stealth",
        "faker": "faker",
        "numpy": "numpy",
        "pydantic": "pydantic",
        "loguru": "loguru",
        "tqdm": "tqdm",
        "beautifulsoup4": "bs4",
        "lxml": "lxml",
        "tenacity": "tenacity",
        "python-dotenv": "dotenv",
        "httpx": "httpx",
    }

    for package_name, import_name in dependencies.items():
        try:
            __import__(import_name)
            logger.success(f"✅ {package_name}")
            tests_passed += 1
        except ImportError as e:
            logger.error(f"❌ {package_name} - NOT INSTALLED")
            logger.debug(f"   Error: {e}")
            tests_failed += 1

    logger.info("")
    logger.info(f"Phase 1 Results: {tests_passed} passed, {tests_failed} failed")

    return tests_failed == 0


async def test_phase2_fingerprinting():
    """Test Phase 2: Fingerprinting module"""
    logger.info("=" * 60)
    logger.info("PHASE 2 - Test 1: Fingerprinting")
    logger.info("=" * 60)

    try:
        from src.browser.fingerprint import FingerprintGenerator, BrowserFingerprint

        # Generate random fingerprint
        gen = FingerprintGenerator()
        fp1 = gen.generate()

        logger.info(f"Generated Fingerprint:")
        logger.info(f"  User Agent: {fp1.user_agent[:60]}...")
        logger.info(f"  Viewport: {fp1.viewport_width}x{fp1.viewport_height}")
        logger.info(f"  Timezone: {fp1.timezone}")
        logger.info(f"  Language: {fp1.language}")
        logger.info(f"  Platform: {fp1.platform}")

        # Test consistent fingerprint
        fp2 = gen.generate_consistent("test-user-123")
        fp3 = gen.generate_consistent("test-user-123")

        assert fp2.user_agent == fp3.user_agent, "Consistent fingerprint failed"
        logger.success("✅ Consistent fingerprint generation works")

        logger.success("✅ Fingerprinting module: PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Fingerprinting module: FAILED")
        logger.exception(e)
        return False


async def test_phase2_timing():
    """Test Phase 2: Timing module"""
    logger.info("=" * 60)
    logger.info("PHASE 2 - Test 2: Timing & Delays")
    logger.info("=" * 60)

    try:
        from src.browser.timing import DelayManager, ActionType, TimingConfig

        # Test delay manager
        config = TimingConfig(randomness_factor=0.5)  # Faster for testing
        manager = DelayManager(config)

        logger.info("Testing different action delays...")

        # Test various action types
        actions_to_test = [
            ActionType.CLICK,
            ActionType.READING,
            ActionType.THINKING,
        ]

        for action in actions_to_test:
            start = asyncio.get_event_loop().time()
            delay = await manager.wait(action)
            elapsed = asyncio.get_event_loop().time() - start

            logger.info(f"  {action.value}: {delay:.3f}s (actual: {elapsed:.3f}s)")

        # Test stats
        stats = manager.get_stats()
        logger.info(f"Stats: {stats['total_actions']} actions performed")

        logger.success("✅ Timing module: PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Timing module: FAILED")
        logger.exception(e)
        return False


async def test_phase2_browser_basic():
    """Test Phase 2: Basic browser automation (no actual browsing)"""
    logger.info("=" * 60)
    logger.info("PHASE 2 - Test 3: Browser Manager (Initialization)")
    logger.info("=" * 60)

    try:
        from src.browser.browser_manager import BrowserManager

        # Test initialization only (don't start browser to avoid dependencies)
        manager = BrowserManager(
            headless=True,
            fingerprint_seed="test-session",
            randomness_factor=1.0
        )

        logger.info("BrowserManager created successfully")
        logger.info(f"  Headless: {manager.headless}")
        logger.info(f"  Fingerprint: {manager.fingerprint.user_agent[:60]}...")
        logger.info(f"  Randomness: {manager.randomness_factor}")

        # Test fingerprint consistency
        fp1 = manager.fingerprint
        manager2 = BrowserManager(fingerprint_seed="test-session")
        fp2 = manager2.fingerprint

        assert fp1.user_agent == fp2.user_agent, "Fingerprint seed consistency failed"
        logger.success("✅ Fingerprint seed consistency works")

        logger.success("✅ Browser Manager initialization: PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Browser Manager: FAILED")
        logger.exception(e)
        return False


async def test_phase2_browser_live():
    """Test Phase 2: Live browser test (requires Playwright installed)"""
    logger.info("=" * 60)
    logger.info("PHASE 2 - Test 4: Live Browser Test")
    logger.info("=" * 60)

    try:
        from src.browser.browser_manager import BrowserManager

        logger.info("Starting browser (this may take a few seconds)...")

        async with BrowserManager(headless=True, randomness_factor=0.5) as browser:
            page = browser.get_page()

            logger.info("Browser started successfully")

            # Navigate to a test page
            test_url = "https://www.example.com"
            logger.info(f"Navigating to {test_url}...")

            await browser.navigate_to(test_url)
            logger.success(f"✅ Navigation successful")

            # Get page title
            title = await page.title()
            logger.info(f"  Page title: {title}")

            # Test scrolling
            logger.info("Testing human-like scrolling...")
            await browser.scroll_page("down", distance=300)
            logger.success("✅ Scrolling works")

            # Test reading simulation
            logger.info("Testing reading simulation (2s)...")
            await browser.read_page(min_duration=1, max_duration=2)
            logger.success("✅ Reading simulation works")

            # Check if webdriver is hidden
            is_webdriver = await page.evaluate("navigator.webdriver")
            if is_webdriver is None or is_webdriver is False:
                logger.success("✅ navigator.webdriver is properly hidden")
            else:
                logger.warning(f"⚠️  navigator.webdriver = {is_webdriver}")

        logger.success("✅ Live browser test: PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Live browser test: FAILED")
        logger.exception(e)
        logger.info("Note: Make sure Playwright browsers are installed:")
        logger.info("  playwright install chromium")
        return False


async def main():
    """Run all tests"""
    logger.info("🧪 Starting Phase 1 & Phase 2 Tests")
    logger.info("")

    results = {}

    # Phase 1 Tests
    results["Phase 1: Dependencies"] = test_phase1_imports()

    logger.info("")

    # Phase 2 Tests (async)
    results["Phase 2.1: Fingerprinting"] = await test_phase2_fingerprinting()
    logger.info("")

    results["Phase 2.2: Timing"] = await test_phase2_timing()
    logger.info("")

    results["Phase 2.3: Browser Init"] = await test_phase2_browser_basic()
    logger.info("")

    # Ask user if they want to run live browser test
    logger.info("=" * 60)
    logger.info("Live Browser Test")
    logger.info("=" * 60)
    logger.info("This test will launch a real browser window.")
    logger.info("Requirements:")
    logger.info("  1. All dependencies installed (pip install -r requirements.txt)")
    logger.info("  2. Playwright browsers installed (playwright install chromium)")
    logger.info("")

    # Run live test
    results["Phase 2.4: Live Browser"] = await test_phase2_browser_live()

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        logger.success("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Inspect Course Page HTML Structure

Navigate to a course page and save HTML for analysis.
This helps us identify selectors for extracting video information.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from loguru import logger


async def main():
    """Inspect course page and save HTML"""

    # Load learn-content.json to get a sample course URL
    content_file = Path("data/courses/learn-content.json")

    if not content_file.exists():
        logger.error(f"❌ Content file not found: {content_file}")
        return

    with open(content_file, 'r', encoding='utf-8') as f:
        content = json.load(f)

    # Get first category's first course
    categories = content.get('categories', [])
    if not categories:
        logger.error("❌ No categories found")
        return

    for category in categories:
        courses = category.get('courses', [])
        if courses:
            course = courses[0]
            course_url = course.get('url', '')
            course_title = course.get('title', 'Unknown')
            break
    else:
        logger.error("❌ No courses found")
        return

    logger.info(f"📚 Inspecting course: {course_title}")
    logger.info(f"🔗 URL: {course_url}")

    # Launch browser
    async with async_playwright() as p:
        # Use Chrome profile copy
        profile_path = Path("data/chrome_profile_copy")

        if not profile_path.exists():
            logger.error(f"❌ Chrome profile not found: {profile_path}")
            logger.info("Please run: python3 run_browser.py test")
            return

        logger.info("🚀 Launching Chrome...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_path.absolute()),
            channel='chrome',
            headless=False,
            viewport={"width": 1920, "height": 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        logger.info("🔗 Navigating to course page...")
        await page.goto(course_url, wait_until="domcontentloaded", timeout=60000)

        # Wait for page to load
        await asyncio.sleep(5)

        # Save HTML
        html_content = await page.content()
        html_file = Path("data/samples/course_page_sample.html")
        html_file.parent.mkdir(parents=True, exist_ok=True)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"💾 HTML saved to: {html_file}")

        # Try to find video elements
        logger.info("\n🔍 Looking for video-related elements...")

        # Common video selectors
        video_selectors = [
            "video",
            "iframe[src*='vimeo']",
            "iframe[src*='player']",
            "[class*='video']",
            "[class*='Video']",
            "[class*='player']",
            "[class*='Player']",
            "[data-vimeo-id]",
            "[data-video-id]",
        ]

        for selector in video_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                logger.info(f"✅ Found {len(elements)} elements matching: {selector}")

                # Get sample HTML
                if elements:
                    first = elements[0]
                    sample_html = await first.evaluate("el => el.outerHTML")
                    logger.info(f"📋 Sample HTML (first 500 chars):")
                    logger.info(sample_html[:500] + "...")

        # Check for step/lesson structure
        step_selectors = [
            "[class*='step']",
            "[class*='Step']",
            "[class*='lesson']",
            "[class*='Lesson']",
            "a[href*='/steps/']",
        ]

        logger.info("\n🔍 Looking for step/lesson elements...")
        for selector in step_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                logger.info(f"✅ Found {len(elements)} elements matching: {selector}")

        logger.info("\n⏸️  Browser will stay open for manual inspection")
        logger.info("Press Ctrl+C to close...")

        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            logger.info("\n👋 Closing browser...")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())

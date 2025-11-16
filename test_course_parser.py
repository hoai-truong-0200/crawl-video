#!/usr/bin/env python3
"""
Test Course Parser

Test the CourseParser by navigating to a course page and extracting steps.
Then navigate to the first step and extract the Vimeo URL.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from loguru import logger

from src.crawler.course_parser import CourseParser


async def main():
    """Test course parser"""

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

    logger.info("=" * 70)
    logger.info("🧪 TESTING COURSE PARSER")
    logger.info("=" * 70)
    logger.info(f"📚 Course: {course_title}")
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

        # Navigate to course page
        logger.info("\n🔗 Navigating to course page...")
        await page.goto(course_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        # Parse course page to extract steps
        logger.info("\n📖 Parsing course page...")
        parser = CourseParser()
        steps = await parser.parse_course_page(page)

        if not steps:
            logger.error("❌ No steps found!")
            await context.close()
            return

        logger.info(f"\n✅ Found {len(steps)} steps:")
        for idx, step in enumerate(steps, 1):
            logger.info(f"  {idx}. {step.title} ({step.duration})")
            logger.info(f"     URL: {step.url}")
            logger.info(f"     Step ID: {step.step_id}")

        # Test extracting Vimeo URL from first step
        if steps:
            logger.info(f"\n🎬 Testing Vimeo extraction for: {steps[0].title}")

            # Navigate to first step
            first_step_url = steps[0].url
            full_url = f"https://unlimited.globis.co.jp{first_step_url}"

            logger.info(f"🔗 Navigating to: {full_url}")
            await page.goto(full_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            # Extract Vimeo URL
            vimeo_url = await parser.extract_vimeo_url(page)

            if vimeo_url:
                logger.info(f"✅ Vimeo URL: {vimeo_url}")

                # Extract Vimeo ID
                vimeo_id = parser.extract_vimeo_id(vimeo_url)
                if vimeo_id:
                    logger.info(f"✅ Vimeo ID: {vimeo_id}")
                else:
                    logger.warning("⚠️  Could not extract Vimeo ID")
            else:
                logger.error("❌ Could not find Vimeo URL")

        logger.info("\n" + "=" * 70)
        logger.info("🎉 TEST COMPLETE")
        logger.info("=" * 70)

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

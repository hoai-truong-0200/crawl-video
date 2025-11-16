"""
Category Crawler

Crawls all category pages from GLOBIS Unlimited and extracts course information.
Implements human-like behavior and error handling.
"""

import asyncio
import random
from pathlib import Path
from typing import List, Optional, Dict
from playwright.async_api import Page
from loguru import logger

from .category_parser import CategoryParser, CourseInfo
from .content_manager import ContentManager, Course


class CategoryCrawler:
    """
    Crawler for GLOBIS Unlimited category pages

    Features:
    - Crawls all categories from learn-content.json
    - Extracts courses using CategoryParser
    - Human-like behavior (random delays, scrolling)
    - Error handling and retry logic
    - Saves results back to learn-content.json
    """

    def __init__(
        self,
        content_file: Path = Path("data/courses/learn-content.json"),
        parser: Optional[CategoryParser] = None,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        max_retries: int = 3,
    ):
        """
        Initialize crawler

        Args:
            content_file: Path to learn-content.json
            parser: CategoryParser instance (creates new if None)
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            max_retries: Maximum retry attempts for failed requests
        """
        self.content_file = content_file
        self.parser = parser or CategoryParser()
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

        # Content manager for loading/saving JSON
        self.content_manager = ContentManager(content_file)

        # Statistics
        self.stats = {
            "categories_crawled": 0,
            "categories_failed": 0,
            "total_courses_found": 0,
            "errors": [],
        }

    async def crawl_all_categories(self, page: Page) -> Dict[str, int]:
        """
        Crawl all categories from learn-content.json

        Args:
            page: Playwright Page object (already logged in)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 70)
        logger.info("🚀 STARTING CATEGORY CRAWLER")
        logger.info("=" * 70)

        # Load content
        self.content_manager.load()

        if not self.content_manager.categories:
            logger.error("❌ No categories found in learn-content.json")
            return self.stats

        logger.info(f"📚 Found {len(self.content_manager.categories)} categories to crawl")
        logger.info(f"⏱️  Delay between requests: {self.min_delay}-{self.max_delay}s")
        logger.info(f"🔄 Max retries per category: {self.max_retries}")

        # Crawl each category
        for idx, category in enumerate(self.content_manager.categories, 1):
            category_title = category.title
            category_url = category.url

            if not category_url:
                logger.warning(f"[{idx}/{len(self.content_manager.categories)}] ⚠️  Skipping '{category_title}' - no URL")
                continue

            logger.info("\n" + "=" * 70)
            logger.info(f"📂 [{idx}/{len(self.content_manager.categories)}] {category_title}")
            logger.info("=" * 70)
            logger.info(f"🔗 URL: {category_url}")

            # Crawl category with retry logic
            courses = await self._crawl_category_with_retry(page, category_url)

            if courses:
                # Convert CourseInfo to Course objects
                course_objects = []
                for course_info in courses:
                    course_obj = Course()
                    course_obj.title = course_info.title
                    course_obj.url = course_info.url
                    course_obj.last_updated = ""  # Will be set when crawling videos
                    course_obj.videos = []
                    course_objects.append(course_obj)

                # Update category courses
                category.courses = course_objects

                self.stats["categories_crawled"] += 1
                self.stats["total_courses_found"] += len(courses)

                logger.info(f"✅ Successfully crawled {len(courses)} courses")
            else:
                self.stats["categories_failed"] += 1
                logger.warning(f"⚠️  Failed to crawl category")

            # Human-like delay before next category
            if idx < len(self.content_manager.categories):
                delay = random.uniform(self.min_delay, self.max_delay)
                logger.info(f"⏳ Waiting {delay:.1f}s before next category...")
                await asyncio.sleep(delay)

        # Save updated content
        logger.info("\n" + "=" * 70)
        logger.info("💾 SAVING RESULTS")
        logger.info("=" * 70)

        self.content_manager.save()

        # Print final statistics
        self._print_statistics()

        return self.stats

    async def _crawl_category_with_retry(
        self,
        page: Page,
        category_url: str,
    ) -> Optional[List[CourseInfo]]:
        """
        Crawl a single category with retry logic

        Args:
            page: Playwright Page object
            category_url: Category page URL

        Returns:
            List of CourseInfo objects or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔄 Attempt {attempt}/{self.max_retries}")

                # Navigate to category page
                await page.goto(
                    category_url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                logger.info("✅ Navigation complete")

                # Wait a bit for page to settle
                await asyncio.sleep(random.uniform(1.5, 3.0))

                # Scroll to simulate human behavior
                await self._human_like_scroll(page)

                # Parse courses
                courses = await self.parser.parse_category_page(page)

                if courses:
                    return courses
                else:
                    logger.warning(f"⚠️  No courses found (attempt {attempt})")
                    if attempt < self.max_retries:
                        await asyncio.sleep(random.uniform(2, 4))
                        continue
                    return None

            except Exception as e:
                error_msg = f"Attempt {attempt} failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                self.stats["errors"].append(error_msg)

                if attempt < self.max_retries:
                    retry_delay = random.uniform(3, 6)
                    logger.info(f"⏳ Retrying in {retry_delay:.1f}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"❌ Failed after {self.max_retries} attempts")
                    return None

        return None

    async def _human_like_scroll(self, page: Page) -> None:
        """
        Simulate human-like scrolling behavior with mouse movements

        Args:
            page: Playwright Page object
        """
        try:
            # Get page height
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")

            if page_height <= viewport_height:
                # Page fits in viewport, no need to scroll
                return

            # Random mouse movements before scrolling
            viewport = page.viewport_size or {"width": 1920, "height": 1080}
            for _ in range(random.randint(1, 2)):
                x = random.randint(100, viewport["width"] - 100)
                y = random.randint(100, viewport["height"] - 100)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # Scroll down in chunks with variations
            scroll_positions = [0.25, 0.45, 0.65, 0.85, 1.0]  # More granular scrolling

            for position in scroll_positions:
                scroll_to = int(page_height * position)

                # Use wheel scroll instead of direct jump (more natural)
                current_scroll = await page.evaluate("window.pageYOffset")
                delta = scroll_to - current_scroll

                # Scroll in smaller increments
                steps = random.randint(3, 6)
                for step in range(steps):
                    step_delta = delta / steps
                    await page.mouse.wheel(0, step_delta)
                    await asyncio.sleep(random.uniform(0.1, 0.3))

                # Pause at this position (reading)
                await asyncio.sleep(random.uniform(0.5, 1.2))

                # Occasionally move mouse
                if random.random() < 0.4:
                    x = random.randint(100, viewport["width"] - 100)
                    y = random.randint(100, viewport["height"] - 100)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.2, 0.4))

            # Sometimes scroll back up a bit (re-reading)
            if random.random() < 0.3:
                await page.mouse.wheel(0, random.randint(-200, -100))
                await asyncio.sleep(random.uniform(0.5, 1.0))

            # Scroll back to top gradually
            await page.mouse.wheel(0, -page_height)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            logger.debug("🖱️  Performed human-like scrolling with mouse movements")

        except Exception as e:
            logger.warning(f"⚠️  Could not perform scrolling: {e}")

    def _print_statistics(self) -> None:
        """Print crawling statistics"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 CRAWLING STATISTICS")
        logger.info("=" * 70)
        logger.info(f"✅ Categories crawled: {self.stats['categories_crawled']}")
        logger.info(f"❌ Categories failed: {self.stats['categories_failed']}")
        logger.info(f"📚 Total courses found: {self.stats['total_courses_found']}")

        if self.stats['categories_crawled'] > 0:
            avg_courses = self.stats['total_courses_found'] / self.stats['categories_crawled']
            logger.info(f"📈 Average courses per category: {avg_courses:.1f}")

        if self.stats['errors']:
            logger.info(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
            for idx, error in enumerate(self.stats['errors'][:5], 1):
                logger.info(f"   {idx}. {error}")
            if len(self.stats['errors']) > 5:
                logger.info(f"   ... and {len(self.stats['errors']) - 5} more")

        logger.info("=" * 70)

    def get_stats(self) -> Dict[str, int]:
        """
        Get current statistics

        Returns:
            Statistics dictionary
        """
        return self.stats.copy()

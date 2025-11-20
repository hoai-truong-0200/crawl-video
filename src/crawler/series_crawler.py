"""
Series Crawler

Crawls series pages from GLOBIS Unlimited explore-content.
"""

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from playwright.async_api import Page
from loguru import logger

from .category_parser import CategoryParser, CourseInfo
from .content_manager import ContentManager, Series, Course


class SeriesCrawler:
    """
    Crawler for GLOBIS Unlimited series pages (explore-content)

    Series are collections of courses grouped by theme/topic.
    Uses the same CategoryParser since HTML structure is similar.
    """

    def __init__(
        self,
        content_file: Path = Path("data/courses/en/explore-content.json"),
        language: str = "en",
        parser: Optional[CategoryParser] = None,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        max_retries: int = 3,
    ):
        """
        Initialize series crawler

        Args:
            content_file: Path to explore-content.json
            language: Language code (en/ja)
            parser: CategoryParser instance (reuses same parser)
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            max_retries: Maximum retry attempts for failed requests
        """
        self.content_file = content_file
        self.language = language
        self.parser = parser or CategoryParser()
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

        # Content manager for loading/saving JSON with language support
        self.content_manager = ContentManager(content_file, language=language)

        # Statistics
        self.stats = {
            "series_crawled": 0,
            "series_failed": 0,
            "total_courses_found": 0,
            "errors": [],
        }

    async def crawl_all_series(self, page: Page) -> Dict[str, int]:
        """
        Crawl all series from explore-content.json

        Args:
            page: Playwright Page object (already logged in)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 70)
        logger.info("🎬 STARTING SERIES CRAWLER (EXPLORE CONTENT)")
        logger.info("=" * 70)

        # Load series data using ContentManager
        self.content_manager.load()

        if not self.content_manager.series:
            logger.error("❌ No series found in explore-content.json")
            return self.stats

        logger.info(f"📚 Found {len(self.content_manager.series)} series to crawl")
        logger.info(f"⏱️  Delay between requests: {self.min_delay}-{self.max_delay}s")
        logger.info(f"🔄 Max retries per series: {self.max_retries}")

        # Crawl each series
        for idx, series in enumerate(self.content_manager.series, 1):
            series_title = series.title
            series_url = series.url

            if not series_url:
                logger.warning(f"[{idx}/{len(self.content_manager.series)}] ⚠️  Skipping '{series_title}' - no URL")
                continue

            logger.info("\n" + "=" * 70)
            logger.info(f"🎬 [{idx}/{len(self.content_manager.series)}] {series_title}")
            logger.info("=" * 70)
            logger.info(f"🔗 URL: {series_url}")

            # Crawl series with retry logic
            courses = await self._crawl_series_with_retry(page, series_url)

            if courses:
                # Convert CourseInfo to Course objects with new schema
                course_objects = []
                for course_info in courses:
                    course_obj = Course(
                        title=course_info.title,
                        url=course_info.url,
                        overview="",  # Will be set when crawling course details
                        transcript="",  # Will be set when crawling course details
                        duration=0,  # Will be set when crawling course details
                        last_updated=datetime.now().isoformat(),
                        learning_points=[]  # Will be filled when crawling videos
                    )
                    course_objects.append(course_obj)

                # Update series courses and last_updated timestamp
                series.courses = course_objects
                series.last_updated = datetime.now().isoformat()

                self.stats["series_crawled"] += 1
                self.stats["total_courses_found"] += len(courses)

                logger.info(f"✅ Successfully crawled {len(courses)} courses")
            else:
                self.stats["series_failed"] += 1
                logger.warning(f"⚠️  Failed to crawl series")
                # Still keep series in JSON, just with empty courses
                series.courses = []

            # Human-like delay before next series
            if idx < len(self.content_manager.series):
                delay = random.uniform(self.min_delay, self.max_delay)
                logger.info(f"⏳ Waiting {delay:.1f}s before next series...")
                await asyncio.sleep(delay)

        # Save updated content using ContentManager
        logger.info("\n" + "=" * 70)
        logger.info("💾 SAVING RESULTS")
        logger.info("=" * 70)

        self.content_manager.save()

        # Print final statistics
        self._print_statistics()

        return self.stats

    async def _crawl_series_with_retry(
        self,
        page: Page,
        series_url: str,
    ) -> Optional[List[CourseInfo]]:
        """
        Crawl a single series with retry logic

        Args:
            page: Playwright Page object
            series_url: Series page URL

        Returns:
            List of CourseInfo objects or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔄 Attempt {attempt}/{self.max_retries}")

                # Navigate to series page
                await page.goto(
                    series_url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                logger.info("✅ Navigation complete")

                # Wait a bit for page to settle
                await asyncio.sleep(random.uniform(1.5, 3.0))

                # Scroll to simulate human behavior
                await self._human_like_scroll(page)

                # Parse courses (series pages have same structure as categories)
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
                return

            # Random mouse movements before scrolling
            viewport = page.viewport_size or {"width": 1920, "height": 1080}
            for _ in range(random.randint(1, 2)):
                x = random.randint(100, viewport["width"] - 100)
                y = random.randint(100, viewport["height"] - 100)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # Scroll down in chunks
            scroll_positions = [0.25, 0.45, 0.65, 0.85, 1.0]

            for position in scroll_positions:
                scroll_to = int(page_height * position)
                current_scroll = await page.evaluate("window.pageYOffset")
                delta = scroll_to - current_scroll

                # Scroll in smaller increments
                steps = random.randint(3, 6)
                for step in range(steps):
                    step_delta = delta / steps
                    await page.mouse.wheel(0, step_delta)
                    await asyncio.sleep(random.uniform(0.1, 0.3))

                # Pause (reading)
                await asyncio.sleep(random.uniform(0.5, 1.2))

                # Occasionally move mouse
                if random.random() < 0.4:
                    x = random.randint(100, viewport["width"] - 100)
                    y = random.randint(100, viewport["height"] - 100)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.2, 0.4))

            # Sometimes scroll back up a bit
            if random.random() < 0.3:
                await page.mouse.wheel(0, random.randint(-200, -100))
                await asyncio.sleep(random.uniform(0.5, 1.0))

            # Scroll back to top
            await page.mouse.wheel(0, -page_height)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            logger.debug("🖱️  Performed human-like scrolling")

        except Exception as e:
            logger.warning(f"⚠️  Could not perform scrolling: {e}")

    def _print_statistics(self) -> None:
        """Print crawling statistics"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 SERIES CRAWLING STATISTICS")
        logger.info("=" * 70)
        logger.info(f"✅ Series crawled: {self.stats['series_crawled']}")
        logger.info(f"❌ Series failed: {self.stats['series_failed']}")
        logger.info(f"📚 Total courses found: {self.stats['total_courses_found']}")

        if self.stats['series_crawled'] > 0:
            avg_courses = self.stats['total_courses_found'] / self.stats['series_crawled']
            logger.info(f"📈 Average courses per series: {avg_courses:.1f}")

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

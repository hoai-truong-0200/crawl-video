"""
Course Crawler

Crawls all courses from learn-content.json and explore-content.json
to extract video information (steps) for each course.
"""

import asyncio
import random
from pathlib import Path
from typing import List, Optional, Dict
from playwright.async_api import Page
from loguru import logger

from .course_parser import CourseParser, StepInfo
from .content_manager import ContentManager, Video


class CourseCrawler:
    """
    Crawler for GLOBIS Unlimited course pages

    Features:
    - Crawls all courses from learn-content.json
    - Extracts steps (video lessons) from each course
    - Navigates to each step to extract Vimeo URLs
    - Saves video information back to JSON
    - Human-like behavior (random delays, error handling)
    """

    def __init__(
        self,
        content_file: Path = Path("data/courses/learn-content.json"),
        parser: Optional[CourseParser] = None,
        min_delay: float = 1.5,
        max_delay: float = 3.0,
        max_retries: int = 3,
    ):
        """
        Initialize course crawler

        Args:
            content_file: Path to learn-content.json or explore-content.json
            parser: CourseParser instance (creates new if None)
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            max_retries: Maximum retry attempts for failed requests
        """
        self.content_file = content_file
        self.parser = parser or CourseParser()
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

        # Content manager for loading/saving JSON
        self.content_manager = ContentManager(content_file)

        # Statistics
        self.stats = {
            "courses_crawled": 0,
            "courses_failed": 0,
            "total_videos_found": 0,
            "videos_with_vimeo": 0,
            "videos_without_vimeo": 0,
            "errors": [],
        }

    async def crawl_all_courses(self, page: Page) -> Dict[str, int]:
        """
        Crawl all courses to extract video information

        Args:
            page: Playwright Page object (already logged in)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 70)
        logger.info("🎬 STARTING COURSE CRAWLER")
        logger.info("=" * 70)

        # Load content
        self.content_manager.load()

        if not self.content_manager.categories:
            logger.error("❌ No categories found in content file")
            return self.stats

        # Count total courses
        total_courses = sum(
            len(cat.courses) for cat in self.content_manager.categories
        )

        logger.info(f"📚 Found {len(self.content_manager.categories)} categories")
        logger.info(f"📚 Total courses to crawl: {total_courses}")
        logger.info(f"⏱️  Delay between requests: {self.min_delay}-{self.max_delay}s")
        logger.info(f"🔄 Max retries per course: {self.max_retries}")

        course_counter = 0

        # Crawl each category
        for cat_idx, category in enumerate(self.content_manager.categories, 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"📂 Category [{cat_idx}/{len(self.content_manager.categories)}]: {category.title}")
            logger.info(f"{'=' * 70}")

            # Crawl each course in category
            for course_idx, course in enumerate(category.courses, 1):
                course_counter += 1

                logger.info(f"\n🎓 Course [{course_counter}/{total_courses}]: {course.title}")
                logger.info(f"🔗 URL: {course.url}")

                # Crawl course with retry logic
                videos = await self._crawl_course_with_retry(page, course.url, course.title)

                if videos:
                    # Update course videos
                    course.videos = videos

                    self.stats["courses_crawled"] += 1
                    self.stats["total_videos_found"] += len(videos)

                    videos_with_vimeo = sum(1 for v in videos if v.vimeo_url)
                    self.stats["videos_with_vimeo"] += videos_with_vimeo
                    self.stats["videos_without_vimeo"] += len(videos) - videos_with_vimeo

                    logger.info(f"✅ Successfully crawled {len(videos)} videos")
                    logger.info(f"   - With Vimeo URL: {videos_with_vimeo}")
                    logger.info(f"   - Without Vimeo URL: {len(videos) - videos_with_vimeo}")
                else:
                    self.stats["courses_failed"] += 1
                    logger.warning(f"⚠️  Failed to crawl course")

                # Human-like delay before next course
                if course_counter < total_courses:
                    delay = random.uniform(self.min_delay, self.max_delay)
                    logger.info(f"⏳ Waiting {delay:.1f}s before next course...")
                    await asyncio.sleep(delay)

        # Save updated content
        logger.info(f"\n{'=' * 70}")
        logger.info("💾 SAVING RESULTS")
        logger.info(f"{'=' * 70}")

        self.content_manager.save()

        # Print final statistics
        self._print_statistics()

        return self.stats

    async def _crawl_course_with_retry(
        self,
        page: Page,
        course_url: str,
        course_title: str,
    ) -> Optional[List[Video]]:
        """
        Crawl a single course with retry logic

        Args:
            page: Playwright Page object
            course_url: Course page URL
            course_title: Course title (for logging)

        Returns:
            List of Video objects or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔄 Attempt {attempt}/{self.max_retries}")

                # Navigate to course page
                full_url = f"https://unlimited.globis.co.jp{course_url}" if not course_url.startswith("http") else course_url

                await page.goto(
                    full_url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                logger.info("✅ Navigation complete")

                # Wait for page to settle
                await asyncio.sleep(random.uniform(1.5, 2.5))

                # Parse course page to get steps
                steps = await self.parser.parse_course_page(page)

                if not steps:
                    logger.warning(f"⚠️  No steps found (attempt {attempt})")
                    if attempt < self.max_retries:
                        await asyncio.sleep(random.uniform(2, 4))
                        continue
                    return None

                logger.info(f"📖 Found {len(steps)} steps")

                # Now visit each step to extract Vimeo URL
                videos = []

                for step_idx, step in enumerate(steps, 1):
                    try:
                        logger.info(f"   🎬 Step [{step_idx}/{len(steps)}]: {step.title}")

                        # Navigate to step page
                        step_full_url = f"https://unlimited.globis.co.jp{step.url}"

                        await page.goto(
                            step_full_url,
                            wait_until="domcontentloaded",
                            timeout=60000
                        )

                        # Wait for video player to load
                        await asyncio.sleep(random.uniform(1.0, 2.0))

                        # Extract Vimeo URL
                        vimeo_url = await self.parser.extract_vimeo_url(page)

                        # Create Video object
                        video = Video(
                            title=step.title,
                            url=step.url,
                            vimeo_url=vimeo_url or "",
                            downloaded=False,
                            uploaded_to_drive=False,
                            drive_file_id=""
                        )

                        videos.append(video)

                        if vimeo_url:
                            logger.info(f"      ✅ Vimeo URL: {vimeo_url}")
                        else:
                            logger.warning(f"      ⚠️  No Vimeo URL found")

                        # Small delay between steps
                        if step_idx < len(steps):
                            await asyncio.sleep(random.uniform(0.8, 1.5))

                    except Exception as e:
                        logger.error(f"      ❌ Failed to extract Vimeo URL for step: {e}")
                        # Still add the video but without Vimeo URL
                        videos.append(Video(
                            title=step.title,
                            url=step.url,
                            vimeo_url="",
                            downloaded=False,
                            uploaded_to_drive=False,
                            drive_file_id=""
                        ))
                        continue

                return videos

            except Exception as e:
                error_msg = f"Attempt {attempt} failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                self.stats["errors"].append(f"{course_title}: {error_msg}")

                if attempt < self.max_retries:
                    retry_delay = random.uniform(3, 6)
                    logger.info(f"⏳ Retrying in {retry_delay:.1f}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"❌ Failed after {self.max_retries} attempts")
                    return None

        return None

    def _print_statistics(self) -> None:
        """Print crawling statistics"""
        logger.info(f"\n{'=' * 70}")
        logger.info("📊 COURSE CRAWLING STATISTICS")
        logger.info(f"{'=' * 70}")
        logger.info(f"✅ Courses crawled: {self.stats['courses_crawled']}")
        logger.info(f"❌ Courses failed: {self.stats['courses_failed']}")
        logger.info(f"🎬 Total videos found: {self.stats['total_videos_found']}")
        logger.info(f"   - With Vimeo URL: {self.stats['videos_with_vimeo']}")
        logger.info(f"   - Without Vimeo URL: {self.stats['videos_without_vimeo']}")

        if self.stats['courses_crawled'] > 0:
            avg_videos = self.stats['total_videos_found'] / self.stats['courses_crawled']
            logger.info(f"📈 Average videos per course: {avg_videos:.1f}")

            if self.stats['total_videos_found'] > 0:
                success_rate = (self.stats['videos_with_vimeo'] / self.stats['total_videos_found']) * 100
                logger.info(f"📈 Vimeo extraction success rate: {success_rate:.1f}%")

        if self.stats['errors']:
            logger.info(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
            for idx, error in enumerate(self.stats['errors'][:5], 1):
                logger.info(f"   {idx}. {error}")
            if len(self.stats['errors']) > 5:
                logger.info(f"   ... and {len(self.stats['errors']) - 5} more")

        logger.info(f"{'=' * 70}")

    def get_stats(self) -> Dict[str, int]:
        """
        Get current statistics

        Returns:
            Statistics dictionary
        """
        return self.stats.copy()

"""
Course Crawler

Crawls all courses from learn-content.json and explore-content.json
to extract video information (steps) for each course.
"""

import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from playwright.async_api import Page
from loguru import logger

from .course_parser import CourseParser, StepInfo
from .content_manager import ContentManager, Video, LearnPoint
from ..browser.human_behavior import HumanBehaviorSimulator
from ..downloader import VideoDownloader, VimeoExtractor


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
        content_file: Path = Path("data/courses/en/learn-content.json"),
        language: str = "en",
        parser: Optional[CourseParser] = None,
        min_delay: float = 1.5,
        max_delay: float = 3.0,
        max_retries: int = 3,
        enable_human_behavior: bool = True,
        enable_download: bool = False,
        download_dir: Path = Path("downloads"),
    ):
        """
        Initialize course crawler

        Args:
            content_file: Path to learn-content.json or explore-content.json
            language: Language code (en/ja)
            parser: CourseParser instance (creates new if None)
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            max_retries: Maximum retry attempts for failed requests
            enable_human_behavior: Enable human-like behavior (scrolling, mouse movements)
            enable_download: Enable video downloading (default: False for course crawling)
            download_dir: Base directory for video downloads
        """
        self.content_file = content_file
        self.language = language
        self.parser = parser or CourseParser()
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.enable_human_behavior = enable_human_behavior
        self.enable_download = enable_download

        # Content manager for loading/saving JSON with language support
        self.content_manager = ContentManager(content_file, language=language)

        # Video downloader (NEW structure with language support)
        self.downloader = VideoDownloader(
            download_dir=download_dir,
            language=language,
            cookies_from_browser="chrome"
        )

        # Statistics
        self.stats = {
            "courses_crawled": 0,
            "courses_failed": 0,
            "total_videos_found": 0,
            "errors": [],
        }

    async def crawl_all_courses(self, page: Page, only_empty: bool = False) -> Dict[str, int]:
        """
        Crawl all courses to extract video information

        Args:
            page: Playwright Page object (already logged in)
            only_empty: If True, only crawl courses with empty learning_points list

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

        # Build list of (category, course) tuples to crawl
        courses_to_crawl = []
        for category in self.content_manager.categories:
            for course in category.courses:
                if only_empty:
                    # Only include courses with empty learning_points
                    if not course.learning_points:
                        courses_to_crawl.append((category, course))
                else:
                    courses_to_crawl.append((category, course))

        # Count statistics
        total_courses_all = sum(len(cat.courses) for cat in self.content_manager.categories)

        logger.info(f"📚 Found {len(self.content_manager.categories)} categories")
        if only_empty:
            logger.info(f"🎯 Only crawling courses with empty learning_points list")
            logger.info(f"📚 Found {len(courses_to_crawl)} empty courses out of {total_courses_all} total")
        else:
            logger.info(f"📚 Total courses to crawl: {len(courses_to_crawl)}")

        if not courses_to_crawl:
            logger.info("✅ No courses to crawl (all have learning_points already)")
            return self.stats

        logger.info(f"⏱️  Delay between requests: {self.min_delay}-{self.max_delay}s")
        logger.info(f"🔄 Max retries per course: {self.max_retries}")

        # Crawl each course
        for course_counter, (category, course) in enumerate(courses_to_crawl, 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"📂 Category: {category.title}")
            logger.info(f"{'=' * 70}")

            logger.info(f"\n🎓 Course [{course_counter}/{len(courses_to_crawl)}]: {course.title}")
            logger.info(f"🔗 URL: {course.url}")

            # Crawl course with retry logic (returns list of LearnPoint objects)
            learning_points = await self._crawl_course_with_retry(
                page, course.url, course.title, category, course
            )

            if learning_points:
                # Update course with LearnPoint structure
                course.learning_points = learning_points
                course.last_updated = datetime.now().isoformat()

                # Count total videos across all LearnPoints
                total_videos = sum(len(lp.videos) for lp in learning_points)

                self.stats["courses_crawled"] += 1
                self.stats["total_videos_found"] += total_videos

                logger.info(f"✅ Successfully crawled {total_videos} videos in {len(learning_points)} LearnPoints")

                # Save immediately after each successful course
                logger.info(f"💾 Saving progress to {self.content_file.name}...")
                self.content_manager.save()
                logger.info(f"✅ Progress saved!")
            else:
                self.stats["courses_failed"] += 1
                logger.warning(f"⚠️  Failed to crawl course")

            # Human-like delay before next course
            if course_counter < len(courses_to_crawl):
                delay = random.uniform(self.min_delay, self.max_delay)
                logger.info(f"⏳ Waiting {delay:.1f}s before next course...")
                await asyncio.sleep(delay)

        # Final save (in case last course failed)
        logger.info(f"\n{'=' * 70}")
        logger.info("💾 FINAL SAVE")
        logger.info(f"{'=' * 70}")

        self.content_manager.save()
        logger.info(f"✅ All progress saved to {self.content_file}")

        # Print final statistics
        self._print_statistics()

        return self.stats

    async def _crawl_course_with_retry(
        self,
        page: Page,
        course_url: str,
        course_title: str,
        category: Optional['Category'] = None,
        course: Optional['Course'] = None,
    ) -> Optional[List[LearnPoint]]:
        """
        Crawl a single course with retry logic

        Args:
            page: Playwright Page object
            course_url: Course page URL
            course_title: Course title (for logging)
            category: Category object (for download path)
            course: Course object (for updating overview, transcript, duration)

        Returns:
            List of LearnPoint objects (each containing videos) or None if failed
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

                # Step 1: Extract course duration
                logger.info("📝 Extracting course duration...")

                # Extract duration
                duration = await self.parser.extract_duration(page)
                if duration > 0:
                    course.duration = duration
                    logger.info(f"   ✅ Duration: {duration} minutes")

                # NOTE: Overview and transcript will be extracted in 'videos' option
                # This keeps 'courses' option focused on: duration + learning_points + vimeo URLs

                # Human-like behavior: Scroll and read course page
                if self.enable_human_behavior:
                    logger.debug("🖱️  Simulating human behavior on course page...")

                    # Create human behavior simulator for this page
                    behavior = HumanBehaviorSimulator(page)

                    # Scroll down to view course content
                    await behavior.human_scroll(
                        direction="down",
                        distance=random.randint(300, 600)
                    )

                    # Small pause to "read" the content
                    await asyncio.sleep(random.uniform(0.8, 1.5))

                    # Scroll back up a bit (natural reading pattern)
                    await behavior.human_scroll(
                        direction="up",
                        distance=random.randint(100, 200)
                    )

                # Step 2: Extract LearnPoint structure with videos
                logger.info("📦 Extracting LearnPoint structure...")
                learning_points_dict = await self.parser.extract_learning_points(page)

                if not learning_points_dict:
                    logger.warning(f"⚠️  No learning points found (attempt {attempt})")
                    if attempt < self.max_retries:
                        await asyncio.sleep(random.uniform(2, 4))
                        continue
                    return None

                # Count total steps across all LearnPoints
                total_steps = sum(len(steps) for steps in learning_points_dict.values())
                logger.info(f"📖 Found {total_steps} steps across {len(learning_points_dict)} LearnPoints")

                # Convert StepInfo objects to Video objects (no need to visit each step)
                # All information is already available from the learning_points structure
                videos_by_learn_point = {}  # Dict[str, List[Video]]

                for lp_name, lp_steps in learning_points_dict.items():
                    videos_by_learn_point[lp_name] = []

                    for step in lp_steps:
                        # Create Video object from StepInfo (all fields already extracted)
                        video = Video(
                            title=step.title,
                            url=step.url,
                            step_id=step.step_id,
                            duration=step.duration,
                            learning_point=lp_name,
                            last_updated=datetime.now().isoformat()
                        )
                        videos_by_learn_point[lp_name].append(video)
                        logger.debug(f"   ✓ {step.title} ({step.duration})")

                # Convert videos_by_learn_point dict to list of LearnPoint objects
                learn_points = []
                for lp_name, lp_videos in videos_by_learn_point.items():
                    learn_point = LearnPoint(
                        title=lp_name,
                        videos=lp_videos
                    )
                    learn_points.append(learn_point)

                return learn_points

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

        if self.stats['courses_crawled'] > 0:
            avg_videos = self.stats['total_videos_found'] / self.stats['courses_crawled']
            logger.info(f"📈 Average videos per course: {avg_videos:.1f}")

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

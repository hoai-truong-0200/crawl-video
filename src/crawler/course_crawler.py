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
        content_file: Path = Path("data/courses/learn-content.json"),
        parser: Optional[CourseParser] = None,
        min_delay: float = 1.5,
        max_delay: float = 3.0,
        max_retries: int = 3,
        enable_human_behavior: bool = True,
        enable_download: bool = True,
        download_dir: Path = Path("downloads"),
    ):
        """
        Initialize course crawler

        Args:
            content_file: Path to learn-content.json or explore-content.json
            parser: CourseParser instance (creates new if None)
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            max_retries: Maximum retry attempts for failed requests
            enable_human_behavior: Enable human-like behavior (scrolling, mouse movements)
            enable_download: Enable video downloading
            download_dir: Base directory for video downloads
        """
        self.content_file = content_file
        self.parser = parser or CourseParser()
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.enable_human_behavior = enable_human_behavior
        self.enable_download = enable_download

        # Content manager for loading/saving JSON
        self.content_manager = ContentManager(content_file)

        # Detect content type from file path
        content_type = "learn-content" if "learn-content" in str(content_file) else "explore-content"

        # Video downloader
        self.downloader = VideoDownloader(
            download_dir=Path("data/downloads"),
            content_type=content_type
        )

        # Statistics
        self.stats = {
            "courses_crawled": 0,
            "courses_failed": 0,
            "total_videos_found": 0,
            "videos_with_vimeo": 0,
            "videos_without_vimeo": 0,
            "videos_downloaded": 0,
            "videos_download_failed": 0,
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
                videos = await self._crawl_course_with_retry(
                    page, course.url, course.title, category, course
                )

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

                    # Save immediately after each successful course
                    logger.info(f"💾 Saving progress to {self.content_file.name}...")
                    self.content_manager.save()
                    logger.info(f"✅ Progress saved!")
                else:
                    self.stats["courses_failed"] += 1
                    logger.warning(f"⚠️  Failed to crawl course")

                # Human-like delay before next course
                if course_counter < total_courses:
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
    ) -> Optional[List[Video]]:
        """
        Crawl a single course with retry logic

        Args:
            page: Playwright Page object
            course_url: Course page URL
            course_title: Course title (for logging)
            category: Category object (for download path)
            course: Course object (for JSON updates)

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

                        # Human-like behavior: Move mouse and simulate viewing
                        if self.enable_human_behavior:
                            # Create behavior simulator
                            behavior = HumanBehaviorSimulator(page)

                            # Try to find video player and move mouse to it
                            try:
                                video_player = await page.query_selector('iframe[src*="vimeo"]')
                                if video_player:
                                    # Get video player position
                                    box = await video_player.bounding_box()
                                    if box:
                                        # Move mouse to center of video player
                                        target_x = box['x'] + box['width'] / 2
                                        target_y = box['y'] + box['height'] / 2

                                        await behavior.move_mouse_to(
                                            target_x,
                                            target_y
                                        )

                                        # Small pause like watching the preview
                                        await asyncio.sleep(random.uniform(0.5, 1.0))
                            except Exception as e:
                                logger.debug(f"Could not move mouse to video player: {e}")

                            # Small scroll to simulate engagement
                            await behavior.human_scroll(
                                direction="down",
                                distance=random.randint(100, 200)
                            )

                        # Step 1: Create Video object with basic info (title + url)
                        video = Video(
                            title=step.title,
                            url=step.url,
                            vimeo_url="",  # Will be filled after extraction
                            downloaded=False,
                            uploaded_to_drive=False,
                            drive_file_id=""
                        )

                        # Step 2: Add video to list and save to JSON immediately
                        videos.append(video)

                        # Save progress to JSON after adding video info (if course object provided)
                        if course:
                            course.videos = videos
                            self.content_manager.save()
                            logger.debug(f"      💾 Saved video info to JSON: {step.title}")

                        # Step 3: Extract video URLs from DOM using VimeoExtractor
                        logger.debug("      🔍 Extracting video URLs from DOM...")
                        video_urls = await VimeoExtractor.extract_video_urls(page, timeout=10000)

                        vimeo_url = None
                        best_download_url = None

                        if video_urls:
                            vimeo_url = video_urls.get('vimeo_player_url', '')
                            best_download_url = video_urls.get('best_download_url', '')
                            logger.debug(f"      ✅ Extracted URLs - Vimeo: {vimeo_url}")
                            logger.debug(f"      ✅ Best download URL: {best_download_url[:100]}...")

                            # Update video with vimeo_url
                            video.vimeo_url = vimeo_url or ""
                            if course:
                                self.content_manager.save()
                        else:
                            logger.warning("      ⚠️  Failed to extract video URLs from DOM")

                        # Step 4: Download video if enabled and best_download_url found
                        if self.enable_download and best_download_url and category and course:
                            # Get category/series name and course name
                            category_or_series = category.title
                            course_name = course.title

                            logger.info(f"      📥 Starting download: {step.title}")

                            # Download video using extracted URL (DOM-based)
                            download_success = await self.downloader.download_from_extracted_url(
                                download_url=best_download_url,
                                category_or_series=category_or_series,
                                course_name=course_name,
                                video_title=step.title,
                            )

                            # Step 5: Update JSON with download status
                            if download_success:
                                video.downloaded = True
                                self.stats["videos_downloaded"] += 1
                                logger.info(f"      ✅ Download complete & JSON updated")
                            else:
                                self.stats["videos_download_failed"] += 1
                                logger.error(f"      ❌ Download failed")

                            # Save download status to JSON
                            if course:
                                self.content_manager.save()

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

        # Download statistics
        if self.enable_download:
            logger.info(f"📥 Video Downloads:")
            logger.info(f"   - Downloaded: {self.stats['videos_downloaded']}")
            logger.info(f"   - Failed: {self.stats['videos_download_failed']}")

            if self.stats['videos_downloaded'] > 0:
                download_stats = self.downloader.get_download_stats()
                logger.info(f"💾 Storage: {download_stats['total_size_mb']:.1f} MB")

        if self.stats['courses_crawled'] > 0:
            avg_videos = self.stats['total_videos_found'] / self.stats['courses_crawled']
            logger.info(f"📈 Average videos per course: {avg_videos:.1f}")

            if self.stats['total_videos_found'] > 0:
                success_rate = (self.stats['videos_with_vimeo'] / self.stats['total_videos_found']) * 100
                logger.info(f"📈 Vimeo extraction success rate: {success_rate:.1f}%")

            if self.enable_download and self.stats['total_videos_found'] > 0:
                download_rate = (self.stats['videos_downloaded'] / self.stats['total_videos_found']) * 100
                logger.info(f"📈 Download success rate: {download_rate:.1f}%")

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

"""
Video Content Crawler

Module to crawl and extract overview/transcript text from individual video pages.
Saves content to .txt files instead of storing in JSON.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import Page
from loguru import logger
from datetime import datetime

from src.crawler.content_manager import ContentManager
from src.crawler.course_parser import CourseParser


class VideoCrawler:
    """
    Crawler for extracting video content (overview + transcript) and saving to .txt files

    Iterates through all videos in JSON and extracts content from individual video step pages.
    """

    def __init__(
        self,
        content_file: Path,
        base_url: str,
        min_delay: float = 1.5,
        max_delay: float = 3.0,
        max_retries: int = 3
    ):
        """
        Initialize video crawler

        Args:
            content_file: Path to learn-content.json or explore-content.json
            base_url: Base URL for video pages (e.g., "https://hodai.globis.co.jp")
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            max_retries: Maximum number of retries per video
        """
        self.content_file = content_file
        self.base_url = base_url
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

        # Initialize managers
        self.content_manager = ContentManager(content_file)
        self.parser = CourseParser()

        # Detect content type
        self.is_explore_content = "explore-content" in str(content_file)

        # Extract language from path
        self.language = "en"
        if "/ja/" in str(content_file):
            self.language = "ja"

        logger.info(f"📹 VideoCrawler initialized for {self.language}")
        logger.info(f"   Content file: {content_file}")
        logger.info(f"   Base URL: {base_url}")
        logger.info(f"   Delay range: {min_delay}-{max_delay}s")

    async def crawl_all_videos(self, page: Page) -> Dict[str, Any]:
        """
        Crawl all videos from JSON and extract overview/transcript

        Args:
            page: Playwright Page object

        Returns:
            Statistics dictionary
        """
        logger.info("\n" + "="*70)
        logger.info("📹 CRAWL VIDEO CONTENT (Overview + Transcript)")
        logger.info("="*70)

        # Load content
        self.content_manager.load()

        # Get items (categories or series)
        items = self.content_manager.categories if self.content_manager.categories else self.content_manager.series
        item_type = "categories" if self.content_manager.categories else "series"

        if not items:
            logger.error(f"❌ No {item_type} found in content file")
            return {
                'total_videos': 0,
                'processed': 0,
                'skipped': 0,
                'failed': 0
            }

        logger.info(f"📊 Found {len(items)} {item_type}")

        # Statistics
        stats = {
            'total_videos': 0,
            'processed': 0,
            'skipped': 0,
            'failed': 0
        }

        # Iterate through items
        for item_idx, item in enumerate(items, 1):
            item_name = item.title
            logger.info(f"\n{'='*70}")
            logger.info(f"📁 [{item_idx}/{len(items)}] {item_type.rstrip('s').upper()}: {item_name}")
            logger.info(f"{'='*70}")

            # Iterate through courses
            for course_idx, course in enumerate(item.courses, 1):
                logger.info(f"\n📘 [{course_idx}/{len(item.courses)}] Course: {course.title}")

                # Iterate through learning points
                for lp_idx, lp in enumerate(course.learning_points, 1):
                    logger.info(f"   📌 [{lp_idx}/{len(course.learning_points)}] {lp.title}")

                    # Iterate through videos
                    for video_idx, video in enumerate(lp.videos, 1):
                        stats['total_videos'] += 1

                        # Skip if already extracted
                        if video.is_content:
                            logger.info(f"      ⏭️  [{video_idx}/{len(lp.videos)}] {video.title} - Already extracted")
                            stats['skipped'] += 1
                            continue

                        logger.info(f"      🎬 [{video_idx}/{len(lp.videos)}] {video.title}")

                        # Extract content
                        success = await self._extract_video_content(
                            page=page,
                            video=video,
                            item_name=item_name,
                            course_name=course.title
                        )

                        if success:
                            # Mark as extracted
                            video.is_content = True
                            video.last_updated = datetime.now().isoformat()
                            stats['processed'] += 1

                            # Save progress incrementally
                            self.content_manager.save()
                            logger.info(f"         ✅ Content extracted and saved")
                        else:
                            stats['failed'] += 1
                            logger.warning(f"         ❌ Failed to extract content")

                        # Random delay
                        delay = self.min_delay + (self.max_delay - self.min_delay) * (hash(video.url) % 100) / 100
                        logger.debug(f"         ⏳ Waiting {delay:.1f}s...")
                        await asyncio.sleep(delay)

        # Summary
        logger.info("\n" + "="*70)
        logger.info("📊 VIDEO CONTENT CRAWLING COMPLETE")
        logger.info("="*70)
        logger.info(f"Total videos:    {stats['total_videos']}")
        logger.info(f"Processed:       {stats['processed']}")
        logger.info(f"Skipped:         {stats['skipped']}")
        logger.info(f"Failed:          {stats['failed']}")
        logger.info("="*70)

        return stats

    async def _extract_video_content(
        self,
        page: Page,
        video: Any,
        item_name: str,
        course_name: str
    ) -> bool:
        """
        Extract overview and transcript for a single video

        Args:
            page: Playwright Page object
            video: Video object
            item_name: Category or Series name
            course_name: Course name

        Returns:
            True if successful, False otherwise
        """
        # Build full URL
        video_url = video.url
        if not video_url.startswith('http'):
            video_url = f"{self.base_url}{video_url}"

        for attempt in range(1, self.max_retries + 1):
            try:
                if attempt > 1:
                    logger.info(f"         🔄 Retry {attempt}/{self.max_retries}")

                # Navigate to video page
                logger.debug(f"         🌐 Navigating to: {video_url}")
                await page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(1)  # Wait for dynamic content

                # Extract overview
                logger.debug(f"         📝 Extracting overview...")
                overview = await self.parser.extract_overview(page)

                # Extract transcript
                logger.debug(f"         📜 Extracting transcript...")
                transcript = await self.parser.extract_transcript(page)

                # Check if we got content
                if not overview and not transcript:
                    logger.warning(f"         ⚠️  No content found on page")
                    if attempt < self.max_retries:
                        continue
                    return False

                # Save to files
                overview_path = None
                transcript_path = None

                if overview:
                    overview_path = self.parser.save_overview_to_file(
                        overview=overview,
                        language=self.language,
                        category_or_series=item_name,
                        course_title=course_name,
                        base_dir=Path("downloads")
                    )
                    logger.debug(f"         💾 Overview saved: {overview_path}")

                if transcript:
                    transcript_path = self.parser.save_transcript_to_file(
                        transcript=transcript,
                        language=self.language,
                        category_or_series=item_name,
                        course_title=course_name,
                        base_dir=Path("downloads")
                    )
                    logger.debug(f"         💾 Transcript saved: {transcript_path}")

                return True

            except Exception as e:
                logger.error(f"         ❌ Error extracting content: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 * attempt)  # Exponential backoff
                    continue
                return False

        return False

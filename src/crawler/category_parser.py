"""
Category Page Parser

Parses GLOBIS Unlimited category pages to extract course information.
"""

from dataclasses import dataclass
from typing import List, Optional
from playwright.async_api import Page
from loguru import logger


@dataclass
class CourseInfo:
    """Course information extracted from category page"""
    title: str
    url: str
    duration: Optional[str] = None  # Format: "00:07:40"


class CategoryParser:
    """
    Parser for GLOBIS Unlimited category pages

    Extracts course information from category listing pages.
    """

    # Selectors (based on HTML structure analysis)
    COURSE_CONTAINER_SELECTOR = '[class*="__course"]'
    COURSE_LINK_SELECTOR = 'a[href*="/courses/"]'
    COURSE_TITLE_SELECTOR = '[class*="__title"]'
    COURSE_DURATION_SELECTOR = '[class*="__duration"]'

    def __init__(self, base_url: str = "https://unlimited.globis.co.jp"):
        """
        Initialize parser

        Args:
            base_url: Base URL for GLOBIS Unlimited
        """
        self.base_url = base_url.rstrip('/')

    async def parse_category_page(self, page: Page) -> List[CourseInfo]:
        """
        Parse a category page and extract all courses

        Args:
            page: Playwright Page object (already navigated to category page)

        Returns:
            List of CourseInfo objects
        """
        logger.info("🔍 Parsing category page...")

        # Wait for courses to load
        try:
            await page.wait_for_selector(self.COURSE_CONTAINER_SELECTOR, timeout=10000)
        except Exception as e:
            logger.warning(f"⚠️  Course containers not found: {e}")
            return []

        # Get all course containers
        course_elements = await page.query_selector_all(self.COURSE_CONTAINER_SELECTOR)
        logger.info(f"Found {len(course_elements)} course containers")

        courses = []

        for idx, course_elem in enumerate(course_elements, 1):
            try:
                course_info = await self._extract_course_info(course_elem)
                if course_info:
                    courses.append(course_info)
                    logger.debug(f"  [{idx}/{len(course_elements)}] ✅ {course_info.title}")
                else:
                    logger.debug(f"  [{idx}/{len(course_elements)}] ⚠️  Skipped (no info)")

            except Exception as e:
                logger.warning(f"  [{idx}/{len(course_elements)}] ❌ Error extracting course: {e}")
                continue

        logger.info(f"✅ Successfully extracted {len(courses)} courses")
        return courses

    async def _extract_course_info(self, course_elem) -> Optional[CourseInfo]:
        """
        Extract course information from a single course element

        Args:
            course_elem: Playwright ElementHandle for course container

        Returns:
            CourseInfo object or None if extraction failed
        """
        # Extract course link and URL
        link_elem = await course_elem.query_selector(self.COURSE_LINK_SELECTOR)
        if not link_elem:
            return None

        href = await link_elem.get_attribute('href')
        if not href:
            return None

        # Make URL absolute if relative
        if href.startswith('/'):
            url = f"{self.base_url}{href}"
        else:
            url = href

        # Extract title
        title_elem = await course_elem.query_selector(self.COURSE_TITLE_SELECTOR)
        if title_elem:
            title = (await title_elem.inner_text()).strip()
        else:
            # Fallback: try to get alt text from image or link text
            title = await self._extract_fallback_title(course_elem)

        if not title:
            return None

        # Extract duration (optional)
        duration = None
        duration_elem = await course_elem.query_selector(self.COURSE_DURATION_SELECTOR)
        if duration_elem:
            duration = (await duration_elem.inner_text()).strip()

        return CourseInfo(
            title=title,
            url=url,
            duration=duration
        )

    async def _extract_fallback_title(self, course_elem) -> Optional[str]:
        """
        Fallback method to extract title if primary selector fails

        Args:
            course_elem: Playwright ElementHandle for course container

        Returns:
            Title string or None
        """
        # Try image alt text
        img_elem = await course_elem.query_selector('img[alt]')
        if img_elem:
            alt = await img_elem.get_attribute('alt')
            if alt and alt.strip():
                return alt.strip()

        # Try link text
        link_elem = await course_elem.query_selector('a')
        if link_elem:
            text = await link_elem.inner_text()
            if text and text.strip():
                # Clean up text (remove extra whitespace, newlines)
                cleaned = ' '.join(text.strip().split())
                if cleaned:
                    return cleaned

        return None

    def filter_by_duration(self, courses: List[CourseInfo], min_duration: Optional[str] = None, max_duration: Optional[str] = None) -> List[CourseInfo]:
        """
        Filter courses by duration

        Args:
            courses: List of CourseInfo objects
            min_duration: Minimum duration (format: "00:05:00" for 5 minutes)
            max_duration: Maximum duration

        Returns:
            Filtered list of courses
        """
        if not min_duration and not max_duration:
            return courses

        filtered = []
        for course in courses:
            if not course.duration:
                # Include courses without duration info
                filtered.append(course)
                continue

            duration_seconds = self._parse_duration(course.duration)
            if duration_seconds is None:
                filtered.append(course)
                continue

            if min_duration:
                min_seconds = self._parse_duration(min_duration)
                if min_seconds and duration_seconds < min_seconds:
                    continue

            if max_duration:
                max_seconds = self._parse_duration(max_duration)
                if max_seconds and duration_seconds > max_seconds:
                    continue

            filtered.append(course)

        return filtered

    @staticmethod
    def _parse_duration(duration_str: str) -> Optional[int]:
        """
        Parse duration string to seconds

        Args:
            duration_str: Duration in format "HH:MM:SS" or "MM:SS"

        Returns:
            Duration in seconds or None if parsing failed
        """
        try:
            parts = duration_str.strip().split(':')
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            else:
                return None
        except (ValueError, AttributeError):
            return None

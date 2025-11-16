"""
Course Parser

Parses individual course pages to extract video information (steps/lessons).
Each course contains multiple steps, where each step is a video lesson.
"""

from typing import List, Optional
from dataclasses import dataclass
from playwright.async_api import Page
from loguru import logger


@dataclass
class StepInfo:
    """
    Information about a single step (video lesson) within a course

    Attributes:
        title: Step title (e.g., "Introduction", "Proposal Structure")
        url: Step URL (e.g., "/en/courses/d8501fa9/learn/steps/60784")
        duration: Video duration (e.g., "01:23")
        vimeo_url: Vimeo player URL (e.g., "https://player.vimeo.com/video/1117632958")
        step_id: Step ID extracted from URL (e.g., "60784")
    """
    title: str
    url: str
    duration: str = ""
    vimeo_url: str = ""
    step_id: str = ""


class CourseParser:
    """
    Parser for GLOBIS Unlimited course pages

    Course Structure:
    - Each course has multiple steps (video lessons)
    - Steps are listed in the sidebar under "Content"
    - Each step has: title, duration, URL
    - When you visit a step URL, the Vimeo iframe loads with the video

    Selectors identified from inspect_course_page.py:
    - Step links: a[href*="/learn/steps/"]
    - Step titles: .sc-TFQUm.fpyALS__styledTitle
    - Step durations: time.sc-TFQUm.fpyALS__styledTime
    - Vimeo iframe: iframe[src*="player.vimeo.com"]
    """

    def __init__(self):
        """Initialize course parser"""
        pass

    async def parse_course_page(self, page: Page) -> List[StepInfo]:
        """
        Parse course page to extract all steps (video lessons)

        This extracts the step list from the sidebar, which shows all steps
        in the course with their titles and durations.

        Args:
            page: Playwright Page object (already on course page)

        Returns:
            List of StepInfo objects
        """
        steps = []

        try:
            # Wait for step links to load
            # Using the selector pattern we found: a[href*="/learn/steps/"]
            await page.wait_for_selector('a[href*="/learn/steps/"]', timeout=10000)

            # Get all step links from sidebar
            step_elements = await page.query_selector_all('a[href*="/learn/steps/"]')

            logger.info(f"Found {len(step_elements)} step elements")

            for element in step_elements:
                try:
                    # Extract step URL
                    url = await element.get_attribute('href')

                    if not url:
                        continue

                    # Extract step ID from URL
                    # URL format: /en/courses/{course_id}/learn/steps/{step_id}
                    step_id = url.split('/')[-1] if url else ""

                    # Extract title
                    # Title is in a span with class containing "styledTitle"
                    title_element = await element.query_selector('span[class*="styledTitle"]')
                    title = await title_element.inner_text() if title_element else ""

                    # Extract duration
                    # Duration is in a time element with class containing "styledTime"
                    duration_element = await element.query_selector('time[class*="styledTime"]')
                    duration = await duration_element.inner_text() if duration_element else ""

                    # Create StepInfo
                    step_info = StepInfo(
                        title=title.strip(),
                        url=url,
                        duration=duration.strip(),
                        step_id=step_id,
                        vimeo_url="",  # Will be extracted when visiting the step
                    )

                    steps.append(step_info)

                    logger.debug(f"Extracted step: {step_info.title} ({step_info.duration})")

                except Exception as e:
                    logger.warning(f"Failed to extract step info: {e}")
                    continue

            logger.info(f"✅ Successfully extracted {len(steps)} steps")

        except Exception as e:
            logger.error(f"❌ Failed to parse course page: {e}")

        return steps

    async def extract_vimeo_url(self, page: Page) -> Optional[str]:
        """
        Extract Vimeo URL from current step page

        When on a step page, the video player is a Vimeo iframe.
        This extracts the Vimeo player URL.

        Args:
            page: Playwright Page object (on a step page)

        Returns:
            Vimeo player URL or None if not found
        """
        try:
            # Wait for Vimeo iframe to load
            iframe = await page.wait_for_selector(
                'iframe[src*="player.vimeo.com"]',
                timeout=10000
            )

            if iframe:
                vimeo_url = await iframe.get_attribute('src')
                logger.debug(f"Found Vimeo URL: {vimeo_url}")
                return vimeo_url

        except Exception as e:
            logger.warning(f"Could not find Vimeo iframe: {e}")

        return None

    def extract_vimeo_id(self, vimeo_url: str) -> Optional[str]:
        """
        Extract Vimeo video ID from player URL

        URL format: https://player.vimeo.com/video/1117632958

        Args:
            vimeo_url: Vimeo player URL

        Returns:
            Vimeo video ID (e.g., "1117632958") or None
        """
        try:
            if "player.vimeo.com/video/" in vimeo_url:
                # Extract ID from URL
                parts = vimeo_url.split("player.vimeo.com/video/")
                if len(parts) > 1:
                    # Get ID (remove any query parameters)
                    video_id = parts[1].split("?")[0].split("#")[0]
                    return video_id
        except Exception as e:
            logger.warning(f"Failed to extract Vimeo ID: {e}")

        return None

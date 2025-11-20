"""
Course Parser

Parses individual course pages to extract video information (steps/lessons).
Each course contains multiple steps, where each step is a video lesson.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path
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

    async def extract_overview(self, page: Page) -> str:
        """
        Extract course overview/description from course page

        The overview is typically found in:
        - Meta description tag
        - Course description section on the page
        - Overview/About section

        Args:
            page: Playwright Page object (on course page)

        Returns:
            Course overview text or empty string if not found
        """
        try:
            # Try multiple selectors to find overview
            selectors = [
                # Common patterns for course description
                'div[class*="overview"]',
                'div[class*="description"]',
                'div[class*="courseDescription"]',
                'div[class*="about"]',
                'meta[name="description"]',
                'meta[property="og:description"]',
                # Generic content areas
                'div[class*="content"] p',
                'section[class*="about"] p',
            ]

            for selector in selectors:
                try:
                    if 'meta' in selector:
                        # Extract from meta tag
                        element = await page.query_selector(selector)
                        if element:
                            content = await element.get_attribute('content')
                            if content and len(content.strip()) > 20:
                                logger.debug(f"Found overview in meta tag: {selector}")
                                return content.strip()
                    else:
                        # Extract from element text
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.inner_text()
                            if text and len(text.strip()) > 20:
                                logger.debug(f"Found overview in: {selector}")
                                return text.strip()
                except Exception:
                    continue

            logger.warning("Could not find course overview")
            return ""

        except Exception as e:
            logger.error(f"Failed to extract overview: {e}")
            return ""

    async def extract_transcript(self, page: Page) -> str:
        """
        Extract course transcript from course page

        Transcripts may be found in:
        - Transcript tab/section
        - Accordion/collapsible sections
        - Separate transcript page

        Args:
            page: Playwright Page object (on course page)

        Returns:
            Full transcript text or empty string if not found
        """
        try:
            # Try to find and click transcript tab if it exists
            transcript_triggers = [
                'button:has-text("Transcript")',
                'a:has-text("Transcript")',
                'div[class*="transcript"]',
                'button:has-text("字幕")',  # Japanese: "Subtitles"
            ]

            for trigger in transcript_triggers:
                try:
                    element = await page.query_selector(trigger)
                    if element:
                        # Try to click to expand transcript
                        await element.click(timeout=2000)
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Try to extract transcript content
            transcript_selectors = [
                'div[class*="transcript"] pre',
                'div[class*="transcript"] p',
                'div[class*="subtitle"]',
                'pre[class*="transcript"]',
            ]

            for selector in transcript_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        transcript_parts = []
                        for elem in elements:
                            text = await elem.inner_text()
                            if text and len(text.strip()) > 10:
                                transcript_parts.append(text.strip())

                        if transcript_parts:
                            full_transcript = "\n".join(transcript_parts)
                            logger.debug(f"Found transcript ({len(full_transcript)} chars)")
                            return full_transcript

                except Exception:
                    continue

            logger.warning("Could not find course transcript")
            return ""

        except Exception as e:
            logger.error(f"Failed to extract transcript: {e}")
            return ""

    async def extract_duration(self, page: Page) -> int:
        """
        Extract total course duration in minutes

        Duration may be calculated from:
        - Sum of all video step durations
        - Course metadata showing total time
        - Duration indicator on page

        Args:
            page: Playwright Page object (on course page)

        Returns:
            Total duration in minutes (0 if not found)
        """
        try:
            # Strategy 1: Sum up all step durations
            step_durations = []
            duration_elements = await page.query_selector_all('time[class*="styledTime"]')

            for elem in duration_elements:
                try:
                    duration_text = await elem.inner_text()
                    # Parse duration like "01:23" or "1:23"
                    if ':' in duration_text:
                        parts = duration_text.strip().split(':')
                        if len(parts) == 2:
                            minutes = int(parts[0])
                            seconds = int(parts[1])
                            total_seconds = minutes * 60 + seconds
                            step_durations.append(total_seconds)
                except Exception:
                    continue

            if step_durations:
                total_seconds = sum(step_durations)
                total_minutes = total_seconds // 60
                logger.debug(f"Calculated total duration: {total_minutes} minutes from {len(step_durations)} steps")
                return total_minutes

            # Strategy 2: Look for total duration indicator
            duration_selectors = [
                'span[class*="duration"]',
                'div[class*="totalTime"]',
                'span:has-text("min")',
                'span:has-text("分")',  # Japanese: "minutes"
            ]

            for selector in duration_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        # Try to extract number from text like "45 min" or "45分"
                        import re
                        match = re.search(r'(\d+)', text)
                        if match:
                            duration = int(match.group(1))
                            logger.debug(f"Found duration indicator: {duration} minutes")
                            return duration
                except Exception:
                    continue

            logger.warning("Could not find course duration")
            return 0

        except Exception as e:
            logger.error(f"Failed to extract duration: {e}")
            return 0

    async def extract_learning_points(self, page: Page) -> Dict[str, List[StepInfo]]:
        """
        Extract LearnPoint structure from course page

        LearnPoints are groups of videos organized by learning objectives.
        They are identified by elements with class containing '__learningPointName'

        Args:
            page: Playwright Page object (on course page)

        Returns:
            Dictionary mapping LearnPoint titles to lists of StepInfo objects
            Example: {"Introduction": [step1, step2], "Main Content": [step3, step4]}
        """
        try:
            learning_points = {}
            current_learn_point = "Default"

            # Strategy 1: Find LearnPoint headers by class pattern
            # Look for elements with class containing '__learningPointName'
            learn_point_selectors = [
                '[class*="__learningPointName"]',
                '[class*="learningPoint"]',
                '[class*="sectionTitle"]',
                '[class*="chapterTitle"]',
            ]

            # Get all step links
            step_elements = await page.query_selector_all('a[href*="/learn/steps/"]')
            logger.debug(f"Found {len(step_elements)} step elements")

            # Try to find LearnPoint structure
            for step_element in step_elements:
                try:
                    # Look for LearnPoint header before this step
                    # Check parent and ancestor elements
                    parent = await step_element.evaluate_handle('el => el.parentElement')

                    # Try to find LearnPoint name in parent hierarchy
                    learn_point_name = None

                    for selector in learn_point_selectors:
                        try:
                            # Look for LearnPoint header in parent or siblings
                            lp_element = await parent.as_element().query_selector(f'xpath=ancestor::*[1]//{selector}')
                            if not lp_element:
                                # Try looking in preceding siblings
                                lp_element = await parent.as_element().query_selector(f'xpath=preceding-sibling::*[1]//{selector}')

                            if lp_element:
                                learn_point_name = await lp_element.inner_text()
                                if learn_point_name and len(learn_point_name.strip()) > 0:
                                    learn_point_name = learn_point_name.strip()
                                    break
                        except Exception:
                            continue

                    # If found a new LearnPoint name, update current
                    if learn_point_name and learn_point_name != current_learn_point:
                        current_learn_point = learn_point_name
                        logger.debug(f"Found LearnPoint: {current_learn_point}")

                    # Extract step info
                    url = await step_element.get_attribute('href')
                    if not url:
                        continue

                    step_id = url.split('/')[-1] if url else ""

                    # Extract title
                    title_element = await step_element.query_selector('span[class*="styledTitle"]')
                    title = await title_element.inner_text() if title_element else ""

                    # Extract duration
                    duration_element = await step_element.query_selector('time[class*="styledTime"]')
                    duration = await duration_element.inner_text() if duration_element else ""

                    # Create StepInfo
                    step_info = StepInfo(
                        title=title.strip(),
                        url=url,
                        duration=duration.strip(),
                        step_id=step_id,
                        vimeo_url="",
                    )

                    # Add to current LearnPoint
                    if current_learn_point not in learning_points:
                        learning_points[current_learn_point] = []

                    learning_points[current_learn_point].append(step_info)

                except Exception as e:
                    logger.debug(f"Error processing step element: {e}")
                    continue

            # Log results
            if learning_points:
                logger.info(f"📦 Found {len(learning_points)} LearnPoints:")
                for lp_name, steps in learning_points.items():
                    logger.info(f"   - {lp_name}: {len(steps)} videos")
            else:
                logger.warning("No LearnPoint structure found, using Default")
                # Fallback: get all steps without grouping
                steps = await self.parse_course_page(page)
                learning_points["Default"] = steps

            return learning_points

        except Exception as e:
            logger.error(f"Failed to extract LearnPoint structure: {e}")
            # Fallback: return all steps in Default group
            try:
                steps = await self.parse_course_page(page)
                return {"Default": steps}
            except Exception:
                return {"Default": []}

    def save_overview_to_file(
        self,
        overview: str,
        language: str,
        category_or_series: str,
        course_title: str,
        base_dir: Path = Path("downloads")
    ) -> Optional[str]:
        """
        Save course overview to overview.txt file

        Args:
            overview: Overview text content
            language: Language code (en/ja)
            category_or_series: Category or Series name
            course_title: Course title
            base_dir: Base downloads directory

        Returns:
            Relative path to overview.txt from base_dir, or None if failed
        """
        if not overview or len(overview.strip()) == 0:
            return None

        try:
            # Sanitize folder names
            safe_category = self._sanitize_filename(category_or_series)
            safe_course = self._sanitize_filename(course_title)

            # Build path: downloads/{lang}/{Category}/{Course}/overview.txt
            course_dir = base_dir / language / safe_category / safe_course
            course_dir.mkdir(parents=True, exist_ok=True)

            overview_file = course_dir / "overview.txt"

            # Write overview
            with open(overview_file, 'w', encoding='utf-8') as f:
                f.write(overview)

            # Return relative path from base_dir
            relative_path = overview_file.relative_to(base_dir)
            logger.debug(f"✅ Saved overview to: {relative_path}")

            return str(relative_path)

        except Exception as e:
            logger.error(f"Failed to save overview to file: {e}")
            return None

    def save_transcript_to_file(
        self,
        transcript: str,
        language: str,
        category_or_series: str,
        course_title: str,
        base_dir: Path = Path("downloads")
    ) -> Optional[str]:
        """
        Save course transcript to transcript.txt file

        Args:
            transcript: Transcript text content
            language: Language code (en/ja)
            category_or_series: Category or Series name
            course_title: Course title
            base_dir: Base downloads directory

        Returns:
            Relative path to transcript.txt from base_dir, or None if failed
        """
        if not transcript or len(transcript.strip()) == 0:
            return None

        try:
            # Sanitize folder names
            safe_category = self._sanitize_filename(category_or_series)
            safe_course = self._sanitize_filename(course_title)

            # Build path: downloads/{lang}/{Category}/{Course}/transcript.txt
            course_dir = base_dir / language / safe_category / safe_course
            course_dir.mkdir(parents=True, exist_ok=True)

            transcript_file = course_dir / "transcript.txt"

            # Write transcript
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript)

            # Return relative path from base_dir
            relative_path = transcript_file.relative_to(base_dir)
            logger.debug(f"✅ Saved transcript to: {relative_path}")

            return str(relative_path)

        except Exception as e:
            logger.error(f"Failed to save transcript to file: {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename/folder name for safe filesystem usage

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(). strip('.')

        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]

        return sanitized if sanitized else "Untitled"

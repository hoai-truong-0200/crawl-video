"""
Content Extractor

Extracts course content (overview, transcript, summary) from GLOBIS course pages
and saves to text files.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict
from playwright.async_api import Page
from loguru import logger


class ContentExtractor:
    """
    Extractor for GLOBIS course content

    Extracts and saves:
    - overview.txt: Course overview from "Overview/概要" tab
    - transcript.txt: Full transcript from "Transcript/字幕" tab
    - summary.txt: AI summary from "learning-agent" tab (if available)

    File structure:
    downloads/[lang]/[categories|series]/[category_title]/[course_title]/
        ├── overview.txt
        ├── transcript.txt
        └── summary.txt (optional)
    """

    def __init__(self, base_dir: Path = Path("downloads")):
        """
        Initialize extractor

        Args:
            base_dir: Base directory for downloads (default: downloads/)
        """
        self.base_dir = base_dir

    async def extract_overview(self, page: Page) -> str:
        """
        Extract overview text from course page

        Steps:
        1. Wait for tab buttons to appear (dynamic content)
        2. Wait for overview content to appear
        3. Extract all text from element with class containing "courseInfoDetail"

        Args:
            page: Playwright Page object (on course page)

        Returns:
            Overview text (empty string if not found)
        """
        try:
            # Wait for page to be fully loaded
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
            logger.debug("Page loaded, waiting for dynamic content...")

            # CRITICAL: Wait for tab buttons to appear (indicates page is ready)
            try:
                await page.wait_for_selector('button[class*="TabButton"]', timeout=15000, state="visible")
                logger.debug("Tab buttons appeared, page is ready")
            except Exception as e:
                logger.warning(f"Tab buttons did not appear: {e}")
                # Continue anyway, maybe already loaded

            # CRITICAL: Wait for overview content to appear
            try:
                await page.wait_for_selector('[class*="courseInfoDetail"]', timeout=15000, state="visible")
                logger.debug("Overview content appeared")
            except Exception as e:
                logger.warning(f"Overview content did not appear: {e}")
                return ""

            # Small delay to ensure content is fully rendered
            await asyncio.sleep(1)

            # Check if Overview tab is already active (should be by default)
            overview_button = page.locator('button[class*="TabButton"]').filter(
                has_text="Overview"
            ).or_(
                page.locator('button[class*="TabButton"]').filter(has_text="概要")
            ).first

            if await overview_button.count() > 0:
                # Check if already active
                is_active = await overview_button.evaluate("el => el.classList.contains('bIzKKx__TabButton--active') || el.className.includes('--active')")

                if not is_active:
                    logger.debug("Overview tab not active, clicking...")
                    await overview_button.click()
                    await asyncio.sleep(2)
                else:
                    logger.debug("Overview tab already active")
            else:
                logger.debug("Overview tab button not found, assuming content already visible")

            # Extract overview content
            # Use actual class pattern from DOM: dKqlQt__courseInfoDetail
            overview_container = page.locator('[class*="courseInfoDetail"]').first
            if await overview_container.count() > 0:
                # Wait for content to be visible
                await overview_container.wait_for(state="visible", timeout=5000)
                overview_text = await overview_container.inner_text()
                logger.debug(f"Extracted overview: {len(overview_text)} characters")
                return overview_text.strip()
            else:
                logger.warning("Overview content container not found")
                return ""

        except Exception as e:
            logger.error(f"Failed to extract overview: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ""

    async def extract_transcript(self, page: Page) -> str:
        """
        Extract transcript text from course page

        Steps:
        1. Wait for tab buttons to appear
        2. Click Transcript tab
        3. Wait for transcript content to load
        4. Extract text

        Args:
            page: Playwright Page object (on course page)

        Returns:
            Transcript text (empty string if not found)
        """
        try:
            # Wait for page to be fully loaded (in case called separately)
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
            logger.debug("Page loaded for transcript extraction...")

            # Wait for tab buttons to appear
            try:
                await page.wait_for_selector('button[class*="TabButton"]', timeout=15000, state="visible")
                logger.debug("Tab buttons appeared")
            except Exception as e:
                logger.warning(f"Tab buttons did not appear: {e}")
                return ""

            # Click Transcript/字幕 tab
            transcript_button = page.locator('button[class*="TabButton"]').filter(
                has_text="Transcript"
            ).or_(
                page.locator('button[class*="TabButton"]').filter(has_text="字幕")
            ).first

            if await transcript_button.count() > 0:
                logger.debug("Clicking Transcript tab...")
                await transcript_button.click()

                # Wait for transcript content to load (with multiple possible selectors)
                logger.debug("Waiting for transcript content to appear...")

                # Try waiting for common transcript container patterns
                transcript_loaded = False
                for selector in ['[class*="transcriptContainer"]', '[class*="transcript"]', '[class*="Transcript"]']:
                    try:
                        await page.wait_for_selector(selector, timeout=10000, state="visible")
                        logger.debug(f"Transcript content appeared (selector: {selector})")
                        transcript_loaded = True
                        break
                    except:
                        continue

                if not transcript_loaded:
                    logger.warning("Transcript content did not appear after clicking tab")
                    # Wait a bit anyway
                    await asyncio.sleep(3)
            else:
                logger.warning("Transcript tab button not found")
                return ""

            # Extract transcript content
            # Try multiple possible container patterns
            transcript_container = page.locator('[class*="transcriptContainer"]').first

            # Fallback: try other common patterns
            if await transcript_container.count() == 0:
                logger.debug("Trying alternative transcript selectors...")
                transcript_container = page.locator('[class*="transcript"]').or_(
                    page.locator('[class*="Transcript"]')
                ).first

            if await transcript_container.count() > 0:
                # Wait for content to be visible
                try:
                    await transcript_container.wait_for(state="visible", timeout=5000)
                except:
                    pass

                transcript_text = await transcript_container.inner_text()
                logger.debug(f"Extracted transcript: {len(transcript_text)} characters")
                return transcript_text.strip()
            else:
                logger.warning("Transcript content container not found")
                return ""

        except Exception as e:
            logger.error(f"Failed to extract transcript: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ""

    async def extract_summary(self, page: Page) -> Optional[str]:
        """
        Extract AI summary from course page (if available)

        Steps:
        1. Check if tab with id="learning-agent" exists
        2. Click the tab
        3. Extract all text from elements with class containing "__messageText"
        4. Preserve line breaks and spacing

        Args:
            page: Playwright Page object (on course page)

        Returns:
            Summary text (None if not available)
        """
        try:
            # Wait for page to be fully loaded (in case called separately)
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
            logger.debug("Page loaded for summary extraction...")

            # Additional wait for dynamic content
            await asyncio.sleep(2)

            # Check if learning-agent tab exists
            summary_tab = page.locator('button[id="learning-agent"]').first

            if await summary_tab.count() == 0:
                logger.debug("Summary tab not available for this course")
                return None

            # Click summary tab
            await summary_tab.click()
            logger.debug("Clicked Summary tab, waiting for content...")

            # Wait for summary content to load
            await asyncio.sleep(2)

            # Extract summary messages
            message_elements = page.locator('[class*="__messageText"]')
            count = await message_elements.count()

            if count == 0:
                logger.warning("Summary tab exists but no messages found")
                return None

            # Collect all message texts
            messages = []
            for i in range(count):
                message_text = await message_elements.nth(i).inner_text()
                messages.append(message_text.strip())

            summary_text = "\n\n".join(messages)
            logger.debug(f"Extracted summary: {len(summary_text)} characters from {count} messages")
            return summary_text

        except Exception as e:
            logger.error(f"Failed to extract summary: {e}")
            return None

    def _get_output_dir(
        self,
        language: str,
        content_type: str,
        category_title: str,
        course_title: str
    ) -> Path:
        """
        Get output directory path for a course

        Args:
            language: Language code (en/ja)
            content_type: "categories" or "series"
            category_title: Category or series title
            course_title: Course title

        Returns:
            Path object for output directory
        """
        # Sanitize titles for filesystem
        safe_category = self._sanitize_filename(category_title)
        safe_course = self._sanitize_filename(course_title)

        return self.base_dir / language / content_type / safe_category / safe_course

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing/replacing invalid characters

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Replace invalid characters with underscore
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length (filesystem limits)
        max_length = 200
        if len(filename) > max_length:
            filename = filename[:max_length]

        return filename.strip()

    async def extract_and_save(
        self,
        page: Page,
        language: str,
        content_type: str,
        category_title: str,
        course_title: str
    ) -> Dict[str, bool]:
        """
        Extract all content and save to files

        Args:
            page: Playwright Page object (on course page)
            language: Language code (en/ja)
            content_type: "categories" or "series"
            category_title: Category or series title
            course_title: Course title

        Returns:
            Dictionary with extraction status for each content type
        """
        # Get output directory
        output_dir = self._get_output_dir(language, content_type, category_title, course_title)

        # Create directory if not exists
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Output directory: {output_dir}")

        results = {
            "overview": False,
            "transcript": False,
            "summary": False
        }

        # Extract and save overview
        overview_text = await self.extract_overview(page)
        if overview_text:
            overview_file = output_dir / "overview.txt"
            overview_file.write_text(overview_text, encoding="utf-8")
            logger.info(f"✅ Saved overview: {overview_file}")
            results["overview"] = True
        else:
            logger.warning("⚠️  No overview content extracted")

        # Extract and save transcript
        transcript_text = await self.extract_transcript(page)
        if transcript_text:
            transcript_file = output_dir / "transcript.txt"
            transcript_file.write_text(transcript_text, encoding="utf-8")
            logger.info(f"✅ Saved transcript: {transcript_file}")
            results["transcript"] = True
        else:
            logger.warning("⚠️  No transcript content extracted")

        # Extract and save summary (if available)
        summary_text = await self.extract_summary(page)
        if summary_text:
            summary_file = output_dir / "summary.txt"
            summary_file.write_text(summary_text, encoding="utf-8")
            logger.info(f"✅ Saved summary: {summary_file}")
            results["summary"] = True
        else:
            logger.debug("ℹ️  No summary available for this course")

        return results

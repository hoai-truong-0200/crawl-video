"""
Vimeo Network Interceptor

Monitors network requests to capture Vimeo progressive download URLs.
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from playwright.async_api import Page, Response
from loguru import logger


@dataclass
class VimeoDownloadURL:
    """Vimeo progressive download URL"""
    quality: str
    url: str
    width: int = 0
    height: int = 0


class VimeoInterceptor:
    """
    Intercepts network requests to capture Vimeo progressive download URLs

    Usage:
        interceptor = VimeoInterceptor(page)
        await interceptor.start()
        await page.goto("https://...")
        await asyncio.sleep(5)
        download_url = interceptor.get_best_quality_url()
        await interceptor.stop()
    """

    def __init__(self, page: Page):
        self.page = page
        self.progressive_urls: List[VimeoDownloadURL] = []
        self._is_listening = False

    async def start(self) -> None:
        """Start intercepting network requests"""
        if self._is_listening:
            return

        logger.debug("🎬 Starting Vimeo interception...")
        self.page.on("response", self._handle_response)
        self._is_listening = True

    async def stop(self) -> None:
        """Stop intercepting network requests"""
        if not self._is_listening:
            return

        try:
            self.page.remove_listener("response", self._handle_response)
        except:
            pass

        self._is_listening = False

    async def _handle_response(self, response: Response) -> None:
        """Handle network response"""
        try:
            url = response.url

            # Look for progressive_redirect URLs (these are downloadable)
            if "progressive_redirect" in url and "vimeo.com" in url:
                await self._extract_progressive_url(response)

        except Exception as e:
            logger.debug(f"Error handling response: {e}")

    async def _extract_progressive_url(self, response: Response) -> None:
        """Extract progressive download URL"""
        try:
            url = response.url

            # Parse quality (e.g., /rendition/720p/file.mp4)
            quality = "unknown"
            width, height = 0, 0

            if "/rendition/" in url:
                parts = url.split("/rendition/")
                if len(parts) > 1:
                    quality = parts[1].split("/")[0]  # e.g., "720p"

                    # Set dimensions
                    if "720p" in quality:
                        width, height = 1280, 720
                    elif "1080p" in quality:
                        width, height = 1920, 1080
                    elif "540p" in quality:
                        width, height = 960, 540
                    elif "360p" in quality:
                        width, height = 640, 360

            download_url = VimeoDownloadURL(
                quality=quality,
                url=url,
                width=width,
                height=height,
            )

            self.progressive_urls.append(download_url)
            logger.debug(f"✅ Captured: {quality} - {url[:80]}...")

        except Exception as e:
            logger.debug(f"Error extracting URL: {e}")

    def get_download_urls(self) -> Dict[str, str]:
        """
        Get all captured download URLs

        Returns:
            Dictionary: quality -> download URL
        """
        urls = {}
        for video_url in self.progressive_urls:
            if video_url.url:
                urls[video_url.quality] = video_url.url
        return urls

    def get_best_quality_url(self) -> Optional[str]:
        """Get the highest quality download URL"""
        urls = self.get_download_urls()

        if not urls:
            return None

        # Priority: 1080p > 720p > 540p > 360p
        for quality in ['1080p', '720p', '540p', '360p']:
            if quality in urls:
                return urls[quality]

        # Return any available
        return next(iter(urls.values())) if urls else None

    def clear(self) -> None:
        """Clear all captured URLs"""
        self.progressive_urls.clear()

    def has_urls(self) -> bool:
        """Check if any URLs were captured"""
        return len(self.progressive_urls) > 0

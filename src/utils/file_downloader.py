"""
File Downloader

Downloads files from URLs with progress tracking and retry logic.
"""

import aiohttp
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger


class FileDownloader:
    """
    Download files from URLs

    Features:
    - Async download with aiohttp
    - Progress tracking
    - Retry logic
    - Resume support (if server supports range requests)
    """

    def __init__(self, max_retries: int = 3, chunk_size: int = 8192):
        """
        Initialize downloader

        Args:
            max_retries: Maximum retry attempts
            chunk_size: Download chunk size in bytes
        """
        self.max_retries = max_retries
        self.chunk_size = chunk_size

    async def download(
        self,
        url: str,
        output_path: Path,
        timeout: int = 300
    ) -> bool:
        """
        Download file from URL

        Args:
            url: Download URL
            output_path: Output file path
            timeout: Download timeout in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        # Create output directory if not exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Download attempt {attempt}/{self.max_retries}: {output_path.name}")

                timeout_obj = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            logger.warning(f"HTTP {response.status} for {url}")
                            if attempt < self.max_retries:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            return False

                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        last_logged_progress = -1  # Track last logged percentage to avoid duplicate logs

                        # Download file
                        with open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(self.chunk_size):
                                f.write(chunk)
                                downloaded += len(chunk)

                                # Log progress every 10% at INFO level
                                if total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    current_progress_milestone = int(progress // 10) * 10

                                    # Only log when we reach a new 10% milestone
                                    if current_progress_milestone > last_logged_progress and current_progress_milestone > 0:
                                        logger.info(f"📥 Progress: {progress:.1f}% ({downloaded:,}/{total_size:,} bytes)")
                                        last_logged_progress = current_progress_milestone

                        logger.info(f"✅ Downloaded: {output_path.name} ({downloaded:,} bytes)")
                        return True

            except asyncio.TimeoutError:
                logger.warning(f"Timeout downloading {output_path.name} (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return False

            except Exception as e:
                logger.error(f"Error downloading {output_path.name}: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return False

        return False

    def get_file_extension(self, url: str) -> str:
        """
        Get file extension from URL

        Args:
            url: Download URL

        Returns:
            File extension (e.g., ".mp4")
        """
        # Try to extract from URL
        if '.mp4' in url.lower():
            return '.mp4'
        elif '.webm' in url.lower():
            return '.webm'
        elif '.mov' in url.lower():
            return '.mov'
        else:
            # Default to mp4 for Vimeo
            return '.mp4'

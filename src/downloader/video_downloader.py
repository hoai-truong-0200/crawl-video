"""
Video Downloader

Downloads videos using yt-dlp with browser cookies.
"""

import asyncio
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
import aiohttp


class VideoDownloader:
    """
    Downloads videos using yt-dlp

    Folder structure:
    - learn-content: data/downloads/learn-content/Category Name/Course Name/video_title.mp4
    - explore-content: data/downloads/explore-content/Series Name/Course Name/video_title.mp4
    """

    def __init__(
        self,
        download_dir: Path = Path("data/downloads"),
        content_type: str = "learn-content",
        cookies_from_browser: str = "chrome",
    ):
        """
        Initialize video downloader

        Args:
            download_dir: Base download directory (data/downloads)
            content_type: Type of content (learn-content or explore-content)
            cookies_from_browser: Browser to extract cookies from (chrome, firefox, etc.)
        """
        self.base_download_dir = download_dir
        self.content_type = content_type
        self.download_dir = download_dir / content_type
        self.cookies_from_browser = cookies_from_browser

        # Create download directory
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)

        # Trim whitespace
        filename = filename.strip()

        # Limit length to 200 characters
        if len(filename) > 200:
            filename = filename[:200]

        return filename

    def get_video_path(
        self,
        category_or_series: str,
        course_name: str,
        video_title: str,
    ) -> Path:
        """
        Get the full path for a video file

        Args:
            category_or_series: Category name (for learn-content) or Series name (for explore-content)
            course_name: Course name
            video_title: Video title

        Returns:
            Full path to video file
        """
        # Sanitize all parts
        category_or_series = self.sanitize_filename(category_or_series)
        course_name = self.sanitize_filename(course_name)
        video_title = self.sanitize_filename(video_title)

        # Build path: downloads/Category/Course/video.mp4
        video_dir = self.download_dir / category_or_series / course_name
        video_path = video_dir / f"{video_title}.mp4"

        return video_path

    async def download_video(
        self,
        vimeo_url: str,
        step_url: str,
        category_or_series: str,
        course_name: str,
        video_title: str,
        max_retries: int = 3,
    ) -> bool:
        """
        Download a video using yt-dlp

        Args:
            vimeo_url: Vimeo player URL (e.g., https://player.vimeo.com/video/123456)
            step_url: GLOBIS step page URL (used as referer)
            category_or_series: Category name or Series name
            course_name: Course name
            video_title: Video title
            max_retries: Maximum retry attempts

        Returns:
            True if download successful, False otherwise
        """
        video_path = self.get_video_path(category_or_series, course_name, video_title)

        # Check if already downloaded
        if video_path.exists():
            file_size = video_path.stat().st_size
            if file_size > 0:
                logger.info(f"      ✅ Already downloaded: {video_path.name} ({file_size / 1024 / 1024:.1f} MB)")
                return True

        # Create directory
        video_path.parent.mkdir(parents=True, exist_ok=True)

        # Build referer URL
        referer_url = f"https://unlimited.globis.co.jp{step_url}"

        # Download with retries
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"      📥 Downloading: {video_title}")
                logger.debug(f"         Attempt {attempt}/{max_retries}")
                logger.debug(f"         Vimeo URL: {vimeo_url}")
                logger.debug(f"         Referer: {referer_url}")

                # Temp output path
                temp_path = video_path.with_suffix('.mp4.part')

                # Build yt-dlp command
                cmd = [
                    'yt-dlp',
                    '--cookies-from-browser', self.cookies_from_browser,
                    '--referer', referer_url,
                    '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    '--merge-output-format', 'mp4',
                    '--output', str(temp_path),
                    '--no-playlist',
                    '--quiet',
                    '--progress',
                    vimeo_url,
                ]

                # Run yt-dlp
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    # Check if file was downloaded
                    if temp_path.exists() and temp_path.stat().st_size > 0:
                        # Rename to final path
                        temp_path.rename(video_path)

                        file_size = video_path.stat().st_size
                        logger.info(f"      ✅ Downloaded: {video_path.name} ({file_size / 1024 / 1024:.1f} MB)")
                        return True
                    else:
                        logger.error(f"      ❌ Download failed: file not created")

                        if attempt < max_retries:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        return False
                else:
                    error_msg = stderr.decode().strip() if stderr else "Unknown error"
                    logger.error(f"      ❌ yt-dlp error: {error_msg[:100]}")

                    if attempt < max_retries:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return False

            except Exception as e:
                logger.error(f"      ❌ Download error (attempt {attempt}): {e}")

                # Clean up temp file
                temp_path = video_path.with_suffix('.mp4.part')
                if temp_path.exists():
                    temp_path.unlink()

                if attempt < max_retries:
                    retry_delay = 2 ** attempt
                    logger.info(f"      ⏳ Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"      ❌ Failed after {max_retries} attempts")
                    return False

        return False

    async def download_from_extracted_url(
        self,
        download_url: str,
        category_or_series: str,
        course_name: str,
        video_title: str,
        max_retries: int = 3,
    ) -> bool:
        """
        Download video from extracted URL (progressive, HLS, or DASH)

        This method works with URLs extracted from window.playerConfig.
        It automatically detects the URL type and uses the appropriate download method.

        Args:
            download_url: Direct download URL (progressive MP4, HLS m3u8, or DASH mpd)
            category_or_series: Category name or Series name
            course_name: Course name
            video_title: Video title
            max_retries: Maximum retry attempts

        Returns:
            True if download successful, False otherwise
        """
        video_path = self.get_video_path(category_or_series, course_name, video_title)

        # Check if already downloaded
        if video_path.exists():
            file_size = video_path.stat().st_size
            if file_size > 0:
                logger.info(f"      ✅ Already downloaded: {video_path.name} ({file_size / 1024 / 1024:.1f} MB)")
                return True

        # Create directory
        video_path.parent.mkdir(parents=True, exist_ok=True)

        # Detect URL type
        is_progressive = 'progressive' in download_url or '.mp4' in download_url
        is_hls = '.m3u8' in download_url or 'playlist' in download_url
        is_dash = '.mpd' in download_url or 'playlist.json' in download_url

        # Download based on type
        for attempt in range(1, max_retries + 1):
            try:
                if is_progressive:
                    # Download progressive MP4 directly with aiohttp
                    logger.info(f"      📥 Downloading (progressive): {video_title}")
                    logger.debug(f"         Attempt {attempt}/{max_retries}")

                    temp_path = video_path.with_suffix('.mp4.part')

                    async with aiohttp.ClientSession() as session:
                        async with session.get(download_url) as resp:
                            if resp.status == 200:
                                total_size = int(resp.headers.get('content-length', 0))

                                with open(temp_path, 'wb') as f:
                                    downloaded = 0
                                    async for chunk in resp.content.iter_chunked(1024 * 1024):
                                        f.write(chunk)
                                        downloaded += len(chunk)

                                # Rename to final path
                                if temp_path.exists() and temp_path.stat().st_size > 0:
                                    temp_path.rename(video_path)
                                    file_size = video_path.stat().st_size
                                    logger.info(f"      ✅ Downloaded: {video_path.name} ({file_size / 1024 / 1024:.1f} MB)")
                                    return True
                                else:
                                    logger.error(f"      ❌ Download failed: file not created")
                                    if attempt < max_retries:
                                        await asyncio.sleep(2 ** attempt)
                                        continue
                                    return False
                            else:
                                logger.error(f"      ❌ HTTP {resp.status}")
                                if attempt < max_retries:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                                return False

                elif is_hls or is_dash:
                    # Download HLS/DASH with yt-dlp
                    logger.info(f"      📥 Downloading (HLS/DASH): {video_title}")
                    logger.debug(f"         Attempt {attempt}/{max_retries}")

                    temp_path = video_path.with_suffix('.mp4.part')

                    cmd = [
                        'yt-dlp',
                        download_url,
                        '-o', str(temp_path),
                        '--no-playlist',
                        '--quiet',
                        '--progress',
                    ]

                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    stdout, stderr = await process.communicate()

                    if process.returncode == 0 and temp_path.exists():
                        # Rename to final path
                        temp_path.rename(video_path)
                        file_size = video_path.stat().st_size
                        logger.info(f"      ✅ Downloaded: {video_path.name} ({file_size / 1024 / 1024:.1f} MB)")
                        return True
                    else:
                        error_msg = stderr.decode().strip() if stderr else "Unknown error"
                        logger.error(f"      ❌ yt-dlp error: {error_msg[:100]}")
                        if attempt < max_retries:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        return False

                else:
                    logger.error(f"      ❌ Unknown URL type: {download_url[:100]}")
                    return False

            except Exception as e:
                logger.error(f"      ❌ Download error (attempt {attempt}): {e}")

                # Clean up temp file
                temp_path = video_path.with_suffix('.mp4.part')
                if temp_path.exists():
                    temp_path.unlink()

                if attempt < max_retries:
                    retry_delay = 2 ** attempt
                    logger.info(f"      ⏳ Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"      ❌ Failed after {max_retries} attempts")
                    return False

        return False

    def is_video_downloaded(
        self,
        category_or_series: str,
        course_name: str,
        video_title: str,
    ) -> bool:
        """
        Check if video is already downloaded

        Args:
            category_or_series: Category name or Series name
            course_name: Course name
            video_title: Video title

        Returns:
            True if video exists and has size > 0
        """
        video_path = self.get_video_path(category_or_series, course_name, video_title)

        if not video_path.exists():
            return False

        return video_path.stat().st_size > 0

    def get_download_stats(self) -> dict:
        """
        Get download statistics

        Returns:
            Dictionary with download stats
        """
        stats = {
            'total_videos': 0,
            'total_size_mb': 0,
            'categories_or_series': 0,
            'courses': 0,
        }

        if not self.download_dir.exists():
            return stats

        # Count categories/series
        categories = [d for d in self.download_dir.iterdir() if d.is_dir()]
        stats['categories_or_series'] = len(categories)

        # Count courses and videos
        courses_set = set()
        for category_dir in categories:
            for course_dir in category_dir.iterdir():
                if course_dir.is_dir():
                    courses_set.add(str(course_dir))

                    # Count videos
                    for video_file in course_dir.glob('*.mp4'):
                        if not video_file.name.endswith('.part'):  # Skip partial downloads
                            stats['total_videos'] += 1
                            stats['total_size_mb'] += video_file.stat().st_size / 1024 / 1024

        stats['courses'] = len(courses_set)

        return stats

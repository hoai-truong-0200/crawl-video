"""
Vimeo URL Extractor

Extracts video download URLs from Vimeo iframe's window.playerConfig object in DOM.
"""

import asyncio
from typing import Optional, Dict, List
from loguru import logger
from playwright.async_api import Page


class VimeoExtractor:
    """
    Extracts video download URLs from Vimeo player iframe in DOM

    This class accesses the Vimeo iframe and extracts window.playerConfig object
    which contains all available video formats (progressive, HLS, DASH).
    """

    @staticmethod
    async def extract_video_urls(page: Page, timeout: int = 10000) -> Optional[Dict]:
        """
        Extract video download URLs from Vimeo iframe in current page

        Args:
            page: Playwright page object (must contain Vimeo iframe)
            timeout: Timeout in milliseconds for finding iframe

        Returns:
            Dictionary with video URLs:
            {
                'video_id': str,
                'vimeo_player_url': str,
                'progressive': [{'quality': str, 'url': str, 'width': int, 'height': int}],
                'hls': {'cdn': str, 'url': str} or None,
                'dash': {'cdn': str, 'url': str} or None,
                'best_download_url': str (best quality URL to download)
            }
            Returns None if extraction fails
        """
        try:
            # Find Vimeo iframe
            logger.debug("   🔍 Finding Vimeo iframe...")
            iframe_element = await page.wait_for_selector(
                'iframe[src*="vimeo"]',
                timeout=timeout
            )

            if not iframe_element:
                logger.error("   ❌ No Vimeo iframe found")
                return None

            # Get iframe URL
            vimeo_player_url = await iframe_element.get_attribute('src')
            logger.debug(f"   ✅ Vimeo iframe: {vimeo_player_url}")

            # Extract video ID
            video_id = None
            if vimeo_player_url and "/video/" in vimeo_player_url:
                video_id = vimeo_player_url.split("/video/")[1].split("?")[0]
                logger.debug(f"   📹 Video ID: {video_id}")

            # Access iframe content
            iframe_content = await iframe_element.content_frame()

            if not iframe_content:
                logger.error("   ❌ Could not access iframe content")
                return None

            # Wait for iframe to load
            await asyncio.sleep(2)

            # Extract playerConfig from iframe DOM
            logger.debug("   🔍 Extracting window.playerConfig from iframe...")
            player_config = await iframe_content.evaluate("""
                () => {
                    return window.playerConfig || null;
                }
            """)

            if not player_config:
                logger.error("   ❌ playerConfig not found in iframe")
                return None

            logger.debug("   ✅ playerConfig extracted successfully")

            # Parse video URLs
            files = player_config.get('request', {}).get('files', {})
            progressive_files = files.get('progressive', [])
            hls_data = files.get('hls', {})
            dash_data = files.get('dash', {})

            # Prepare result
            result = {
                'video_id': video_id,
                'vimeo_player_url': vimeo_player_url,
                'progressive': [],
                'hls': None,
                'dash': None,
                'best_download_url': None
            }

            # Process progressive URLs (sorted by quality)
            if progressive_files:
                sorted_videos = sorted(
                    progressive_files,
                    key=lambda x: x.get('height', 0),
                    reverse=True
                )

                for video in sorted_videos:
                    result['progressive'].append({
                        'quality': video.get('quality', 'unknown'),
                        'url': video.get('url', ''),
                        'width': video.get('width', 0),
                        'height': video.get('height', 0),
                    })

                # Best quality = first after sorting
                result['best_download_url'] = sorted_videos[0].get('url', '')

                logger.debug(f"   ✅ Found {len(sorted_videos)} progressive URLs")
                logger.debug(f"   📹 Best quality: {sorted_videos[0].get('quality')} "
                           f"({sorted_videos[0].get('width')}x{sorted_videos[0].get('height')})")

            # Process HLS URL
            if hls_data:
                default_cdn = hls_data.get('default_cdn', '')
                hls_url = hls_data.get('cdns', {}).get(default_cdn, {}).get('url', '')

                if hls_url:
                    result['hls'] = {
                        'cdn': default_cdn,
                        'url': hls_url
                    }

                    # Use HLS as fallback if no progressive
                    if not result['best_download_url']:
                        result['best_download_url'] = hls_url

                    logger.debug(f"   ✅ HLS URL found (CDN: {default_cdn})")

            # Process DASH URL
            if dash_data:
                default_cdn = dash_data.get('default_cdn', '')
                dash_url = dash_data.get('cdns', {}).get(default_cdn, {}).get('url', '')

                if dash_url:
                    result['dash'] = {
                        'cdn': default_cdn,
                        'url': dash_url
                    }

                    logger.debug(f"   ✅ DASH URL found (CDN: {default_cdn})")

            if result['best_download_url']:
                logger.debug(f"   ✅ Best download URL selected")
                return result
            else:
                logger.warning("   ⚠️  No download URL available")
                return None

        except Exception as e:
            logger.error(f"   ❌ Error extracting video URLs: {e}")
            return None

    @staticmethod
    def is_progressive_url(url: str) -> bool:
        """Check if URL is progressive (direct MP4 download)"""
        return 'progressive' in url or '.mp4' in url

    @staticmethod
    def is_hls_url(url: str) -> bool:
        """Check if URL is HLS (adaptive streaming)"""
        return '.m3u8' in url or 'playlist' in url

    @staticmethod
    def is_dash_url(url: str) -> bool:
        """Check if URL is DASH (adaptive streaming)"""
        return '.mpd' in url or 'playlist.json' in url

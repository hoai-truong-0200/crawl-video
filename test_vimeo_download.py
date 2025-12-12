"""
Test script to extract Vimeo download URL from a single video step
Uses Chrome profile like run_browser.py for authentication
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from loguru import logger
from src.browser.stealth_config import get_browser_launch_args, apply_stealth_to_page

# Configure logger
logger.add("logs/test_vimeo.log", rotation="10 MB")

# Chrome profile path (same as run_browser.py)
DEST_PROFILE = Path("data/chrome_profile_copy")

async def test_vimeo_extraction():
    """Test extracting Vimeo download URL from a single video"""

    # Test URL - replace with actual video step URL
    test_url = "https://unlimited.globis.co.jp/en/courses/863ef044/learn/steps/61826"

    playwright = await async_playwright().start()

    # Get stealth args
    base_args = get_browser_launch_args()
    additional_args = ['--exclude-switches=enable-automation']
    all_args = list(set(base_args + additional_args))

    logger.info("🚀 Launching Chrome with profile...")
    logger.info(f"📁 Profile: {DEST_PROFILE}")

    # Launch persistent context with Chrome profile
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=str(DEST_PROFILE.absolute()),
        channel='chrome',
        args=all_args,
        ignore_default_args=['--enable-automation'],
        headless=False,
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='America/New_York'
    )

    page = context.pages[0] if context.pages else await context.new_page()

    # Apply stealth
    await apply_stealth_to_page(page)

    logger.info(f"🔗 Navigating to: {test_url}")
    await page.goto(test_url, wait_until="domcontentloaded", timeout=30000)

    # Wait for page to load
    logger.info("⏳ Waiting for page to load...")
    await asyncio.sleep(3)

    # Method 1: Try to find iframe src directly
    logger.info("\n" + "="*60)
    logger.info("METHOD 1: Extract iframe src")
    logger.info("="*60)
    try:
        iframe_src = await page.evaluate('''
            () => {
                const iframe = document.querySelector('iframe[src*="player.vimeo.com"]');
                return iframe ? iframe.src : null;
            }
        ''')
        logger.info(f"✅ Iframe src: {iframe_src}")
    except Exception as e:
        logger.error(f"❌ Error getting iframe src: {e}")

    # Method 2: Wait for iframe to load and navigate to it directly
    logger.info("\n" + "="*60)
    logger.info("METHOD 2: Navigate to iframe directly")
    logger.info("="*60)
    try:
        await page.wait_for_selector('iframe[src*="player.vimeo.com"]', timeout=10000)
        iframe_element = await page.query_selector('iframe[src*="player.vimeo.com"]')
        iframe_url = await iframe_element.get_attribute('src')

        logger.info(f"🎬 Opening iframe URL directly: {iframe_url}")

        # Open iframe in new page
        iframe_page = await context.new_page()
        await iframe_page.goto(iframe_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Extract playerConfig from iframe page
        player_config = await iframe_page.evaluate('''
            () => {
                if (!window.playerConfig) {
                    return null;
                }

                const files = window.playerConfig.request?.files;
                if (!files) {
                    return null;
                }

                return {
                    hasProgressive: !!files.progressive,
                    hasDash: !!files.dash,
                    hasHls: !!files.hls,
                    progressive: files.progressive || [],
                    dashCdns: files.dash ? Object.keys(files.dash.cdns || {}) : [],
                    hlsCdns: files.hls ? Object.keys(files.hls.cdns || {}) : []
                };
            }
        ''')

        logger.info(f"📊 PlayerConfig info: {player_config}")

        # Try to get download URLs
        if player_config and player_config['hasProgressive']:
            progressive_urls = await iframe_page.evaluate('''
                () => {
                    const files = window.playerConfig.request.files;
                    if (!files.progressive) return [];

                    return files.progressive.map(p => ({
                        quality: p.quality,
                        width: p.width,
                        height: p.height,
                        url: p.url
                    }));
                }
            ''')

            logger.info(f"\n✅ Found {len(progressive_urls)} progressive URLs:")
            for url_info in progressive_urls:
                logger.info(f"  - {url_info['quality']} ({url_info['width']}x{url_info['height']})")
                logger.info(f"    URL: {url_info['url'][:100]}...")

            # Get best quality
            if progressive_urls:
                best = max(progressive_urls, key=lambda x: x['height'])
                logger.info(f"\n🏆 Best quality: {best['quality']} - {best['url'][:100]}...")

        # Try DASH/HLS if no progressive
        if player_config and (player_config['hasDash'] or player_config['hasHls']):
            logger.info("⚠️  No progressive URLs, trying DASH/HLS...")

            dash_url = await iframe_page.evaluate('''
                () => {
                    const files = window.playerConfig.request.files;
                    if (files.dash && files.dash.cdns) {
                        const cdnKey = files.dash.default_cdn || Object.keys(files.dash.cdns)[0];
                        const cdn = files.dash.cdns[cdnKey];
                        return cdn.url || cdn.avc_url;
                    }
                    return null;
                }
            ''')

            if dash_url:
                logger.info(f"✅ DASH URL: {dash_url[:100]}...")

        await iframe_page.close()

    except Exception as e:
        logger.error(f"❌ Error in Method 2: {e}")

    # Method 3: Enhanced network interception - Track all video-related requests
    logger.info("\n" + "="*60)
    logger.info("METHOD 3: Enhanced Network Tracking")
    logger.info("="*60)

    captured_urls = {
        'progressive': [],  # Direct MP4 downloads
        'm3u8': [],         # HLS playlists
        'mpd': [],          # DASH manifests
        'json': [],         # Playlist JSONs
        'other': []         # Other video-related URLs
    }

    def handle_response(response):
        url = response.url

        # Track video-related domains
        video_domains = ['vimeocdn.com', 'vimeo.com', 'player.vimeo.com']

        if any(domain in url for domain in video_domains):
            # Categorize by file type
            if '.m3u8' in url or 'playlist.m3u8' in url:
                logger.info(f"📺 HLS M3U8: {url}")
                captured_urls['m3u8'].append({
                    'url': url,
                    'type': 'hls',
                    'status': response.status
                })
            elif '.mpd' in url or 'manifest.mpd' in url:
                logger.info(f"📺 DASH MPD: {url}")
                captured_urls['mpd'].append({
                    'url': url,
                    'type': 'dash',
                    'status': response.status
                })
            elif '.mp4' in url or 'progressive' in url:
                logger.info(f"🎬 Progressive MP4: {url}")
                captured_urls['progressive'].append({
                    'url': url,
                    'type': 'progressive',
                    'status': response.status
                })
            elif '.json' in url and ('playlist' in url or 'config' in url):
                logger.info(f"📋 Playlist JSON: {url}")
                captured_urls['json'].append({
                    'url': url,
                    'type': 'json',
                    'status': response.status
                })
            elif response.request.resource_type == 'media':
                logger.info(f"🎞️  Media: {url}")
                captured_urls['other'].append({
                    'url': url,
                    'type': 'media',
                    'status': response.status
                })

    page.on("response", handle_response)

    # Reload page to capture network requests
    logger.info("🔄 Reloading page to capture network traffic...")
    await page.reload()

    # Wait longer for all network requests
    logger.info("⏳ Waiting for network requests (10 seconds)...")
    await asyncio.sleep(10)

    # Summary
    logger.info("\n" + "="*60)
    logger.info("NETWORK TRACKING SUMMARY")
    logger.info("="*60)

    total_captured = sum(len(urls) for urls in captured_urls.values())
    logger.info(f"Total URLs captured: {total_captured}")

    for category, urls in captured_urls.items():
        if urls:
            logger.info(f"\n📊 {category.upper()} URLs ({len(urls)}):")
            for i, item in enumerate(urls[:3], 1):  # Show first 3 of each type
                logger.info(f"  {i}. [{item['status']}] {item['url'][:100]}...")
            if len(urls) > 3:
                logger.info(f"  ... and {len(urls) - 3} more")

    if total_captured == 0:
        logger.warning("⚠️  No video URLs captured!")

    # Keep browser open for inspection
    logger.info("\n" + "="*60)
    logger.info("Browser will stay open. Press Ctrl+C to close.")
    logger.info("="*60)

    try:
        await asyncio.sleep(300)  # Wait 5 minutes
    except KeyboardInterrupt:
        logger.info("Closing browser...")

    await context.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_vimeo_extraction())

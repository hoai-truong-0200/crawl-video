"""
Analyze Single Video - Network & DOM Inspection

Opens a video page and captures:
1. DOM structure (Vimeo iframe)
2. Network requests (progressive download URLs)
3. Direct video download links
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Response
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    colorize=True,
)


async def analyze_video(video_url: str):
    """Analyze a single video page with network monitoring"""

    logger.info("=" * 70)
    logger.info("🔍 VIDEO ANALYSIS - DOM & NETWORK")
    logger.info("=" * 70)
    logger.info(f"\n📹 Video URL: {video_url}")

    # Storage for captured URLs
    vimeo_player_url = None
    progressive_urls = []
    cdn_urls = []

    async def handle_response(response: Response):
        """Capture network responses"""
        url = response.url

        # Capture Vimeo progressive redirect URLs
        if "progressive_redirect" in url and "vimeo.com" in url:
            logger.info(f"\n🎯 PROGRESSIVE URL FOUND:")
            logger.info(f"   {url}")

            # Extract quality
            quality = "unknown"
            if "/rendition/" in url:
                parts = url.split("/rendition/")
                if len(parts) > 1:
                    quality = parts[1].split("/")[0]

            progressive_urls.append({
                'quality': quality,
                'url': url,
                'status': response.status
            })

        # Capture CDN URLs
        elif "vimeocdn.com" in url and "/playback/" in url:
            logger.info(f"\n📦 CDN URL FOUND:")
            logger.info(f"   {url[:100]}...")

            cdn_urls.append({
                'url': url,
                'status': response.status
            })

    # Get Chrome profile
    chrome_profile_path = Path.home() / ".config/google-chrome/Default"

    if not chrome_profile_path.exists():
        logger.error(f"❌ Chrome profile not found")
        return

    async with async_playwright() as p:
        logger.info(f"\n🚀 Launching browser...")

        browser = await p.chromium.launch_persistent_context(
            str(chrome_profile_path),
            headless=False,
            channel="chrome",
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Start network monitoring
        logger.info("🔍 Starting network monitoring...")
        page.on("response", handle_response)

        # Navigate to video
        logger.info(f"\n🌐 Navigating to video...")
        full_url = f"https://unlimited.globis.co.jp{video_url}" if not video_url.startswith("http") else video_url

        await page.goto(full_url, wait_until="domcontentloaded", timeout=60000)
        logger.info("✅ Page loaded")

        # Wait for video player
        await asyncio.sleep(2)

        # Extract Vimeo player URL from DOM
        logger.info("\n🔍 Analyzing DOM...")
        iframe = await page.query_selector('iframe[src*="vimeo"]')
        if iframe:
            vimeo_player_url = await iframe.get_attribute('src')
            logger.info(f"✅ Vimeo player iframe found:")
            logger.info(f"   {vimeo_player_url}")
        else:
            logger.warning("⚠️  No Vimeo iframe found in DOM")

        # Try to click play button to trigger video load
        logger.info("\n▶️  Attempting to trigger video load...")
        try:
            iframe_element = await page.wait_for_selector('iframe[src*="vimeo"]', timeout=5000)
            if iframe_element:
                iframe_content = await iframe_element.content_frame()
                if iframe_content:
                    try:
                        # Try to find and click play button
                        play_button = await iframe_content.wait_for_selector(
                            'button[aria-label="Play"], .vp-center, .vp-preview',
                            timeout=3000
                        )
                        if play_button:
                            await play_button.click()
                            logger.info("   ✅ Clicked play button")
                    except:
                        logger.info("   ℹ️  No play button found (video may auto-load)")
        except Exception as e:
            logger.debug(f"   Could not interact with iframe: {e}")

        # Wait for network requests to complete
        logger.info("\n⏳ Waiting for network requests (10 seconds)...")
        await asyncio.sleep(10)

        # Print results
        logger.info(f"\n{'=' * 70}")
        logger.info("📊 ANALYSIS RESULTS")
        logger.info(f"{'=' * 70}")

        logger.info(f"\n📺 DOM Analysis:")
        logger.info(f"   Vimeo Player URL: {'✅ Found' if vimeo_player_url else '❌ Not found'}")
        if vimeo_player_url:
            logger.info(f"   {vimeo_player_url}")

        logger.info(f"\n🌐 Network Analysis:")
        logger.info(f"   Progressive URLs captured: {len(progressive_urls)}")
        logger.info(f"   CDN URLs captured: {len(cdn_urls)}")

        if progressive_urls:
            logger.info(f"\n🎯 PROGRESSIVE DOWNLOAD URLs:")
            for idx, item in enumerate(progressive_urls, 1):
                logger.info(f"\n   [{idx}] Quality: {item['quality']}")
                logger.info(f"       Status: {item['status']}")
                logger.info(f"       URL: {item['url']}")

        if cdn_urls:
            logger.info(f"\n📦 CDN DOWNLOAD URLs:")
            for idx, item in enumerate(cdn_urls[:3], 1):  # Show first 3
                logger.info(f"\n   [{idx}] Status: {item['status']}")
                logger.info(f"       URL: {item['url'][:120]}...")
            if len(cdn_urls) > 3:
                logger.info(f"\n   ... and {len(cdn_urls) - 3} more CDN URLs")

        # Summary
        logger.info(f"\n{'=' * 70}")
        logger.info("📋 SUMMARY")
        logger.info(f"{'=' * 70}")

        if vimeo_player_url:
            logger.info(f"✅ Vimeo player URL extracted from DOM")

        if progressive_urls:
            logger.info(f"✅ {len(progressive_urls)} progressive download URLs captured")
            logger.info(f"   Qualities: {', '.join(set(u['quality'] for u in progressive_urls))}")
        else:
            logger.warning(f"⚠️  No progressive URLs captured from network")
            logger.info(f"   💡 Try: Video may need manual play or different trigger")

        if cdn_urls:
            logger.info(f"✅ {len(cdn_urls)} CDN URLs captured")

        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        if not progressive_urls and not cdn_urls:
            logger.info(f"   1. Video may require actual playback to generate download URLs")
            logger.info(f"   2. Use yt-dlp with Vimeo player URL instead")
            logger.info(f"   3. yt-dlp command:")
            if vimeo_player_url:
                logger.info(f"      yt-dlp --cookies-from-browser chrome \\")
                logger.info(f"             --referer '{full_url}' \\")
                logger.info(f"             '{vimeo_player_url}'")
        else:
            logger.info(f"   ✅ Can download directly using captured URLs")

        logger.info(f"\n{'=' * 70}")

        # Keep browser open
        logger.info("\n⏸️  Browser staying open for 120 seconds...")
        logger.info("💡 You can manually play the video to see more network requests")
        logger.info("💡 Open DevTools (F12) > Network tab to see all requests")
        await asyncio.sleep(120)

        await browser.close()


async def main():
    """Main function"""

    # Test video URL - change this to any video you want to analyze
    test_video_url = "/en/courses/d8501fa9/learn/steps/60784"

    logger.info("\n💡 Analyzing video: " + test_video_url)
    logger.info("💡 Edit test_video_url in analyze_video.py to change video\n")

    await analyze_video(test_video_url)


if __name__ == "__main__":
    asyncio.run(main())

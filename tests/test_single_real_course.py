"""
Test Single Real Course

Test crawling a real course from GLOBIS Unlimited to verify:
- Overview extraction works
- Transcript extraction works
- Duration calculation works
- LearnPoint structure extraction works
- Text files are created correctly
- JSON stores paths (not content)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler.course_parser import CourseParser
from src.crawler.content_manager import Course, Category, Video, LearnPoint, ContentManager
from src.browser.browser_manager import BrowserManager

# Configure logger
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    colorize=True,
)


async def test_real_course_crawl():
    """
    Test crawling a real course from GLOBIS Unlimited

    This test will:
    1. Navigate to a real course page
    2. Extract overview, transcript, duration
    3. Save overview.txt and transcript.txt
    4. Extract LearnPoint structure
    5. Verify files were created
    6. Save results to JSON
    """
    logger.info("\n" + "="*70)
    logger.info("🧪 SINGLE REAL COURSE TEST")
    logger.info("="*70)

    # Test configuration
    # TODO: Replace with actual course URL after login
    # Example: "/en/courses/abc123/learn/steps"
    TEST_COURSE_URL = None  # Will be set after browsing
    TEST_LANGUAGE = "en"
    TEST_CATEGORY = "Test Category"
    TEST_COURSE_TITLE = "Test Course"

    browser_manager = None

    try:
        # Step 1: Start browser
        logger.info("\n📱 Starting browser...")
        browser_manager = BrowserManager()
        page = await browser_manager.start()

        # Step 2: Login (required for GLOBIS Unlimited)
        logger.info("\n🔐 Please login to GLOBIS Unlimited manually...")
        logger.info("After login, navigate to a course page and press Enter")
        logger.info("Example course page: https://unlimited.globis.co.jp/en/courses/.../learn/steps")

        # Navigate to login page
        await page.goto("https://unlimited.globis.co.jp/en/login")

        # Wait for user to login and navigate to course
        input("\nPress ENTER after you've logged in and navigated to a course page...")

        # Get current URL
        current_url = page.url
        logger.info(f"\n📍 Current URL: {current_url}")

        # Parse URL to get course info
        if "/courses/" in current_url:
            # Extract course URL path
            from urllib.parse import urlparse
            parsed = urlparse(current_url)
            TEST_COURSE_URL = parsed.path

            # Try to extract course ID from URL
            parts = TEST_COURSE_URL.split('/')
            if len(parts) >= 4:
                course_id = parts[3]
                TEST_COURSE_TITLE = f"Course_{course_id}"

            logger.info(f"✅ Detected course URL: {TEST_COURSE_URL}")
        else:
            logger.error("❌ Not a valid course page URL")
            return False

        # Step 3: Extract course details
        logger.info("\n📝 Extracting course details...")
        parser = CourseParser()

        # Extract overview
        logger.info("\n🔍 Extracting overview...")
        overview_text = await parser.extract_overview(page)
        if overview_text:
            logger.info(f"✅ Overview extracted: {len(overview_text)} characters")
            logger.info(f"   Preview: {overview_text[:100]}...")

            # Save to file
            overview_path = parser.save_overview_to_file(
                overview=overview_text,
                language=TEST_LANGUAGE,
                category_or_series=TEST_CATEGORY,
                course_title=TEST_COURSE_TITLE,
                base_dir=Path("tests/test_real_data")
            )

            if overview_path:
                logger.info(f"✅ Overview saved to: {overview_path}")
            else:
                logger.error("❌ Failed to save overview")
        else:
            logger.warning("⚠️  No overview found")

        # Extract transcript
        logger.info("\n🔍 Extracting transcript...")
        transcript_text = await parser.extract_transcript(page)
        if transcript_text:
            logger.info(f"✅ Transcript extracted: {len(transcript_text)} characters")
            logger.info(f"   Preview: {transcript_text[:100]}...")

            # Save to file
            transcript_path = parser.save_transcript_to_file(
                transcript=transcript_text,
                language=TEST_LANGUAGE,
                category_or_series=TEST_CATEGORY,
                course_title=TEST_COURSE_TITLE,
                base_dir=Path("tests/test_real_data")
            )

            if transcript_path:
                logger.info(f"✅ Transcript saved to: {transcript_path}")
            else:
                logger.error("❌ Failed to save transcript")
        else:
            logger.warning("⚠️  No transcript found")

        # Extract duration
        logger.info("\n🔍 Extracting duration...")
        duration = await parser.extract_duration(page)
        if duration > 0:
            logger.info(f"✅ Duration: {duration} minutes")
        else:
            logger.warning("⚠️  No duration found")

        # Step 4: Extract LearnPoint structure
        logger.info("\n📦 Extracting LearnPoint structure...")
        learning_points_dict = await parser.extract_learning_points(page)

        if learning_points_dict:
            total_videos = sum(len(steps) for steps in learning_points_dict.values())
            logger.info(f"✅ Found {len(learning_points_dict)} LearnPoints with {total_videos} videos")

            for lp_name, steps in learning_points_dict.items():
                logger.info(f"\n   📌 {lp_name}: {len(steps)} videos")
                for idx, step in enumerate(steps[:3], 1):  # Show first 3
                    logger.info(f"      {idx}. {step.title} ({step.duration})")
                if len(steps) > 3:
                    logger.info(f"      ... and {len(steps) - 3} more")
        else:
            logger.error("❌ No LearnPoints found")

        # Step 5: Verify files were created
        logger.info("\n📂 Verifying created files...")
        base_dir = Path("tests/test_real_data")
        course_dir = base_dir / TEST_LANGUAGE / TEST_CATEGORY / TEST_COURSE_TITLE

        if course_dir.exists():
            logger.info(f"✅ Course directory exists: {course_dir}")

            overview_file = course_dir / "overview.txt"
            transcript_file = course_dir / "transcript.txt"

            if overview_file.exists():
                size = overview_file.stat().st_size
                logger.info(f"   ✅ overview.txt ({size} bytes)")
            else:
                logger.warning("   ⚠️  overview.txt not found")

            if transcript_file.exists():
                size = transcript_file.stat().st_size
                logger.info(f"   ✅ transcript.txt ({size} bytes)")
            else:
                logger.warning("   ⚠️  transcript.txt not found")
        else:
            logger.warning(f"⚠️  Course directory not created: {course_dir}")

        # Step 6: Create Course object and save to JSON
        logger.info("\n💾 Creating Course object and saving to JSON...")

        # Create course with extracted data
        course = Course(
            title=TEST_COURSE_TITLE,
            url=TEST_COURSE_URL,
            overview=overview_path if overview_text else "",
            transcript=transcript_path if transcript_text else "",
            duration=duration,
            last_updated=datetime.now().isoformat(),
            learning_points=[]  # Would need to crawl all videos for full data
        )

        # Create category
        category = Category(
            title=TEST_CATEGORY,
            url="/test/category",
            last_updated=datetime.now().isoformat(),
            courses=[course]
        )

        # Save to JSON
        test_json = Path("tests/test_real_course_result.json")
        manager = ContentManager(test_json, language=TEST_LANGUAGE)
        manager.categories = [category]
        manager.save()

        logger.info(f"✅ Saved to: {test_json}")

        # Verify JSON content
        import json
        with open(test_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"\n📊 JSON content verification:")
        logger.info(f"   language: {data.get('language')}")
        logger.info(f"   categories: {len(data.get('categories', []))}")

        saved_course = data['categories'][0]['courses'][0]
        logger.info(f"\n📚 Course in JSON:")
        logger.info(f"   title: {saved_course['title']}")
        logger.info(f"   overview: {saved_course['overview']}")  # Should be path, not content!
        logger.info(f"   transcript: {saved_course['transcript']}")  # Should be path, not content!
        logger.info(f"   duration: {saved_course['duration']}")

        # Verify paths are stored, not content
        if saved_course['overview']:
            if len(saved_course['overview']) < 200:  # Path should be short
                logger.info(f"   ✅ Overview field contains PATH (not content)")
            else:
                logger.warning(f"   ⚠️  Overview field might contain content instead of path!")

        if saved_course['transcript']:
            if len(saved_course['transcript']) < 200:  # Path should be short
                logger.info(f"   ✅ Transcript field contains PATH (not content)")
            else:
                logger.warning(f"   ⚠️  Transcript field might contain content instead of path!")

        logger.info("\n" + "="*70)
        logger.info("✅ TEST COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        logger.info("\nVerify the following:")
        logger.info(f"1. Files created in: {course_dir}")
        logger.info(f"2. JSON saved to: {test_json}")
        logger.info(f"3. JSON contains PATHS, not full content")

        return True

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        # Cleanup
        if browser_manager:
            logger.info("\n🔄 Closing browser...")
            await browser_manager.close()


def main():
    """Run the test"""
    logger.info("\n" + "="*70)
    logger.info("🧪 REAL COURSE CRAWLING TEST")
    logger.info("="*70)
    logger.info("\nThis test will:")
    logger.info("1. Open browser and wait for you to login")
    logger.info("2. Wait for you to navigate to a course page")
    logger.info("3. Extract overview, transcript, duration, LearnPoints")
    logger.info("4. Save text files and JSON")
    logger.info("5. Verify everything works correctly")
    logger.info("\nPress Ctrl+C to cancel")

    try:
        result = asyncio.run(test_real_course_crawl())
        if result:
            logger.info("\n✅ All tests passed!")
        else:
            logger.error("\n❌ Test failed")
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()

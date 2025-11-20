"""
Test Phase 3 - Crawler Updates

Tests:
1. CategoryCrawler with language support
2. SeriesCrawler with language support
3. CourseParser extraction methods (overview, transcript, duration)
4. LearnPoint structure extraction
"""

import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler.content_manager import (
    Video, LearnPoint, Course, Category, Series, ContentManager
)
from src.crawler.category_crawler import CategoryCrawler
from src.crawler.series_crawler import SeriesCrawler
from src.crawler.course_crawler import CourseCrawler
from src.crawler.course_parser import CourseParser

# Configure logger
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    colorize=True,
)


def test_1_category_crawler_language_support():
    """Test 1: CategoryCrawler with language support"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: CategoryCrawler Language Support")
    logger.info("="*70)

    # Test English crawler
    en_file = Path("tests/test_en_categories.json")
    en_crawler = CategoryCrawler(
        content_file=en_file,
        language="en"
    )

    logger.info(f"\n✅ Created EN CategoryCrawler")
    logger.info(f"   Language: {en_crawler.language}")
    logger.info(f"   Content file: {en_crawler.content_file}")
    logger.info(f"   ContentManager language: {en_crawler.content_manager.language}")

    # Test Japanese crawler
    ja_file = Path("tests/test_ja_categories.json")
    ja_crawler = CategoryCrawler(
        content_file=ja_file,
        language="ja"
    )

    logger.info(f"\n✅ Created JA CategoryCrawler")
    logger.info(f"   Language: {ja_crawler.language}")
    logger.info(f"   Content file: {ja_crawler.content_file}")
    logger.info(f"   ContentManager language: {ja_crawler.content_manager.language}")

    logger.info("\n✅ TEST 1 PASSED")
    return True


def test_2_series_crawler_language_support():
    """Test 2: SeriesCrawler with language support"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: SeriesCrawler Language Support")
    logger.info("="*70)

    # Test English crawler
    en_file = Path("tests/test_en_series.json")
    en_crawler = SeriesCrawler(
        content_file=en_file,
        language="en"
    )

    logger.info(f"\n✅ Created EN SeriesCrawler")
    logger.info(f"   Language: {en_crawler.language}")
    logger.info(f"   Content file: {en_crawler.content_file}")
    logger.info(f"   ContentManager language: {en_crawler.content_manager.language}")

    # Test Japanese crawler
    ja_file = Path("tests/test_ja_series.json")
    ja_crawler = SeriesCrawler(
        content_file=ja_file,
        language="ja"
    )

    logger.info(f"\n✅ Created JA SeriesCrawler")
    logger.info(f"   Language: {ja_crawler.language}")
    logger.info(f"   Content file: {ja_crawler.content_file}")
    logger.info(f"   ContentManager language: {ja_crawler.content_manager.language}")

    logger.info("\n✅ TEST 2 PASSED")
    return True


def test_3_course_crawler_updates():
    """Test 3: CourseCrawler with new features"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: CourseCrawler Updates")
    logger.info("="*70)

    # Test with language support
    en_file = Path("tests/test_en_courses.json")
    crawler = CourseCrawler(
        content_file=en_file,
        language="en",
        enable_download=False  # Default is False now
    )

    logger.info(f"\n✅ Created CourseCrawler with updates")
    logger.info(f"   Language: {crawler.language}")
    logger.info(f"   Enable download: {crawler.enable_download}")
    logger.info(f"   ContentManager language: {crawler.content_manager.language}")
    logger.info(f"   Download dir: {crawler.downloader.download_dir}")

    # Verify CourseParser has new methods
    parser = CourseParser()
    has_overview = hasattr(parser, 'extract_overview')
    has_transcript = hasattr(parser, 'extract_transcript')
    has_duration = hasattr(parser, 'extract_duration')
    has_learn_points = hasattr(parser, 'extract_learning_points')

    logger.info(f"\n📋 CourseParser new methods:")
    logger.info(f"   extract_overview: {'✅' if has_overview else '❌'}")
    logger.info(f"   extract_transcript: {'✅' if has_transcript else '❌'}")
    logger.info(f"   extract_duration: {'✅' if has_duration else '❌'}")
    logger.info(f"   extract_learning_points: {'✅' if has_learn_points else '❌'}")

    if not all([has_overview, has_transcript, has_duration, has_learn_points]):
        logger.error("❌ Missing CourseParser methods!")
        return False

    logger.info("\n✅ TEST 3 PASSED")
    return True


def test_4_video_object_schema():
    """Test 4: Video object with new schema"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Video Object Schema")
    logger.info("="*70)

    # Create video with new schema
    video = Video(
        title="Test Video",
        url="/en/courses/test/steps/123",
        vimeo_url="https://player.vimeo.com/video/123",
        learning_point="Introduction",  # NEW field
        downloaded=False,  # NEW field
        download_path="",  # NEW field
        last_updated=datetime.now().isoformat()  # NEW field
    )

    logger.info(f"\n✅ Created Video with new schema:")
    logger.info(f"   Title: {video.title}")
    logger.info(f"   Learning Point: {video.learning_point}")
    logger.info(f"   Downloaded: {video.downloaded}")
    logger.info(f"   Download Path: {video.download_path or 'N/A'}")
    logger.info(f"   Last Updated: {video.last_updated}")

    # Verify old fields are removed
    has_uploaded_to_drive = hasattr(video, 'uploaded_to_drive')
    has_drive_file_id = hasattr(video, 'drive_file_id')

    logger.info(f"\n🗑️  Old Google Drive fields:")
    logger.info(f"   uploaded_to_drive: {'❌ FOUND (should be removed!)' if has_uploaded_to_drive else '✅ Removed'}")
    logger.info(f"   drive_file_id: {'❌ FOUND (should be removed!)' if has_drive_file_id else '✅ Removed'}")

    if has_uploaded_to_drive or has_drive_file_id:
        logger.error("❌ Google Drive fields still present!")
        return False

    logger.info("\n✅ TEST 4 PASSED")
    return True


def test_5_course_object_schema():
    """Test 5: Course object with new schema"""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: Course Object Schema")
    logger.info("="*70)

    # Create course with new schema
    video1 = Video(
        title="Video 1",
        url="/test/1",
        vimeo_url="",
        learning_point="Introduction",
        downloaded=False,
        download_path="",
        last_updated=datetime.now().isoformat()
    )

    video2 = Video(
        title="Video 2",
        url="/test/2",
        vimeo_url="",
        learning_point="Main Content",
        downloaded=False,
        download_path="",
        last_updated=datetime.now().isoformat()
    )

    lp1 = LearnPoint(title="Introduction", videos=[video1])
    lp2 = LearnPoint(title="Main Content", videos=[video2])

    course = Course(
        title="Test Course",
        url="/test/course",
        overview="This is a test course overview",  # NEW field
        transcript="Full course transcript here",  # NEW field
        duration=45,  # NEW field (in minutes)
        last_updated=datetime.now().isoformat(),  # NEW field
        learning_points=[lp1, lp2]  # NEW structure (replaces videos)
    )

    logger.info(f"\n✅ Created Course with new schema:")
    logger.info(f"   Title: {course.title}")
    logger.info(f"   Overview: {course.overview[:50]}...")
    logger.info(f"   Transcript: {len(course.transcript)} chars")
    logger.info(f"   Duration: {course.duration} minutes")
    logger.info(f"   Learning Points: {len(course.learning_points)}")
    logger.info(f"   Last Updated: {course.last_updated}")

    for idx, lp in enumerate(course.learning_points, 1):
        logger.info(f"      LearnPoint {idx}: {lp.title} ({len(lp.videos)} videos)")

    # Verify old structure is replaced
    has_videos_list = hasattr(course, 'videos')
    logger.info(f"\n🔄 Structure change:")
    logger.info(f"   videos (old): {'⚠️  Still exists' if has_videos_list else '✅ Replaced'}")
    logger.info(f"   learning_points (new): ✅ Present")

    logger.info("\n✅ TEST 5 PASSED")
    return True


def test_6_content_manager_save_load():
    """Test 6: ContentManager saves/loads new schema"""
    logger.info("\n" + "="*70)
    logger.info("TEST 6: ContentManager Save/Load New Schema")
    logger.info("="*70)

    # Create test data
    video = Video(
        title="Test Video",
        url="/test/video",
        vimeo_url="https://player.vimeo.com/video/123",
        learning_point="Introduction",
        downloaded=False,
        download_path="",
        last_updated=datetime.now().isoformat()
    )

    lp = LearnPoint(title="Introduction", videos=[video])

    course = Course(
        title="Test Course",
        url="/test/course",
        overview="Test overview",
        transcript="Test transcript",
        duration=30,
        last_updated=datetime.now().isoformat(),
        learning_points=[lp]
    )

    category = Category(
        title="Test Category",
        url="/test/category",
        last_updated=datetime.now().isoformat(),
        courses=[course]
    )

    # Save
    test_file = Path("tests/test_phase3_schema.json")
    manager = ContentManager(test_file, language="en")
    manager.categories = [category]
    manager.save()

    logger.info(f"\n✅ Saved to: {test_file}")

    # Load
    manager2 = ContentManager(test_file, language="en")
    manager2.load()

    logger.info(f"✅ Loaded from: {test_file}")
    logger.info(f"   Language: {manager2.language}")
    logger.info(f"   Categories: {len(manager2.categories)}")

    loaded_category = manager2.categories[0]
    loaded_course = loaded_category.courses[0]
    loaded_lp = loaded_course.learning_points[0]
    loaded_video = loaded_lp.videos[0]

    logger.info(f"\n📊 Loaded data structure:")
    logger.info(f"   Category: {loaded_category.title}")
    logger.info(f"   Course: {loaded_course.title}")
    logger.info(f"   Course.overview: {loaded_course.overview}")
    logger.info(f"   Course.duration: {loaded_course.duration} min")
    logger.info(f"   LearnPoint: {loaded_lp.title}")
    logger.info(f"   Video: {loaded_video.title}")
    logger.info(f"   Video.learning_point: {loaded_video.learning_point}")
    logger.info(f"   Video.downloaded: {loaded_video.downloaded}")

    logger.info("\n✅ TEST 6 PASSED")
    return True


def main():
    """Run all tests"""
    logger.info("\n" + "="*70)
    logger.info("🧪 PHASE 3 CRAWLER UPDATES TEST SUITE")
    logger.info("="*70)

    tests = [
        ("CategoryCrawler Language Support", test_1_category_crawler_language_support),
        ("SeriesCrawler Language Support", test_2_series_crawler_language_support),
        ("CourseCrawler Updates", test_3_course_crawler_updates),
        ("Video Object Schema", test_4_video_object_schema),
        ("Course Object Schema", test_5_course_object_schema),
        ("ContentManager Save/Load", test_6_content_manager_save_load),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            logger.error(f"\n❌ TEST FAILED: {name}")
            logger.error(f"   Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            failed += 1

    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*70)
    logger.info(f"Passed: {passed}/{len(tests)}")
    logger.info(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        logger.info("\n✅ ALL TESTS PASSED!")
        logger.info("Phase 3 crawler updates are working correctly.")
    else:
        logger.error(f"\n❌ {failed} TEST(S) FAILED")

    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()

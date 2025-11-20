"""
Test Phase 2 - Data Models & ContentManager

Tests:
1. Create data models with new schema
2. Load old format (backward compatibility)
3. Load new format (LearnPoint structure)
4. Save new format
5. Statistics with LearnPoint structure
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler.content_manager import (
    Video, LearnPoint, Course, Category, ContentManager
)

# Configure logger
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    colorize=True,
)


def test_1_create_data_models():
    """Test 1: Create data models with new schema"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Create Data Models with New Schema")
    logger.info("="*70)

    # Create video
    video1 = Video(
        title="What is a Proposal?",
        url="/en/courses/abc/steps/123",
        vimeo_url="https://player.vimeo.com/video/123",
        learning_point="Introduction",
        downloaded=False,
        download_path="",
        last_updated=datetime.now().isoformat()
    )

    video2 = Video(
        title="Why Proposals Matter",
        url="/en/courses/abc/steps/124",
        vimeo_url="https://player.vimeo.com/video/124",
        learning_point="Introduction",
        downloaded=True,
        download_path="downloads/en/Category/Course/Introduction/Why Proposals Matter.mp4",
        last_updated=datetime.now().isoformat()
    )

    logger.info(f"\n✅ Created 2 videos")
    logger.info(f"   Video 1: {video1.title} (downloaded: {video1.downloaded})")
    logger.info(f"   Video 2: {video2.title} (downloaded: {video2.downloaded})")

    # Create LearnPoint
    learn_point = LearnPoint(
        title="Introduction",
        videos=[video1, video2]
    )

    logger.info(f"\n✅ Created LearnPoint: {learn_point.title}")
    logger.info(f"   Videos in LearnPoint: {len(learn_point.videos)}")

    # Create Course
    course = Course(
        title="Business Proposals",
        url="/en/courses/abc/learn/steps",
        overview="Learn how to structure strong proposals...",
        transcript="Full course transcript here...",
        duration=45,
        last_updated=datetime.now().isoformat(),
        learning_points=[learn_point]
    )

    logger.info(f"\n✅ Created Course: {course.title}")
    logger.info(f"   Overview: {course.overview[:50]}...")
    logger.info(f"   Duration: {course.duration} minutes")
    logger.info(f"   Learning Points: {len(course.learning_points)}")

    # Create Category
    category = Category(
        title="Critical Thinking",
        url="/en/categories/critical-thinking",
        last_updated=datetime.now().isoformat(),
        courses=[course]
    )

    logger.info(f"\n✅ Created Category: {category.title}")
    logger.info(f"   Courses: {len(category.courses)}")

    logger.info("\n✅ TEST 1 PASSED")
    return True


def test_2_save_new_format():
    """Test 2: Save with new schema"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Save with New Schema")
    logger.info("="*70)

    # Create test data
    video1 = Video(
        title="Video 1",
        url="/en/courses/test/steps/1",
        vimeo_url="https://player.vimeo.com/video/111",
        learning_point="Introduction",
        downloaded=False,
        download_path="",
        last_updated=datetime.now().isoformat()
    )

    video2 = Video(
        title="Video 2",
        url="/en/courses/test/steps/2",
        vimeo_url="https://player.vimeo.com/video/222",
        learning_point="Main Content",
        downloaded=True,
        download_path="downloads/en/Test/Course/Main Content/Video 2.mp4",
        last_updated=datetime.now().isoformat()
    )

    lp1 = LearnPoint(title="Introduction", videos=[video1])
    lp2 = LearnPoint(title="Main Content", videos=[video2])

    course = Course(
        title="Test Course",
        url="/en/courses/test/learn/steps",
        overview="This is a test course",
        transcript="Test transcript",
        duration=30,
        last_updated=datetime.now().isoformat(),
        learning_points=[lp1, lp2]
    )

    category = Category(
        title="Test Category",
        url="/en/categories/test",
        last_updated=datetime.now().isoformat(),
        courses=[course]
    )

    # Save to file
    test_file = Path("tests/test_new_format.json")
    manager = ContentManager(test_file, language="en")
    manager.categories = [category]
    manager.save()

    logger.info(f"\n✅ Saved to: {test_file}")

    # Verify file structure
    with open(test_file, 'r') as f:
        data = json.load(f)

    logger.info(f"\n📊 Verifying saved structure:")
    logger.info(f"   language: {data.get('language')}")
    logger.info(f"   last_updated: {data.get('last_updated')}")
    logger.info(f"   categories: {len(data.get('categories', []))}")

    cat = data['categories'][0]
    logger.info(f"   category.last_updated: {cat.get('last_updated')}")
    logger.info(f"   courses: {len(cat.get('courses', []))}")

    crs = cat['courses'][0]
    logger.info(f"   course.overview: {crs.get('overview')}")
    logger.info(f"   course.duration: {crs.get('duration')}")
    logger.info(f"   learning_points: {len(crs.get('learning_points', []))}")

    lp = crs['learning_points'][0]
    logger.info(f"   learning_point.title: {lp.get('title')}")
    logger.info(f"   videos: {len(lp.get('videos', []))}")

    vid = lp['videos'][0]
    logger.info(f"   video.learning_point: {vid.get('learning_point')}")
    logger.info(f"   video.downloaded: {vid.get('downloaded')}")
    logger.info(f"   video.download_path: {vid.get('download_path')}")

    logger.info("\n✅ TEST 2 PASSED")
    return True


def test_3_load_new_format():
    """Test 3: Load new format"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Load New Format")
    logger.info("="*70)

    test_file = Path("tests/test_new_format.json")
    manager = ContentManager(test_file, language="en")
    manager.load()

    logger.info(f"\n✅ Loaded: {test_file}")
    logger.info(f"   Language: {manager.language}")
    logger.info(f"   Categories: {len(manager.categories)}")

    # Verify structure
    category = manager.categories[0]
    logger.info(f"\n📂 Category: {category.title}")
    logger.info(f"   Last updated: {category.last_updated}")
    logger.info(f"   Courses: {len(category.courses)}")

    course = category.courses[0]
    logger.info(f"\n📚 Course: {course.title}")
    logger.info(f"   Overview: {course.overview}")
    logger.info(f"   Transcript: {course.transcript}")
    logger.info(f"   Duration: {course.duration} minutes")
    logger.info(f"   Learning Points: {len(course.learning_points)}")

    for idx, lp in enumerate(course.learning_points, 1):
        logger.info(f"\n📦 LearnPoint {idx}: {lp.title}")
        logger.info(f"   Videos: {len(lp.videos)}")

        for video in lp.videos:
            status = "✅" if video.downloaded else "⏳"
            logger.info(f"   {status} {video.title}")
            logger.info(f"      downloaded: {video.downloaded}")
            logger.info(f"      download_path: {video.download_path or 'N/A'}")

    logger.info("\n✅ TEST 3 PASSED")
    return True


def test_4_backward_compatibility():
    """Test 4: Load old format (backward compatibility)"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Backward Compatibility (Old Format)")
    logger.info("="*70)

    # Create old format JSON
    old_format = {
        "categories": [
            {
                "title": "Old Category",
                "url": "/old/category",
                "courses": [
                    {
                        "title": "Old Course",
                        "url": "/old/course",
                        "last_updated": "2025-01-01",
                        "videos": [
                            {
                                "title": "Old Video 1",
                                "url": "/old/video1",
                                "vimeo_url": "https://player.vimeo.com/video/999",
                                "downloaded": False,
                                "uploaded_to_drive": False,
                                "drive_file_id": ""
                            },
                            {
                                "title": "Old Video 2",
                                "url": "/old/video2",
                                "vimeo_url": "https://player.vimeo.com/video/998",
                                "downloaded": True,
                                "uploaded_to_drive": False,
                                "drive_file_id": ""
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Save old format
    old_file = Path("tests/test_old_format.json")
    with open(old_file, 'w') as f:
        json.dump(old_format, f, indent=2)

    logger.info(f"\n📄 Created old format file: {old_file}")

    # Load with ContentManager
    manager = ContentManager(old_file, language="en")
    manager.load()

    logger.info(f"\n✅ Loaded old format")
    logger.info(f"   Categories: {len(manager.categories)}")

    # Verify conversion to new structure
    category = manager.categories[0]
    course = category.courses[0]

    logger.info(f"\n📚 Course: {course.title}")
    logger.info(f"   Learning Points: {len(course.learning_points)}")

    # Old format should be converted to single "Default" LearnPoint
    if course.learning_points:
        lp = course.learning_points[0]
        logger.info(f"\n📦 LearnPoint: {lp.title} (auto-converted)")
        logger.info(f"   Videos: {len(lp.videos)}")

        for video in lp.videos:
            logger.info(f"   - {video.title} (downloaded: {video.downloaded})")

    logger.info("\n✅ TEST 4 PASSED - Old format loaded and converted")
    return True


def test_5_statistics():
    """Test 5: Statistics with LearnPoint structure"""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: Statistics")
    logger.info("="*70)

    test_file = Path("tests/test_new_format.json")
    manager = ContentManager(test_file, language="en")
    manager.load()

    # Get stats
    stats = manager.get_stats()

    logger.info(f"\n📊 Statistics:")
    logger.info(f"   Categories: {stats['categories']}")
    logger.info(f"   Courses: {stats['courses']}")
    logger.info(f"   Learning Points: {stats['learning_points']}")
    logger.info(f"   Total Videos: {stats['videos']}")
    logger.info(f"   Downloaded: {stats['downloaded']}")
    logger.info(f"   Pending: {stats['pending_download']}")

    # Print formatted stats
    manager.print_stats()

    logger.info("✅ TEST 5 PASSED")
    return True


def main():
    """Run all tests"""
    logger.info("\n" + "="*70)
    logger.info("🧪 PHASE 2 DATA MODELS TEST SUITE")
    logger.info("="*70)

    tests = [
        ("Create Data Models", test_1_create_data_models),
        ("Save New Format", test_2_save_new_format),
        ("Load New Format", test_3_load_new_format),
        ("Backward Compatibility", test_4_backward_compatibility),
        ("Statistics", test_5_statistics),
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
        logger.info("Phase 2 data models are working correctly.")
    else:
        logger.error(f"\n❌ {failed} TEST(S) FAILED")

    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()

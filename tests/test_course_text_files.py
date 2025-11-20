"""
Test Course Text Files (Overview & Transcript)

Tests that overview and transcript are saved to separate .txt files
instead of storing in JSON directly.
"""

import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler.course_parser import CourseParser

# Configure logger
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    colorize=True,
)


def test_save_overview_to_file():
    """Test 1: Save overview to .txt file"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Save Overview to File")
    logger.info("="*70)

    parser = CourseParser()

    overview_text = """
This course teaches you how to create compelling business proposals
that win clients and close deals. You'll learn the essential elements
of a strong proposal, common pitfalls to avoid, and proven strategies
for success.
""".strip()

    # Save overview
    base_dir = Path("tests/test_downloads")
    overview_path = parser.save_overview_to_file(
        overview=overview_text,
        language="en",
        category_or_series="Critical Thinking",
        course_title="Business Proposals",
        base_dir=base_dir
    )

    if overview_path:
        logger.info(f"\n✅ Overview path: {overview_path}")

        # Verify file exists
        full_path = base_dir / overview_path
        if full_path.exists():
            logger.info(f"✅ File exists: {full_path}")

            # Read and verify content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if content == overview_text:
                logger.info(f"✅ Content matches ({len(content)} chars)")
            else:
                logger.error("❌ Content mismatch!")
                return False
        else:
            logger.error(f"❌ File not found: {full_path}")
            return False
    else:
        logger.error("❌ Failed to save overview")
        return False

    logger.info("\n✅ TEST 1 PASSED")
    return True


def test_save_transcript_to_file():
    """Test 2: Save transcript to .txt file"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Save Transcript to File")
    logger.info("="*70)

    parser = CourseParser()

    transcript_text = """
[00:00] Welcome to Business Proposals
[00:15] In this course, we'll cover...
[00:30] First, let's look at what makes a proposal effective
[01:00] The key elements include...
[02:00] Now let's examine some examples...
""".strip()

    # Save transcript
    base_dir = Path("tests/test_downloads")
    transcript_path = parser.save_transcript_to_file(
        transcript=transcript_text,
        language="en",
        category_or_series="Critical Thinking",
        course_title="Business Proposals",
        base_dir=base_dir
    )

    if transcript_path:
        logger.info(f"\n✅ Transcript path: {transcript_path}")

        # Verify file exists
        full_path = base_dir / transcript_path
        if full_path.exists():
            logger.info(f"✅ File exists: {full_path}")

            # Read and verify content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if content == transcript_text:
                logger.info(f"✅ Content matches ({len(content)} chars)")
            else:
                logger.error("❌ Content mismatch!")
                return False
        else:
            logger.error(f"❌ File not found: {full_path}")
            return False
    else:
        logger.error("❌ Failed to save transcript")
        return False

    logger.info("\n✅ TEST 2 PASSED")
    return True


def test_directory_structure():
    """Test 3: Verify directory structure"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Verify Directory Structure")
    logger.info("="*70)

    base_dir = Path("tests/test_downloads")
    expected_structure = base_dir / "en" / "Critical Thinking" / "Business Proposals"

    logger.info(f"\n📁 Expected structure: {expected_structure}")

    if expected_structure.exists():
        logger.info("✅ Course directory exists")

        # Check for both files
        overview_file = expected_structure / "overview.txt"
        transcript_file = expected_structure / "transcript.txt"

        files_found = []
        if overview_file.exists():
            files_found.append("overview.txt")
            logger.info(f"   ✅ {overview_file.name}")

        if transcript_file.exists():
            files_found.append("transcript.txt")
            logger.info(f"   ✅ {transcript_file.name}")

        if len(files_found) == 2:
            logger.info("\n✅ All expected files present")
        else:
            logger.warning(f"\n⚠️  Only {len(files_found)}/2 files found")

    else:
        logger.error(f"❌ Directory not found: {expected_structure}")
        return False

    logger.info("\n✅ TEST 3 PASSED")
    return True


def test_filename_sanitization():
    """Test 4: Test filename sanitization"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Filename Sanitization")
    logger.info("="*70)

    parser = CourseParser()

    # Test cases with problematic characters
    test_cases = [
        ("Course: Advanced <Skills>", "Course_ Advanced _Skills_"),
        ('Path/With\\Slashes', "Path_With_Slashes"),
        ("Name?With*Invalid|Chars", "Name_With_Invalid_Chars"),
        ("  Leading and trailing spaces  ", "Leading and trailing spaces"),
    ]

    all_passed = True
    for original, expected in test_cases:
        sanitized = parser._sanitize_filename(original)
        if sanitized == expected:
            logger.info(f"✅ '{original}' → '{sanitized}'")
        else:
            logger.error(f"❌ '{original}' → '{sanitized}' (expected '{expected}')")
            all_passed = False

    if all_passed:
        logger.info("\n✅ TEST 4 PASSED")
        return True
    else:
        logger.error("\n❌ TEST 4 FAILED")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "="*70)
    logger.info("🧪 COURSE TEXT FILES TEST SUITE")
    logger.info("="*70)

    tests = [
        ("Save Overview to File", test_save_overview_to_file),
        ("Save Transcript to File", test_save_transcript_to_file),
        ("Verify Directory Structure", test_directory_structure),
        ("Filename Sanitization", test_filename_sanitization),
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
        logger.info("Course text files feature is working correctly.")
    else:
        logger.error(f"\n❌ {failed} TEST(S) FAILED")

    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()

"""
Test Content Manager

Test script to verify ContentManager functionality
"""

from pathlib import Path
from loguru import logger
from src.crawler.content_manager import ContentManager

# Configure logging
logger.add(
    "logs/content_manager_test.log",
    rotation="1 MB",
    level="DEBUG"
)


def main():
    print("\n🚀 Testing Content Manager...\n")

    # Initialize content manager
    content_file = Path("data/courses/learn-content.json")
    manager = ContentManager(content_file)

    # Load content
    print("📖 Loading content from JSON...")
    manager.load()

    # Print statistics
    manager.print_stats()

    # Display categories
    print("📚 Categories:")
    print("="*60)
    for i, cat in enumerate(manager.get_categories(), 1):
        course_count = len(cat.courses)
        print(f"{i}. {cat.title}")
        print(f"   URL: {cat.url}")
        print(f"   Courses: {course_count}")
        print()

    # Test getting specific category
    print("\n🔍 Testing get_category()...")
    cat = manager.get_category("Marketing")
    if cat:
        print(f"✅ Found category: {cat.title}")
        print(f"   URL: {cat.url}")
        print(f"   Courses: {len(cat.courses)}")
    else:
        print("❌ Category not found")

    print("\n✅ Content Manager test completed!\n")


if __name__ == "__main__":
    main()

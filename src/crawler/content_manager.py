"""
Content Manager

Module to read, manage and update learn-content.json
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class Video:
    """Video information"""
    title: str = ""
    url: str = ""
    vimeo_url: str = ""  # Actual video download URL
    downloaded: bool = False
    uploaded_to_drive: bool = False
    drive_file_id: str = ""


@dataclass
class Course:
    """Course information"""
    title: str = ""
    url: str = ""
    last_updated: str = ""
    videos: List[Video] = None

    def __post_init__(self):
        if self.videos is None:
            self.videos = []


@dataclass
class Category:
    """Category information"""
    title: str = ""
    url: str = ""
    courses: List[Course] = None

    def __post_init__(self):
        if self.courses is None:
            self.courses = []


class ContentManager:
    """Manage learn-content.json file"""

    def __init__(self, content_file: Path):
        """
        Initialize content manager

        Args:
            content_file: Path to learn-content.json
        """
        self.content_file = content_file
        self.categories: List[Category] = []

        logger.info(f"📚 Content Manager initialized: {content_file}")

    def load(self) -> None:
        """Load content from JSON file"""
        if not self.content_file.exists():
            logger.warning(f"⚠️  Content file not found: {self.content_file}")
            return

        try:
            with open(self.content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.categories = []
            for cat_data in data.get('categories', []):
                # Parse courses
                courses = []
                for course_data in cat_data.get('courses', []):
                    # Parse videos
                    videos = []
                    for video_data in course_data.get('videos', []):
                        videos.append(Video(**video_data))

                    courses.append(Course(
                        title=course_data.get('title', ''),
                        url=course_data.get('url', ''),
                        last_updated=course_data.get('last_updated', ''),
                        videos=videos
                    ))

                self.categories.append(Category(
                    title=cat_data.get('title', ''),
                    url=cat_data.get('url', ''),
                    courses=courses
                ))

            logger.info(f"✅ Loaded {len(self.categories)} categories")

        except Exception as e:
            logger.error(f"❌ Failed to load content: {e}")
            raise

    def save(self) -> None:
        """Save content to JSON file"""
        try:
            # Ensure parent directory exists
            self.content_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict
            data = {
                'categories': [
                    {
                        'title': cat.title,
                        'url': cat.url,
                        'courses': [
                            {
                                'title': course.title,
                                'url': course.url,
                                'last_updated': course.last_updated,
                                'videos': [
                                    {
                                        'title': video.title,
                                        'url': video.url,
                                        'vimeo_url': video.vimeo_url,
                                        'downloaded': video.downloaded,
                                        'uploaded_to_drive': video.uploaded_to_drive,
                                        'drive_file_id': video.drive_file_id
                                    }
                                    for video in course.videos
                                ]
                            }
                            for course in cat.courses
                        ]
                    }
                    for cat in self.categories
                ]
            }

            # Write to file with pretty formatting
            with open(self.content_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            logger.info(f"💾 Content saved to {self.content_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save content: {e}")
            raise

    def get_categories(self) -> List[Category]:
        """Get all categories"""
        return self.categories

    def get_category(self, title: str) -> Optional[Category]:
        """Get category by title"""
        for cat in self.categories:
            if cat.title == title:
                return cat
        return None

    def get_category_by_url(self, url: str) -> Optional[Category]:
        """Get category by URL"""
        for cat in self.categories:
            if cat.url == url:
                return cat
        return None

    def add_courses_to_category(
        self,
        category_title: str,
        courses: List[Course]
    ) -> None:
        """
        Add courses to a category

        Args:
            category_title: Category title
            courses: List of courses to add
        """
        category = self.get_category(category_title)
        if category:
            category.courses.extend(courses)
            logger.info(f"✅ Added {len(courses)} courses to '{category_title}'")
        else:
            logger.warning(f"⚠️  Category not found: {category_title}")

    def add_videos_to_course(
        self,
        category_title: str,
        course_title: str,
        videos: List[Video]
    ) -> None:
        """
        Add videos to a course

        Args:
            category_title: Category title
            course_title: Course title
            videos: List of videos to add
        """
        category = self.get_category(category_title)
        if not category:
            logger.warning(f"⚠️  Category not found: {category_title}")
            return

        for course in category.courses:
            if course.title == course_title:
                course.videos.extend(videos)
                logger.info(f"✅ Added {len(videos)} videos to '{course_title}'")
                return

        logger.warning(f"⚠️  Course not found: {course_title}")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the content"""
        total_categories = len(self.categories)
        total_courses = sum(len(cat.courses) for cat in self.categories)
        total_videos = sum(
            len(course.videos)
            for cat in self.categories
            for course in cat.courses
        )
        downloaded_videos = sum(
            sum(1 for video in course.videos if video.downloaded)
            for cat in self.categories
            for course in cat.courses
        )
        uploaded_videos = sum(
            sum(1 for video in course.videos if video.uploaded_to_drive)
            for cat in self.categories
            for course in cat.courses
        )

        return {
            'categories': total_categories,
            'courses': total_courses,
            'videos': total_videos,
            'downloaded': downloaded_videos,
            'uploaded': uploaded_videos,
            'pending_download': total_videos - downloaded_videos,
            'pending_upload': downloaded_videos - uploaded_videos
        }

    def print_stats(self) -> None:
        """Print content statistics"""
        stats = self.get_stats()

        print("\n" + "="*60)
        print("📊 CONTENT STATISTICS")
        print("="*60)
        print(f"Categories:        {stats['categories']}")
        print(f"Courses:           {stats['courses']}")
        print(f"Videos:            {stats['videos']}")
        print(f"Downloaded:        {stats['downloaded']} / {stats['videos']}")
        print(f"Uploaded to Drive: {stats['uploaded']} / {stats['videos']}")
        print(f"Pending Download:  {stats['pending_download']}")
        print(f"Pending Upload:    {stats['pending_upload']}")
        print("="*60 + "\n")

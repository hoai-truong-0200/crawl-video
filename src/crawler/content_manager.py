"""
Content Manager

Module to read, manage and update learn-content.json and explore-content.json
Supports multi-language (EN/JA) with LearnPoint grouping
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from loguru import logger


@dataclass
class Video:
    """
    Video information

    Fields:
        title: Video title
        url: Video page URL (/en/courses/.../steps/123)
        step_id: Step ID extracted from URL
        duration: Video duration (e.g., "5:23")
        learning_point: LearnPoint group name
        last_updated: ISO 8601 timestamp
        is_downloaded: Whether video file has been downloaded (default: False)
    """
    title: str = ""
    url: str = ""
    step_id: str = ""
    duration: str = ""
    learning_point: str = ""
    last_updated: str = ""
    is_downloaded: bool = False


@dataclass
class LearnPoint:
    """
    Learning Point grouping

    Groups videos by learning objectives within a course.

    Fields:
        title: LearnPoint name (e.g., "Introduction", "Main Content")
        videos: List of videos in this LearnPoint
    """
    title: str = ""
    videos: List[Video] = field(default_factory=list)

    def __post_init__(self):
        if self.videos is None:
            self.videos = []


@dataclass
class Course:
    """
    Course information

    Fields:
        title: Course title
        url: Course page URL
        duration: Total course duration in minutes
        last_updated: ISO 8601 timestamp
        learning_points: List of LearnPoints grouping videos by learning objectives
    """
    title: str = ""
    url: str = ""
    duration: int = 0  # Duration in minutes
    last_updated: str = ""
    learning_points: List[LearnPoint] = field(default_factory=list)

    def __post_init__(self):
        if self.learning_points is None:
            self.learning_points = []


@dataclass
class Category:
    """
    Category information (for learn-content)

    Fields:
        title: Category name
        url: Category page URL
        last_updated: ISO 8601 timestamp
        courses: List of courses in this category
    """
    title: str = ""
    url: str = ""
    last_updated: str = ""  # NEW: Timestamp
    courses: List[Course] = field(default_factory=list)

    def __post_init__(self):
        if self.courses is None:
            self.courses = []


@dataclass
class Series:
    """
    Series information (for explore-content)

    Same structure as Category but for series/playlists
    """
    title: str = ""
    url: str = ""
    last_updated: str = ""
    courses: List[Course] = field(default_factory=list)

    def __post_init__(self):
        if self.courses is None:
            self.courses = []


class ContentManager:
    """Manage learn-content.json and explore-content.json files"""

    def __init__(self, content_file: Path, language: str = "en"):
        """
        Initialize content manager

        Args:
            content_file: Path to learn-content.json or explore-content.json
            language: Language code (en/ja)
        """
        self.content_file = content_file
        self.language = language
        self.root_last_updated = ""
        self.categories: List[Category] = []
        self.series: List[Series] = []  # For explore-content.json

        # Auto-detect file type
        self.is_explore_content = "explore-content" in str(content_file)

        logger.info(f"📚 Content Manager initialized: {content_file} ({language})")

    def load(self) -> None:
        """
        Load content from JSON file

        Supports both old format (flat videos) and new format (LearnPoint structure)
        Auto-initializes with correct structure if file is empty or invalid
        """
        # If file doesn't exist, initialize with empty structure
        if not self.content_file.exists():
            logger.warning(f"⚠️  Content file not found: {self.content_file}")
            logger.info(f"📝 Will create new file with empty structure on first save")
            self.categories = []
            return

        # If file exists but is empty or too small, initialize structure
        if self.content_file.stat().st_size < 3:  # Less than "{}" or "[]"
            logger.warning(f"⚠️  Content file is empty: {self.content_file}")
            logger.info(f"📝 Initializing with empty structure")
            self._initialize_empty_file()
            return

        try:
            with open(self.content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle empty array [] - initialize proper structure
            if isinstance(data, list):
                logger.warning(f"⚠️  File contains array instead of object: {self.content_file}")
                logger.info(f"📝 Initializing with correct structure")
                self._initialize_empty_file()
                return

            # Get language and last_updated from root (if present)
            self.language = data.get('language', self.language)  # Use provided language as fallback
            self.root_last_updated = data.get('last_updated', '')

            self.categories = []
            for cat_data in data.get('categories', []):
                # Parse courses
                courses = []
                for course_data in cat_data.get('courses', []):

                    # NEW FORMAT: Parse learning_points (if present)
                    if 'learning_points' in course_data:
                        learning_points = []
                        for lp_data in course_data.get('learning_points', []):
                            # Parse videos in this LearnPoint
                            videos = []
                            for video_data in lp_data.get('videos', []):
                                videos.append(Video(
                                    title=video_data.get('title', ''),
                                    url=video_data.get('url', ''),
                                    step_id=video_data.get('step_id', ''),
                                    duration=video_data.get('duration', ''),
                                    learning_point=video_data.get('learning_point', ''),
                                    last_updated=video_data.get('last_updated', ''),
                                    is_downloaded=video_data.get('is_downloaded', False)
                                ))

                            learning_points.append(LearnPoint(
                                title=lp_data.get('title', ''),
                                videos=videos
                            ))

                        courses.append(Course(
                            title=course_data.get('title', ''),
                            url=course_data.get('url', ''),
                            duration=course_data.get('duration', 0),
                            last_updated=course_data.get('last_updated', ''),
                            learning_points=learning_points
                        ))

                    # OLD FORMAT: Parse flat videos list (backward compatibility)
                    else:
                        videos = []
                        for video_data in course_data.get('videos', []):
                            videos.append(Video(
                                title=video_data.get('title', ''),
                                url=video_data.get('url', ''),
                                step_id=video_data.get('step_id', ''),
                                duration=video_data.get('duration', ''),
                                learning_point='',
                                last_updated=''
                            ))

                        # Convert to LearnPoint structure (single default LearnPoint)
                        default_lp = LearnPoint(title='Default', videos=videos)

                        courses.append(Course(
                            title=course_data.get('title', ''),
                            url=course_data.get('url', ''),
                            duration=0,
                            last_updated=course_data.get('last_updated', ''),
                            learning_points=[default_lp] if videos else []
                        ))

                self.categories.append(Category(
                    title=cat_data.get('title', ''),
                    url=cat_data.get('url', ''),
                    last_updated=cat_data.get('last_updated', ''),
                    courses=courses
                ))

            # Parse series (for explore-content.json)
            self.series = []
            for series_data in data.get('series', []):
                # Parse courses (same structure as categories)
                courses = []
                for course_data in series_data.get('courses', []):
                    # NEW FORMAT: Parse learning_points (if present)
                    if 'learning_points' in course_data:
                        learning_points = []
                        for lp_data in course_data.get('learning_points', []):
                            videos = []
                            for video_data in lp_data.get('videos', []):
                                videos.append(Video(
                                    title=video_data.get('title', ''),
                                    url=video_data.get('url', ''),
                                    step_id=video_data.get('step_id', ''),
                                    duration=video_data.get('duration', ''),
                                    learning_point=video_data.get('learning_point', ''),
                                    last_updated=video_data.get('last_updated', ''),
                                    is_downloaded=video_data.get('is_downloaded', False)
                                ))

                            learning_points.append(LearnPoint(
                                title=lp_data.get('title', ''),
                                videos=videos
                            ))

                        courses.append(Course(
                            title=course_data.get('title', ''),
                            url=course_data.get('url', ''),
                            duration=course_data.get('duration', 0),
                            last_updated=course_data.get('last_updated', ''),
                            learning_points=learning_points
                        ))
                    # OLD FORMAT: Parse flat videos list
                    else:
                        videos = []
                        for video_data in course_data.get('videos', []):
                            videos.append(Video(
                                title=video_data.get('title', ''),
                                url=video_data.get('url', ''),
                                step_id=video_data.get('step_id', ''),
                                duration=video_data.get('duration', ''),
                                learning_point='',
                                last_updated=''
                            ))

                        default_lp = LearnPoint(title='Default', videos=videos)
                        courses.append(Course(
                            title=course_data.get('title', ''),
                            url=course_data.get('url', ''),
                            duration=0,
                            last_updated=course_data.get('last_updated', ''),
                            learning_points=[default_lp] if videos else []
                        ))

                self.series.append(Series(
                    title=series_data.get('title', ''),
                    url=series_data.get('url', ''),
                    last_updated=series_data.get('last_updated', ''),
                    courses=courses
                ))

            # Log results
            if self.categories:
                logger.info(f"✅ Loaded {len(self.categories)} categories")
            if self.series:
                logger.info(f"✅ Loaded {len(self.series)} series")

        except Exception as e:
            logger.error(f"❌ Failed to load content: {e}")
            # On error, initialize with empty structure and save it
            logger.info(f"📝 Initializing with empty structure due to load error")
            self._initialize_empty_file()

    def _initialize_empty_file(self) -> None:
        """
        Initialize file with correct empty structure and save it immediately
        Auto-detects whether to create categories (learn-content) or series (explore-content)
        """
        self.categories = []
        self.series = []
        self.root_last_updated = ''

        # Save the correct structure immediately
        try:
            self.content_file.parent.mkdir(parents=True, exist_ok=True)

            # Different structure for explore-content vs learn-content
            if self.is_explore_content:
                data = {
                    'series': []
                }
                logger.info(f"📝 Initializing explore-content structure (series)")
            else:
                data = {
                    'language': self.language,
                    'last_updated': '',
                    'categories': []
                }
                logger.info(f"📝 Initializing learn-content structure (categories)")

            with open(self.content_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Initialized empty structure in {self.content_file}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize file: {e}")

    def save(self) -> None:
        """
        Save content to JSON file with NEW schema

        Includes language, last_updated, and LearnPoint structure
        Auto-detects whether to save categories (learn-content) or series (explore-content)
        """
        try:
            # Ensure parent directory exists
            self.content_file.parent.mkdir(parents=True, exist_ok=True)

            # Update root last_updated if not set
            if not self.root_last_updated:
                self.root_last_updated = datetime.now().isoformat()

            # Different structure for explore-content vs learn-content
            if self.is_explore_content:
                # Save series (explore-content.json)
                data = {
                    'series': [
                        {
                            'title': series.title,
                            'url': series.url,
                            'last_updated': series.last_updated or datetime.now().isoformat(),
                            'courses': [
                                {
                                    'title': course.title,
                                    'url': course.url,
                                    'duration': course.duration,
                                    'last_updated': course.last_updated or datetime.now().isoformat(),
                                    'learning_points': [
                                        {
                                            'title': lp.title,
                                            'videos': [
                                                {
                                                    'title': video.title,
                                                    'url': video.url,
                                                    'step_id': video.step_id,
                                                    'duration': video.duration,
                                                    'learning_point': video.learning_point,
                                                    'last_updated': video.last_updated or datetime.now().isoformat(),
                                                    'is_downloaded': video.is_downloaded
                                                }
                                                for video in lp.videos
                                            ]
                                        }
                                        for lp in course.learning_points
                                    ]
                                }
                                for course in series.courses
                            ]
                        }
                        for series in self.series
                    ]
                }
            else:
                # Save categories (learn-content.json)
                data = {
                    'language': self.language,
                    'last_updated': self.root_last_updated,
                    'categories': [
                    {
                        'title': cat.title,
                        'url': cat.url,
                        'last_updated': cat.last_updated or datetime.now().isoformat(),
                        'courses': [
                            {
                                'title': course.title,
                                'url': course.url,
                                'duration': course.duration,
                                'last_updated': course.last_updated or datetime.now().isoformat(),
                                'learning_points': [
                                    {
                                        'title': lp.title,
                                        'videos': [
                                            {
                                                'title': video.title,
                                                'url': video.url,
                                                'step_id': video.step_id,
                                                'duration': video.duration,
                                                'learning_point': video.learning_point,
                                                'last_updated': video.last_updated or datetime.now().isoformat(),
                                                'is_downloaded': video.is_downloaded
                                            }
                                            for video in lp.videos
                                        ]
                                    }
                                    for lp in course.learning_points
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
                json.dump(data, f, indent=2, ensure_ascii=False)

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
        """Get statistics about the content (NEW schema with LearnPoints)"""
        total_categories = len(self.categories)
        total_courses = sum(len(cat.courses) for cat in self.categories)

        # Count videos across all LearnPoints
        total_videos = sum(
            len(lp.videos)
            for cat in self.categories
            for course in cat.courses
            for lp in course.learning_points
        )

        downloaded_videos = sum(
            sum(1 for video in lp.videos if video.downloaded)
            for cat in self.categories
            for course in cat.courses
            for lp in course.learning_points
        )

        total_learning_points = sum(
            len(course.learning_points)
            for cat in self.categories
            for course in cat.courses
        )

        return {
            'categories': total_categories,
            'courses': total_courses,
            'learning_points': total_learning_points,
            'videos': total_videos,
            'downloaded': downloaded_videos,
            'pending_download': total_videos - downloaded_videos
        }

    def print_stats(self) -> None:
        """Print content statistics"""
        stats = self.get_stats()

        print("\n" + "="*60)
        print("📊 CONTENT STATISTICS")
        print("="*60)
        print(f"Language:          {self.language.upper()}")
        print(f"Categories:        {stats['categories']}")
        print(f"Courses:           {stats['courses']}")
        print(f"Learning Points:   {stats['learning_points']}")
        print(f"Videos:            {stats['videos']}")
        print(f"Downloaded:        {stats['downloaded']} / {stats['videos']}")
        print(f"Pending Download:  {stats['pending_download']}")
        print("="*60 + "\n")

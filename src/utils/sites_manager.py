"""
Sites Manager

Manages site URLs for different languages from sites.json
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


class SitesManager:
    """
    Manages GLOBIS Unlimited site URLs for multiple languages

    Reads from data/courses/sites.json:
    {
        "en": [
            "https://unlimited.globis.co.jp/en/learn-content",
            "https://unlimited.globis.co.jp/en/explore-content"
        ],
        "ja": [
            "https://unlimited.globis.co.jp/ja/learn-content",
            "https://unlimited.globis.co.jp/ja/explore-content"
        ]
    }
    """

    def __init__(self, sites_file: Path = Path("data/courses/sites.json")):
        """
        Initialize SitesManager

        Args:
            sites_file: Path to sites.json
        """
        self.sites_file = sites_file
        self.sites: Dict[str, List[str]] = {}
        self.load()

    def load(self) -> None:
        """Load sites from JSON file"""
        if not self.sites_file.exists():
            logger.error(f"❌ Sites file not found: {self.sites_file}")
            raise FileNotFoundError(f"Sites file not found: {self.sites_file}")

        try:
            with open(self.sites_file, 'r', encoding='utf-8') as f:
                self.sites = json.load(f)

            logger.info(f"✅ Loaded sites for {len(self.sites)} languages")
            for lang in self.sites.keys():
                logger.debug(f"   - {lang.upper()}: {len(self.sites[lang])} URLs")

        except Exception as e:
            logger.error(f"❌ Failed to load sites: {e}")
            raise

    def get_languages(self) -> List[str]:
        """
        Get list of available languages

        Returns:
            List of language codes (e.g., ['en', 'ja'])
        """
        return list(self.sites.keys())

    def get_urls(self, language: str) -> List[str]:
        """
        Get all URLs for a specific language

        Args:
            language: Language code (e.g., 'en', 'ja')

        Returns:
            List of URLs for the language

        Raises:
            ValueError: If language not found
        """
        if language not in self.sites:
            available = ', '.join(self.get_languages())
            raise ValueError(f"Language '{language}' not found. Available: {available}")

        return self.sites[language]

    def get_learn_content_url(self, language: str) -> str:
        """
        Get learn-content URL for a language

        Args:
            language: Language code (e.g., 'en', 'ja')

        Returns:
            Learn-content URL

        Example:
            "https://unlimited.globis.co.jp/en/learn-content"
        """
        urls = self.get_urls(language)

        for url in urls:
            if 'learn-content' in url:
                return url

        raise ValueError(f"No learn-content URL found for language '{language}'")

    def get_explore_content_url(self, language: str) -> str:
        """
        Get explore-content URL for a language

        Args:
            language: Language code (e.g., 'en', 'ja')

        Returns:
            Explore-content URL

        Example:
            "https://unlimited.globis.co.jp/en/explore-content"
        """
        urls = self.get_urls(language)

        for url in urls:
            if 'explore-content' in url:
                return url

        raise ValueError(f"No explore-content URL found for language '{language}'")

    def get_base_url(self, language: str) -> str:
        """
        Get base URL for a language (without path)

        Args:
            language: Language code (e.g., 'en', 'ja')

        Returns:
            Base URL

        Example:
            "https://unlimited.globis.co.jp/en"
        """
        urls = self.get_urls(language)

        if urls:
            # Extract base from first URL
            # e.g., "https://unlimited.globis.co.jp/en/learn-content"
            #    -> "https://unlimited.globis.co.jp/en"
            parts = urls[0].split('/')
            return '/'.join(parts[:5])  # https://domain/lang

        raise ValueError(f"No URLs found for language '{language}'")

    def get_content_file_path(
        self,
        language: str,
        content_type: str = "learn-content"
    ) -> Path:
        """
        Get path to JSON file for language and content type

        Args:
            language: Language code (e.g., 'en', 'ja')
            content_type: 'learn-content' or 'explore-content'

        Returns:
            Path to JSON file

        Example:
            Path("data/courses/en/learn-content.json")
        """
        if content_type not in ["learn-content", "explore-content"]:
            raise ValueError(f"Invalid content_type: {content_type}")

        return Path(f"data/courses/{language}/{content_type}.json")

    def ensure_language_dirs(self) -> None:
        """Create language directories if they don't exist"""
        for lang in self.get_languages():
            lang_dir = Path(f"data/courses/{lang}")
            lang_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"   ✅ Ensured directory: {lang_dir}")

    def __str__(self) -> str:
        """String representation"""
        langs = ', '.join(self.get_languages())
        return f"SitesManager({len(self.sites)} languages: {langs})"

    def __repr__(self) -> str:
        """Repr"""
        return self.__str__()


# Example usage
if __name__ == "__main__":
    # Configure logger for testing
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
        colorize=True,
    )

    # Test SitesManager
    logger.info("=" * 70)
    logger.info("Testing SitesManager")
    logger.info("=" * 70)

    manager = SitesManager()

    logger.info(f"\n{manager}")
    logger.info(f"\nLanguages: {manager.get_languages()}")

    for lang in manager.get_languages():
        logger.info(f"\n--- {lang.upper()} ---")
        logger.info(f"Learn URL: {manager.get_learn_content_url(lang)}")
        logger.info(f"Explore URL: {manager.get_explore_content_url(lang)}")
        logger.info(f"Base URL: {manager.get_base_url(lang)}")
        logger.info(f"Learn JSON: {manager.get_content_file_path(lang, 'learn-content')}")
        logger.info(f"Explore JSON: {manager.get_content_file_path(lang, 'explore-content')}")

    logger.info(f"\n{'=' * 70}")
    logger.info("Creating language directories...")
    manager.ensure_language_dirs()
    logger.info("✅ Done")

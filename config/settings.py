import os
from pathlib import Path
from typing import List, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

class VimeoCrawlerSettings(BaseSettings):
    """Enhanced settings with validation"""
    
    # Project paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CONFIG_DIR: Path = BASE_DIR / "config"
    
    # Browser settings
    BROWSER_HEADLESS: bool = False
    BROWSER_TIMEOUT: int = 45000
    PAGE_TIMEOUT: int = 20000
    BROWSER_ARGS: List[str] = [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security",
        "--enable-webgl",
        "--use-gl=swiftshader",
        "--disable-dev-shm-usage",
        "--disable-gpu-sandbox",
        "--no-first-run",
        "--disable-infobars"
    ]
    
    # Anti-detection settings
    STEALTH_MODE: str = "advanced"
    FINGERPRINT_SPOOFING: bool = True
    BEHAVIOR_SIMULATION: bool = True
    SESSION_PERSISTENCE: bool = True
    
    # Vimeo specific
    VIMEO_API_KEY: Optional[str] = None
    VIMEO_RATE_LIMIT: int = 10
    VIMEO_QUALITY_PREFERENCE: List[str] = ["720p", "1080p", "480p"]
    VIMEO_MAX_DURATION: int = 3600
    
    # Download configuration
    DOWNLOAD_PATH: Path = Path("./data/downloads")
    MAX_CONCURRENT_DOWNLOADS: int = 3
    CHUNK_SIZE: int = 1048576  # 1MB
    RETRY_ATTEMPTS: int = 3
    RESUME_DOWNLOADS: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Performance
    WORKER_THREADS: int = 4
    MEMORY_LIMIT: str = "2048MB"
    CPU_LIMIT: int = 80
    
    @validator('DOWNLOAD_PATH')
    def create_download_path(cls, v):
        Path(v).mkdir(parents=True, exist_ok=True)
        return Path(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

# Global settings instance
settings = VimeoCrawlerSettings()

"""
Browser Fingerprinting Protection Module

Provides realistic browser fingerprints to avoid detection.
Generates randomized but consistent fingerprints for each session.
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from faker import Faker

fake = Faker()


@dataclass
class BrowserFingerprint:
    """Container for browser fingerprint data"""
    user_agent: str
    viewport_width: int
    viewport_height: int
    timezone: str
    language: str
    platform: str
    vendor: str
    webgl_vendor: str
    webgl_renderer: str


class FingerprintGenerator:
    """Generate realistic browser fingerprints"""

    # Realistic user agents (recent Chrome versions)
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    # Common viewport sizes (realistic desktop resolutions)
    VIEWPORTS = [
        (1920, 1080),  # Full HD
        (1366, 768),   # Common laptop
        (1536, 864),   # HD+
        (1440, 900),   # MacBook
        (1680, 1050),  # WSXGA+
    ]

    # Common timezones
    TIMEZONES = [
        "America/New_York",
        "America/Los_Angeles",
        "America/Chicago",
        "Europe/London",
        "Europe/Paris",
        "Asia/Tokyo",
        "Asia/Singapore",
    ]

    # Language preferences
    LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.9,ja;q=0.8",
    ]

    # Platform strings
    PLATFORMS = {
        "Windows": "Win32",
        "macOS": "MacIntel",
        "Linux": "Linux x86_64",
    }

    # WebGL configurations
    WEBGL_CONFIGS = [
        {
            "vendor": "Google Inc. (Intel)",
            "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"
        },
        {
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)"
        },
        {
            "vendor": "Google Inc. (AMD)",
            "renderer": "ANGLE (AMD, AMD Radeon RX 5700 XT Direct3D11 vs_5_0 ps_5_0)"
        },
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize fingerprint generator

        Args:
            seed: Random seed for reproducible fingerprints
        """
        if seed:
            random.seed(seed)

    def generate(self) -> BrowserFingerprint:
        """
        Generate a complete browser fingerprint

        Returns:
            BrowserFingerprint object with all properties
        """
        # Select user agent
        user_agent = random.choice(self.USER_AGENTS)

        # Detect platform from user agent
        if "Windows" in user_agent:
            platform = self.PLATFORMS["Windows"]
        elif "Macintosh" in user_agent:
            platform = self.PLATFORMS["macOS"]
        else:
            platform = self.PLATFORMS["Linux"]

        # Select viewport
        viewport_width, viewport_height = random.choice(self.VIEWPORTS)

        # Select timezone (prefer US/Europe for English content)
        timezone = random.choice(self.TIMEZONES[:4])

        # Select language
        language = random.choice(self.LANGUAGES)

        # WebGL configuration
        webgl_config = random.choice(self.WEBGL_CONFIGS)

        return BrowserFingerprint(
            user_agent=user_agent,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            timezone=timezone,
            language=language,
            platform=platform,
            vendor="Google Inc.",
            webgl_vendor=webgl_config["vendor"],
            webgl_renderer=webgl_config["renderer"],
        )

    def generate_consistent(self, identifier: str) -> BrowserFingerprint:
        """
        Generate consistent fingerprint for a given identifier
        Useful for maintaining same fingerprint across sessions

        Args:
            identifier: Unique identifier (e.g., user ID, session ID)

        Returns:
            BrowserFingerprint that will be same for same identifier
        """
        # Use identifier as seed for consistency
        seed = hash(identifier) % (2**32)
        random.seed(seed)

        fingerprint = self.generate()

        # Reset random seed
        random.seed()

        return fingerprint


def apply_fingerprint_to_context(context, fingerprint: BrowserFingerprint):
    """
    Apply fingerprint to Playwright browser context

    Args:
        context: Playwright BrowserContext
        fingerprint: BrowserFingerprint to apply
    """
    # Set user agent
    context.set_extra_http_headers({
        "User-Agent": fingerprint.user_agent,
        "Accept-Language": fingerprint.language,
    })

    # Set viewport
    context.set_viewport_size({
        "width": fingerprint.viewport_width,
        "height": fingerprint.viewport_height
    })

    # Set geolocation and timezone via browser context options
    # Note: Some settings need to be set during context creation


def get_fingerprint_override_script(fingerprint: BrowserFingerprint) -> str:
    """
    Generate JavaScript to override browser properties
    Execute this script on every page load

    Args:
        fingerprint: BrowserFingerprint to apply

    Returns:
        JavaScript code as string
    """
    script = f"""
    // Override navigator properties
    Object.defineProperty(navigator, 'platform', {{
        get: () => '{fingerprint.platform}'
    }});

    Object.defineProperty(navigator, 'vendor', {{
        get: () => '{fingerprint.vendor}'
    }});

    Object.defineProperty(navigator, 'language', {{
        get: () => '{fingerprint.language.split(',')[0]}'
    }});

    Object.defineProperty(navigator, 'languages', {{
        get: () => ['{fingerprint.language.split(',')[0]}', 'en']
    }});

    // Override WebGL
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) {{
            return '{fingerprint.webgl_vendor}';
        }}
        if (parameter === 37446) {{
            return '{fingerprint.webgl_renderer}';
        }}
        return getParameter.apply(this, arguments);
    }};

    // Override timezone
    const originalDateTimeFormat = Intl.DateTimeFormat;
    Intl.DateTimeFormat = function(...args) {{
        if (args.length === 0) {{
            args[0] = undefined;
            args[1] = {{ timeZone: '{fingerprint.timezone}' }};
        }}
        return new originalDateTimeFormat(...args);
    }};

    // Override getTimezoneOffset
    Date.prototype.getTimezoneOffset = function() {{
        return 0; // UTC offset - adjust based on timezone
    }};

    console.log('🔒 Fingerprint protection applied');
    """

    return script


# Convenience instance
fingerprint_gen = FingerprintGenerator()

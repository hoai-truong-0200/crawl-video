"""
Stealth Mode Configuration

Provides stealth patches to bypass anti-bot detection.
Works in conjunction with playwright-stealth plugin.
"""

from typing import Dict, Any, Optional
from playwright.async_api import BrowserContext, Page


def get_stealth_init_scripts() -> list[str]:
    """
    Get JavaScript scripts to inject on page initialization
    These scripts patch browser automation indicators

    Returns:
        List of JavaScript code strings
    """
    scripts = []

    # 1. Remove webdriver flag
    scripts.append("""
    // Remove navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    """)

    # 2. Patch Chrome runtime
    scripts.append("""
    // Remove chrome.runtime
    if (window.chrome) {
        // Keep chrome object but remove automation indicators
        delete window.chrome.runtime;
    }
    """)

    # 3. Patch permissions API
    scripts.append("""
    // Override permissions query
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    """)

    # 4. Patch plugin array
    scripts.append("""
    // Add fake plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {
                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "Chrome PDF Plugin"
            },
            {
                0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                description: "Portable Document Format",
                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                length: 1,
                name: "Chrome PDF Viewer"
            },
            {
                0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                description: "",
                filename: "internal-nacl-plugin",
                length: 2,
                name: "Native Client"
            }
        ]
    });
    """)

    # 5. Patch automation-controlled flag
    scripts.append("""
    // Remove automation controlled
    delete Object.getPrototypeOf(navigator).webdriver;
    """)

    # 6. Add realistic screen properties
    scripts.append("""
    // Screen properties
    Object.defineProperty(screen, 'availTop', { get: () => 0 });
    Object.defineProperty(screen, 'availLeft', { get: () => 0 });
    """)

    # 7. Patch iframe contentWindow
    scripts.append("""
    // Patch iframe detection
    const originalCreateElement = document.createElement;
    document.createElement = function(...args) {
        const element = originalCreateElement.apply(this, args);
        if (args[0] === 'iframe') {
            try {
                const originalContentWindow = Object.getOwnPropertyDescriptor(
                    HTMLIFrameElement.prototype,
                    'contentWindow'
                ).get;

                Object.defineProperty(element, 'contentWindow', {
                    get: function() {
                        const win = originalContentWindow.call(this);
                        if (win) {
                            try {
                                win.navigator.webdriver = undefined;
                            } catch (e) {}
                        }
                        return win;
                    }
                });
            } catch (e) {}
        }
        return element;
    };
    """)

    # 8. Add realistic navigator properties
    scripts.append("""
    // Add realistic properties
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8
    });

    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8
    });

    Object.defineProperty(navigator, 'maxTouchPoints', {
        get: () => 0
    });
    """)

    # 9. Canvas fingerprint noise
    scripts.append("""
    // Add slight noise to canvas fingerprinting
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(...args) {
        // Add minimal noise - too much noise is also suspicious
        const context = this.getContext('2d');
        if (context) {
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 3) - 1;
            }
            context.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.apply(this, args);
    };
    """)

    # 10. Mouse movement tracking prevention
    scripts.append("""
    // Add realistic mouse entropy
    let mouseEntropyCounter = 0;
    document.addEventListener('mousemove', () => {
        mouseEntropyCounter++;
    }, true);

    Object.defineProperty(navigator, 'mouseEntropy', {
        get: () => mouseEntropyCounter
    });
    """)

    return scripts


def get_playwright_stealth_config() -> Dict[str, Any]:
    """
    Configuration for playwright-stealth plugin

    Returns:
        Configuration dictionary
    """
    return {
        "chrome_runtime": True,
        "navigator_vendor": True,
        "navigator_webdriver": True,
        "navigator_plugins": True,
        "navigator_permissions": True,
        "navigator_languages": True,
        "webgl_vendor": True,
        "navigator_hardware_concurrency": True,
    }


async def apply_stealth_to_context(context: BrowserContext) -> None:
    """
    Apply stealth configurations to browser context

    Args:
        context: Playwright BrowserContext
    """
    # Add init scripts
    for script in get_stealth_init_scripts():
        await context.add_init_script(script)

    # Set extra HTTP headers to look more realistic
    await context.set_extra_http_headers({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    })


async def apply_stealth_to_page(page: Page) -> None:
    """
    Apply additional stealth measures to a specific page

    Args:
        page: Playwright Page
    """
    # Mask automation indicators in page context
    await page.add_init_script("""
    // Final webdriver cleanup
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false
    });

    // Add window.chrome if missing (common in real Chrome)
    if (!window.chrome) {
        window.chrome = {
            app: {},
            runtime: {},
        };
    }

    console.log('🥷 Stealth mode active');
    """)


def get_browser_launch_args() -> list[str]:
    """
    Get command-line arguments for launching browser in stealth mode

    Returns:
        List of browser arguments
    """
    return [
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-infobars",
        "--window-size=1920,1080",
        "--disable-features=TranslateUI",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-client-side-phishing-detection",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-domain-reliability",
        "--disable-hang-monitor",
        "--disable-ipc-flooding-protection",
        "--disable-notifications",
        "--disable-offer-store-unmasked-wallet-cards",
        "--disable-popup-blocking",
        "--disable-print-preview",
        "--disable-prompt-on-repost",
        "--disable-renderer-backgrounding",
        "--disable-sync",
        "--metrics-recording-only",
        "--mute-audio",
        "--no-pings",
        "--password-store=basic",
        "--force-color-profile=srgb",
    ]


def get_context_options(headless: bool = False) -> Dict[str, Any]:
    """
    Get browser context options for stealth mode

    Args:
        headless: Whether to run in headless mode

    Returns:
        Context options dictionary
    """
    return {
        "ignore_https_errors": True,
        "java_script_enabled": True,
        "bypass_csp": True,
        "screen": {
            "width": 1920,
            "height": 1080
        },
        "viewport": {
            "width": 1920,
            "height": 1080
        },
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
        "default_browser_type": "chromium",
    }

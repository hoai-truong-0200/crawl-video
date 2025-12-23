#!/usr/bin/env python3
"""
Verification script to check if all dependencies are installed correctly.
Run this after installing requirements.txt
"""

import sys
from importlib import import_module

def check_python_version():
    """Check Python version is 3.10+"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.10+)")
        return False

def check_package(package_name, import_name=None):
    """Check if a package can be imported"""
    if import_name is None:
        import_name = package_name

    try:
        module = import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"   ✅ {package_name} ({version})")
        return True
    except ImportError as e:
        print(f"   ❌ {package_name} - NOT INSTALLED")
        return False

def check_system_commands():
    """Check system commands availability"""
    import subprocess

    commands = {
        'ffmpeg': ['ffmpeg', '-version'],
        'ffprobe': ['ffprobe', '-version'],
    }

    results = {}
    for name, cmd in commands.items():
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Extract version from first line
                version_line = result.stdout.split('\n')[0]
                print(f"   ✅ {name} - {version_line}")
                results[name] = True
            else:
                print(f"   ❌ {name} - Command failed")
                results[name] = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"   ❌ {name} - NOT FOUND")
            results[name] = False

    return all(results.values())

def main():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("🔧 SETUP VERIFICATION - Crawl Video Project")
    print("="*60 + "\n")

    all_passed = True

    # Check Python version
    if not check_python_version():
        all_passed = False

    print("\n🔍 Checking core dependencies...")
    core_packages = [
        ('playwright', 'playwright'),
        ('playwright-stealth', 'playwright_stealth'),
        ('yt-dlp', 'yt_dlp'),
    ]

    for package, import_name in core_packages:
        if not check_package(package, import_name):
            all_passed = False

    print("\n🔍 Checking Google Drive API packages...")
    google_packages = [
        ('google-auth', 'google.auth'),
        ('google-auth-oauthlib', 'google_auth_oauthlib'),
        ('google-api-python-client', 'googleapiclient'),
    ]

    for package, import_name in google_packages:
        if not check_package(package, import_name):
            all_passed = False

    print("\n🔍 Checking utility packages...")
    utility_packages = [
        ('httpx', 'httpx'),
        ('pydantic', 'pydantic'),
        ('loguru', 'loguru'),
        ('tqdm', 'tqdm'),
        ('faker', 'faker'),
        ('numpy', 'numpy'),
        ('beautifulsoup4', 'bs4'),
        ('lxml', 'lxml'),
        ('tenacity', 'tenacity'),
        ('python-dotenv', 'dotenv'),
    ]

    for package, import_name in utility_packages:
        if not check_package(package, import_name):
            all_passed = False

    print("\n🔍 Checking system commands...")
    if not check_system_commands():
        all_passed = False

    print("\n🔍 Checking project structure...")
    from pathlib import Path

    required_dirs = [
        'src',
        'src/browser',
        'src/crawler',
        'src/downloader',
        'src/uploader',
        'src/utils',
        'data/courses',
        'downloads',
    ]

    base_dir = Path(__file__).parent
    structure_ok = True

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ⚠️  {dir_path}/ - Will be created on first run")

    # Don't fail if directories don't exist, they'll be created automatically
    # structure_ok is always True now

    print("\n🔍 Checking configuration files...")
    config_files = [
        'requirements.txt',
        'README.md',
        'run_browser.py',
        'verify_setup.py',
    ]

    config_ok = True
    for file_name in config_files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} - NOT FOUND")
            config_ok = False

    if not config_ok:
        all_passed = False

    # Optional files (don't fail if missing)
    optional_files = [
        ('.env.example', 'Template for environment configuration'),
        ('.env', 'Environment configuration (will use defaults if missing)'),
    ]

    for file_name, description in optional_files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ℹ️  {file_name} - Optional ({description})")

    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\nYour environment is ready to use!")
        print("\nQuick start:")
        print("1. Run: python3 run_browser.py <mode>")
        print("")
        print("Available modes:")
        print("  - sites      : Parse initial categories/series")
        print("  - categories : Crawl category details")
        print("  - series     : Crawl series details")
        print("  - courses    : Crawl course details and videos")
        print("  - content    : Extract course content (overview + transcript)")
        print("  - downloads  : Download videos")
        print("")
        print("Example: python3 run_browser.py content en")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease fix the issues above and run this script again.")
        print("Or run: ./quick_install.sh")
    print("="*60 + "\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

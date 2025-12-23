"""
Chrome Profile Manager

Module to manage Chrome profile copying with interactive profile selection
"""

import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger


class ChromeProfileManager:
    """Manager for Chrome profile operations"""

    def __init__(self, dest_profile: Path = Path("data/chrome_profile")):
        """
        Initialize profile manager

        Args:
            dest_profile: Destination path for copied profile
        """
        self.dest_profile = dest_profile

        # Detect Chrome directory based on OS
        self.chrome_dirs = self._get_chrome_directories()

    def _get_chrome_directories(self) -> List[Path]:
        """
        Get Chrome profile directories based on OS

        Returns:
            List of possible Chrome profile directories
        """
        home = Path.home()

        # Common Chrome profile locations
        possible_dirs = [
            # Linux
            home / ".config/google-chrome",
            home / ".config/chromium",
            # macOS
            home / "Library/Application Support/Google/Chrome",
            # Windows (if running under WSL)
            Path("/mnt/c/Users") / home.name / "AppData/Local/Google/Chrome/User Data",
        ]

        return [d for d in possible_dirs if d.exists()]

    def _get_profile_names_from_local_state(self, chrome_dir: Path) -> dict:
        """
        Read profile names from Local State file

        Args:
            chrome_dir: Chrome directory path

        Returns:
            Dict mapping profile folder name to display name
        """
        local_state_file = chrome_dir / "Local State"
        profile_names = {}

        if not local_state_file.exists():
            return profile_names

        try:
            import json
            with open(local_state_file, 'r', encoding='utf-8') as f:
                local_state = json.load(f)

            # Profile info is stored in profile.info_cache
            if 'profile' in local_state and 'info_cache' in local_state['profile']:
                info_cache = local_state['profile']['info_cache']

                # info_cache is a dict: {"Profile 1": {...}, "Default": {...}}
                for folder_name, profile_info in info_cache.items():
                    # Get the display name
                    if 'name' in profile_info:
                        profile_names[folder_name] = profile_info['name']
                    # Also try gaia_name for full name
                    elif 'gaia_name' in profile_info:
                        profile_names[folder_name] = profile_info['gaia_name']

        except Exception:
            pass

        return profile_names

    def list_available_profiles(self) -> List[Tuple[Path, str]]:
        """
        List all available Chrome profiles

        Returns:
            List of (profile_path, profile_name) tuples
        """
        profiles = []

        for chrome_dir in self.chrome_dirs:
            # First, get all profile names from Local State
            profile_names_map = self._get_profile_names_from_local_state(chrome_dir)
            for item in chrome_dir.iterdir():
                if not item.is_dir():
                    continue

                # Check if it's a profile directory
                if "Profile" in item.name or item.name == "Default":
                    folder_name = item.name

                    # Priority 1: Get display name from Local State (most reliable)
                    display_name = profile_names_map.get(folder_name)
                    email = None

                    # If not in Local State, try reading from Preferences
                    prefs_file = item / "Preferences"

                    # Only read from Preferences if we don't have name from Local State
                    if not display_name and prefs_file.exists():
                        try:
                            import json
                            with open(prefs_file, 'r', encoding='utf-8') as f:
                                prefs_data = json.load(f)

                                # Try to get profile name from multiple sources
                                if 'profile' in prefs_data:
                                    profile_info = prefs_data['profile']

                                    # Priority 1: profile.name (user-set name)
                                    if 'name' in profile_info and profile_info['name']:
                                        display_name = profile_info['name']

                                    # Priority 2: profile.user_name (may contain full name)
                                    if not display_name and 'user_name' in profile_info:
                                        display_name = profile_info['user_name']

                                    # Try to get email from profile.user_name (often is email)
                                    if 'user_name' in profile_info:
                                        user_name = profile_info['user_name']
                                        # Check if user_name is an email
                                        if '@' in str(user_name):
                                            email = user_name

                                # Try to get email and full name from account_info
                                if 'account_info' in prefs_data:
                                    accounts = prefs_data['account_info']
                                    if accounts and len(accounts) > 0:
                                        first_account = list(accounts.values())[0]

                                        # Get email
                                        if 'email' in first_account:
                                            email = first_account['email']

                                        # If no display_name yet, try full_name from account
                                        if not display_name and 'full_name' in first_account:
                                            display_name = first_account['full_name']

                                        # Or try given_name
                                        if not display_name and 'given_name' in first_account:
                                            display_name = first_account['given_name']

                                # Fallback: Try to get gaia name (Google account name)
                                if 'gaia_name' in prefs_data.get('profile', {}):
                                    gaia_name = prefs_data['profile']['gaia_name']
                                    if not display_name:
                                        display_name = gaia_name
                                    # gaia_name might be full name like "Jester Jz"

                                # Try to get email from signin section
                                if not email and 'account_tracker_service_last_update' in prefs_data:
                                    # Sometimes email is stored here
                                    pass

                                # Debug: Log what we found (can be removed later)
                                # print(f"DEBUG {folder_name}: display_name={display_name}, email={email}")

                        except Exception as e:
                            # Silently ignore errors
                            pass

                    # Build display name
                    if display_name and email:
                        profile_name = f"{folder_name}: {display_name} ({email})"
                    elif display_name:
                        profile_name = f"{folder_name}: {display_name}"
                    elif email:
                        profile_name = f"{folder_name} ({email})"
                    else:
                        profile_name = folder_name

                    profiles.append((item, profile_name))

        return profiles

    def select_profile_interactive(self) -> Optional[Path]:
        """
        Interactively select a Chrome profile

        Returns:
            Selected profile path or None if cancelled
        """
        profiles = self.list_available_profiles()

        if not profiles:
            logger.error("❌ No Chrome profiles found")
            return None

        print("\n" + "=" * 70)
        print("📂 Available Chrome Profiles")
        print("=" * 70)

        for idx, (profile_path, profile_name) in enumerate(profiles, 1):
            # Get profile size
            try:
                import subprocess
                result = subprocess.run(
                    ["du", "-sh", str(profile_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                size = result.stdout.split()[0] if result.returncode == 0 else "unknown"
            except Exception:
                size = "unknown"

            # Parse profile_name to display nicely
            parts = profile_name.split(": ", 1)
            if len(parts) == 2:
                folder, rest = parts
                print(f"\n[{idx}] {rest}")
                print(f"    Profile: {folder}")
            else:
                print(f"\n[{idx}] {profile_name}")

            print(f"    Path: {profile_path}")
            print(f"    Size: {size}")

        print("\n[0] Cancel")
        print("=" * 70)

        # Get user input
        while True:
            try:
                choice = input("\nSelect profile number: ").strip()

                if not choice:
                    continue

                choice_num = int(choice)

                if choice_num == 0:
                    logger.info("❌ Profile selection cancelled")
                    return None

                if 1 <= choice_num <= len(profiles):
                    selected_profile = profiles[choice_num - 1][0]
                    selected_name = profiles[choice_num - 1][1]

                    print(f"\n✅ Selected: {selected_name}")
                    return selected_profile
                else:
                    print(f"❌ Invalid choice. Please enter 0-{len(profiles)}")

            except ValueError:
                print("❌ Please enter a number")
            except KeyboardInterrupt:
                print("\n\n❌ Selection cancelled")
                return None

    def copy_profile(self, source_profile: Path, force: bool = False) -> bool:
        """
        Copy Chrome profile to destination

        Args:
            source_profile: Source profile path
            force: Force overwrite if destination exists

        Returns:
            True if successful, False otherwise
        """
        # Check if destination exists
        if self.dest_profile.exists():
            if not force:
                logger.warning(f"⚠️  Destination profile already exists: {self.dest_profile}")
                response = input("Overwrite? (y/N): ").strip().lower()
                if response != 'y':
                    logger.info("❌ Copy cancelled")
                    return False

            # Remove existing profile
            logger.info("🗑️  Removing existing profile...")
            shutil.rmtree(self.dest_profile)

        # Validate source
        if not source_profile.exists():
            logger.error(f"❌ Source profile not found: {source_profile}")
            return False

        logger.info(f"\n📋 Copying Chrome profile...")
        logger.info(f"   From: {source_profile}")
        logger.info(f"   To:   {self.dest_profile}")

        try:
            # Get profile size
            import subprocess
            result = subprocess.run(
                ["du", "-sh", str(source_profile)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                size = result.stdout.split()[0]
                logger.info(f"   Size: {size}")

            # Copy profile (this includes cookies, sessions, history, etc.)
            logger.info("📦 Copying files...")
            shutil.copytree(
                source_profile,
                self.dest_profile,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(
                    # Ignore cache and temp files to reduce size
                    "Cache",
                    "Code Cache",
                    "GPUCache",
                    "Service Worker",
                    "*.tmp",
                    "*.log"
                )
            )

            logger.info("✅ Chrome profile copied successfully")
            logger.info("\nProfile includes:")
            logger.info("  ✅ Cookies")
            logger.info("  ✅ Sessions")
            logger.info("  ✅ Login data")
            logger.info("  ✅ Bookmarks")
            logger.info("  ✅ Extensions")
            logger.info("  ✅ History")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to copy profile: {e}")
            return False

    def get_profile_info(self, profile_path: Path) -> dict:
        """
        Get information about a Chrome profile

        Args:
            profile_path: Path to Chrome profile

        Returns:
            Dictionary with profile information
        """
        info = {
            'path': str(profile_path),
            'exists': profile_path.exists(),
            'cookies': False,
            'sessions': False,
        }

        if not profile_path.exists():
            return info

        # Check for cookies
        cookies_file = profile_path / "Cookies"
        network_cookies = profile_path / "Network" / "Cookies"

        info['cookies'] = cookies_file.exists() or network_cookies.exists()

        # Check for sessions
        sessions_dir = profile_path / "Sessions"
        info['sessions'] = sessions_dir.exists()

        return info

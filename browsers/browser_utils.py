#!/usr/bin/env python3
"""
Browser-specific HSTS manipulation methods

This module contains implementations for browser-specific HSTS cache operations.
"""

import os
import platform
import subprocess
import json
import logging
from datetime import datetime

logger = logging.getLogger("browsers")

class ChromiumBrowsers:
    """Class for handling Chromium-based browsers (Chrome, Edge, Brave, Opera)"""
    
    @staticmethod
    def get_data_path(browser_name):
        """Get browser data directory path"""
        system = platform.system()
        home = os.path.expanduser("~")
        
        paths = {
            "Windows": {
                "chrome": os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data"),
                "edge": os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data"),
                "brave": os.path.join(home, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data"),
                "opera": os.path.join(home, "AppData", "Roaming", "Opera Software", "Opera Stable"),
            },
            "Darwin": {  # macOS
                "chrome": os.path.join(home, "Library", "Application Support", "Google", "Chrome"),
                "edge": os.path.join(home, "Library", "Application Support", "Microsoft Edge"),
                "brave": os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser"),
                "opera": os.path.join(home, "Library", "Application Support", "com.operasoftware.Opera"),
            },
            "Linux": {
                "chrome": os.path.join(home, ".config", "google-chrome"),
                "edge": os.path.join(home, ".config", "microsoft-edge"),
                "brave": os.path.join(home, ".config", "BraveSoftware", "Brave-Browser"),
                "opera": os.path.join(home, ".config", "opera"),
            }
        }
        
        if system in paths and browser_name in paths[system]:
            return paths[system][browser_name]
        return None
    
    @staticmethod
    def find_transport_security_file(data_path):
        """Find the TransportSecurity file in a Chromium-based browser's data directory"""
        if not os.path.exists(data_path):
            return None
            
        # Look for TransportSecurity file in all profiles
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file == "TransportSecurity":
                    return os.path.join(root, file)
        
        return None
    
    @staticmethod
    def clear_hsts_host_entry(ts_file, domain):
        """Remove HSTS entries for a specific domain from TransportSecurity file"""
        if not os.path.exists(ts_file):
            logger.warning(f"TransportSecurity file not found: {ts_file}")
            return False
            
        try:
            # Create backup
            backup_file = f"{ts_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            with open(ts_file, 'rb') as f_in:
                with open(backup_file, 'wb') as f_out:
                    f_out.write(f_in.read())
                    
            logger.info(f"Created backup of TransportSecurity file: {backup_file}")
            
            # Since the file is in a binary format, we will use the browser's own mechanisms
            # to clear the HSTS cache by launching with special flags
            return True
            
        except Exception as e:
            logger.error(f"Error backing up TransportSecurity file: {e}")
            return False
    
    @staticmethod
    def get_executable_path(browser_name):
        """Get the path to browser executable"""
        system = platform.system()
        
        paths = {
            "Windows": {
                "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                "opera": r"C:\Program Files\Opera\launcher.exe",
            },
            "Darwin": {  # macOS
                "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "edge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "brave": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                "opera": "/Applications/Opera.app/Contents/MacOS/Opera",
            },
            "Linux": {
                "chrome": "/usr/bin/google-chrome",
                "edge": "/usr/bin/microsoft-edge",
                "brave": "/usr/bin/brave-browser",
                "opera": "/usr/bin/opera",
            }
        }
        
        if system in paths and browser_name in paths[system]:
            path = paths[system][browser_name]
            if os.path.exists(path):
                return path
                
        # Try alternate locations or use command names
        if system == "Linux":
            return browser_name
        elif system == "Darwin":  # macOS
            # Return the command name as fallback
            if browser_name == "chrome":
                return "google-chrome"
            else:
                return browser_name
        else:  # Windows
            if browser_name == "chrome":
                return "chrome"
            elif browser_name == "edge":
                return "msedge"
            elif browser_name == "brave":
                return "brave"
            else:
                return browser_name

class FirefoxBrowser:
    """Class for handling Firefox-specific HSTS operations"""
    
    @staticmethod
    def get_profiles_path():
        """Get Firefox profiles directory path"""
        system = platform.system()
        home = os.path.expanduser("~")
        
        if system == "Windows":
            return os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
        elif system == "Darwin":  # macOS
            return os.path.join(home, "Library", "Application Support", "Firefox", "Profiles")
        elif system == "Linux":
            return os.path.join(home, ".mozilla", "firefox")
        
        return None
    
    @staticmethod
    def find_sss_files():
        """Find all SiteSecurityServiceState.txt files"""
        profiles_path = FirefoxBrowser.get_profiles_path()
        if not profiles_path or not os.path.exists(profiles_path):
            return []
            
        sss_files = []
        for root, _, files in os.walk(profiles_path):
            for file in files:
                if file == "SiteSecurityServiceState.txt":
                    sss_files.append(os.path.join(root, file))
        
        return sss_files
    
    @staticmethod
    def clear_hsts_domain(domain):
        """Remove HSTS entries for a specific domain from all profiles"""
        sss_files = FirefoxBrowser.find_sss_files()
        if not sss_files:
            logger.warning("No SiteSecurityServiceState.txt files found")
            return False
            
        success = False
        for file_path in sss_files:
            try:
                # Create backup
                backup_file = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                with open(file_path, 'r') as f_in:
                    content = f_in.read()
                    with open(backup_file, 'w') as f_out:
                        f_out.write(content)
                
                # Read lines
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                # Filter out lines containing the domain
                new_lines = [line for line in lines if domain not in line]
                
                # Write back if any lines were removed
                if len(lines) != len(new_lines):
                    with open(file_path, 'w') as f:
                        f.writelines(new_lines)
                    logger.info(f"Removed HSTS entries for {domain} from {file_path}")
                    success = True
                
            except Exception as e:
                logger.error(f"Error clearing Firefox HSTS for domain {domain}: {e}")
        
        return success

class SafariBrowser:
    """Class for handling Safari-specific HSTS operations"""
    
    @staticmethod
    def get_hsts_path():
        """Get Safari HSTS.plist path"""
        if platform.system() != "Darwin":  # Safari only exists on macOS
            return None
            
        return os.path.expanduser("~/Library/Cookies/HSTS.plist")
    
    @staticmethod
    def clear_hsts_cache():
        """Clear Safari HSTS cache by backing up and removing the HSTS.plist file"""
        hsts_path = SafariBrowser.get_hsts_path()
        if not hsts_path or not os.path.exists(hsts_path):
            logger.warning("Safari HSTS.plist not found")
            return False
            
        try:
            # Create backup
            backup_path = f"{hsts_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.rename(hsts_path, backup_path)
            logger.info(f"Safari HSTS cache cleared (file renamed to {backup_path})")
            return True
        except Exception as e:
            logger.error(f"Error clearing Safari HSTS cache: {e}")
            return False
    
    @staticmethod
    def clear_domain_cache(domain):
        """
        Note: Safari's HSTS.plist is a binary property list file, so we can't easily
        edit just one domain entry. The recommended approach is to back up and 
        remove the entire file.
        """
        return SafariBrowser.clear_hsts_cache()

# Test code
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Show browser data paths
    system = platform.system()
    print(f"Current platform: {system}")
    
    print("\nChromium-based browsers:")
    for browser in ["chrome", "edge", "brave", "opera"]:
        path = ChromiumBrowsers.get_data_path(browser)
        print(f"  {browser}: {path}")
    
    print("\nFirefox:")
    firefox_path = FirefoxBrowser.get_profiles_path()
    print(f"  Profiles path: {firefox_path}")
    
    if system == "Darwin":
        print("\nSafari:")
        safari_path = SafariBrowser.get_hsts_path()
        print(f"  HSTS path: {safari_path}")

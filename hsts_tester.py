#!/usr/bin/env python3
"""
HSTS Bypass Testing Tool

This script provides utilities to test HSTS bypass methods across different browsers and platforms.
It includes functionality to clear browser-specific HSTS caches and verify bypass attempts.
"""

import platform
import subprocess
import requests
import os
import sys
import json
import logging
from datetime import datetime
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hsts_testing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("hsts_tester")

class HSTSTester:
    def __init__(self, target_domain=None):
        """Initialize the HSTS tester with a target domain"""
        self.system = platform.system()
        self.target_domain = target_domain
        self.results = {}
        
        if not self.target_domain:
            logger.warning("No target domain provided. Use set_target_domain() to set one.")
    
    def set_target_domain(self, domain):
        """Set the target domain for testing"""
        self.target_domain = domain
        logger.info(f"Target domain set to: {domain}")
        
        # Validate domain format
        try:
            parsed = urlparse(domain)
            if not parsed.netloc:
                parsed = urlparse(f"https://{domain}")
            if not parsed.netloc:
                logger.error(f"Invalid domain format: {domain}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error parsing domain: {e}")
            return False
    
    def check_hsts_status(self, domain=None):
        """Check if a domain has HSTS enabled"""
        target = domain or self.target_domain
        if not target:
            logger.error("No domain specified for HSTS check")
            return None
            
        try:
            logger.info(f"Checking HSTS status for {target}")
            response = requests.get(f"https://{target}", allow_redirects=True)
            hsts_header = response.headers.get('Strict-Transport-Security')
            
            if hsts_header:
                logger.info(f"HSTS header found: {hsts_header}")
                return {
                    "enabled": True,
                    "header": hsts_header,
                    "max_age": self._parse_max_age(hsts_header),
                    "include_subdomains": "includeSubDomains" in hsts_header,
                    "preload": "preload" in hsts_header
                }
            else:
                logger.info("No HSTS header found")
                return {"enabled": False}
                
        except Exception as e:
            logger.error(f"Error checking HSTS status: {e}")
            return {"enabled": False, "error": str(e)}
    
    def _parse_max_age(self, hsts_header):
        """Parse max-age value from HSTS header"""
        try:
            if "max-age=" in hsts_header:
                max_age_part = hsts_header.split("max-age=")[1].split(";")[0]
                return int(max_age_part)
        except:
            pass
        return None
    
    def get_browser_data_path(self, browser_name):
        """Get the path to browser data based on platform and browser"""
        browser_name = browser_name.lower()
        system = self.system
        home = os.path.expanduser("~")
        
        paths = {
            "Windows": {
                "chrome": os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default"),
                "firefox": os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),
                "edge": os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default"),
                "opera": os.path.join(home, "AppData", "Roaming", "Opera Software", "Opera Stable"),
                "brave": os.path.join(home, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default"),
                "safari": None  # Not applicable on Windows
            },
            "Darwin": {  # macOS
                "chrome": os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Default"),
                "firefox": os.path.join(home, "Library", "Application Support", "Firefox", "Profiles"),
                "edge": os.path.join(home, "Library", "Application Support", "Microsoft Edge", "Default"),
                "opera": os.path.join(home, "Library", "Application Support", "com.operasoftware.Opera"),
                "brave": os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser", "Default"),
                "safari": os.path.join(home, "Library", "Safari")
            },
            "Linux": {
                "chrome": os.path.join(home, ".config", "google-chrome", "Default"),
                "firefox": os.path.join(home, ".mozilla", "firefox"),
                "edge": os.path.join(home, ".config", "microsoft-edge", "Default"),
                "opera": os.path.join(home, ".config", "opera"),
                "brave": os.path.join(home, ".config", "BraveSoftware", "Brave-Browser", "Default"),
                "safari": None  # Not applicable on Linux
            }
        }
        
        if system in paths and browser_name in paths[system]:
            path = paths[system][browser_name]
            if path and os.path.exists(path):
                logger.info(f"Found browser data path for {browser_name} on {system}: {path}")
                return path
        
        logger.warning(f"Could not find browser data path for {browser_name} on {system}")
        return None

    def clear_browser_hsts(self, browser_name):
        """Clear HSTS for specific browser"""
        browser_name = browser_name.lower()
        system = self.system
        result = {"browser": browser_name, "platform": system, "success": False}
        
        logger.info(f"Attempting to clear HSTS cache for {browser_name} on {system}")
        
        try:
            # Browser-specific methods
            if browser_name == "chrome":
                self._clear_chrome_hsts()
                result["success"] = True
            elif browser_name == "firefox":
                self._clear_firefox_hsts()
                result["success"] = True
            elif browser_name == "safari":
                if system == "Darwin":  # Safari only exists on macOS
                    self._clear_safari_hsts()
                    result["success"] = True
                else:
                    result["error"] = "Safari is not available on this platform"
            elif browser_name == "edge":
                self._clear_edge_hsts()
                result["success"] = True
            elif browser_name == "opera":
                self._clear_opera_hsts()
                result["success"] = True
            elif browser_name == "brave":
                self._clear_brave_hsts()
                result["success"] = True
            else:
                result["error"] = f"Unsupported browser: {browser_name}"
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error clearing {browser_name} HSTS cache: {e}")
        
        self.results[f"{browser_name}_{system}"] = result
        return result

    def _clear_chrome_hsts(self):
        """Clear Chrome HSTS cache"""
        if self.system == "Windows":
            # Close Chrome if running
            subprocess.run("taskkill /F /IM chrome.exe", shell=True, stderr=subprocess.DEVNULL)
            # Net command for Chrome
            subprocess.run(f'start chrome --host-resolver-rules="MAP {self.target_domain} 127.0.0.1" {self.target_domain}', shell=True)
        elif self.system == "Darwin":  # macOS
            # Close Chrome if running
            subprocess.run("pkill -f 'Google Chrome'", shell=True, stderr=subprocess.DEVNULL)
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                subprocess.run(f'"{chrome_path}" --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
            else:
                raise FileNotFoundError("Chrome application not found")
        elif self.system == "Linux":
            # Close Chrome if running
            subprocess.run("pkill -f chrome", shell=True, stderr=subprocess.DEVNULL)
            # Command for Linux
            subprocess.run(f'google-chrome --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
        
        logger.info("Chrome HSTS cache clearing attempted")

    def _clear_firefox_hsts(self):
        """Clear Firefox HSTS cache"""
        profile_path = self.get_browser_data_path("firefox")
        
        if not profile_path:
            raise FileNotFoundError("Firefox profile directory not found")
            
        if self.system == "Windows":
            # Close Firefox if running
            subprocess.run("taskkill /F /IM firefox.exe", shell=True, stderr=subprocess.DEVNULL)
            # Find SiteSecurityServiceState.txt files
            for root, _, files in os.walk(profile_path):
                for file in files:
                    if file == "SiteSecurityServiceState.txt":
                        file_path = os.path.join(root, file)
                        self._clean_firefox_sss_file(file_path)
        elif self.system == "Darwin":  # macOS
            # Close Firefox if running
            subprocess.run("pkill -f firefox", shell=True, stderr=subprocess.DEVNULL)
            # Find SiteSecurityServiceState.txt files
            for root, _, files in os.walk(profile_path):
                for file in files:
                    if file == "SiteSecurityServiceState.txt":
                        file_path = os.path.join(root, file)
                        self._clean_firefox_sss_file(file_path)
        elif self.system == "Linux":
            # Close Firefox if running
            subprocess.run("pkill -f firefox", shell=True, stderr=subprocess.DEVNULL)
            # Find SiteSecurityServiceState.txt files
            for root, _, files in os.walk(profile_path):
                for file in files:
                    if file == "SiteSecurityServiceState.txt":
                        file_path = os.path.join(root, file)
                        self._clean_firefox_sss_file(file_path)
        
        logger.info("Firefox HSTS cache clearing attempted")

    def _clean_firefox_sss_file(self, file_path):
        """Clean Firefox SiteSecurityServiceState.txt file"""
        if not self.target_domain:
            logger.warning("No target domain set, can't clean specific HSTS entries")
            return
            
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Filter out lines containing target domain
            new_lines = [line for line in lines if self.target_domain not in line]
            
            # Write back if any lines were removed
            if len(lines) != len(new_lines):
                with open(file_path, 'w') as f:
                    f.writelines(new_lines)
                logger.info(f"Removed HSTS entries for {self.target_domain} from {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning Firefox HSTS file: {e}")

    def _clear_safari_hsts(self):
        """Clear Safari HSTS cache"""
        if self.system != "Darwin":  # Safari only exists on macOS
            raise OSError("Safari is only available on macOS")
        
        # Close Safari if running
        subprocess.run("pkill -f Safari", shell=True, stderr=subprocess.DEVNULL)
        
        # Safari stores HSTS in a binary property list
        hsts_path = os.path.expanduser("~/Library/Cookies/HSTS.plist")
        
        if os.path.exists(hsts_path):
            backup_path = f"{hsts_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"Creating backup of Safari HSTS.plist: {backup_path}")
            os.rename(hsts_path, backup_path)
            logger.info("Safari HSTS cache cleared (file renamed)")
        else:
            logger.warning("Safari HSTS.plist not found")

    def _clear_edge_hsts(self):
        """Clear Edge HSTS cache - similar to Chrome as they share codebase"""
        if self.system == "Windows":
            # Close Edge if running
            subprocess.run("taskkill /F /IM msedge.exe", shell=True, stderr=subprocess.DEVNULL)
            # Launch with host rules
            subprocess.run(f'start msedge --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
        elif self.system == "Darwin":  # macOS
            # Close Edge if running
            subprocess.run("pkill -f 'Microsoft Edge'", shell=True, stderr=subprocess.DEVNULL)
            edge_path = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
            if os.path.exists(edge_path):
                subprocess.run(f'"{edge_path}" --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
            else:
                raise FileNotFoundError("Microsoft Edge application not found")
        elif self.system == "Linux":
            # Close Edge if running
            subprocess.run("pkill -f msedge", shell=True, stderr=subprocess.DEVNULL)
            # Command for Linux
            subprocess.run(f'microsoft-edge-stable --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
        
        logger.info("Microsoft Edge HSTS cache clearing attempted")

    def _clear_opera_hsts(self):
        """Clear Opera HSTS cache - similar to Chrome as they share codebase"""
        if self.system == "Windows":
            # Close Opera if running
            subprocess.run("taskkill /F /IM opera.exe", shell=True, stderr=subprocess.DEVNULL)
            # Launch with host rules
            subprocess.run(f'start opera --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
        elif self.system == "Darwin":  # macOS
            # Close Opera if running
            subprocess.run("pkill -f Opera", shell=True, stderr=subprocess.DEVNULL)
            opera_path = "/Applications/Opera.app/Contents/MacOS/Opera"
            if os.path.exists(opera_path):
                subprocess.run(f'"{opera_path}" --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
            else:
                raise FileNotFoundError("Opera application not found")
        elif self.system == "Linux":
            # Close Opera if running
            subprocess.run("pkill -f opera", shell=True, stderr=subprocess.DEVNULL)
            # Command for Linux
            subprocess.run(f'opera --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
        
        logger.info("Opera HSTS cache clearing attempted")

    def _clear_brave_hsts(self):
        """Clear Brave HSTS cache - similar to Chrome as they share codebase"""
        if self.system == "Windows":
            # Close Brave if running
            subprocess.run("taskkill /F /IM brave.exe", shell=True, stderr=subprocess.DEVNULL)
            # Launch with host rules
            subprocess.run(f'start brave --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
        elif self.system == "Darwin":  # macOS
            # Close Brave if running
            subprocess.run("pkill -f 'Brave Browser'", shell=True, stderr=subprocess.DEVNULL)
            brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            if os.path.exists(brave_path):
                subprocess.run(f'"{brave_path}" --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
            else:
                raise FileNotFoundError("Brave Browser application not found")
        elif self.system == "Linux":
            # Close Brave if running
            subprocess.run("pkill -f brave", shell=True, stderr=subprocess.DEVNULL)
            # Command for Linux
            subprocess.run(f'brave-browser --host-resolver-rules="MAP {self.target_domain} 127.0.0.1"', shell=True)
        
        logger.info("Brave HSTS cache clearing attempted")

    def test_hsts_bypass_methods(self):
        """Test various HSTS bypass methods"""
        if not self.target_domain:
            logger.error("No target domain set for testing")
            return {"error": "No target domain set"}
            
        results = {
            "domain": self.target_domain,
            "timestamp": datetime.now().isoformat(),
            "platform": self.system,
            "methods": {}
        }
        
        # Method 1: Direct HTTPS access (baseline)
        try:
            response = requests.get(f"https://{self.target_domain}", verify=True)
            results["methods"]["https_direct"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "hsts_present": "Strict-Transport-Security" in response.headers
            }
        except Exception as e:
            results["methods"]["https_direct"] = {"error": str(e)}
            
        # Method 2: HTTP access (should redirect if HSTS is working)
        try:
            response = requests.get(f"http://{self.target_domain}", allow_redirects=False)
            results["methods"]["http_direct"] = {
                "status_code": response.status_code,
                "is_redirect": 300 <= response.status_code < 400,
                "location": response.headers.get("Location", "")
            }
        except Exception as e:
            results["methods"]["http_direct"] = {"error": str(e)}
            
        # Method 3: Subdomain access (if not includeSubdomains)
        try:
            subdomain = f"test.{self.target_domain}"
            response = requests.get(f"http://{subdomain}", allow_redirects=False, timeout=5)
            results["methods"]["subdomain"] = {
                "status_code": response.status_code,
                "is_redirect": 300 <= response.status_code < 400,
                "location": response.headers.get("Location", "")
            }
        except Exception as e:
            results["methods"]["subdomain"] = {"error": str(e)}
            
        # Method 4: Via localhost/IP
        try:
            # Add entry to hosts file would be needed for complete test
            results["methods"]["localhost"] = {
                "note": "Manual modification of hosts file required"
            }
        except Exception as e:
            results["methods"]["localhost"] = {"error": str(e)}
            
        # Method 5: Disable SSL verification
        try:
            response = requests.get(f"https://{self.target_domain}", verify=False)
            results["methods"]["disable_ssl_verify"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "hsts_present": "Strict-Transport-Security" in response.headers
            }
        except Exception as e:
            results["methods"]["disable_ssl_verify"] = {"error": str(e)}
        
        logger.info("HSTS bypass methods tested")
        return results
        
    def test_all_browsers(self):
        """Test HSTS clearing across all supported browsers"""
        browsers = ["chrome", "firefox", "safari", "edge", "opera", "brave"]
        results = {}
        
        for browser in browsers:
            try:
                if browser == "safari" and self.system != "Darwin":
                    results[browser] = {"status": "skipped", "reason": "Not available on this platform"}
                    continue
                    
                logger.info(f"Testing HSTS clearing for {browser}")
                result = self.clear_browser_hsts(browser)
                results[browser] = result
            except Exception as e:
                logger.error(f"Error testing {browser}: {e}")
                results[browser] = {"status": "error", "error": str(e)}
        
        return results
        
    def save_results(self, filename=None):
        """Save test results to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hsts_test_results_{timestamp}.json"
            
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"Results saved to {filename}")
        return filename
        
def test_hsts_bypass(domain):
    """Main testing function"""
    tester = HSTSTester(domain)
    
    # Check initial HSTS status
    initial_status = tester.check_hsts_status()
    print(f"Initial HSTS status for {domain}: {json.dumps(initial_status, indent=2)}")
    
    # Test all browsers on current platform
    browser_results = tester.test_all_browsers()
    print(f"Browser HSTS clearing results: {json.dumps(browser_results, indent=2)}")
    
    # Test bypass methods
    bypass_results = tester.test_hsts_bypass_methods()
    print(f"HSTS bypass testing results: {json.dumps(bypass_results, indent=2)}")
    
    # Save all results
    tester.results["initial_status"] = initial_status
    tester.results["bypass_results"] = bypass_results
    
    results_file = tester.save_results()
    return f"Testing completed. Results saved to {results_file}"

def display_help():
    """Display help information"""
    print("""
HSTS Bypass Testing Tool
========================

Usage:
    python hsts_tester.py <domain>
    
Examples:
    python hsts_tester.py example.com
    
Note: 
    This tool should only be used on domains you own or have permission to test.
    Using this tool without permission may violate legal terms.
    """)

# Run the test
if __name__ == "__main__":
    if len(sys.argv) < 2 or "--help" in sys.argv or "-h" in sys.argv:
        display_help()
    else:
        target_domain = sys.argv[1]
        print(f"Starting HSTS bypass testing for domain: {target_domain}")
        result = test_hsts_bypass(target_domain)
        print(result)

#!/usr/bin/env python3
"""
Comprehensive HSTS Bypass Testing Platform

This script combines browser-based HSTS cache clearing with
MITM attack techniques for thorough HSTS bypass testing.
"""

import os
import sys
import argparse
import platform
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hsts_comprehensive.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("hsts_comprehensive")

# Try to import our modules, provide useful error if not found
try:
    # Import browser-based HSTS tester
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from hsts_tester import HSTSTester
    
    # Only import Kali Linux tools if on Linux
    if platform.system() == "Linux":
        try:
            from hsts_bypass_kali import HSTSBypassTester
            KALI_AVAILABLE = True
        except ImportError:
            logger.warning("Kali Linux HSTS bypass module not available")
            KALI_AVAILABLE = False
    else:
        KALI_AVAILABLE = False
        
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    print("ERROR: Required modules not found. Make sure you're running from the project directory.")
    sys.exit(1)

class ComprehensiveHSTSTester:
    """Combines browser and MITM-based approaches for HSTS testing"""
    
    def __init__(self, domain, browsers=None):
        """
        Initialize the comprehensive tester
        
        Args:
            domain (str): Target domain to test
            browsers (list): List of browsers to test, or None for all
        """
        self.domain = domain
        self.browsers = browsers or ["chrome", "firefox", "safari", "edge", "opera", "brave"]
        self.results = {}
        self.timestamp = datetime.now().isoformat()
        
        # Initialize browser-based tester
        self.browser_tester = HSTSTester(domain)
        
        # Initialize Kali-based tester if available
        self.kali_tester = None
        if KALI_AVAILABLE and platform.system() == "Linux":
            # These would need to be set by the user through command arguments
            self.kali_tester_ready = False
        else:
            self.kali_tester_ready = False
            
        logger.info(f"Comprehensive HSTS tester initialized for domain: {domain}")
    
    def setup_kali_tester(self, interface, gateway_ip, victim_ip=None, all_targets=False):
        """Set up the Kali Linux HSTS bypass tester"""
        if not KALI_AVAILABLE:
            logger.error("Kali Linux HSTS bypass module not available")
            return False
            
        try:
            self.kali_tester = HSTSBypassTester(
                interface=interface,
                gateway_ip=gateway_ip,
                victim_ip=victim_ip,
                all_targets=all_targets
            )
            self.kali_tester_ready = True
            logger.info("Kali Linux HSTS bypass tester set up successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to set up Kali Linux HSTS bypass tester: {e}")
            self.kali_tester_ready = False
            return False
    
    def check_hsts_status(self):
        """Check the HSTS status of the target domain"""
        try:
            status = self.browser_tester.check_hsts_status()
            self.results["hsts_status"] = status
            return status
        except Exception as e:
            logger.error(f"Failed to check HSTS status: {e}")
            self.results["hsts_status"] = {"error": str(e)}
            return {"error": str(e)}
    
    def test_browser_clearing(self):
        """Test browser-based HSTS cache clearing"""
        try:
            browser_results = {}
            
            for browser in self.browsers:
                if browser == "safari" and platform.system() != "Darwin":
                    browser_results[browser] = {
                        "status": "skipped", 
                        "reason": "Safari not available on this platform"
                    }
                    continue
                    
                logger.info(f"Testing HSTS clearing for {browser}")
                result = self.browser_tester.clear_browser_hsts(browser)
                browser_results[browser] = result
                
            self.results["browser_clearing"] = browser_results
            return browser_results
        except Exception as e:
            logger.error(f"Failed to test browser clearing: {e}")
            self.results["browser_clearing"] = {"error": str(e)}
            return {"error": str(e)}
    
    def test_bypass_methods(self):
        """Test browser-based HSTS bypass methods"""
        try:
            bypass_results = self.browser_tester.test_hsts_bypass_methods()
            self.results["bypass_methods"] = bypass_results
            return bypass_results
        except Exception as e:
            logger.error(f"Failed to test bypass methods: {e}")
            self.results["bypass_methods"] = {"error": str(e)}
            return {"error": str(e)}
    
    def test_kali_mitm(self, method="sslstrip"):
        """Test Kali Linux MITM-based HSTS bypass"""
        if not self.kali_tester_ready:
            msg = "Kali Linux HSTS bypass tester not set up"
            logger.error(msg)
            self.results["kali_mitm"] = {"error": msg}
            return {"error": msg}
            
        try:
            # Start the MITM attack
            logger.info(f"Starting Kali Linux MITM attack using {method}")
            
            # Record the attack configuration
            self.results["kali_mitm"] = {
                "method": method,
                "timestamp_start": datetime.now().isoformat(),
                "configuration": {
                    "interface": self.kali_tester.interface,
                    "gateway_ip": self.kali_tester.gateway_ip,
                    "victim_ip": self.kali_tester.victim_ip,
                    "all_targets": self.kali_tester.all_targets
                }
            }
            
            # Start the attack and return success status
            success = self.kali_tester.start_full_mitm_attack(method=method)
            
            return {
                "success": success,
                "method": method,
                "note": "Attack is running in the background. Call stop_kali_mitm() to stop."
            }
        except Exception as e:
            logger.error(f"Failed to start Kali Linux MITM attack: {e}")
            self.results["kali_mitm"]["error"] = str(e)
            return {"error": str(e)}
    
    def stop_kali_mitm(self):
        """Stop the Kali Linux MITM attack"""
        if not self.kali_tester_ready:
            return {"error": "Kali Linux HSTS bypass tester not set up"}
            
        try:
            logger.info("Stopping Kali Linux MITM attack")
            self.kali_tester.cleanup()
            
            # Update the results
            if "kali_mitm" in self.results:
                self.results["kali_mitm"]["timestamp_end"] = datetime.now().isoformat()
                self.results["kali_mitm"]["status"] = "stopped"
                
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to stop Kali Linux MITM attack: {e}")
            if "kali_mitm" in self.results:
                self.results["kali_mitm"]["error"] = str(e)
            return {"error": str(e)}
    
    def run_comprehensive_test(self, include_kali=False, kali_method="sslstrip"):
        """Run a comprehensive HSTS test including all methods"""
        results = {}
        
        # Step 1: Check HSTS status
        logger.info("Checking HSTS status")
        results["hsts_status"] = self.check_hsts_status()
        
        # Step 2: Test browser clearing
        logger.info("Testing browser-based HSTS clearing")
        results["browser_clearing"] = self.test_browser_clearing()
        
        # Step 3: Test bypass methods
        logger.info("Testing browser-based bypass methods")
        results["bypass_methods"] = self.test_bypass_methods()
        
        # Step 4: Test Kali Linux MITM if available and requested
        if include_kali and self.kali_tester_ready:
            logger.info(f"Testing Kali Linux MITM attack using {kali_method}")
            results["kali_mitm"] = self.test_kali_mitm(method=kali_method)
            
            # Wait for user to review results then stop
            input("\nKali Linux MITM attack is running. Press Enter to stop...")
            self.stop_kali_mitm()
        
        # Save the results
        self.results = results
        self.save_results()
        
        return results
    
    def save_results(self, filename=None):
        """Save test results to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hsts_comprehensive_results_{timestamp}.json"
            
        # Add metadata
        self.results["metadata"] = {
            "domain": self.domain,
            "timestamp": self.timestamp,
            "platform": platform.system(),
            "browsers_tested": self.browsers
        }
            
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"Results saved to {filename}")
        return filename

def main():
    """Main function to parse arguments and run the tests"""
    parser = argparse.ArgumentParser(
        description="Comprehensive HSTS Bypass Testing Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic browser-based testing
  python hsts_comprehensive.py example.com
  
  # Specify browsers to test
  python hsts_comprehensive.py example.com --browsers chrome firefox
  
  # Include Kali Linux MITM attack (Linux only)
  python hsts_comprehensive.py example.com --kali --interface eth0 --gateway 192.168.1.1 --target 192.168.1.100
        """
    )
    
    parser.add_argument('domain', help='Target domain to test')
    
    parser.add_argument('--browsers', nargs='+',
                      choices=['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave', 'all'],
                      default=['all'],
                      help='Browsers to test (default: all)')
    
    parser.add_argument('--kali', action='store_true',
                      help='Include Kali Linux MITM attack testing')
    
    parser.add_argument('--interface',
                      help='Network interface for Kali Linux testing (required with --kali)')
    
    parser.add_argument('--gateway',
                      help='Gateway IP address for Kali Linux testing (required with --kali)')
    
    parser.add_argument('--target',
                      help='Target victim IP address for Kali Linux testing')
    
    parser.add_argument('--all-targets', action='store_true',
                      help='Target all devices on the network for Kali Linux testing')
    
    parser.add_argument('--method', choices=['sslstrip', 'mitmproxy'],
                      default='sslstrip',
                      help='MITM method to use for Kali Linux testing')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate Kali arguments
    if args.kali:
        if platform.system() != "Linux":
            logger.error("Kali Linux MITM attack testing is only available on Linux")
            return 1
            
        if not args.interface or not args.gateway:
            logger.error("--interface and --gateway are required with --kali")
            return 1
            
        if not args.target and not args.all_targets:
            logger.error("Either --target or --all-targets is required with --kali")
            return 1
            
        if not KALI_AVAILABLE:
            logger.error("Kali Linux HSTS bypass module not available")
            return 1
            
        # Check if running as root for Kali testing
        if os.geteuid() != 0:
            logger.error("Kali Linux MITM attack testing requires root privileges")
            return 1
    
    # Process browser selection
    if 'all' in args.browsers:
        browsers = ["chrome", "firefox", "safari", "edge", "opera", "brave"]
    else:
        browsers = args.browsers
    
    # Initialize tester
    tester = ComprehensiveHSTSTester(args.domain, browsers)
    
    # Set up Kali tester if requested
    if args.kali:
        if not tester.setup_kali_tester(
            interface=args.interface,
            gateway_ip=args.gateway,
            victim_ip=args.target,
            all_targets=args.all_targets
        ):
            logger.error("Failed to set up Kali Linux HSTS bypass tester")
            return 1
    
    # Run the comprehensive test
    try:
        tester.run_comprehensive_test(include_kali=args.kali, kali_method=args.method)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        if args.kali and tester.kali_tester_ready:
            tester.stop_kali_mitm()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

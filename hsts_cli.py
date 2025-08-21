#!/usr/bin/env python3
"""
Command-line interface for HSTS Bypass Testing Tool
"""

import argparse
import sys
import logging
from hsts_tester import HSTSTester

def setup_logging(verbose=False):
    """Configure logging level based on verbosity"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("hsts_cli.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="HSTS Bypass Testing Tool - Test HTTP Strict Transport Security configurations"
    )
    
    # Required arguments
    parser.add_argument("domain", help="Target domain to test (e.g., example.com)")
    
    # Optional arguments
    parser.add_argument("-b", "--browser", 
                        choices=["chrome", "firefox", "safari", "edge", "opera", "brave", "all"],
                        default="all",
                        help="Specify browser to test (default: all)")
    parser.add_argument("-m", "--method",
                        choices=["clear", "domain", "localhost", "ssl", "all"],
                        default="all",
                        help="Specify bypass method to test (default: all)")
    parser.add_argument("-o", "--output",
                        help="Output file for results (default: auto-generated)")
    parser.add_argument("-v", "--verbose", 
                        action="store_true",
                        help="Enable verbose output")
    parser.add_argument("-c", "--check-only",
                        action="store_true",
                        help="Only check HSTS status without attempting bypass")
    parser.add_argument("--no-browser-restart",
                        action="store_true",
                        help="Do not close/restart browsers during testing")
                        
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger("hsts_cli")
    
    try:
        # Initialize tester
        tester = HSTSTester(args.domain)
        
        # Check initial HSTS status
        status = tester.check_hsts_status()
        print(f"\nHSTS Status for {args.domain}:")
        if status.get("enabled", False):
            print(f"✅ HSTS is enabled")
            print(f"   Max-Age: {status.get('max_age', 'Not specified')}")
            print(f"   Include Subdomains: {status.get('include_subdomains', False)}")
            print(f"   Preload: {status.get('preload', False)}")
        else:
            print(f"❌ HSTS is not enabled")
            if "error" in status:
                print(f"   Error: {status['error']}")
        
        # Stop if check-only mode
        if args.check_only:
            return
        
        # Test browser clearing
        if args.browser == "all":
            print("\nTesting all available browsers...")
            browser_results = tester.test_all_browsers()
        else:
            print(f"\nTesting {args.browser}...")
            result = tester.clear_browser_hsts(args.browser)
            browser_results = {args.browser: result}
            
        # Print results summary
        print("\nBrowser HSTS Clearing Results:")
        for browser, result in browser_results.items():
            success = result.get("success", False)
            status = "✅ Success" if success else "❌ Failed"
            error = f": {result.get('error')}" if "error" in result else ""
            print(f"   {browser}: {status}{error}")
        
        # Test bypass methods if requested
        if args.method != "none":
            print("\nTesting HSTS bypass methods...")
            bypass_results = tester.test_hsts_bypass_methods()
            
            # Print results summary
            print("\nHSTS Bypass Methods Results:")
            for method, result in bypass_results.get("methods", {}).items():
                if "error" in result:
                    print(f"   {method}: ❌ Error - {result['error']}")
                elif method == "https_direct":
                    hsts = "✅ Present" if result.get("hsts_present", False) else "❌ Not present"
                    print(f"   {method}: Status {result.get('status_code', 'unknown')} - HSTS header: {hsts}")
                elif method == "http_direct":
                    redirect = "✅ Redirects" if result.get("is_redirect", False) else "❌ Does not redirect"
                    print(f"   {method}: {redirect} - Status {result.get('status_code', 'unknown')}")
                else:
                    print(f"   {method}: Tested")
        
        # Save results
        output_file = args.output
        saved_file = tester.save_results(output_file)
        print(f"\nResults saved to: {saved_file}")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())

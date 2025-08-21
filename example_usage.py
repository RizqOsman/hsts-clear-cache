#!/usr/bin/env python3
"""
Example usage of the HSTS Tester library
"""

from hsts_tester import HSTSTester
import json
import sys

def example_usage(domain):
    """Example of using the HSTSTester class programmatically"""
    print(f"Running HSTS tests for {domain}")
    
    # Initialize the tester with target domain
    tester = HSTSTester(domain)
    
    # 1. Check current HSTS status
    print("\n1. Checking HSTS status...")
    status = tester.check_hsts_status()
    print(json.dumps(status, indent=2))
    
    # 2. Test a specific browser (Chrome in this example)
    print("\n2. Testing Chrome HSTS clearing...")
    chrome_result = tester.clear_browser_hsts("chrome")
    print(json.dumps(chrome_result, indent=2))
    
    # 3. Test bypass methods
    print("\n3. Testing bypass methods...")
    bypass_results = tester.test_hsts_bypass_methods()
    print(json.dumps(bypass_results, indent=2))
    
    # 4. Save results to file
    tester.results = {
        "domain": domain,
        "hsts_status": status,
        "chrome_result": chrome_result,
        "bypass_results": bypass_results
    }
    
    results_file = tester.save_results("example_results.json")
    print(f"\nResults saved to {results_file}")

if __name__ == "__main__":
    # Get domain from command line or use default
    domain = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    example_usage(domain)

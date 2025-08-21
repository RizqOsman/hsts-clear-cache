# HSTS Bypass Testing Tool

A comprehensive tool for testing HTTP Strict Transport Security (HSTS) bypass methods across multiple browsers and platforms.

## Overview

This tool helps security professionals test and verify HSTS configurations on domains they own or have permission to test. It provides functionality to:

1. Check HSTS status of domains
2. Clear browser-specific HSTS caches
3. Test various HSTS bypass methods
4. Document results across different platforms and browsers

## Legal Requirements

Before using this tool, ensure you:

- Own the target website or have explicit permission to test it
- Have proper authorization from all relevant stakeholders
- Follow ethical hacking guidelines
- Do not modify production environments without approval

## Supported Platforms

- Windows
- macOS
- Linux

## Supported Browsers

- Google Chrome
- Mozilla Firefox
- Safari (macOS only)
- Microsoft Edge
- Opera
- Brave Browser

## Installation

```bash
# Clone the repository
git clone https://github.com/RizqOsman/hsts-clear-cache.git
cd hsts-clear-cache

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python hsts_tester.py example.com
```

This will:
1. Check the current HSTS status of example.com
2. Attempt to clear HSTS cache for all available browsers
3. Test various bypass methods
4. Save the results to a JSON file

### Advanced Usage

For more granular control, you can use the HSTSTester class directly in your code:

```python
from hsts_tester import HSTSTester

# Initialize with a target domain
tester = HSTSTester("example.com")

# Check HSTS status
status = tester.check_hsts_status()
print(status)

# Clear HSTS for a specific browser
result = tester.clear_browser_hsts("chrome")
print(result)

# Test bypass methods
bypass_results = tester.test_hsts_bypass_methods()
print(bypass_results)

# Save results
tester.save_results("my_test_results.json")
```

## Testing Methods

The tool includes several HSTS bypass testing methods:

1. **Clear HSTS cache**: Directly clear browser-specific HSTS cache storage
2. **Domain variations**: Test with different subdomains or domain forms
3. **Local development**: Use localhost/127.0.0.1 access methods
4. **SSL verification**: Test with SSL verification disabled
5. **Proxy tools**: Documentation for using with proxy tools like Burp Suite

## Browser-Specific Notes

### Chrome, Edge, Brave, Opera (Chromium-based)
These browsers store HSTS information in a `TransportSecurity` file. The tool uses `--host-resolver-rules` flag to bypass HSTS for specific domains.

### Firefox
Firefox stores HSTS settings in `SiteSecurityServiceState.txt` files within profile directories. The tool directly modifies these files to remove domain entries.

### Safari
Safari stores HSTS data in a binary property list file (`HSTS.plist`). The tool backs up and removes this file to clear all HSTS entries.

## Interpreting Results

The tool generates a detailed JSON report with results from all tests. Key sections include:

- **initial_status**: The HSTS configuration of the target domain
- **browser_results**: Results of clearing HSTS cache for each browser
- **bypass_results**: Outcomes of different bypass methods

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is provided for educational and legitimate security testing purposes only. Improper use may violate laws or terms of service. Always obtain proper authorization before testing any system you don't own.

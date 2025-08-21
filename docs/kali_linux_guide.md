# HSTS Bypass and SSL/TLS MITM Attacks on Kali Linux

This guide explains how to conduct HSTS bypass and SSL/TLS MITM attacks using the `hsts_bypass_kali.py` script on Kali Linux. This is part of the HSTS Clear Cache project, focused on security testing of HSTS implementations.

⚠️ **IMPORTANT: Only use these techniques on systems you own or have explicit permission to test!** ⚠️

## Prerequisites

Ensure you have the following installed on your Kali Linux system:

```bash
# Update package list
sudo apt update

# Install required tools
sudo apt install -y \
  ettercap-text-only \
  bettercap \
  dsniff \
  sslstrip \
  mitmproxy \
  python3-pip

# Install Python dependencies
pip3 install -r requirements.txt
```

## Understanding the Techniques

This tool implements several methods for HSTS bypass and MITM attacks:

### 1. ARP Spoofing

ARP spoofing positions your machine between the target and gateway to intercept traffic:

- **arpspoof**: Simple ARP cache poisoning
- **ettercap**: More advanced ARP spoofing with filtering capabilities
- **bettercap**: Modern framework with extensive features

### 2. SSL/TLS Downgrade and MITM

- **SSLStrip**: Attempts to downgrade HTTPS connections to HTTP
- **MITMProxy**: Provides a complete HTTPS interception proxy

### 3. DNS Spoofing

- **dnsspoof**: Intercepts and modifies DNS queries
- **bettercap dns.spoof**: Advanced DNS spoofing module
- **ettercap dns filters**: Custom DNS manipulation

## Usage Guide

### Basic Attack (Single Target)

```bash
sudo python3 hsts_bypass_kali.py -i eth0 -g 192.168.1.1 -t 192.168.1.100
```

This command:
1. Uses the `eth0` interface
2. Sets the gateway IP to `192.168.1.1`
3. Targets the device at `192.168.1.100`
4. Uses SSLStrip by default

### Target All Network Devices

```bash
sudo python3 hsts_bypass_kali.py -i eth0 -g 192.168.1.1 -a
```

The `-a` flag enables targeting all devices on the network instead of a specific IP.

### Using MITMProxy Instead of SSLStrip

```bash
sudo python3 hsts_bypass_kali.py -i eth0 -g 192.168.1.1 -t 192.168.1.100 -m mitmproxy
```

This uses MITMProxy for more advanced interception capabilities.

## How HSTS Bypass Works

HSTS (HTTP Strict Transport Security) is designed to prevent downgrade attacks. This tool attempts to bypass HSTS using several techniques:

1. **First-time Visit Interception**: Catch users before they've visited a site with HSTS
2. **DNS Spoofing**: Redirect to similar domains not covered by the HSTS policy
3. **Subdomain Navigation**: Exploit situations where HSTS doesn't include subdomains

## Understanding the Results

When running the tool, look for:

1. **Captured Credentials**: Check the generated log files (`sslstrip_*.log`)
2. **HTTP Traffic**: Examine intercepted HTTP requests for sensitive information
3. **DNS Manipulation**: Observe DNS queries being redirected

## Advanced Techniques

### Custom Domain Targeting

You can modify the script to target specific domains by editing the DNS spoofing configuration.

### JavaScript Injection

The Ettercap filter can be extended to inject custom JavaScript into HTTP responses.

### Certificate Manipulation

MITMProxy allows custom certificate generation to make interception less obvious.

## Limitations

HSTS bypass techniques have limitations:

1. **HSTS Preloading**: Sites in browser preload lists are nearly impossible to bypass
2. **Certificate Pinning**: Some applications implement certificate pinning
3. **Modern Browsers**: Increasingly implement protections against these attacks

## Cleanup

The script automatically cleans up when you press Ctrl+C, including:

1. Killing all attack processes
2. Restoring iptables rules
3. Disabling IP forwarding
4. Removing temporary files

However, if the script crashes unexpectedly, you might need to run cleanup manually:

```bash
# Disable IP forwarding
echo 0 > /proc/sys/net/ipv4/ip_forward

# Reset iptables
iptables -t nat -F

# Kill running processes
pkill -f arpspoof
pkill -f ettercap
pkill -f bettercap
pkill -f sslstrip
pkill -f dnsspoof
pkill -f mitmproxy
```

## Ethical Considerations

Always adhere to:

1. **Legal Authorization**: Only test systems you own or have explicit permission for
2. **Scope Limitations**: Stay within authorized testing boundaries
3. **Data Protection**: Handle any captured data according to legal requirements
4. **Documentation**: Maintain detailed records of all testing activities

## References

- [SecureDebug: MITM Attacks and SSL Bypass](https://securedebug.com/mitm-attacks-and-ssl-bypass-in-kali-linux-17062025/)
- [OWASP: SSL/TLS Testing Guide](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/01-Testing_for_Weak_Transport_Layer_Security)
- [Kali Linux Tools Documentation](https://www.kali.org/tools/)

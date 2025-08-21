#!/bin/bash
# HSTS Bypass Testing Tool Launcher
# This script determines the right testing approach based on the platform

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo -e "${BLUE}HSTS Bypass Testing Tool${NC}"
    echo ""
    echo "Usage: $0 <domain> [options]"
    echo ""
    echo "Options:"
    echo "  --browser <browser>    Specify a browser (chrome, firefox, safari, edge, opera, brave)"
    echo "  --all-browsers         Test all available browsers"
    echo "  --mitm                 Include MITM attack testing (Linux only, requires root)"
    echo "  --interface <iface>    Network interface for MITM testing"
    echo "  --gateway <ip>         Gateway IP for MITM testing"
    echo "  --target <ip>          Target IP for MITM testing"
    echo "  --all-targets          Target all devices on network for MITM testing"
    echo "  --verbose              Enable verbose output"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 example.com --browser chrome"
    echo "  $0 example.com --all-browsers"
    echo "  $0 example.com --mitm --interface eth0 --gateway 192.168.1.1 --target 192.168.1.100"
    echo ""
}

# Check if we have enough arguments
if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

# Parse the domain
DOMAIN=$1
shift

# Default options
BROWSERS=""
MITM=false
VERBOSE=""
INTERFACE=""
GATEWAY=""
TARGET=""
ALL_TARGETS=false

# Parse options
while [ "$#" -gt 0 ]; do
    case "$1" in
        --browser)
            BROWSERS="$BROWSERS $2"
            shift 2
            ;;
        --all-browsers)
            BROWSERS="all"
            shift
            ;;
        --mitm)
            MITM=true
            shift
            ;;
        --interface)
            INTERFACE="--interface $2"
            shift 2
            ;;
        --gateway)
            GATEWAY="--gateway $2"
            shift 2
            ;;
        --target)
            TARGET="--target $2"
            shift 2
            ;;
        --all-targets)
            ALL_TARGETS=true
            shift
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Detect platform
PLATFORM=$(uname)
echo -e "${BLUE}Detected platform: $PLATFORM${NC}"

# Construct browser arguments
if [ -n "$BROWSERS" ]; then
    if [ "$BROWSERS" == "all" ]; then
        BROWSER_ARGS="--browsers all"
    else
        BROWSER_ARGS="--browsers$BROWSERS"
    fi
else
    BROWSER_ARGS=""
fi

# Check for Kali Linux MITM requirements
if [ "$MITM" = true ]; then
    if [ "$PLATFORM" != "Linux" ]; then
        echo -e "${RED}MITM attack testing is only available on Linux${NC}"
        exit 1
    fi
    
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${RED}MITM attack testing requires root privileges${NC}"
        echo "Please run with: sudo $0 $DOMAIN --mitm ..."
        exit 1
    fi
    
    if [ -z "$INTERFACE" ] || [ -z "$GATEWAY" ]; then
        echo -e "${RED}MITM attack testing requires --interface and --gateway options${NC}"
        show_help
        exit 1
    fi
    
    if [ -z "$TARGET" ] && [ "$ALL_TARGETS" = false ]; then
        echo -e "${RED}MITM attack testing requires either --target or --all-targets option${NC}"
        show_help
        exit 1
    fi
    
    MITM_ARGS="--kali $INTERFACE $GATEWAY"
    
    if [ -n "$TARGET" ]; then
        MITM_ARGS="$MITM_ARGS $TARGET"
    fi
    
    if [ "$ALL_TARGETS" = true ]; then
        MITM_ARGS="$MITM_ARGS --all-targets"
    fi
else
    MITM_ARGS=""
fi

# Run the comprehensive test
echo -e "${GREEN}Starting HSTS bypass test for: $DOMAIN${NC}"
echo -e "${YELLOW}This may require browser windows to open and close automatically${NC}"

# Construct the command
CMD="python3 $(dirname "$0")/hsts_comprehensive.py $DOMAIN $BROWSER_ARGS $MITM_ARGS $VERBOSE"
echo -e "${BLUE}Running: $CMD${NC}"
echo ""

# Execute the command
$CMD

# Get the exit status
STATUS=$?

if [ $STATUS -eq 0 ]; then
    echo -e "${GREEN}Test completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Test failed with status $STATUS${NC}"
    exit $STATUS
fi

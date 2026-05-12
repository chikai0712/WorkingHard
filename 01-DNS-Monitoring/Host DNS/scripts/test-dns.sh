#!/bin/bash
# ============================================
# DNS Resolver Test Script
# ============================================

set -euo pipefail

# Default values
DNS_SERVER=""
TEST_DOMAIN="google.com"
QPS=100
DURATION=10

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test DNS resolver performance and functionality.

Options:
    -s, --server SERVER    DNS server IP or hostname (required)
    -d, --domain DOMAIN    Test domain (default: google.com)
    -q, --qps QPS          Queries per second (default: 100)
    -t, --duration SECONDS Test duration in seconds (default: 10)
    -h, --help             Show this help message

Examples:
    # Basic test
    $0 -s 1.2.3.4
    
    # High QPS test
    $0 -s 1.2.3.4 -q 1000 -t 30
    
    # Test specific domain
    $0 -s 1.2.3.4 -d example.com
EOF
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--server)
            DNS_SERVER="$2"
            shift 2
            ;;
        -d|--domain)
            TEST_DOMAIN="$2"
            shift 2
            ;;
        -q|--qps)
            QPS="$2"
            shift 2
            ;;
        -t|--duration)
            DURATION="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check if DNS server is provided
if [ -z "${DNS_SERVER}" ]; then
    log_error "DNS server is required"
    usage
    exit 1
fi

# Check prerequisites
check_dig() {
    if ! command -v dig &> /dev/null; then
        log_error "dig is not installed. Please install bind-utils or dnsutils"
        exit 1
    fi
}

check_dnsperf() {
    if ! command -v dnsperf &> /dev/null; then
        log_warn "dnsperf is not installed. Install for performance testing."
        log_warn "Basic dig test will be performed instead."
        return 1
    fi
    return 0
}

# Basic functionality test
test_basic() {
    log_info "Testing basic DNS resolution..."
    
    if dig @"${DNS_SERVER}" "${TEST_DOMAIN}" +short +timeout=5 > /dev/null 2>&1; then
        log_info "✓ Basic resolution works"
        
        # Show response
        RESPONSE=$(dig @"${DNS_SERVER}" "${TEST_DOMAIN}" +short | head -1)
        log_info "Response for ${TEST_DOMAIN}: ${RESPONSE}"
        return 0
    else
        log_error "✗ Basic resolution failed"
        return 1
    fi
}

# Performance test with dnsperf
test_performance() {
    log_info "Running performance test (${QPS} QPS for ${DURATION}s)..."
    
    # Create query file
    QUERY_FILE=$(mktemp)
    echo "${TEST_DOMAIN} A" > "${QUERY_FILE}"
    
    # Run dnsperf
    dnsperf -s "${DNS_SERVER}" -d "${QUERY_FILE}" -Q "${QPS}" -l "${DURATION}" -c 10 || {
        log_error "Performance test failed"
        rm -f "${QUERY_FILE}"
        return 1
    }
    
    rm -f "${QUERY_FILE}"
    log_info "Performance test completed"
}

# Test DNSSEC
test_dnssec() {
    log_info "Testing DNSSEC validation..."
    
    if dig @"${DNS_SERVER}" "${TEST_DOMAIN}" +dnssec +cdflag | grep -q "ad"; then
        log_info "✓ DNSSEC validation working"
    else
        log_warn "DNSSEC validation may not be working (check manually)"
    fi
}

# Test TCP fallback
test_tcp() {
    log_info "Testing TCP fallback..."
    
    if dig @"${DNS_SERVER}" "${TEST_DOMAIN}" +tcp +short > /dev/null 2>&1; then
        log_info "✓ TCP resolution works"
    else
        log_warn "TCP resolution failed"
    fi
}

# Main test function
main() {
    log_info "Starting DNS resolver tests..."
    log_info "Target server: ${DNS_SERVER}"
    
    check_dig
    
    # Run tests
    test_basic || exit 1
    test_dnssec
    test_tcp
    
    # Performance test if available
    if check_dnsperf; then
        test_performance
    else
        log_info "Skipping performance test (dnsperf not available)"
    fi
    
    log_info "All tests completed"
}

main "$@"


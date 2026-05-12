#!/bin/bash
# ============================================
# Node-level sysctl Configuration Script
# ============================================
# This script configures kernel parameters for high-performance DNS
# Run on each Kubernetes node (via DaemonSet or manual execution)

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run as root"
    exit 1
fi

# Calculate conntrack_max based on expected QPS
# Formula: QPS * connection_duration * safety_factor
# Example: 400k QPS * 15s * 1.5 = 9M
EXPECTED_QPS=${EXPECTED_QPS:-400000}
CONN_DURATION=${CONN_DURATION:-15}
SAFETY_FACTOR=${SAFETY_FACTOR:-1.5}
CONNTRACK_MAX=$((EXPECTED_QPS * CONN_DURATION * SAFETY_FACTOR / 1000))

log_info "Configuring kernel parameters for DNS resolver..."
log_info "Expected QPS: ${EXPECTED_QPS}"
log_info "Calculated conntrack_max: ${CONNTRACK_MAX}"

# Apply sysctl settings
apply_sysctl() {
    local key=$1
    local value=$2
    local file="/etc/sysctl.d/99-dns-resolver.conf"
    
    # Add to sysctl.d file
    if ! grep -q "^${key}" "${file}" 2>/dev/null; then
        echo "${key} = ${value}" >> "${file}"
        log_info "Added ${key} = ${value}"
    else
        sed -i "s|^${key}.*|${key} = ${value}|" "${file}"
        log_info "Updated ${key} = ${value}"
    fi
    
    # Apply immediately
    sysctl -w "${key}=${value}" || {
        log_warn "Failed to set ${key}, may require reboot"
    }
}

# Create sysctl.d file if it doesn't exist
mkdir -p /etc/sysctl.d
touch /etc/sysctl.d/99-dns-resolver.conf

# ============================================
# Conntrack Settings
# ============================================
log_info "Configuring conntrack settings..."
apply_sysctl "net.netfilter.nf_conntrack_max" "${CONNTRACK_MAX}"
apply_sysctl "net.netfilter.nf_conntrack_udp_timeout" "10"
apply_sysctl "net.netfilter.nf_conntrack_udp_timeout_stream" "30"

# ============================================
# UDP Buffer Sizes
# ============================================
log_info "Configuring UDP buffer sizes..."
apply_sysctl "net.core.rmem_max" "134217728"  # 128MB
apply_sysctl "net.core.wmem_max" "134217728"  # 128MB
apply_sysctl "net.core.rmem_default" "8388608"  # 8MB
apply_sysctl "net.core.wmem_default" "8388608"  # 8MB

# ============================================
# Socket Options
# ============================================
log_info "Configuring socket options..."
apply_sysctl "net.ipv4.udp_mem" "8388608 16777216 33554432"
apply_sysctl "net.ipv4.udp_rmem_min" "4096"
apply_sysctl "net.ipv4.udp_wmem_min" "4096"

# ============================================
# Network Performance
# ============================================
log_info "Configuring network performance settings..."
apply_sysctl "net.core.netdev_max_backlog" "5000"
apply_sysctl "net.core.somaxconn" "4096"
apply_sysctl "net.ipv4.tcp_max_syn_backlog" "4096"

# ============================================
# IP Forwarding (if needed)
# ============================================
# Uncomment if nodes need to forward packets
# apply_sysctl "net.ipv4.ip_forward" "1"
# apply_sysctl "net.ipv6.conf.all.forwarding" "1"

log_info "Kernel parameters configured"
log_info "Settings saved to /etc/sysctl.d/99-dns-resolver.conf"
log_warn "Some settings may require a reboot to take full effect"
log_info "To apply without reboot: sysctl -p /etc/sysctl.d/99-dns-resolver.conf"


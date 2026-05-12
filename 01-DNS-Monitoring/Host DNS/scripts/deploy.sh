#!/bin/bash
# ============================================
# DNS Resolver Deployment Script
# ============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
K8S_DIR="${PROJECT_ROOT}/k8s"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check kustomize (optional, can use kubectl apply -k)
    if ! command -v kustomize &> /dev/null; then
        log_warn "kustomize is not installed, will use kubectl apply -k"
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

deploy() {
    log_info "Deploying DNS Resolver to Kubernetes..."
    
    # Apply using kustomize or kubectl
    if command -v kustomize &> /dev/null; then
        log_info "Using kustomize to build and apply manifests..."
        kustomize build "${K8S_DIR}" | kubectl apply -f -
    else
        log_info "Using kubectl apply -k..."
        kubectl apply -k "${K8S_DIR}"
    fi
    
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/dns-resolver -n dns || {
        log_error "Deployment failed to become ready"
        kubectl describe deployment dns-resolver -n dns
        exit 1
    }
    
    log_info "Deployment completed successfully"
}

get_service_info() {
    log_info "Getting service information..."
    
    # Get LoadBalancer external IP
    EXTERNAL_IP=$(kubectl get svc dns-resolver -n dns -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Pending")
    
    if [ "${EXTERNAL_IP}" != "Pending" ] && [ -n "${EXTERNAL_IP}" ]; then
        log_info "DNS Resolver is available at: ${EXTERNAL_IP}"
        log_info "Test with: dig @${EXTERNAL_IP} google.com"
    else
        log_warn "LoadBalancer IP is still pending. Check with: kubectl get svc dns-resolver -n dns"
    fi
    
    # Get pod status
    log_info "Pod status:"
    kubectl get pods -n dns -l app=dns-resolver
}

main() {
    log_info "Starting DNS Resolver deployment..."
    
    check_prerequisites
    deploy
    get_service_info
    
    log_info "Deployment script completed"
}

# Run main function
main "$@"


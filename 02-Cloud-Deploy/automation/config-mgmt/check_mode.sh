#!/usr/bin/env bash
set -euo pipefail

INVENTORY="${1:-inventory.ini}"
PLAYBOOK="${2:-site.yml}"

echo "[config-mgmt] Would run ansible-playbook -i $INVENTORY $PLAYBOOK --check --diff"

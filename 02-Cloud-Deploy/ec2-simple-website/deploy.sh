#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

AWS_PROFILE_NAME="${AWS_PROFILE:-new-website}"
AWS_REGION_NAME="${AWS_REGION:-ap-northeast-1}"
KEY_NAME="cloudsite-new-website-key"
PRIVATE_KEY_PATH="$SCRIPT_DIR/$KEY_NAME"
PUBLIC_KEY_PATH="$SCRIPT_DIR/$KEY_NAME.pub"
TFVARS_PATH="$SCRIPT_DIR/terraform.tfvars"

print_step() {
  printf '\n==> %s\n' "$1"
}

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

print_step "Checking required tools"
command -v aws >/dev/null 2>&1 || fail "AWS CLI is not installed. Install it with: brew install awscli"
command -v terraform >/dev/null 2>&1 || fail "Terraform is not installed. Install it with: brew install terraform"
command -v ssh-keygen >/dev/null 2>&1 || fail "ssh-keygen is not available."

print_step "Checking AWS identity"
AWS_IDENTITY_JSON="$(aws sts get-caller-identity --profile "$AWS_PROFILE_NAME" --region "$AWS_REGION_NAME")" || fail "Cannot access AWS profile '$AWS_PROFILE_NAME'. Run: aws configure --profile $AWS_PROFILE_NAME"
printf '%s\n' "$AWS_IDENTITY_JSON"

ACCOUNT_ID="$(printf '%s' "$AWS_IDENTITY_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["Account"])')"
printf 'Using AWS account: %s\n' "$ACCOUNT_ID"
printf 'Using AWS region: %s\n' "$AWS_REGION_NAME"

print_step "Preparing local SSH key"
if [ ! -f "$PRIVATE_KEY_PATH" ]; then
  ssh-keygen -t ed25519 -f "$PRIVATE_KEY_PATH" -N "" -C "cloudsite-new-website" >/dev/null
  chmod 600 "$PRIVATE_KEY_PATH"
  printf 'Created SSH key: %s\n' "$PRIVATE_KEY_PATH"
else
  chmod 600 "$PRIVATE_KEY_PATH"
  printf 'Using existing SSH key: %s\n' "$PRIVATE_KEY_PATH"
fi

if [ ! -f "$PUBLIC_KEY_PATH" ]; then
  ssh-keygen -y -f "$PRIVATE_KEY_PATH" > "$PUBLIC_KEY_PATH"
fi

print_step "Detecting current public IP for SSH access"
PUBLIC_IP="$(curl -fsS https://checkip.amazonaws.com 2>/dev/null | tr -d '[:space:]' || true)"
if [ -z "$PUBLIC_IP" ]; then
  PUBLIC_IP="$(curl -fsS https://api.ipify.org 2>/dev/null | tr -d '[:space:]' || true)"
fi
if [ -z "$PUBLIC_IP" ]; then
  fail "Cannot detect public IP. Create terraform.tfvars manually from terraform.tfvars.example."
fi
SSH_CIDR="$PUBLIC_IP/32"
printf 'SSH will be allowed from: %s\n' "$SSH_CIDR"

print_step "Preparing terraform.tfvars"
if [ ! -f "$TFVARS_PATH" ]; then
  cat > "$TFVARS_PATH" <<EOF_VARS
aws_profile = "$AWS_PROFILE_NAME"
aws_region  = "$AWS_REGION_NAME"

project_name  = "ec2-simple-website"
environment   = "dev"
instance_name = "cloudsite-simple-web"
instance_type = "t3.micro"

key_pair_name        = "$KEY_NAME"
public_key_path      = "./$KEY_NAME.pub"
ssh_private_key_path = "./$KEY_NAME"
ssh_allowed_cidr     = "$SSH_CIDR"

domain_name = "clouddeployment168.site"
EOF_VARS
  printf 'Created terraform.tfvars\n'
else
  printf 'terraform.tfvars already exists. Keeping existing values.\n'
  printf 'If your network IP changed, update ssh_allowed_cidr manually to: %s\n' "$SSH_CIDR"
fi

print_step "Terraform init"
terraform init

print_step "Terraform format check"
terraform fmt -check

print_step "Terraform plan"
terraform plan -out=tfplan

printf '\nThis will create or update AWS resources in account %s (%s).\n' "$ACCOUNT_ID" "$AWS_REGION_NAME"
printf 'Type yes to apply: '
read -r CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  printf 'Deployment cancelled.\n'
  exit 0
fi

print_step "Terraform apply"
terraform apply tfplan

print_step "Deployment outputs"
terraform output

WEBSITE_URL="$(terraform output -raw website_url)"
printf '\nWebsite URL: %s\n' "$WEBSITE_URL"
printf 'If the page is not ready immediately, wait 1-2 minutes for EC2 user data to finish.\n'

#!/usr/bin/env bash
# Deploy daily-office-app infrastructure via Terraform.
# Run from any directory — script resolves paths relative to itself.
# Prerequisites:
#   - Terraform >= 1.5 on PATH
#   - AWS credentials configured (aws configure or environment variables)
#   - Copy infra/terraform.tfvars.example to infra/terraform.tfvars and edit it
#   - web.sqlite uploaded to s3://daily-office-app-assets/web.sqlite
#   - IAM role daily-office-app-ec2-role exists in the account
set -euo pipefail

INFRA_DIR="$(dirname "$0")/../infra"
cd "$INFRA_DIR"

echo "=== terraform init ==="
terraform init

echo "=== terraform plan ==="
terraform plan -out=tfplan

echo "=== terraform apply ==="
terraform apply tfplan

echo ""
echo "=== Outputs ==="
terraform output

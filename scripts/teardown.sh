#!/usr/bin/env bash
# Destroy all daily-office-app infrastructure.
# This is irreversible — all EC2 instances, the ALB, WAF ACL, and log groups
# will be deleted. The S3 bucket has prevent_destroy = true and will NOT be
# destroyed; empty and delete it manually if needed.
set -euo pipefail

INFRA_DIR="$(dirname "$0")/../infra"
cd "$INFRA_DIR"

echo "WARNING: This will destroy all daily-office-app infrastructure."
echo "The S3 bucket (daily-office-app-assets) is protected and will NOT be deleted."
echo ""
printf "Type 'yes' to confirm destruction: "
read -r confirmation

if [[ "$confirmation" != "yes" ]]; then
  echo "Aborted."
  exit 1
fi

terraform init
terraform destroy

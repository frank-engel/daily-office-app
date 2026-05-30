# Deployment Guide — Anglican Daily Office App

Infrastructure lives in `infra/` (Terraform, local state file).  
Application runs on EC2 (Amazon Linux 2023) behind an ALB + WAF.  
All scripts in `scripts/` are Bash — run from Linux/macOS/WSL or Git Bash on Windows.

---

## Prerequisites

| Tool | Minimum version | Notes |
|---|---|---|
| [Terraform](https://developer.hashicorp.com/terraform/downloads) | 1.5 | `terraform -version` |
| [AWS CLI](https://aws.amazon.com/cli/) | 2.x | `aws --version` |
| AWS credentials | — | `aws sts get-caller-identity` to verify |
| Python | 3.11 | Only needed locally to generate `SECRET_KEY` |

AWS credentials must have permission to create EC2, ALB, WAF, S3, ACM, and CloudWatch resources.

---

## One-Time AWS Setup (already done for this account)

The IAM instance profile `daily-office-app-ec2-role` must exist before the first `terraform apply`.  
It was pre-created via the AWS console with these managed policies attached:
- `AmazonSSMManagedInstanceCore`
- `CloudWatchAgentServerPolicy`
- Inline policy: `s3:GetObject` on `arn:aws:s3:::daily-office-app-assets/*`

**Do not recreate this role** — Terraform references it by name and does not manage it.

The S3 bucket `daily-office-app-assets` must contain the Bible database before the first deploy:
```bash
aws s3 cp backend/data/web.sqlite s3://daily-office-app-assets/web.sqlite
```

---

## Configuration

### 1. Copy the example tfvars and fill in your values

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

`infra/terraform.tfvars` is gitignored and must never be committed — it contains your `secret_key`.

### 2. Generate a secret key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as `secret_key` in `terraform.tfvars`. This signs session cookies.  
**Rotating this key logs out all active users.**

### 3. Key variables

| Variable | Required | Description |
|---|---|---|
| `secret_key` | **Yes** | Random 64-char hex string (see above) |
| `domain_name` | No | Custom domain, e.g. `office.example.com`. Leave `""` to serve HTTP only. |
| `allowed_emails` | No | Comma-separated list of emails permitted to self-register, e.g. `"a@b.com,c@d.com"`. Empty = unrestricted (only matters when `REGISTRATION_ENABLED=true` on the instance). |
| `allowed_ips` | No | Restrict ALB inbound to specific CIDRs. Empty = open to internet. |
| `instance_type` | No | Default: `t3.micro` |

`HTTPS_ONLY` is derived automatically: `true` when `domain_name` is set, `false` otherwise.  
You do not need to set it manually.

---

## Deploying

```bash
scripts/deploy.sh
```

This runs `terraform init → plan → apply` and prints the outputs.

Key outputs:
- `alb_dns_name` — the public URL for the app (or CNAME target for your domain)
- `instance_id` — needed for SSM Session Manager access
- `ssm_connect_command` — ready-to-run shell session command

### On first deploy only

After the instance boots (~2 min), set `REGISTRATION_ENABLED=true` on the instance so you can create your account:

```bash
# Connect via SSM
aws ssm start-session --target <instance_id> --region us-east-1

# On the instance:
sudo sed -i 's/REGISTRATION_ENABLED=false/REGISTRATION_ENABLED=true/' \
    /opt/daily-office-app/backend/.env
sudo systemctl restart daily-office

# Visit http://<alb_dns_name>/register — create your account
# Then lock registration again:
sudo sed -i 's/REGISTRATION_ENABLED=true/REGISTRATION_ENABLED=false/' \
    /opt/daily-office-app/backend/.env
sudo systemctl restart daily-office
```

---

## User Management

All user management is done via the admin CLI on the instance over SSM.  
Always prefix commands with `sudo -u appuser` — the SQLite files are owned by `appuser`.

```bash
# Connect
aws ssm start-session --target <instance_id> --region us-east-1

# On the instance — activate venv first:
cd /opt/daily-office-app/backend
source ../.venv/bin/activate

# Invite a new user (creates account, prints set-password URL)
sudo -u appuser .venv/bin/python -m app.auth.cli invite user@example.com --name "Their Name"

# List all users and their status
sudo -u appuser .venv/bin/python -m app.auth.cli list-users

# Reset a password
sudo -u appuser .venv/bin/python -m app.auth.cli reset-password user@example.com newpassword123
```

The invite command prints a `/set-password?token=...` URL.  
Prepend the app URL and share it with the user. The link expires in 48 hours.  
Run `invite` again for the same email to regenerate an expired link.

---

## Updating the Application (no Terraform required)

For code-only changes (new features, bug fixes, DB schema additions), **do not run `terraform apply`**.  
A Terraform apply that modifies `user_data` replaces the EC2 instance and wipes all SQLite data.

Instead, update via SSM:

```bash
aws ssm start-session --target <instance_id> --region us-east-1

# On the instance:
cd /opt/daily-office-app
sudo -u appuser git pull
sudo -u appuser .venv/bin/pip install -e "backend/.[dev]" --quiet
sudo systemctl restart daily-office
```

Schema migrations (new columns) run automatically at startup via the migration runner in `app/auth/db.py` and `app/habits/db.py` — no manual SQL needed.

---

## Infrastructure Operations

### Take app offline without destroying anything

```bash
scripts/toggle-access.sh off   # removes ALB inbound rules → all traffic blocked
scripts/toggle-access.sh on    # restores inbound rules
```

### View application logs

```bash
# Via SSM on the instance:
sudo tail -f /var/log/daily-office.log

# Or via CloudWatch (no SSM session needed):
aws logs tail /daily-office-app/app --follow --region us-east-1
```

### Connect to the instance (no SSH — SSM only)

```bash
# Use the ready-to-run command from Terraform output:
terraform -chdir=infra output ssm_connect_command

# Or directly:
aws ssm start-session --target <instance_id> --region us-east-1
```

---

## Adding HTTPS / Custom Domain

When you're ready to add a domain:

1. Purchase a domain (AWS Route 53, Namecheap, Porkbun, etc.)
2. Use a **subdomain** — e.g. `office.yourdomain.com` — not the bare root domain (CNAME limitations)
3. Set in `infra/terraform.tfvars`:
   ```hcl
   domain_name = "office.yourdomain.com"
   ```
4. Run `scripts/deploy.sh`
5. After apply, get the DNS validation records for the ACM certificate:
   ```bash
   terraform -chdir=infra output acm_validation_cnames
   ```
6. Add those CNAME records at your DNS provider. Cert validates in minutes.
7. Add a `CNAME` record at your DNS provider pointing `office.yourdomain.com` to the `alb_dns_name` output.

`HTTPS_ONLY` will automatically be `true` once `domain_name` is set — no other changes needed.  
The ALB HTTP→HTTPS redirect listener activates automatically.

---

## Data Persistence Warning

`users.sqlite` and `habits.sqlite` live on the EC2 instance's root EBS volume.  
**They are destroyed if Terraform replaces the instance** (triggered by changes to `user_data`, the AMI, or instance type).

Safe operations (instance NOT replaced):
- Code updates via `git pull`
- WAF rule changes
- ALB / security group changes

Unsafe operations (instance IS replaced, data lost):
- First-time deploy
- Changing `user_data.sh`
- Changing `instance_type`

Before any potentially destructive Terraform apply, back up the databases:
```bash
# From SSM session on instance:
aws s3 cp /opt/daily-office-app/backend/data/users.sqlite \
    s3://daily-office-app-assets/backups/users-$(date +%Y%m%d).sqlite
aws s3 cp /opt/daily-office-app/backend/data/habits.sqlite \
    s3://daily-office-app-assets/backups/habits-$(date +%Y%m%d).sqlite
```

---

## Teardown

```bash
scripts/teardown.sh
```

Prompts for confirmation before destroying. The S3 bucket (`daily-office-app-assets`) has `prevent_destroy = true` and will not be deleted — empty and remove it manually if needed.

The IAM role `daily-office-app-ec2-role` was created outside of Terraform and must be deleted manually from the AWS console if desired.

---

## Troubleshooting

**Login page loops (redirects back to login after submitting credentials)**  
The session cookie has the `Secure` flag set but the app is being accessed over HTTP.  
Check `/opt/daily-office-app/backend/.env` on the instance — `HTTPS_ONLY` should be `false` when no domain is configured.
```bash
sudo grep HTTPS_ONLY /opt/daily-office-app/backend/.env
# If wrong: sudo sed -i 's/HTTPS_ONLY=true/HTTPS_ONLY=false/' /opt/daily-office-app/backend/.env
# Then: sudo systemctl restart daily-office
```

**App not starting after code update**  
Check the log for Python errors:
```bash
sudo tail -50 /var/log/daily-office.log
```
A missing dependency is the most common cause — run `pip install -e "backend/.[dev]"` and restart.

**Set-password link expired**  
Links expire after 48 hours. Re-run the `invite` CLI command for the same email to generate a new link.

**`users.sqlite`: attempt to write a readonly database**  
Run CLI commands with `sudo -u appuser` — the database files are owned by `appuser`, not the SSM session user.

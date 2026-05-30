#!/bin/bash
# EC2 bootstrap for Anglican Daily Office App.
# This file is a Terraform template — $${...} placeholders are substituted at plan time.
# Shell variables that use braces must be written as $${...} to survive templatefile().
set -euo pipefail
exec > >(tee /var/log/user-data.log | logger -t user-data) 2>&1

echo "=== Bootstrap started ==="

# ── 1. System update and packages ────────────────────────────────────────────
dnf update -y
dnf install -y python3.11 git nginx amazon-cloudwatch-agent

# ── 2. App system user ────────────────────────────────────────────────────────
useradd --system --no-create-home --shell /sbin/nologin appuser 2>/dev/null || true

# ── 3. Clone repository ───────────────────────────────────────────────────────
git clone https://github.com/frank-engel/daily-office-app.git /opt/daily-office-app

# ── 4. Python venv at project root (matches local dev convention) ─────────────
cd /opt/daily-office-app
python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e "backend/.[dev]"

# ── 5. Download Bible database from S3 ───────────────────────────────────────
# The EC2 instance role grants s3:GetObject on daily-office-app-assets — no
# credentials needed. If the bucket isn't populated yet, log a warning and
# continue; the app handles missing web.sqlite gracefully.
if ! aws s3 cp "s3://daily-office-app-assets/${bible_db_s3_key}" \
    /opt/daily-office-app/backend/data/web.sqlite \
    --region "${aws_region}"; then
  echo "WARNING: S3 download failed — app will start without Bible text." >&2
fi

# ── 6. Ensure data directory exists (habits.sqlite is created by SQLAlchemy) ──
mkdir -p /opt/daily-office-app/backend/data

# ── 7. Ownership ──────────────────────────────────────────────────────────────
chown -R appuser:appuser /opt/daily-office-app

# ── 8. Systemd service ────────────────────────────────────────────────────────
touch /var/log/daily-office.log
chown appuser:appuser /var/log/daily-office.log

cat > /etc/systemd/system/daily-office.service << 'SVCEOF'
[Unit]
Description=Anglican Daily Office App
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/daily-office-app/backend
ExecStart=/opt/daily-office-app/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=append:/var/log/daily-office.log
StandardError=append:/var/log/daily-office.log
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVCEOF

# ── 9. Nginx reverse proxy ────────────────────────────────────────────────────
# ALB handles TLS termination; nginx proxies plain HTTP on port 80.
# limit_req_zone provides a second rate-limiting layer behind WAF.
cat > /etc/nginx/conf.d/daily-office.conf << 'NGINXEOF'
limit_req_zone $binary_remote_addr zone=app:10m rate=10r/s;

server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 1m;

    location / {
        limit_req zone=app burst=20 nodelay;

        proxy_pass            http://127.0.0.1:8000;
        proxy_set_header      Host              $host;
        proxy_set_header      X-Real-IP         $remote_addr;
        proxy_set_header      X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header      X-Forwarded-Proto $scheme;
        proxy_read_timeout    60s;
        proxy_connect_timeout 10s;
    }
}
NGINXEOF

# Remove the default nginx welcome page.
rm -f /etc/nginx/conf.d/default.conf

# ── 10. CloudWatch agent ──────────────────────────────────────────────────────
# ${log_group_name} and ${aws_region} are substituted by Terraform templatefile().
# {instance_id} is a CloudWatch agent placeholder — no $ prefix, so Terraform
# leaves it alone; the agent expands it at runtime.
mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CWAEOF'
{
  "agent": {
    "region": "${aws_region}"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/messages",
            "log_group_name": "${log_group_name}",
            "log_stream_name": "{instance_id}/messages",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "${log_group_name}",
            "log_stream_name": "{instance_id}/user-data",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/daily-office.log",
            "log_group_name": "${log_group_name}",
            "log_stream_name": "{instance_id}/daily-office",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
CWAEOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# ── 11. Enable and start services ─────────────────────────────────────────────
systemctl daemon-reload
systemctl enable --now daily-office
systemctl enable --now nginx

echo "=== Bootstrap complete ==="

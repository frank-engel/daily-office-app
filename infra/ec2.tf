data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# The IAM role daily-office-app-ec2-role was pre-created via the AWS console,
# which also auto-creates an instance profile with the same name. We reference
# it directly by name — no iam:CreateInstanceProfile or iam:GetRole needed.

resource "aws_security_group" "ec2" {
  name        = "daily-office-app-ec2-${var.environment}"
  description = "Allow inbound on app port from ALB only. No SSH - use SSM."
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "nginx from CloudFront origin-facing IPs"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    prefix_list_ids = [data.aws_ec2_managed_prefix_list.cloudfront.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "daily-office-app-ec2-${var.environment}"
  }
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = tolist(data.aws_subnets.default.ids)[0]
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = "daily-office-app-ec2-role"

  user_data = templatefile("${path.module}/user_data.sh", {
    bible_db_s3_key = var.bible_db_s3_key
    log_group_name  = "/daily-office-app/app"
    aws_region      = var.aws_region
    secret_key      = var.secret_key
    allowed_emails  = var.allowed_emails
    https_only      = var.domain_name != "" ? "true" : "false"
  })

  user_data_replace_on_change = true

  tags = {
    Name = "daily-office-app-${var.environment}"
  }
}

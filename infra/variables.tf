variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for all resources."
}

variable "environment" {
  type        = string
  default     = "prototype"
  description = "Environment tag applied to all resources."
}

variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type."
}

variable "domain_name" {
  type        = string
  default     = ""
  description = "Optional domain name (e.g. office.example.com). When set, an ACM certificate is created and the ALB serves HTTPS on port 443. When empty, ALB serves HTTP only on port 80."
}

variable "enable_public_access" {
  type        = bool
  default     = true
  description = "When false, the ALB security group has no inbound rules, effectively taking the app offline without destroying infrastructure."
}

variable "allowed_ips" {
  type        = list(string)
  default     = []
  description = "When non-empty and enable_public_access is true, restrict ALB inbound to these CIDRs only (e.g. [\"1.2.3.4/32\"]). Empty = open to internet."
}

variable "bible_db_s3_key" {
  type        = string
  default     = "web.sqlite"
  description = "S3 object key for the Bible database in the daily-office-app-assets bucket."
}

variable "app_port" {
  type        = number
  default     = 8000
  description = "Port uvicorn listens on inside the EC2 instance."
}

variable "secret_key" {
  type        = string
  sensitive   = true
  description = "Secret key for session cookie signing. Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
}

variable "allowed_emails" {
  type        = string
  default     = ""
  description = "Comma-separated list of emails allowed to self-register (e.g. \"frank@example.com,tester@example.com\"). Empty = unrestricted when REGISTRATION_ENABLED=true."
}

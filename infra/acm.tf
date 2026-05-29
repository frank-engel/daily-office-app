# ACM certificate — only created when var.domain_name is set.
# After terraform apply, retrieve the CNAME records from outputs.acm_validation_cnames
# and add them to your DNS provider. Validation typically completes within a few minutes.
# The HTTPS listener in alb.tf will serve traffic once validation is complete.
resource "aws_acm_certificate" "main" {
  count             = var.domain_name != "" ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "daily-office-app-${var.environment}"
  }
}

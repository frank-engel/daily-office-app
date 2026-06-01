# Elastic IP — gives the CloudFront origin a stable hostname that survives EC2
# stop/start cycles. Without this, public_dns changes and CloudFront returns 502
# until terraform apply is re-run.
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name = "daily-office-app-${var.environment}"
  }
}

# CloudFront managed prefix list for origin-facing IPs.
# Used here for reference and in ec2.tf (Phase 4) to lock the EC2 SG.
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_cloudfront_distribution" "main" {
  enabled             = var.cloudfront_enabled
  is_ipv6_enabled     = true
  price_class         = "PriceClass_100" # US / Canada / Europe PoPs — cheapest tier
  web_acl_id          = aws_wafv2_web_acl.cloudfront.arn
  aliases             = var.domain_name != "" ? [var.domain_name] : []

  origin {
    domain_name = aws_eip.app.public_dns # stable across instance stop/start
    origin_id   = "ec2-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only" # CloudFront → EC2 on AWS backbone; EC2 SG restricts inbound
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # All paths: caching disabled, all viewer headers/cookies forwarded.
  # The app is entirely session-cookie-driven (FastAPI + HTMX); nothing is safely cacheable.
  default_cache_behavior {
    target_origin_id       = "ec2-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    # AWS managed policy IDs — stable, no resource creation needed
    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac" # AllViewerExceptHostHeader
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # When domain_name is set: use ACM cert (already in us-east-1 — no provider alias needed).
  # When domain_name is empty: use CloudFront's default *.cloudfront.net certificate.
  viewer_certificate {
    acm_certificate_arn            = var.domain_name != "" ? aws_acm_certificate.main[0].arn : null
    ssl_support_method             = var.domain_name != "" ? "sni-only" : null
    minimum_protocol_version       = var.domain_name != "" ? "TLSv1.2_2021" : "TLSv1"
    cloudfront_default_certificate = var.domain_name == ""
  }

  tags = {
    Name = "daily-office-app-${var.environment}"
  }
}

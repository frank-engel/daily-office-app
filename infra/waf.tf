resource "aws_wafv2_web_acl" "main" {
  name  = "daily-office-app-${var.environment}"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Rule 1: Rate limit — 1000 requests per 5 minutes per IP.
  rule {
    name     = "RateLimitPerIP"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitPerIP"
      sampled_requests_enabled   = true
    }
  }

  # Rule 2: AWS Managed Common Rule Set — COUNT only during testing to avoid
  # blocking legitimate traffic. Change override_action to none {} to enforce.
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Rule 3: AWS Managed Known Bad Inputs — BLOCK.
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "daily-office-app-waf-${var.environment}"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "daily-office-app-waf-${var.environment}"
  }
}

# WAF logging to CloudWatch can be enabled after deploy via the AWS console or CLI:
#   aws wafv2 put-logging-configuration \
#     --logging-configuration ResourceArn=<waf_acl_arn>,LogDestinationConfigs=[<log_group_arn>] \
#     --region us-east-1
# The target log group (aws-waf-logs-daily-office-app) and its resource policy
# are created in cloudwatch.tf — the log group name must start with "aws-waf-logs-".

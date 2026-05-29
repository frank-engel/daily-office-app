# App log group — receives /var/log/messages and the daily-office systemd journal.
resource "aws_cloudwatch_log_group" "app" {
  name              = "/daily-office-app/app"
  retention_in_days = 30

  tags = {
    Name = "daily-office-app-app-${var.environment}"
  }
}

# WAF log group — AWS requires the name to start with "aws-waf-logs-".
resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-daily-office-app"
  retention_in_days = 14

  tags = {
    Name = "daily-office-app-waf-${var.environment}"
  }
}

# Resource policy granting WAFv2 permission to write to the WAF log group.
data "aws_iam_policy_document" "waf_logging" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.waf.arn}:*"]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "waf_logging" {
  policy_document = data.aws_iam_policy_document.waf_logging.json
  policy_name     = "daily-office-app-waf-logging"
}

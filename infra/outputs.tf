output "alb_dns_name" {
  description = "DNS name of the ALB — point your domain's CNAME here."
  value       = aws_lb.main.dns_name
}

output "instance_id" {
  description = "EC2 instance ID — use with ssm_connect_command to open a shell."
  value       = aws_instance.app.id
}

output "waf_acl_arn" {
  description = "WAF Web ACL ARN."
  value       = aws_wafv2_web_acl.main.arn
}

output "acm_validation_cnames" {
  description = "DNS CNAME records to add to your DNS provider for ACM certificate validation. Empty when domain_name is not set."
  value = try(
    {
      for dvo in aws_acm_certificate.main[0].domain_validation_options : dvo.domain_name => {
        record_name  = dvo.resource_record_name
        record_type  = dvo.resource_record_type
        record_value = dvo.resource_record_value
      }
    },
    {}
  )
}

output "ssm_connect_command" {
  description = "Ready-to-run command to open an SSM Session Manager shell on the EC2 instance."
  value       = "aws ssm start-session --target ${aws_instance.app.id} --region ${var.aws_region}"
}

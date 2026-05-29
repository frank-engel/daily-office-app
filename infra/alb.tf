resource "aws_security_group" "alb" {
  name        = "daily-office-app-alb-${var.environment}"
  description = "ALB inbound controlled by enable_public_access and allowed_ips variables."
  vpc_id      = data.aws_vpc.default.id

  # When enable_public_access = false: no ingress rules — all inbound is denied.
  # When enable_public_access = true and allowed_ips is non-empty: restrict to those CIDRs.
  # When enable_public_access = true and allowed_ips is empty: open to internet.
  dynamic "ingress" {
    for_each = var.enable_public_access ? [80, 443] : []
    content {
      description      = length(var.allowed_ips) > 0 ? "HTTP/HTTPS from allowed CIDRs" : "HTTP/HTTPS from internet"
      from_port        = ingress.value
      to_port          = ingress.value
      protocol         = "tcp"
      cidr_blocks      = length(var.allowed_ips) > 0 ? var.allowed_ips : ["0.0.0.0/0"]
      ipv6_cidr_blocks = length(var.allowed_ips) > 0 ? [] : ["::/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "daily-office-app-alb-${var.environment}"
  }
}

resource "aws_lb" "main" {
  name               = "daily-office-app-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids

  tags = {
    Name = "daily-office-app-${var.environment}"
  }
}

resource "aws_lb_target_group" "main" {
  name     = "daily-office-app-${var.environment}"
  port     = var.app_port
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "daily-office-app-${var.environment}"
  }
}

resource "aws_lb_target_group_attachment" "app" {
  target_group_arn = aws_lb_target_group.main.arn
  target_id        = aws_instance.app.id
  port             = var.app_port
}

# Port 80: redirect to 443 when domain_name is set, otherwise forward to target group.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = var.domain_name != "" ? "redirect" : "forward"
    target_group_arn = var.domain_name != "" ? null : aws_lb_target_group.main.arn

    dynamic "redirect" {
      for_each = var.domain_name != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }
}

# Port 443: only created when domain_name is set.
# The ACM certificate may be PENDING_VALIDATION immediately after apply — add the
# CNAME records from outputs.acm_validation_cnames to your DNS provider to complete
# validation before HTTPS traffic will be served.
resource "aws_lb_listener" "https" {
  count             = var.domain_name != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main[0].arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# Load Balancer and Auto-Scaling Configuration for Dinner1
# High-availability load balancing with intelligent traffic routing

resource "aws_lb" "dinner1_main_alb" {
  name               = "dinner1-main-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets           = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  enable_deletion_protection = true
  enable_http2              = true
  idle_timeout              = 400

  # Access logs for monitoring and debugging
  access_logs {
    bucket  = aws_s3_bucket.dinner1_logs.id
    prefix  = "alb-logs"
    enabled = true
  }

  tags = {
    Name        = "Dinner1-Main-ALB"
    Environment = var.environment
    Project     = "Dinner1"
  }
}

# Network Load Balancer for WebSocket connections and high-performance APIs
resource "aws_lb" "dinner1_nlb" {
  name               = "dinner1-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets           = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  enable_deletion_protection = false
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "Dinner1-Network-LB"
    Environment = var.environment
    Project     = "Dinner1"
  }
}

# Security Group for ALB
resource "aws_security_group" "alb_sg" {
  name_prefix = "dinner1-alb-sg"
  vpc_id      = aws_vpc.dinner1_vpc.id

  # HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Custom API port
  ingress {
    description = "API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Dinner1-ALB-SecurityGroup"
  }
}

# Target Groups for different services

# Backend API Target Group
resource "aws_lb_target_group" "backend_tg" {
  name     = "dinner1-backend-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.dinner1_vpc.id

  # Health check configuration optimized for dating platform
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  # Connection draining
  deregistration_delay = 300

  # Stickiness for user sessions
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 3600  # 1 hour
    enabled         = true
  }

  tags = {
    Name = "Dinner1-Backend-TargetGroup"
  }
}

# Frontend Target Group
resource "aws_lb_target_group" "frontend_tg" {
  name     = "dinner1-frontend-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.dinner1_vpc.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  deregistration_delay = 60  # Shorter for static content

  tags = {
    Name = "Dinner1-Frontend-TargetGroup"
  }
}

# WebSocket Target Group for real-time features
resource "aws_lb_target_group" "websocket_tg" {
  name     = "dinner1-websocket-tg"
  port     = 9000
  protocol = "TCP"
  vpc_id   = aws_vpc.dinner1_vpc.id

  health_check {
    enabled             = true
    healthy_threshold   = 3
    interval            = 30
    port                = "traffic-port"
    protocol            = "TCP"
    timeout             = 6
    unhealthy_threshold = 3
  }

  tags = {
    Name = "Dinner1-WebSocket-TargetGroup"
  }
}

# SSL Certificate for HTTPS
resource "aws_acm_certificate" "dinner1_cert" {
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "Dinner1-SSL-Certificate"
  }
}

# ALB Listeners

# HTTPS Listener with SSL termination
resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = aws_lb.dinner1_main_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.dinner1_cert.arn

  # Default action - route to frontend
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_tg.arn
  }
}

# HTTP Listener with redirect to HTTPS
resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.dinner1_main_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# Listener Rules for intelligent routing

# API routing rule
resource "aws_lb_listener_rule" "api_routing" {
  listener_arn = aws_lb_listener.https_listener.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_tg.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# Admin panel routing
resource "aws_lb_listener_rule" "admin_routing" {
  listener_arn = aws_lb_listener.https_listener.arn
  priority     = 90

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_tg.arn
  }

  condition {
    path_pattern {
      values = ["/admin/*"]
    }
  }
}

# Static content routing with caching headers
resource "aws_lb_listener_rule" "static_routing" {
  listener_arn = aws_lb_listener.https_listener.arn
  priority     = 110

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_tg.arn
  }

  condition {
    path_pattern {
      values = ["/static/*", "/assets/*", "*.js", "*.css", "*.png", "*.jpg", "*.ico"]
    }
  }
}

# WebSocket listener on NLB
resource "aws_lb_listener" "websocket_listener" {
  load_balancer_arn = aws_lb.dinner1_nlb.arn
  port              = "9000"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.websocket_tg.arn
  }
}

# Auto Scaling Groups

# Backend Auto Scaling Group
resource "aws_autoscaling_group" "backend_asg" {
  name                = "dinner1-backend-asg"
  vpc_zone_identifier = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  target_group_arns   = [aws_lb_target_group.backend_tg.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = 2
  max_size         = 20
  desired_capacity = 4

  # Launch template
  launch_template {
    id      = aws_launch_template.backend_lt.id
    version = "$Latest"
  }

  # Scaling policies
  enabled_metrics = [
    "GroupMinSize",
    "GroupMaxSize",
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupTotalInstances"
  ]

  # Instance refresh for rolling updates
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
      instance_warmup        = 300
    }
  }

  tag {
    key                 = "Name"
    value               = "Dinner1-Backend-ASG"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }
}

# Frontend Auto Scaling Group
resource "aws_autoscaling_group" "frontend_asg" {
  name                = "dinner1-frontend-asg"
  vpc_zone_identifier = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  target_group_arns   = [aws_lb_target_group.frontend_tg.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 180

  min_size         = 2
  max_size         = 10
  desired_capacity = 3

  launch_template {
    id      = aws_launch_template.frontend_lt.id
    version = "$Latest"
  }

  enabled_metrics = [
    "GroupMinSize",
    "GroupMaxSize",
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupTotalInstances"
  ]

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 66
      instance_warmup        = 180
    }
  }

  tag {
    key                 = "Name"
    value               = "Dinner1-Frontend-ASG"
    propagate_at_launch = true
  }
}

# Launch Templates

# Backend Launch Template
resource "aws_launch_template" "backend_lt" {
  name_prefix   = "dinner1-backend-lt"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.medium"
  key_name      = aws_key_pair.dinner1_key.key_name

  vpc_security_group_ids = [aws_security_group.backend_sg.id]

  # IAM instance profile
  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  # User data for application setup
  user_data = base64encode(templatefile("${path.module}/scripts/backend_userdata.sh", {
    environment    = var.environment
    redis_endpoint = aws_elasticache_replication_group.dinner1_redis.primary_endpoint_address
    db_endpoint    = aws_db_instance.dinner1_postgres.endpoint
  }))

  # EBS optimization
  ebs_optimized = true

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = 20
      volume_type = "gp3"
      encrypted   = true
    }
  }

  # Monitoring
  monitoring {
    enabled = true
  }

  # Metadata options for security
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "Dinner1-Backend-LaunchTemplate"
  }
}

# Frontend Launch Template
resource "aws_launch_template" "frontend_lt" {
  name_prefix   = "dinner1-frontend-lt"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.small"
  key_name      = aws_key_pair.dinner1_key.key_name

  vpc_security_group_ids = [aws_security_group.frontend_sg.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  user_data = base64encode(templatefile("${path.module}/scripts/frontend_userdata.sh", {
    environment = var.environment
    api_endpoint = aws_lb.dinner1_main_alb.dns_name
  }))

  ebs_optimized = true

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = 10
      volume_type = "gp3"
      encrypted   = true
    }
  }

  monitoring {
    enabled = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "Dinner1-Frontend-LaunchTemplate"
  }
}

# Auto Scaling Policies

# Backend CPU-based scaling policy
resource "aws_autoscaling_policy" "backend_cpu_up" {
  name                   = "dinner1-backend-cpu-up"
  scaling_adjustment     = 2
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.backend_asg.name
}

resource "aws_autoscaling_policy" "backend_cpu_down" {
  name                   = "dinner1-backend-cpu-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.backend_asg.name
}

# Backend memory-based scaling policy
resource "aws_autoscaling_policy" "backend_memory_up" {
  name                   = "dinner1-backend-memory-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.backend_asg.name
}

# Frontend request count scaling policy
resource "aws_autoscaling_policy" "frontend_requests_up" {
  name                   = "dinner1-frontend-requests-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 180
  autoscaling_group_name = aws_autoscaling_group.frontend_asg.name
}

resource "aws_autoscaling_policy" "frontend_requests_down" {
  name                   = "dinner1-frontend-requests-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.frontend_asg.name
}

# CloudWatch Alarms for Auto Scaling

# Backend CPU utilization alarms
resource "aws_cloudwatch_metric_alarm" "backend_cpu_high" {
  alarm_name          = "dinner1-backend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "70"
  alarm_description   = "This metric monitors backend CPU utilization"
  alarm_actions       = [aws_autoscaling_policy.backend_cpu_up.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.backend_asg.name
  }
}

resource "aws_cloudwatch_metric_alarm" "backend_cpu_low" {
  alarm_name          = "dinner1-backend-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "20"
  alarm_description   = "This metric monitors backend CPU utilization"
  alarm_actions       = [aws_autoscaling_policy.backend_cpu_down.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.backend_asg.name
  }
}

# Backend memory utilization alarm
resource "aws_cloudwatch_metric_alarm" "backend_memory_high" {
  alarm_name          = "dinner1-backend-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "CWAgent"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors backend memory utilization"
  alarm_actions       = [aws_autoscaling_policy.backend_memory_up.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.backend_asg.name
  }
}

# ALB request count alarms
resource "aws_cloudwatch_metric_alarm" "alb_requests_high" {
  alarm_name          = "dinner1-alb-requests-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "RequestCount"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"
  alarm_description   = "This metric monitors ALB request count"
  alarm_actions       = [aws_autoscaling_policy.frontend_requests_up.arn]

  dimensions = {
    LoadBalancer = aws_lb.dinner1_main_alb.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_requests_low" {
  alarm_name          = "dinner1-alb-requests-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "RequestCount"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "200"
  alarm_description   = "This metric monitors ALB request count"
  alarm_actions       = [aws_autoscaling_policy.frontend_requests_down.arn]

  dimensions = {
    LoadBalancer = aws_lb.dinner1_main_alb.arn_suffix
  }
}

# Data source for AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Variables
variable "domain_name" {
  description = "Domain name for SSL certificate"
  type        = string
  default     = "dinner1.com"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.dinner1_main_alb.dns_name
}

output "nlb_dns_name" {
  description = "DNS name of the network load balancer"
  value       = aws_lb.dinner1_nlb.dns_name
}

output "ssl_certificate_arn" {
  description = "ARN of the SSL certificate"
  value       = aws_acm_certificate.dinner1_cert.arn
}
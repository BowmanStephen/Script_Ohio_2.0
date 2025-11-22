# Terraform configuration for Script Ohio 2.0 Production Infrastructure
# Provider configuration
terraform {
  required_version = ">= 1.5.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "script-ohio-2.0"
      Environment = "production"
      ManagedBy   = "terraform"
      Owner       = "platform-ops"
    }
  }
}

# Configure Kubernetes Provider (will be configured after EKS creation)
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

# Configure Helm Provider
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# -----------------------------------------------------------------------------
# VPC and Networking
# -----------------------------------------------------------------------------

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  database_subnets = var.database_subnet_cidrs

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  enable_dns_support     = true

  public_subnet_tags = {
    Type = "Public"
    Tier = "Web"
  }

  private_subnet_tags = {
    Type = "Private"
    Tier = "Application"
  }

  database_subnet_tags = {
    Type = "Private"
    Tier = "Database"
  }

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# -----------------------------------------------------------------------------
# EKS Kubernetes Cluster
# -----------------------------------------------------------------------------

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 19.15"

  cluster_name    = "${var.project_name}-eks"
  cluster_version = var.kubernetes_version
  subnet_ids      = module.vpc.private_subnets

  vpc_id = module.vpc.vpc_id

  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access       = false
  cluster_public_access_cidrs          = []
  cluster_security_group_id            = aws_security_group.eks_cluster.id

  # IAM role for the EKS cluster
  iam_role_arn = aws_iam_role.eks_cluster_role.arn

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    general = {
      name = "general-node-group"

      instance_types = ["m6i.xlarge", "m6a.xlarge"]
      capacity_type  = "ON_DEMAND"

      min_size     = 3
      max_size     = 20
      desired_size = 6

      k8s_labels = {
        node-type = "application"
      }

      taints = {
        application = {
          key    = "node-type"
          value  = "application"
          effect = "NO_SCHEDULE"
        }
      }

      additional_tags = {
        Name        = "${var.project_name}-general-node-group"
        NodeGroup   = "General"
        Kubernetes  = "EKS"
      }
    }

    system = {
      name = "system-node-group"

      instance_types = ["m6i.large"]
      capacity_type  = "ON_DEMAND"

      min_size     = 2
      max_size     = 4
      desired_size = 2

      k8s_labels = {
        node-type = "system"
      }

      additional_tags = {
        Name        = "${var.project_name}-system-node-group"
        NodeGroup   = "System"
        Kubernetes  = "EKS"
      }
    }
  }

  tags = {
    Name = "${var.project_name}-eks"
  }
}

# -----------------------------------------------------------------------------
# Application Load Balancer
# -----------------------------------------------------------------------------

module "alb" {
  source = "terraform-aws-modules/alb/aws"
  version = "~> 8.0"

  name = "${var.project_name}-alb"

  load_balancer_type = "application"
  vpc_id             = module.vpc.vpc_id
  subnets            = module.vpc.public_subnets
  security_groups    = [aws_security_group.alb.id]

  # HTTP to HTTPS redirect
  http_tcp_listeners = {
    http = {
      port        = 80
      protocol    = "HTTP"
      action_type = "redirect"
      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  # HTTPS listener
  https_listeners = {
    https = {
      port               = 443
      protocol           = "HTTPS"
      certificate_arn    = acm_certificate.main.arn
      target_group_index = 0
    }
  }

  target_groups = {
    app = {
      name                             = "${var.project_name}-tg"
      backend_protocol                 = "HTTP"
      backend_port                     = 80
      target_type                      = "ip"
      deregistration_delay             = 30
      health_check = {
        enabled             = true
        healthy_threshold   = 3
        interval            = 30
        matcher             = "200"
        path                = "/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 3
      }
      target_group_tags = {
        Name = "${var.project_name}-tg"
      }
    }
  }

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL Database
# -----------------------------------------------------------------------------

module "rds" {
  source = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-db"

  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.r5.large"

  allocated_storage     = 500
  max_allocated_storage = 1000
  storage_encrypted     = true
  storage_type          = "gp3"

  db_name  = var.database_name
  username = var.database_username
  password = var.database_password
  port     = 5432

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  delete_automated_backups = false
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.project_name}-final-snapshot"

  # Enhanced Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn

  # Performance Insights
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  # Deletion Protection
  deletion_protection = true

  tags = {
    Name = "${var.project_name}-db"
  }
}

# -----------------------------------------------------------------------------
# ElastiCache Redis
# -----------------------------------------------------------------------------

module "elasticache" {
  source = "terraform-aws-modules/elasticache/aws"
  version = "~> 1.0"

  replication_group_id       = "${var.project_name}-redis"
  description                = "Redis cluster for ${var.project_name}"

  node_type                  = "cache.r6g.large"
  port                       = 6379
  parameter_group_name       = "default.redis7"

  num_cache_clusters         = 3
  automatic_failover_enabled = true
  multi_az_enabled          = true

  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token

  log_delivery_configuration = {
    cloudwatch_log_group_name = aws_cloudwatch_log_group.redis.name
  }

  tags = {
    Name = "${var.project_name}-redis"
  }
}

# -----------------------------------------------------------------------------
# S3 Buckets
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-main"
    Environment = "production"
  }
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "backups" {
  bucket = "${var.project_name}-backups-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-backups"
    Environment = "production"
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "backup_retention"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555  # 7 years
    }
  }
}

# -----------------------------------------------------------------------------
# CloudWatch and Monitoring
# -----------------------------------------------------------------------------

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/eks/${module.eks.cluster_name}/application"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-application-logs"
  }
}

resource "aws_cloudwatch_log_group" "redis" {
  name              = "/aws/elasticache/${module.elasticache.replication_group_id}"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-redis-logs"
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"

  tags = {
    Name = "${var.project_name}-alerts"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EKS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors EKS cluster CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = module.eks.cluster_name
  }

  tags = {
    Name = "${var.project_name}-high-cpu-alarm"
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.db_instance_endpoint
}

output "redis_primary_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = module.elasticache.primary_endpoint_address
}

output "load_balancer_dns_name" {
  description = "Load balancer DNS name"
  value       = module.alb.dns_name
}

output "s3_bucket_name" {
  description = "Main S3 bucket name"
  value       = aws_s3_bucket.main.id
}
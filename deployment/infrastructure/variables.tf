# Variables for Script Ohio 2.0 Production Infrastructure

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "script-ohio"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "dr_region" {
  description = "AWS region for disaster recovery"
  type        = string
  default     = "us-west-2"
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "script_ohio_prod"
  sensitive   = true
}

variable "database_username" {
  description = "Username for the database"
  type        = string
  default     = "script_ohio_user"
  sensitive   = true
}

variable "database_password" {
  description = "Password for the database"
  type        = string
  default     = ""
  sensitive   = true
}

variable "redis_auth_token" {
  description = "Auth token for Redis"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for ALB"
  type        = string
  default     = ""
}

variable "enable_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable logging services"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Environment = "production"
    Project     = "script-ohio-2.0"
    ManagedBy   = "terraform"
  }
}
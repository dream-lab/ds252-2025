variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ds252-hybrid"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "lab"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "lambda_timeout" {
  description = "Lambda function timeout"
  type        = number
  default     = 60
}

variable "lambda_memory" {
  description = "Lambda function memory"
  type        = number
  default     = 256
}

variable "random_suffix" {
  description = "Random suffix for resource names to ensure uniqueness"
  type        = string
  default     = ""
}

locals {
  # Use random suffix directly for unique naming
  suffix = random_string.suffix.result
}

# Generate random string for unique naming
resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

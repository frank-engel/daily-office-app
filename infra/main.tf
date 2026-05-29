terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Local state — suitable for a single-developer prototype.
  # To migrate to a shared S3 backend later:
  #   1. Create an S3 bucket and DynamoDB table for state locking.
  #   2. Replace this block with:
  #        backend "s3" {
  #          bucket         = "your-tfstate-bucket"
  #          key            = "daily-office-app/terraform.tfstate"
  #          region         = "us-east-1"
  #          dynamodb_table = "terraform-state-lock"
  #          encrypt        = true
  #        }
  #   3. Run: terraform init -migrate-state
  backend "local" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "daily-office-app"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

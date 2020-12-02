/**
 * # Terraform Module - RotateIAMUserCreds
 *
 * This Terraform module builds and deploys a Lambda function using Python source located at  
 * `src/lambdas/RotateIAMUserCreds` directory, and creates a VPC endpoint attached to Lambda service
 * within the specified VPC and subnets. 
 * 
 * ### Usage: 
 * 
 * ```hcl
 * module "RotateIAMUserCreds" {
 *   source                 = "./RotateIAMUserCreds"
 * 
 *   app_name               = "RotateUserAccessKey"
 *   app_shortcode          = "RotateUAK"
 *   aws_env                = "Dev"
 *   aws_profile            = "default"
 *   aws_region             = "us-east-1"
 *   iam_user_name          = "myuser"
 *   principal_arn          = "arn:aws:iam::012345678910:role/MyDevOpsRole"
 *   source_cidr_blocks     = [ "200.20.2.0/24" ]
 *   subnet_ids             = [ "subnet-a1b2c3d4", "subnet-e5f6a7b8", "subnet-c9d0e1f2" ]
 *   vpc_id                 = "vpc-f0e1d2c3b4"
 * }
 * ```
 *
 */

terraform {
  required_version        = ">= 0.12.24"
  required_providers {
    aws                   = ">= 3.11.0"
    archive               = "~> 2.0.0"
    null                  = "~> 3.0.0"
  }
}

provider "aws" {
  profile                 = var.aws_profile
  region                  = var.aws_region
}

locals {
  # Common tags to be assigned to all resources
  common_tags             = {
    Application           = var.app_name
    Environment           = var.aws_env
  }
}

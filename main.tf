/**
 * # RotateIAMUserCreds - Root Terraform Module
 *
 * TODO
 * 
 * 
 */

terraform {
  required_version        = ">= 0.13"
  required_providers {
    aws                   = ">= 3.11.0"
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
    Project               = "${var.app_name} - Demo"
    Environment           = var.aws_env
  }
}

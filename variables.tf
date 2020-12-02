variable "aws_profile" {
  type                    = string
  default                 = "default"
  description             = "Specify an aws profile name to be used for access credentials (run `aws configure help` for more information on creating a new profile)"
}

variable "aws_region" {
  type                    = string
  default                 = "us-east-1"
  description             = "Specify the AWS region to be used for resource creations"
}

variable "aws_env" {
  type                    = string
  default                 = "dev"
  description             = "Specify a value for the Environment tag"
}

variable "app_name" {
  type                    = string
  default                 = "RotateIAMUserCreds"
  description             = "Specify an application or project name, used primarily for tagging"
}

variable "app_shortcode" {
  type                    = string
  default                 = "RtUsr"
  description             = "Specify a short-code or pneumonic for this application or project"
}

variable "vpc_id" {
  type                    = string
  description             = "Specify a VPC ID for attaching a Lambda VPC endpoint"
}

variable "subnet_ids" {
  type                    = list 
  description             = "Specify a list of Subnet IDs where Lambda VPC endpoint will be deployed"
}

variable "principal_arn" {
  type                    = string 
  description             = "Specify ARN of Principal to grant Lambda invoke access at VPC endpoint"
}

variable "source_cidr_blocks" {
  type                    = list
  description             = "Specify list of source CIDR ranges for Lambda VPC endpoint's security group ingress rules"
}

variable "iam_user_name" {
  type                    = string 
  description             = "Specify an IAM User name whose access keys will be managed by Lambda"
}

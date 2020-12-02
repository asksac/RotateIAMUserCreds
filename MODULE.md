# Terraform Module - RotateIAMUserCreds

This Terraform module builds and deploys a Lambda function using Python source located at
`src/lambdas/RotateIAMUserCreds` directory, and creates a VPC endpoint attached to Lambda service  
within the specified VPC and subnets.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 0.12.24 |
| archive | ~> 2.0.0 |
| aws | >= 3.11.0 |
| null | ~> 3.0.0 |

## Providers

| Name | Version |
|------|---------|
| archive | ~> 2.0.0 |
| aws | >= 3.11.0 |
| null | ~> 3.0.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| app\_name | Specify an application or project name, used primarily for tagging | `string` | `"RotateIAMUserCreds"` | no |
| app\_shortcode | Specify a short-code or pneumonic for this application or project | `string` | `"RtUsr"` | no |
| aws\_env | Specify a value for the Environment tag | `string` | `"dev"` | no |
| aws\_profile | Specify an aws profile name to be used for access credentials (run `aws configure help` for more information on creating a new profile) | `string` | `"default"` | no |
| aws\_region | Specify the AWS region to be used for resource creations | `string` | `"us-east-1"` | no |
| iam\_user\_name | Specify an IAM User name whose access keys will be managed by Lambda | `string` | n/a | yes |
| principal\_arn | Specify ARN of Principal to grant Lambda invoke access at VPC endpoint | `string` | n/a | yes |
| source\_cidr\_blocks | Specify list of source CIDR ranges for Lambda VPC endpoint's security group ingress rules | `list` | n/a | yes |
| subnet\_ids | Specify a list of Subnet IDs where Lambda VPC endpoint will be deployed | `list` | n/a | yes |
| vpc\_id | Specify a VPC ID for attaching a Lambda VPC endpoint | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| endpoint\_dns | List of Private DNS entries associated with the Lambda VPC endpoint |
| lambda\_arn | ARN of RotateIAMUserCreds Lambda |


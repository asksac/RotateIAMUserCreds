# define terraform module output values here 
output "lambda_arn" {
  description             = "ARN of RotateIAMUserCreds Lambda"
  value                   = aws_lambda_function.mylambda_func.arn
}

output "endpoint_dns" {
  description             = "List of Private DNS entries associated with the Lambda VPC endpoint"
  value                   = aws_vpc_endpoint.mylambda_endpoint.dns_entry 
}

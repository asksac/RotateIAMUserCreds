# create a security group for lambda vpc endpoint
# lambda endpoint only require 443 ingress port access
resource "aws_security_group" "mylambda_endpoint_sg" {
  name                        = "${var.app_shortcode}_vpc_endpoint_sg"
  vpc_id                      = var.vpc_id

  ingress {
    cidr_blocks               = var.source_cidr_blocks
    from_port                 = 443
    to_port                   = 443
    protocol                  = "tcp"
  }

  tags                        = local.common_tags
}

# create a vpc endpoint for lambda and deploy in specified subnets
# restrict access granted through this endpoint to only lambda:InvokeFunction call
resource "aws_vpc_endpoint" "mylambda_endpoint" {
  service_name                = "com.amazonaws.${var.aws_region}.lambda"
  vpc_id                      = var.vpc_id
  subnet_ids                  = var.subnet_ids
  private_dns_enabled         = true

  auto_accept                 = true
  vpc_endpoint_type           = "Interface"

  security_group_ids          = [ aws_security_group.mylambda_endpoint_sg.id ]

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowLambdaInvokeFunctionOnly", 
      "Principal": {
        "AWS": "${var.principal_arn}"
      },
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "${aws_lambda_function.mylambda_func.arn}"
      ]
    }
  ]
}
POLICY

  tags                        = merge(local.common_tags, map("Name", "${var.app_shortcode}_lambda_endpoint"))
}

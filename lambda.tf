#
# Upload and create RotateIAMUserCreds Lambda function
#
resource "null_resource" "mylambda_build" {
  triggers = {
    handler       = filesha1("src/lambdas/RotateIAMUserCreds/main.py")
    requirements  = filesha1("src/lambdas/RotateIAMUserCreds/requirements.txt")
    build         = filesha1("src/lambdas/RotateIAMUserCreds/build.sh")
  }

  provisioner "local-exec" {
    command       = "${path.module}/src/lambdas/RotateIAMUserCreds/build.sh"
  }
}

data "archive_file" "mylambda_archive" {
  source_dir  = "${path.module}/dist/lambdas/RotateIAMUserCreds/"
  output_path = "${path.module}/dist/RotateIAMUserCreds.zip"
  type        = "zip"

  depends_on = [ null_resource.mylambda_build ]
}

resource "aws_lambda_function" "mylambda_func" {
  function_name    = "RotateIAMUserCreds"

  handler          = "main.lambda_handler"
  role             = aws_iam_role.lambda_exec_role.arn
  runtime          = "python3.7"
  timeout          = 60

  filename         = data.archive_file.mylambda_archive.output_path
  source_code_hash = data.archive_file.mylambda_archive.output_base64sha256

  environment {
    variables = {
      IAM_USER_NAME = var.iam_user_name
    }
  }

  tags             = local.common_tags
}


# Create Lambda execution IAM role, giving permissions to access other AWS services

resource "aws_iam_role" "lambda_exec_role" {
  name                = "${var.app_shortcode}_Lambda_Exec_Role"
  assume_role_policy  = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
      {
      "Action": [
        "sts:AssumeRole"
      ],
      "Principal": {
          "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": "LambdaAssumeRolePolicy"
      }
  ]
}
EOF
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "${var.app_shortcode}_Lambda_Policy"
  path        = "/"
  description = "IAM policy with minimum permissions for ${var.app_name} Lambda function"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*",
      "Effect": "Allow"
    }, 
    {
      "Action": [
        "iam:ListUsers",
        "iam:CreateAccessKey",
        "iam:DeleteAccessKey",
        "iam:GetAccessKeyLastUsed",
        "iam:GetUser",
        "iam:ListAccessKeys",
        "iam:UpdateAccessKey"
      ],
      "Resource": "*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_exec_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}


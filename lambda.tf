#
# Upload and create RotateIAMUserCreds Lambda function
#
resource "null_resource" "riuc_build" {
  triggers = {
    handler       = filesha1("src/lambdas/RotateIAMUserCreds/main.py")
    requirements  = filesha1("src/lambdas/RotateIAMUserCreds/requirements.txt")
    build         = filesha1("src/lambdas/RotateIAMUserCreds/build.sh")
  }

  provisioner "local-exec" {
    command       = "${path.module}/src/lambdas/RotateIAMUserCreds/build.sh"
  }
}

data "archive_file" "riuc_archive" {
  source_dir  = "${path.module}/dist/lambdas/RotateIAMUserCreds/"
  output_path = "${path.module}/dist/RotateIAMUserCreds.zip"
  type        = "zip"

  depends_on = [ null_resource.riuc_build ]
}

resource "aws_lambda_function" "riuc_lambda" {
  function_name    = "RotateIAMUserCreds"

  handler          = "main.lambda_handler"
  role             = aws_iam_role.lambda_exec_role.arn
  runtime          = "python3.7"
  timeout          = 60

  filename         = data.archive_file.riuc_archive.output_path
  source_code_hash = data.archive_file.riuc_archive.output_base64sha256

  environment {
    variables = {
      IAM_USER_NAME = "x"
      IAM_ACCESS_KEY_MIN_AGE = "0"
    }
  }

  tags             = local.common_tags
}


# Create Lambda execution IAM role, giving permissions to access other AWS services

resource "aws_iam_role" "lambda_exec_role" {
  name = "riuc_lambda_exec_role"
  assume_role_policy = <<EOF
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
  name        = "riuc_lambda_policy"
  path        = "/"
  description = "IAM policy with basic permissions for Lambda"

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
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:*",
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


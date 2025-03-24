# Data source for account ID
data "aws_caller_identity" "current" {}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  count = var.create_lambda ? 1 : 0
  name  = "${var.lambda_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# CloudWatch Alarms policy
resource "aws_iam_policy" "cloudwatch_alarms_policy" {
  count       = var.create_lambda ? 1 : 0
  name        = "${var.lambda_function_name}-cloudwatch-alarms"
  description = "Allow managing CloudWatch alarms and publishing to SNS"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "cloudwatch:PutMetricAlarm",
          "cloudwatch:DescribeAlarms",
          "cloudwatch:DeleteAlarms",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "sns:Publish"
        ]
        Effect   = "Allow"
        Resource = aws_sns_topic.lambda_alarms[0].arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_alarms_access" {
  count      = var.create_lambda ? 1 : 0
  role       = aws_iam_role.lambda_role[0].name
  policy_arn = aws_iam_policy.cloudwatch_alarms_policy[0].arn
}

# Lambda basic execution policy (for CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  count      = var.create_lambda ? 1 : 0
  role       = aws_iam_role.lambda_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Cost Explorer access policy
resource "aws_iam_policy" "cost_explorer_access" {
  count       = var.create_lambda ? 1 : 0
  name        = "${var.lambda_function_name}-cost-explorer-access"
  description = "Allow access to AWS Cost Explorer API"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "ce:GetCostAndUsage"
      ]
      Effect   = "Allow"
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cost_explorer_access" {
  count      = var.create_lambda ? 1 : 0
  role       = aws_iam_role.lambda_role[0].name
  policy_arn = aws_iam_policy.cost_explorer_access[0].arn
}

# Bedrock access policy
resource "aws_iam_policy" "bedrock_access" {
  count       = var.create_lambda ? 1 : 0
  name        = "${var.lambda_function_name}-bedrock-access"
  description = "Allow access to Amazon Bedrock models"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "bedrock:InvokeModel"
      ]
      Effect   = "Allow"
      Resource = "*"
    }]
  })
}

# Attach Bedrock access policy to Lambda role
resource "aws_iam_role_policy_attachment" "bedrock_access" {
  count      = var.create_lambda ? 1 : 0
  role       = aws_iam_role.lambda_role[0].name
  policy_arn = aws_iam_policy.bedrock_access[0].arn
}


# IAM Policy for accessing the DynamoDB table
resource "aws_iam_policy" "ddb_access_policy" {
  count       = var.create_dynamodb ? 1 : 0
  name        = "${var.dynamodb_table_name}-policy"
  description = "Allows access to AWS Feature Announcements DynamoDB table"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DescribeTable"
        ]
        Effect   = "Allow"
        Resource = var.create_dynamodb ? aws_dynamodb_table.aws_feature_announcements_ddb_table[0].arn : "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.dynamodb_table_name}"
      }
    ]
  })
}

# DynamoDB access policy attachment for Lambda role
resource "aws_iam_role_policy_attachment" "dynamodb_access" {
  count      = var.create_lambda && var.create_dynamodb ? 1 : 0
  role       = aws_iam_role.lambda_role[0].name
  policy_arn = aws_iam_policy.ddb_access_policy[0].arn
}

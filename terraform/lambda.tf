# Lambda function
resource "aws_lambda_function" "personalized_aws_features" {
  count            = var.create_lambda ? 1 : 0
  function_name    = var.lambda_function_name
  description      = "AWS service feature notifier based on your usage patterns"
  filename         = "${path.module}/lambda_function.zip"
  source_code_hash = var.create_lambda ? filebase64sha256("${path.module}/lambda_function.zip") : null
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.13"
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout
  role             = aws_iam_role.lambda_role[0].arn
  logging_config {
    log_format = "JSON"
  }

  environment {
    variables = {
      DDB_TABLE      = var.create_dynamodb ? aws_dynamodb_table.aws_feature_announcements_ddb_table[0].name : var.dynamodb_table_name
      BEDROCK_MODEL  = var.bedrock_model
      DAYS_BACK      = tostring(var.days_back)
      MAX_WORKERS    = tostring(var.max_workers)
      APP_AWS_REGION = var.aws_region
      LOG_LEVEL      = var.log_level
      NO_HISTORY     = var.create_dynamodb ? "false" : "true"
      SLACK_ENABLED  = tostring(var.slack_enabled)
      SLACK_TOKEN    = var.slack_token
      SLACK_CHANNEL  = var.slack_channel
      VERBOSE        = tostring(var.verbose)
    }
  }
}

# CloudWatch Event Rule
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  count               = var.create_lambda ? 1 : 0
  name                = "${var.lambda_function_name}-schedule"
  description         = "Schedule for running AWS Feature Notifier Lambda"
  schedule_expression = var.schedule_expression
}

# CloudWatch Event Target
resource "aws_cloudwatch_event_target" "lambda_target" {
  count     = var.create_lambda ? 1 : 0
  rule      = aws_cloudwatch_event_rule.lambda_schedule[0].name
  target_id = "personalized-aws-features"
  arn       = aws_lambda_function.personalized_aws_features[0].arn
}

# Lambda permission for CloudWatch Event
resource "aws_lambda_permission" "allow_cloudwatch" {
  count         = var.create_lambda ? 1 : 0
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.personalized_aws_features[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule[0].arn
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  count             = var.create_lambda ? 1 : 0
  name              = "/aws/lambda/${aws_lambda_function.personalized_aws_features[0].function_name}"
  retention_in_days = var.log_retention_days
}

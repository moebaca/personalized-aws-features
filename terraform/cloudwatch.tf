# SNS Topic for alarm notifications
resource "aws_sns_topic" "lambda_alarms" {
  count = var.create_lambda ? 1 : 0
  name  = "${var.lambda_function_name}-alarms"
}

# Optional: SNS Topic subscription - Uncomment and configure as needed
resource "aws_sns_topic_subscription" "lambda_alarms_email" {
  count     = var.create_lambda && var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.lambda_alarms[0].arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# CloudWatch Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count               = var.create_lambda ? 1 : 0
  alarm_name          = "${var.lambda_function_name}-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "This alarm monitors for errors in the AWS Feature Notifier Lambda function"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.personalized_aws_features[0].function_name
  }

  alarm_actions = [aws_sns_topic.lambda_alarms[0].arn]
  ok_actions    = [aws_sns_topic.lambda_alarms[0].arn]
}

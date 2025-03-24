output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = var.create_lambda ? aws_lambda_function.personalized_aws_features[0].function_name : "Lambda function not created"
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = var.create_lambda ? aws_lambda_function.personalized_aws_features[0].arn : "Lambda function not created"
}

output "cloudwatch_event_rule_name" {
  description = "Name of the CloudWatch Event rule"
  value       = var.create_lambda ? aws_cloudwatch_event_rule.lambda_schedule[0].name : "CloudWatch Event rule not created"
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for tracking announcements"
  value       = var.create_dynamodb ? aws_dynamodb_table.aws_feature_announcements_ddb_table[0].name : "DynamoDB table not created"
}

output "lambda_role_name" {
  description = "Name of the IAM role for the Lambda function"
  value       = var.create_lambda ? aws_iam_role.lambda_role[0].name : "Lambda role not created"
}

output "lambda_role_arn" {
  description = "ARN of the IAM role for the Lambda function"
  value       = var.create_lambda ? aws_iam_role.lambda_role[0].arn : "Lambda role not created"
}

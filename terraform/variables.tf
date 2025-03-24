variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  type        = string
  default     = "personalized-aws-features-terraform-state"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for tracking announcements"
  type        = string
  default     = "personalized-aws-features"
}

variable "dynamodb_table_billing_mode" {
  description = "DynamoDB table billing mode"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "create_dynamodb" {
  description = "Whether to create DynamoDB table or not"
  type        = bool
  default     = true
}

variable "create_lambda" {
  description = "Whether to create Lambda function and associated resources"
  type        = bool
  default     = true
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "personalized-aws-features"
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda function in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 300
}

variable "schedule_expression" {
  description = "CloudWatch Event schedule expression"
  type        = string
  default     = "cron(0 12 * * ? *)" # Run at 12:00 PM UTC every day
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch Logs"
  type        = number
  default     = 30
}

variable "bedrock_model" {
  description = "Bedrock model ID to use for service identification and summarization"
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "days_back" {
  description = "Number of days to look back for announcements"
  type        = number
  default     = 7
}

variable "max_workers" {
  description = "Number of parallel workers for processing announcements"
  type        = number
  default     = 10
}

variable "log_level" {
  description = "Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
  type        = string
  default     = "INFO"
}

variable "slack_enabled" {
  description = "Whether to enable Slack notifications"
  type        = bool
  default     = true
}

variable "slack_token" {
  description = "Slack API token (xoxb-xxxxxx)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_channel" {
  description = "Slack channel to post to (e.g., #personalized-aws-features)"
  type        = string
  default     = ""
}

variable "verbose" {
  description = "Enable verbose output in Lambda"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email address to notify for alarms (leave empty to disable email notifications)"
  type        = string
  default     = "moebaca@hotmail.com"
}

# DynamoDB table for tracking announcements
resource "aws_dynamodb_table" "aws_feature_announcements_ddb_table" {
  count        = var.create_dynamodb ? 1 : 0
  name         = var.dynamodb_table_name
  billing_mode = var.dynamodb_table_billing_mode
  hash_key     = "announcement_id"

  attribute {
    name = "announcement_id"
    type = "S"
  }
  tags = {
    Name = "personalized-aws-features"
  }
}

#!/usr/bin/env python3
"""
Lambda handler for Personalized AWS Features.
"""

import os
import json
from personalized_aws_features.core.processor import process_features
from personalized_aws_features.core.logger import setup_logging, logger


def lambda_handler(event, context):
    """
    AWS Lambda handler for Personalized AWS Features.
    """
    # Get configuration from environment variables
    config = {
        "days": int(os.environ.get("DAYS_BACK", "7")),
        "workers": int(os.environ.get("MAX_WORKERS", "10")),
        "model": os.environ.get("BEDROCK_MODEL", "amazon.nova-lite-v1:0"),
        "region": os.environ.get("APP_AWS_REGION", "us-east-1"),
        "no_history": os.environ.get("NO_HISTORY", "false").lower() == "true",
        "ddb_table": os.environ.get("DDB_TABLE", "personalized-aws-features"),
        "verbose": os.environ.get("VERBOSE", "false").lower() == "true",
        "slack_enabled": os.environ.get("SLACK_ENABLED", "false").lower() == "true",
        "slack_token": os.environ.get("SLACK_TOKEN", ""),
        "slack_channel": os.environ.get("SLACK_CHANNEL", ""),
        "log_level": os.environ.get("LOG_LEVEL", "INFO"),
    }

    setup_logging(log_level=config["log_level"])

    try:
        # Process features using the core processor
        logger.info("Starting AWS Feature Notifier Lambda handler")
        result = process_features(config)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "AWS Feature Notifier executed successfully",
                    "result": result,
                }
            ),
        }
    except Exception as e:
        logger.error(f"Error executing AWS Feature Notifier: {e}", exc_info=True)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Error executing AWS Feature Notifier", "error": str(e)}
            ),
        }

#!/usr/bin/env python3
"""
Main application runner for the AWS Feature Notifier.
Supports  CLI execution.
"""

import argparse
import sys
from typing import List, Optional

from personalized_aws_features.core.processor import process_features
from personalized_aws_features.core.logger import setup_logging, logger


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AWS Feature Notifier based on your usage patterns"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for announcements (default: 7)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of parallel workers for processing announcements (default: 10)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="amazon.nova-lite-v1:0",
        help="Bedrock model ID to use for service identification and summarization (default: amazon.nova-lite-v1:0)",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region for Cost Explorer and DynamoDB (default: us-east-1)",
    )
    parser.add_argument(
        "--no-history", action="store_true", help="Disable DynamoDB history tracking"
    )
    parser.add_argument(
        "--ddb-table",
        type=str,
        default="personalized-aws-features",
        help="DynamoDB table for tracking processed announcements (default: personalized-aws-features)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed announcement information",
    )
    parser.add_argument(
        "--slack-enabled",
        action="store_true",
        help="Enable sending announcements to Slack",
    )
    parser.add_argument(
        "--slack-token",
        type=str,
        help="Slack API token (xoxb-xxxxxx)",
    )
    parser.add_argument(
        "--slack-channel",
        type=str,
        help="Slack channel to post to (e.g., #aws-updates)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the AWS Feature Notifier."""

    # Parse arguments
    parsed_args = parse_args(args)

    # Convert namespace to dict for easier handling
    config = vars(parsed_args)

    # Initialize logging
    setup_logging(log_level=config["log_level"])

    try:
        # Process features using the core processor
        process_features(config)
        return 0
    except Exception as e:
        logger.error(f"{e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

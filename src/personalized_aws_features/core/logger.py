#!/usr/bin/env python3
"""
Simple logging configuration for AWS Feature Notifier.
"""

import logging
import os

# Create the base logger
logger = logging.getLogger("personalized_aws_features")


def setup_logging(log_level="INFO") -> logging.Logger:
    """
    Set up basic logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Determine if running in aws (simpler timestamps for CloudWatch)
    is_aws_env = "AWS_EXECUTION_ENV" in os.environ

    # Set format based on environment
    log_format = (
        "%(levelname)s - %(name)s - %(message)s"
        if is_aws_env
        else "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Configure logging
    logging.basicConfig(level=numeric_level, format=log_format)
    logger.setLevel(numeric_level)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    return logger

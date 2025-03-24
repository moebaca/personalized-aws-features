#!/usr/bin/env python3
"""
Unit tests for logger.py
"""

import logging
from unittest.mock import patch
import os
from personalized_aws_features.core.logger import setup_logging, logger


class TestLogger:
    """Tests for the logger module."""

    def test_logger_exists(self):
        """Test that the logger exists and is configured."""
        assert logger.name == "personalized_aws_features"

    @patch("logging.basicConfig")
    def test_setup_logging_default(self, mock_basic_config):
        """Test setup_logging with default log level."""
        result = setup_logging()

        assert result == logger
        assert logger.level == logging.INFO
        mock_basic_config.assert_called_once()

        # Check format - should be the default (non-AWS) format
        format_arg = mock_basic_config.call_args[1]["format"]
        assert "%(asctime)s" in format_arg

    @patch("logging.basicConfig")
    def test_setup_logging_debug(self, mock_basic_config):
        """Test setup_logging with DEBUG log level."""
        result = setup_logging("DEBUG")

        assert result == logger
        assert logger.level == logging.DEBUG
        mock_basic_config.assert_called_once()

        # Check level passed to basicConfig
        level_arg = mock_basic_config.call_args[1]["level"]
        assert level_arg == logging.DEBUG

    @patch("logging.basicConfig")
    @patch.dict(os.environ, {"AWS_EXECUTION_ENV": "AWS_Lambda_python3.13"})
    def test_setup_logging_aws_env(self, mock_basic_config):
        """Test setup_logging in AWS environment."""
        result = setup_logging()

        assert result == logger

        # Check format - should be the AWS format (without timestamps)
        format_arg = mock_basic_config.call_args[1]["format"]
        assert "%(asctime)s" not in format_arg
        assert "%(levelname)s - %(name)s - %(message)s" == format_arg

    @patch("logging.basicConfig")
    def test_setup_logging_invalid_level(self, mock_basic_config):
        """Test setup_logging with invalid log level falls back to INFO."""
        result = setup_logging("INVALID")

        assert result == logger
        assert logger.level == logging.INFO

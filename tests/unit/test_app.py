#!/usr/bin/env python3
"""
Unit tests for app.py
"""

from unittest.mock import patch
from personalized_aws_features.cli import parse_args, main


class TestApp:
    """Tests for the app module."""

    def test_parse_args_defaults(self):
        """Test parse_args with default values."""
        args = parse_args([])

        assert args.days == 7
        assert args.workers == 10
        assert args.model == "amazon.nova-lite-v1:0"
        assert args.region == "us-east-1"
        assert args.no_history is False
        assert args.ddb_table == "personalized-aws-features"
        assert args.verbose is False
        assert args.slack_enabled is False
        assert args.slack_token is None
        assert args.slack_channel is None
        assert args.log_level == "INFO"

    def test_parse_args_custom_values(self):
        """Test parse_args with custom values."""
        args = parse_args(
            [
                "--days",
                "14",
                "--workers",
                "5",
                "--model",
                "custom-model",
                "--region",
                "us-west-2",
                "--no-history",
                "--ddb-table",
                "custom-table",
                "--verbose",
                "--slack-enabled",
                "--slack-token",
                "xoxb-test-token",
                "--slack-channel",
                "#test-channel",
                "--log-level",
                "DEBUG",
            ]
        )

        assert args.days == 14
        assert args.workers == 5
        assert args.model == "custom-model"
        assert args.region == "us-west-2"
        assert args.no_history is True
        assert args.ddb_table == "custom-table"
        assert args.verbose is True
        assert args.slack_enabled is True
        assert args.slack_token == "xoxb-test-token"
        assert args.slack_channel == "#test-channel"
        assert args.log_level == "DEBUG"

    @patch("personalized_aws_features.cli.process_features")
    @patch("personalized_aws_features.cli.setup_logging")
    def test_main_success(self, mock_setup_logging, mock_process_features):
        """Test main function successful execution."""
        # Configure the mock to not raise an exception
        mock_process_features.return_value = {
            "service_count": 5,
            "announcement_count": 10,
        }

        # Call the main function with some args
        result = main(["--days", "3", "--verbose"])

        # Verify the expected behavior
        assert result == 0  # Should return 0 for success
        mock_setup_logging.assert_called_once()
        mock_process_features.assert_called_once()

        # Check the config passed to process_features
        config = mock_process_features.call_args[0][0]
        assert config["days"] == 3
        assert config["verbose"] is True

    @patch("personalized_aws_features.cli.process_features")
    @patch("personalized_aws_features.cli.setup_logging")
    def test_main_exception(self, mock_setup_logging, mock_process_features):
        """Test main function with exception."""
        # Configure the mock to raise an exception
        mock_process_features.side_effect = Exception("Test error")

        # Call the main function
        result = main([])

        # Verify the expected behavior
        assert result == 1  # Should return 1 for failure
        mock_setup_logging.assert_called_once()
        mock_process_features.assert_called_once()

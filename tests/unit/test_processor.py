#!/usr/bin/env python3
"""
Unit tests for processor.py
"""

import pytest
from unittest.mock import patch, MagicMock
from personalized_aws_features.core.processor import (
    initialize_results,
    setup_dynamodb,
    get_and_analyze_services,
    fetch_and_process_announcements,
    filter_seen_announcements,
    send_slack_notifications,
    process_features,
)


class TestProcessorFunctions:
    """Tests for individual processor functions."""

    def test_initialize_results(self):
        """Test initialize_results function."""
        results = initialize_results()

        assert results["service_count"] == 0
        assert results["announcement_count"] == 0
        assert results["relevant_count"] == 0
        assert results["filtered_history_count"] == 0

    @patch("personalized_aws_features.core.processor.get_dynamodb_table")
    def test_setup_dynamodb_enabled(self, mock_get_table):
        """Test setup_dynamodb with history enabled."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        result = setup_dynamodb("test-table", "us-east-1", False)

        assert result == mock_table
        mock_get_table.assert_called_once_with(
            table_name="test-table", region="us-east-1"
        )

    @patch("personalized_aws_features.core.processor.get_dynamodb_table")
    def test_setup_dynamodb_disabled(self, mock_get_table):
        """Test setup_dynamodb with history disabled."""
        result = setup_dynamodb("test-table", "us-east-1", True)

        assert result is None
        mock_get_table.assert_not_called()

    @patch("personalized_aws_features.core.processor.get_services")
    def test_get_and_analyze_services(self, mock_get_services, sample_services):
        """Test get_and_analyze_services function."""
        mock_get_services.return_value = sample_services

        user_services, service_count, services_list = get_and_analyze_services()

        assert user_services == sample_services
        assert service_count == 5
        assert services_list == [
            "AWS Lambda",
            "Amazon EC2",
            "Amazon RDS",
            "Amazon S3",
            "Amazon VPC",
        ]

    @patch("personalized_aws_features.core.processor.process_announcements_in_parallel")
    @patch("personalized_aws_features.core.processor.fetch_aws_whats_new")
    def test_fetch_and_process_announcements(
        self, mock_fetch, mock_process, sample_announcements, sample_services
    ):
        """Test fetch_and_process_announcements function."""
        mock_fetch.return_value = sample_announcements

        # Mock relevant and non-relevant announcements
        relevant = [sample_announcements[0], sample_announcements[1]]
        non_relevant = [sample_announcements[2]]
        mock_process.return_value = (relevant, non_relevant)

        result_relevant, result_non_relevant = fetch_and_process_announcements(
            7, sample_services, "test-model", 5, "us-east-1"
        )

        assert result_relevant == relevant
        assert result_non_relevant == non_relevant
        mock_fetch.assert_called_once_with(days_back=7)
        mock_process.assert_called_once_with(
            sample_announcements, sample_services, "test-model", 5, "us-east-1"
        )

    @patch("personalized_aws_features.core.processor.is_announcement_seen")
    def test_filter_seen_announcements(
        self, mock_is_seen, sample_processed_announcements
    ):
        """Test filter_seen_announcements function."""
        # First announcement is seen, others are new
        mock_is_seen.side_effect = [True, False, False]

        mock_table = MagicMock()
        new_announcements, filtered_announcements = filter_seen_announcements(
            sample_processed_announcements, mock_table, True
        )

        assert len(new_announcements) == 2
        assert len(filtered_announcements) == 1
        assert filtered_announcements[0] == sample_processed_announcements[0]
        assert new_announcements[0] == sample_processed_announcements[1]
        assert new_announcements[1] == sample_processed_announcements[2]

    def test_filter_seen_announcements_disabled(self, sample_processed_announcements):
        """Test filter_seen_announcements with history disabled."""
        mock_table = MagicMock()
        new_announcements, filtered_announcements = filter_seen_announcements(
            sample_processed_announcements, mock_table, False
        )

        assert new_announcements == sample_processed_announcements
        assert filtered_announcements == []

    @patch("personalized_aws_features.core.processor.send_announcements_to_slack")
    def test_send_slack_notifications_success(
        self, mock_send, sample_processed_announcements
    ):
        """Test send_slack_notifications function success case."""
        # Mock successful sending
        mock_send.return_value = {"success": 3, "failure": 0}

        results = {}
        send_slack_notifications(
            sample_processed_announcements, "test-token", "#test-channel", results
        )

        assert results["slack_success"] == 3
        assert results["slack_failure"] == 0
        mock_send.assert_called_once_with(
            sample_processed_announcements, "test-token", "#test-channel"
        )

    @patch("personalized_aws_features.core.processor.send_announcements_to_slack")
    def test_send_slack_notifications_failure(
        self, mock_send, sample_processed_announcements
    ):
        """Test send_slack_notifications function failure case."""
        # Mock failed sending
        mock_send.return_value = {"success": 1, "failure": 2}

        results = {}
        with pytest.raises(RuntimeError):
            send_slack_notifications(
                sample_processed_announcements, "test-token", "#test-channel", results
            )

        assert results["slack_success"] == 1
        assert results["slack_failure"] == 2


class TestProcessFeatures:
    """Tests for the main process_features function."""

    @patch("personalized_aws_features.core.processor.setup_dynamodb")
    @patch("personalized_aws_features.core.processor.get_and_analyze_services")
    @patch("personalized_aws_features.core.processor.fetch_and_process_announcements")
    @patch("personalized_aws_features.core.processor.filter_seen_announcements")
    @patch("personalized_aws_features.core.processor.save_announcement")
    @patch("personalized_aws_features.core.processor.display_announcement_list")
    @patch("personalized_aws_features.core.processor.display_detailed_announcements")
    @patch("personalized_aws_features.core.processor.display_service_summary")
    def test_process_features_success(
        self,
        mock_display_summary,
        mock_display_detailed,
        mock_display_list,
        mock_save,
        mock_filter,
        mock_fetch_process,
        mock_get_services,
        mock_setup_ddb,
        sample_config,
        sample_services,
        sample_processed_announcements,
    ):
        """Test process_features function successful execution."""
        # Setup mocks
        mock_ddb = MagicMock()
        mock_setup_ddb.return_value = mock_ddb

        # Service mocks
        mock_get_services.return_value = (
            sample_services,
            5,
            ["AWS Lambda", "Amazon EC2", "Amazon RDS", "Amazon S3", "Amazon VPC"],
        )

        # Announcement mocks
        relevant = [
            sample_processed_announcements[0],
            sample_processed_announcements[1],
        ]
        non_relevant = [sample_processed_announcements[2]]
        mock_fetch_process.return_value = (relevant, non_relevant)

        # Filtering mocks - one announcement is filtered out
        filtered_relevant = [relevant[1]]
        filtered_out = [relevant[0]]
        mock_filter.return_value = (filtered_relevant, filtered_out)

        # Call the function
        results = process_features(sample_config)

        # Verify the expected behavior and results
        assert results["service_count"] == 5
        assert results["announcement_count"] == 3
        assert results["relevant_count"] == 2
        assert results["filtered_history_count"] == 1

        # Check function calls
        mock_setup_ddb.assert_called_once()
        mock_get_services.assert_called_once()
        mock_fetch_process.assert_called_once()
        mock_filter.assert_called_once()
        mock_save.assert_called_once_with(filtered_relevant, mock_ddb)

        # Check if display functions were called (verbose is True)
        mock_display_summary.assert_called_once()
        mock_display_list.assert_called()
        mock_display_detailed.assert_called_once()

    @patch("personalized_aws_features.core.processor.setup_dynamodb")
    @patch("personalized_aws_features.core.processor.get_and_analyze_services")
    @patch("personalized_aws_features.core.processor.fetch_and_process_announcements")
    def test_process_features_no_announcements(
        self,
        mock_fetch_process,
        mock_get_services,
        mock_setup_ddb,
        sample_config,
        sample_services,
    ):
        """Test process_features function with no relevant announcements."""
        # Setup mocks
        mock_ddb = MagicMock()
        mock_setup_ddb.return_value = mock_ddb

        # Service mocks
        mock_get_services.return_value = (
            sample_services,
            5,
            ["AWS Lambda", "Amazon EC2", "Amazon RDS", "Amazon S3", "Amazon VPC"],
        )

        # No relevant announcements
        mock_fetch_process.return_value = ([], [])

        # Call the function
        results = process_features(sample_config)

        # Verify results
        assert results["service_count"] == 5
        assert results["announcement_count"] == 0
        assert results["relevant_count"] == 0

    @patch("personalized_aws_features.core.processor.setup_dynamodb")
    @patch("personalized_aws_features.core.processor.get_and_analyze_services")
    def test_process_features_exception(
        self, mock_get_services, mock_setup_ddb, sample_config
    ):
        """Test process_features function with an exception."""
        # Setup mocks to raise an exception
        mock_get_services.side_effect = Exception("Test error")

        # Call the function and expect an exception
        with pytest.raises(Exception):
            process_features(sample_config)

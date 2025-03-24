#!/usr/bin/env python3
"""
Shared pytest fixtures for AWS Feature Notifier unit tests.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


@pytest.fixture
def sample_config():
    """Sample configuration for tests."""
    return {
        "days": 7,
        "workers": 5,
        "model": "amazon.nova-lite-v1:0",
        "region": "us-east-1",
        "no_history": False,
        "ddb_table": "test-table",
        "verbose": True,
        "slack_enabled": False,
        "log_level": "INFO",
    }


@pytest.fixture
def sample_services():
    """Sample AWS services for tests."""
    return {
        "services": [
            {"service": "Amazon EC2"},
            {"service": "Amazon S3"},
            {"service": "Amazon RDS"},
            {"service": "AWS Lambda"},
            {"service": "Amazon VPC"},
        ]
    }


@pytest.fixture
def sample_announcements():
    """Sample AWS announcements for tests."""
    current_time = datetime.now()
    return [
        {
            "title": "AWS Lambda now supports Python 3.13",
            "description": "AWS Lambda now supports Python 3.13 runtime.",
            "link": "https://aws.amazon.com/about-aws/whats-new/2025/03/aws-lambda-python-3-13/",
            "datePosted": current_time.isoformat(),
        },
        {
            "title": "Amazon EC2 introduces new instance types",
            "description": "Amazon EC2 introduces new high-performance instance types.",
            "link": "https://aws.amazon.com/about-aws/whats-new/2025/03/amazon-ec2-instance-types/",
            "datePosted": (current_time - timedelta(days=1)).isoformat(),
        },
        {
            "title": "Amazon CloudFront adds new edge locations",
            "description": "Amazon CloudFront adds new edge locations in Europe.",
            "link": "https://aws.amazon.com/about-aws/whats-new/2025/03/amazon-cloudfront-edge-locations/",
            "datePosted": (current_time - timedelta(days=2)).isoformat(),
        },
    ]


@pytest.fixture
def sample_processed_announcements(sample_announcements):
    """Sample processed AWS announcements for tests."""
    processed = []

    # Lambda announcement (relevant)
    processed.append(
        {
            **sample_announcements[0],
            "services": ["AWS Lambda", "Python"],
            "relevant": True,
            "summary": "AWS Lambda now supports Python 3.13 runtime, enabling developers to use the latest Python features.",
        }
    )

    # EC2 announcement (relevant)
    processed.append(
        {
            **sample_announcements[1],
            "services": ["Amazon EC2"],
            "relevant": True,
            "summary": "Amazon EC2 introduces new high-performance instance types optimized for compute-intensive workloads.",
        }
    )

    # CloudFront announcement (not relevant)
    processed.append(
        {
            **sample_announcements[2],
            "services": ["Amazon CloudFront"],
            "relevant": False,
        }
    )

    return processed


@pytest.fixture
def mock_processor_dependencies():
    """Mocks all external dependencies used by the processor module."""
    with (
        patch(
            "personalized_aws_features.core.processor.get_services"
        ) as mock_get_services,
        patch(
            "personalized_aws_features.core.processor.process_announcements_in_parallel"
        ) as mock_process,
        patch(
            "personalized_aws_features.core.processor.fetch_aws_whats_new"
        ) as mock_fetch,
        patch(
            "personalized_aws_features.core.processor.get_dynamodb_table"
        ) as mock_get_table,
        patch(
            "personalized_aws_features.core.processor.is_announcement_seen"
        ) as mock_is_seen,
        patch(
            "personalized_aws_features.core.processor.save_announcement"
        ) as mock_save,
        patch(
            "personalized_aws_features.core.processor.send_announcements_to_slack"
        ) as mock_send_slack,
        patch(
            "personalized_aws_features.core.processor.display_announcement_list"
        ) as mock_display_list,
        patch(
            "personalized_aws_features.core.processor.display_detailed_announcements"
        ) as mock_display_detailed,
        patch(
            "personalized_aws_features.core.processor.display_service_summary"
        ) as mock_display_summary,
    ):

        # Configure default returns
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        yield {
            "get_services": mock_get_services,
            "process_announcements": mock_process,
            "fetch_aws_whats_new": mock_fetch,
            "get_dynamodb_table": mock_get_table,
            "is_announcement_seen": mock_is_seen,
            "save_announcement": mock_save,
            "send_announcements_to_slack": mock_send_slack,
            "display_announcement_list": mock_display_list,
            "display_detailed_announcements": mock_display_detailed,
            "display_service_summary": mock_display_summary,
            "dynamodb_table": mock_table,
        }

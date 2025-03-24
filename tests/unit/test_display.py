#!/usr/bin/env python3
"""
Unit tests for display.py
"""

from unittest.mock import patch, call
from personalized_aws_features.core.display import (
    display_announcement_list,
    display_detailed_announcements,
    display_service_summary,
)


class TestDisplayFunctions:
    """Tests for display functions."""

    @patch("builtins.print")
    def test_display_announcement_list_empty(self, mock_print):
        """Test display_announcement_list with empty announcements."""
        display_announcement_list("Test Title", [])

        # Should not print anything for empty announcements
        mock_print.assert_not_called()

    @patch("builtins.print")
    def test_display_announcement_list_with_services(
        self, mock_print, sample_processed_announcements
    ):
        """Test display_announcement_list with announcements that have services."""
        # Only use the relevant announcements that have services
        relevant = [
            a for a in sample_processed_announcements if a.get("relevant", False)
        ]

        display_announcement_list("Relevant Announcements", relevant)

        # Check that the title and each announcement was printed
        calls = [call("\nRelevant Announcements:\n")]
        for i, announcement in enumerate(relevant, 1):
            calls.append(call(f"  {i}. {announcement['title']}"))
            services_str = ", ".join(announcement.get("services", []))
            calls.append(call(f"     [Services detected: {services_str}]\n"))

        mock_print.assert_has_calls(calls)

    @patch("builtins.print")
    def test_display_announcement_list_without_services(self, mock_print):
        """Test display_announcement_list with announcements that don't have services."""
        announcements = [
            {"title": "Announcement 1", "link": "link1"},
            {"title": "Announcement 2", "link": "link2"},
        ]

        display_announcement_list("Test Announcements", announcements)

        # Check that the title and each announcement was printed
        calls = [
            call("\nTest Announcements:\n"),
            call("  1. Announcement 1"),
            call("  2. Announcement 2"),
        ]

        mock_print.assert_has_calls(calls)

    @patch("personalized_aws_features.core.display.logger")
    def test_display_detailed_announcements_empty(self, mock_logger):
        """Test display_detailed_announcements with empty announcements."""
        display_detailed_announcements([])

        mock_logger.info.assert_called_once_with("No announcements to display")

    @patch("builtins.print")
    @patch("personalized_aws_features.core.display.logger")
    def test_display_detailed_announcements(
        self, mock_logger, mock_print, sample_processed_announcements
    ):
        """Test display_detailed_announcements with announcements."""
        # Only use the relevant announcements
        relevant = [
            a for a in sample_processed_announcements if a.get("relevant", False)
        ]

        display_detailed_announcements(relevant)

        # Check logger calls
        mock_logger.info.assert_called_once_with(
            f"Displaying {len(relevant)} detailed announcements"
        )

        # Check that the header was printed
        mock_print.assert_any_call("\n=== Relevant AWS Service Updates ===\n")

        # Check that each announcement was printed with details
        for i, announcement in enumerate(relevant, 1):
            mock_print.assert_any_call(f"Update {i}: {announcement['title']}")
            mock_print.assert_any_call(f"Posted: {announcement['datePosted']}")

            # Check summary
            mock_print.assert_any_call(
                f"\nSummary: {announcement.get('summary', 'No summary available.')}"
            )

            # Check services
            services_str = ", ".join(announcement.get("services", []))
            mock_print.assert_any_call(f"\nMentioned Services: {services_str}")

            # Check link
            mock_print.assert_any_call(f"\nMore info: {announcement['link']}")

            # Check separator
            mock_print.assert_any_call("-" * 80)

    @patch("builtins.print")
    @patch("personalized_aws_features.core.display.logger")
    def test_display_service_summary(self, mock_logger, mock_print):
        """Test display_service_summary function."""
        services_list = [
            "Amazon EC2",
            "Amazon S3",
            "AWS Lambda",
            "Amazon RDS",
            "Amazon VPC",
        ]

        display_service_summary(len(services_list), services_list)

        # Check logger call
        mock_logger.info.assert_called_once_with(
            f"Displaying summary of {len(services_list)} service(s)"
        )

        # Check header
        mock_print.assert_any_call("\nServices found in your AWS environment:")

        # Check that services are printed in a formatted way
        # The exact formatting depends on the column width calculation,
        # but we can check that print is called with some service names
        for service in services_list:
            found = False
            for call_args in mock_print.call_args_list:
                if service in call_args[0][0]:
                    found = True
                    break
            assert found, f"Service {service} not found in printed output"

        # Final newline
        mock_print.assert_any_call("\n")

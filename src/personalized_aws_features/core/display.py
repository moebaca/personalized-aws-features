#!/usr/bin/env python3
"""
Display functions for AWS Feature Notifier to stdout.
"""

from typing import Dict, List
from personalized_aws_features.core.logger import logger


def display_announcement_list(title: str, announcements: List[Dict]) -> None:
    """Display a list of announcements with their titles and services."""
    if not announcements:
        return

    print(f"\n{title}:\n")

    for i, announcement in enumerate(announcements, 1):
        services_str = ", ".join(announcement.get("services", []))
        print(f"  {i}. {announcement['title']}")
        if services_str:
            print(f"     [Services detected: {services_str}]\n")


def display_detailed_announcements(announcements: List[Dict]) -> None:
    """Display detailed information for each announcement."""
    if not announcements:
        logger.info("No announcements to display")
        return

    logger.info(f"Displaying {len(announcements)} detailed announcements")
    print("\n=== Relevant AWS Service Updates ===\n")

    for i, announcement in enumerate(announcements, 1):
        logger.debug(f"Displaying announcement {i}: {announcement['title']}")
        print(f"Update {i}: {announcement['title']}")
        print(f"Posted: {announcement['datePosted']}")

        # Display summary
        summary = announcement.get("summary", "No summary available.")
        print(f"\nSummary: {summary}")

        # Display services directly without formatting
        services_str = ", ".join(announcement.get("services", []))
        print(f"\nMentioned Services: {services_str}")
        logger.debug(f"Services: {services_str}")

        print(f"\nMore info: {announcement['link']}")
        print("-" * 80)
        logger.debug(f"Summary: {summary}")
        logger.debug(f"Link: {announcement['link']}")


def display_service_summary(service_count: int, services_list: List[str]) -> None:
    """Display a summary of services found."""
    logger.info(f"Displaying summary of {service_count} service(s)")

    if service_count > 0:
        print("\nServices found in your AWS environment:")
        col_width = max(len(s) for s in services_list) + 2
        cols = 3
        rows = (service_count + cols - 1) // cols

        for i in range(rows):
            row_services = []
            for j in range(cols):
                idx = i + j * rows
                if idx < service_count:
                    row_services.append(services_list[idx].ljust(col_width))
            print("  " + "".join(row_services))

        logger.debug(f"All services: {', '.join(services_list)}")

    print("\n")

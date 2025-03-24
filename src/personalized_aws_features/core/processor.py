#!/usr/bin/env python3
"""Core processing logic for the AWS Feature Notifier."""

from typing import Dict, List, Tuple, Any

from personalized_aws_features.integrations.cost_explorer import get_services
from personalized_aws_features.integrations.bedrock import (
    process_announcements_in_parallel,
)
from personalized_aws_features.integrations.rss_feed import fetch_aws_whats_new
from personalized_aws_features.integrations.dynamodb import (
    get_dynamodb_table,
    save_announcement,
    is_announcement_seen,
)
from personalized_aws_features.core.display import (
    display_announcement_list,
    display_detailed_announcements,
    display_service_summary,
)
from personalized_aws_features.integrations.slack import send_announcements_to_slack
from personalized_aws_features.core.logger import logger


def initialize_results() -> Dict:
    """Initialize the results dictionary."""
    return {
        "service_count": 0,
        "announcement_count": 0,
        "relevant_count": 0,
        "filtered_history_count": 0,
    }


def setup_dynamodb(table_name: str, region: str, no_history: bool) -> Any:
    """Initialize DynamoDB table if history tracking is enabled."""
    if no_history:
        logger.info("History tracking disabled, skipping DynamoDB setup")
        return None

    logger.debug(f"Setting up DynamoDB table '{table_name}' in region '{region}'")
    return get_dynamodb_table(table_name=table_name, region=region)


def get_and_analyze_services() -> Tuple[Dict, int, List[str]]:
    """Fetch and analyze services from Cost Explorer."""
    logger.debug("Preparing Cost Explorer query")
    user_services = get_services()

    service_count = len(user_services["services"])
    services_list = sorted([s["service"] for s in user_services["services"]])

    logger.debug(f"Found {service_count} services")
    return user_services, service_count, services_list


def fetch_and_process_announcements(
    days_back: int, user_services: Dict, model_id: str, max_workers: int, region: str
) -> Tuple[List[Dict], List[Dict]]:
    """Fetch and process AWS announcements."""
    raw_announcements = fetch_aws_whats_new(days_back=days_back)

    if not raw_announcements:
        return [], []

    logger.info(
        f"Processing {len(raw_announcements)} announcement(s) with model {model_id}"
    )
    return process_announcements_in_parallel(
        raw_announcements, user_services, model_id, max_workers, region
    )


def filter_seen_announcements(
    announcements: List[Dict], ddb_table: Any, use_history: bool
) -> Tuple[List[Dict], List[Dict]]:
    """Filter out previously seen announcements."""
    if not use_history or ddb_table is None:
        logger.info("History tracking disabled, skipping filtering")
        return announcements, []

    new_announcements = []
    filtered_announcements = []

    for announcement in announcements:
        if is_announcement_seen(announcement, ddb_table):
            filtered_announcements.append(announcement)
        else:
            new_announcements.append(announcement)

    logger.info(
        f"Filtered {len(filtered_announcements)} previously seen announcement(s)"
    )
    return new_announcements, filtered_announcements


def send_slack_notifications(
    announcements: List[Dict], slack_token: str, slack_channel: str, results: Dict
) -> None:
    """Send announcements to Slack if configured."""
    if not (slack_token and slack_channel):
        logger.warning("Slack integration enabled but missing token or channel")
        return

    logger.debug(f"Preparing to send {len(announcements)} announcements to Slack")
    slack_results = send_announcements_to_slack(
        announcements, slack_token, slack_channel
    )

    results["slack_success"] = slack_results["success"]
    results["slack_failure"] = slack_results["failure"]

    if slack_results["failure"] > 0:
        raise RuntimeError(
            f"Failed to send {slack_results['failure']} announcement(s) to Slack"
        )


def process_features(config: Dict) -> Dict:
    """Process AWS feature announcements based on usage."""
    logger.info("Starting AWS Feature Notifier")
    logger.debug(f"Configuration: {config}")
    region = config["region"]
    results = initialize_results()

    # Setup resources
    ddb_table = setup_dynamodb(config["ddb_table"], region, config["no_history"])
    use_history = not config["no_history"]
    verbose = config.get("verbose", False)

    try:
        # Get and analyze services
        user_services, service_count, services_list = get_and_analyze_services()
        results["service_count"] = service_count

        logger.info(f"Found {service_count} services in your AWS environment")
        if verbose:
            display_service_summary(service_count, services_list)

        # Process announcements
        relevant, non_relevant = fetch_and_process_announcements(
            config["days"], user_services, config["model"], config["workers"], region
        )

        # Update results
        results["announcement_count"] = len(relevant) + len(non_relevant)
        results["relevant_count"] = len(relevant)

        # Show non-relevant announcements if verbose
        logger.info(f"Found {len(non_relevant)} non-relevant announcements")
        if verbose and non_relevant:
            display_announcement_list(
                f"All {len(non_relevant)} non-relevant announcements", non_relevant
            )

        # Filter out previously seen announcements
        if use_history and ddb_table:
            relevant, filtered = filter_seen_announcements(
                relevant, ddb_table, use_history
            )
            results["filtered_history_count"] = len(filtered)
            if verbose and filtered:
                display_announcement_list(
                    f"Filtered out {len(filtered)} previously seen announcements",
                    filtered,
                )

        # Display and save relevant announcements
        logger.info(f"Found {len(relevant)} relevant announcements for your services")
        if verbose and relevant:
            display_announcement_list(
                f"Found {len(relevant)} relevant announcements", relevant
            )
            display_detailed_announcements(relevant)

        if relevant and use_history and ddb_table:
            save_announcement(relevant, ddb_table)
        elif not relevant:
            logger.info("No relevant AWS announcements found for your services")

        # Send to Slack if enabled
        if config.get("slack_enabled") and relevant:
            send_slack_notifications(
                relevant,
                config.get("slack_token", ""),
                config.get("slack_channel", ""),
                results,
            )

        logger.info("AWS Feature Notifier completed successfully")
        return results

    except Exception as e:
        logger.error(f"Error processing features: {e}", exc_info=True)
        raise

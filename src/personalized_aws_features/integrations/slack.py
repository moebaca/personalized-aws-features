#!/usr/bin/env python3
"""
Slack integration for AWS Feature Notifier.

Sends AWS service announcements to a Slack channel.
"""

import requests
import json
from typing import Dict, List
from personalized_aws_features.core.logger import logger

SLACK_API_URL = "https://slack.com/api/chat.postMessage"


def send_to_slack(
    announcement: Dict,
    slack_token: str,
    slack_channel: str,
) -> bool:
    """Send an AWS service announcement to a Slack channel."""
    try:
        logger.debug(f"Preparing Slack message for: {announcement['title']}")
        blocks = format_slack_blocks(announcement)

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {slack_token}",
        }

        payload = {"channel": slack_channel, "blocks": blocks}

        logger.debug(f"Sending to Slack channel: {slack_channel}")
        response = requests.post(
            SLACK_API_URL,
            headers=headers,
            data=json.dumps(payload),
        )

        # Check response
        result = response.json()
        if not result.get("ok", False):
            error = result.get("error", "Unknown error")
            logger.error(f"Error sending to Slack: {error}")
            return False

        logger.debug(f"Successfully sent to Slack: {announcement['title']}")
        return True

    except Exception as e:
        logger.error(f"Error sending to Slack: {e}", exc_info=True)
        return False


def format_slack_blocks(announcement: Dict) -> List[Dict]:
    """
    Format an announcement as Slack blocks for better presentation.

    Args:
        announcement: The announcement to format

    Returns:
        List of Slack block objects
    """
    blocks = []

    # Title as header (no prefix)
    blocks.append(
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": announcement["title"],
                "emoji": True,
            },
        }
    )

    # Clean up the summary text
    summary = announcement.get("summary", "No summary available.")

    # Remove any "Title:" or "Summary:" prefixes from the Bedrock output
    summary = summary.replace("Title:", "").replace("Summary:", "")
    summary = summary.replace("**Title:**", "").replace("**Summary:**", "")
    summary = summary.replace("**", "")  # Remove any remaining bold markers
    summary = summary.strip()  # Remove leading/trailing whitespace

    # Summary section
    blocks.append(
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Summary:*\n{summary}"},
        }
    )

    # Service info section
    service_text = ", ".join([f"`{service}`" for service in announcement["services"]])
    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Mentioned Services:* {service_text}",
            },
        }
    )

    # Link button
    blocks.append(
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Details",
                        "emoji": True,
                    },
                    "url": announcement["link"],
                }
            ],
        }
    )

    return blocks


def send_announcements_to_slack(
    announcements: List[Dict],
    slack_token: str,
    slack_channel: str,
) -> Dict:
    """
    Send multiple announcements to Slack.

    Args:
        announcements: List of announcements to send
        slack_token: Slack API token
        slack_channel: Slack channel to post to

    Returns:
        Dictionary with success and failure counts
    """
    logger.info(
        f"Sending {len(announcements)} announcements to Slack channel {slack_channel}"
    )
    results = {"success": 0, "failure": 0}

    for announcement in announcements:
        success = send_to_slack(announcement, slack_token, slack_channel)

        if success:
            results["success"] += 1
        else:
            results["failure"] += 1

    logger.info(
        f"Slack results: {results['success']} sent successfully, {results['failure']} failed"
    )
    return results

#!/usr/bin/env python3
"""
DynamoDB integration to track seen announcements.
"""

import boto3
from datetime import datetime
from typing import Dict, List, Union, Any
import hashlib
import json
from personalized_aws_features.core.logger import logger


def get_dynamodb_table(table_name: str, region: str) -> Any:
    """
    Get the DynamoDB table for storing announcements.

    Args:
        table_name: DynamoDB table name to use
        region: AWS region for DynamoDB

    Returns:
        DynamoDB table resource

    Raises:
        Exception: If table doesn't exist or can't be accessed
    """
    logger.info(f"Getting DynamoDB table {table_name} in {region}")

    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)
        table.table_status  # Verify table exists
        logger.debug(f"DynamoDB table status: '{table.table_status}'")
        return table
    except Exception as e:
        logger.error(f"Failed to access DynamoDB table '{table_name}': {str(e)}")
        logger.error(f"Did you create the table in the correct region?")
        raise


def generate_announcement_id(announcement: Dict) -> str:
    """
    Generate a unique ID for an announcement.

    Args:
        announcement: The announcement dictionary

    Returns:
        A unique ID string
    """
    # Use title and link as the basis for the ID
    key_parts = [announcement.get("title", ""), announcement.get("link", "")]
    key_string = "|".join(key_parts)

    # Create a hash of the key string
    return hashlib.md5(key_string.encode()).hexdigest()


def save_announcement(
    announcements: Union[Dict, List[Dict]],
    table: Any,
) -> Dict:
    """
    Save one or more announcements to DynamoDB.

    Args:
        announcements: A single announcement dictionary or list of announcements
        table: DynamoDB table resource

    Returns:
        Dictionary with success and failure counts
    """
    results = {"success": 0, "failure": 0}

    # Handle single announcement case
    if isinstance(announcements, dict):
        announcements = [announcements]

    logger.info(f"Saving {len(announcements)} announcement(s) to DynamoDB")
    for announcement in announcements:
        try:
            announcement_id = generate_announcement_id(announcement)

            # Prepare item for DynamoDB
            item = {
                "announcement_id": announcement_id,
                "title": announcement.get("title", ""),
                "link": announcement.get("link", ""),
                "datePosted": announcement.get("datePosted", ""),
                "services": json.dumps(announcement.get("services", [])),
                "processed_at": datetime.now().isoformat(),
            }

            # Save to DynamoDB
            logger.debug(f"Saving announcement: {item['title']}")
            table.put_item(Item=item)
            results["success"] += 1
        except Exception as e:
            logger.error(f"Error saving announcement to DynamoDB: {e}", exc_info=True)
            results["failure"] += 1

    logger.info(
        f"Saved {results['success']} announcements, failed {results['failure']}"
    )
    return results


def is_announcement_seen(
    announcement: Dict,
    table: Any,
) -> bool:
    """
    Check if an announcement has been seen before.

    Args:
        announcement: The announcement to check
        table: DynamoDB table resource

    Returns:
        True if announcement has been seen before, False otherwise
    """
    try:
        announcement_id = generate_announcement_id(announcement)
        logger.debug(f"Checking if announcement {announcement_id} exists")

        # Check if item exists in DynamoDB
        response = table.get_item(
            Key={"announcement_id": announcement_id},
            ProjectionExpression="announcement_id",
        )

        seen = "Item" in response
        logger.debug(
            f"Announcement {announcement_id} {'already seen' if seen else 'is new'}"
        )
        return seen

    except Exception as e:
        logger.error(f"Error checking announcement in DynamoDB: {e}", exc_info=True)
        # Return False in case of error to avoid skipping potentially new announcements
        return False

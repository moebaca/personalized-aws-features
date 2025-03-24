#!/usr/bin/env python3
"""
AWS RSS Feed Parser

Fetches and parses the AWS What's New RSS feed to find recent announcements.
"""

import re
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List
import html
from personalized_aws_features.core.logger import logger

RSS_FEED_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"


def fetch_aws_whats_new(days_back: int) -> List[Dict]:
    """
    Fetch the AWS What's New RSS feed and parse it into a list of announcements.

    Args:
        days_back: Number of days to look back for announcements

    Returns:
        List of announcement dictionaries
    """
    logger.info(f"Fetching AWS What's New feed for the last {days_back} day(s)")
    # Calculate the cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_back)
    logger.debug(f"Using cutoff date: {cutoff_date.isoformat()}")

    # Fetch the RSS feed
    feed_url = RSS_FEED_URL
    logger.debug(f"Fetching RSS feed from {feed_url}")
    feed = feedparser.parse(feed_url)

    if hasattr(feed, "bozo_exception") and feed.bozo_exception:
        logger.warning(f"Warning while parsing feed: {feed.bozo_exception}")

    announcements = []
    total_entries = len(feed.entries)
    logger.debug(f"Found {total_entries} entries in the AWS What's New feed")

    for entry in feed.entries:
        date_posted = datetime(*entry.published_parsed[:6])

        # Skip if the announcement is older than the cutoff date
        if date_posted < cutoff_date:
            logger.debug(f"Skipping old announcement from {date_posted.isoformat()}")
            continue

        # Extract basic information
        title = entry.title
        link = entry.link
        description = entry.get("description", "")

        # Clean HTML from description
        if description:
            # Remove HTML tags but preserve content
            description = re.sub(r"<[^>]+>", " ", description)
            description = html.unescape(description)
            description = re.sub(r"\s+", " ", description).strip()

        logger.debug(f"Processing announcement: {title}")

        announcement = {
            "title": title,
            "description": description,
            "link": link,
            "datePosted": date_posted.isoformat(),
        }

        announcements.append(announcement)

    logger.debug(
        f"Found {len(announcements)} announcements within the {days_back} day window"
    )
    return announcements

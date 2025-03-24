#!/usr/bin/env python3
"""
Cost Explorer integration for AWS Feature Notifier.

Uses AWS Cost Explorer API to identify services in use.
"""

import boto3
from typing import Dict
from datetime import datetime, timedelta
from personalized_aws_features.core.logger import logger


def get_services() -> Dict:
    """Get services from Cost Explorer API results."""
    logger.info("Fetching services from AWS Cost Explorer API")

    try:
        # Hardcoded to us-east-1 due to availability
        ce = boto3.client("ce", "us-east-1")

        # Calculate time period (current month)
        today = datetime.now()
        first_day = today.replace(day=1).strftime("%Y-%m-%d")
        tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        # Query Cost Explorer API for all billing data across accounts (if consolidated billing)
        # Otherwise, grab data for the current account only
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": first_day, "End": tomorrow},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        services_list = []

        # Process the results
        if "ResultsByTime" in response and len(response["ResultsByTime"]) > 0:
            groups = response["ResultsByTime"][0].get("Groups", [])

            for group in groups:
                if len(group["Keys"]) > 0:
                    service_name = group["Keys"][0]
                    if service_name:  # Skip empty service names
                        services_list.append({"service": service_name})

            logger.info(
                f"Found {len(services_list)} unique service(s) in Cost Explorer data"
            )

        # Create the services result dictionary
        services_result = {"services": services_list}

        # Add default services
        services_result = add_default_services(services_result)
        logger.info(
            f"Added default services, total count: {len(services_result['services'])}"
        )

        return services_result

    except Exception as e:
        error_msg = f"Error querying Cost Explorer API: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg)


def add_default_services(services_dict: Dict) -> Dict:
    """Add some default AWS services likely in use but not appearing in billing (this is not exhaustive)."""
    logger.debug("Adding default services to the service list")

    # List of default services to add if they don't already exist.. this isn't exhaustive
    default_services = [
        "Amazon VPC",
        "AWS CloudFormation",
        "AWS Identity Management",
        "AWS Single Sign-On",
        "AWS STS",
        "AWS Organizations",
        "AWS Billing",
        "AWS Cost Management",
        "AWS Management Console",
        "AWS Artifact",
        "AWS Tag Editor",
        "AWS Resource Access Manager",
    ]

    # Add default services if they don't exist (sanity check)
    existing_services = {s["service"] for s in services_dict["services"]}

    for service_name in default_services:
        if service_name not in existing_services:
            services_dict["services"].append({"service": service_name})

    return services_dict

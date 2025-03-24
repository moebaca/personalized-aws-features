#!/usr/bin/env python3
"""
Bedrock integration for AWS Service News Analyzer
"""

import json
import re
import boto3
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from personalized_aws_features.core.logger import logger

# API call tracking (to be refactored later as exportable metrics)
_api_calls = {"total": 0, "throttled": 0, "errors": 0}


def process_announcement_with_bedrock(
    announcement: Dict,
    user_services: Dict,
    model_id: Optional[str] = None,
    region: str = "us-east-1",
) -> Dict:
    """Process AWS announcements using Amazon Bedrock.

    Args:
        announcement: The announcement to process
        user_services: Dictionary of user services
        model_id: Bedrock model ID to use
        region: AWS region for Bedrock client

    Returns:
        Processed announcement with relevance and services
    """
    try:
        logger.debug(f"Processing announcement with Bedrock: {announcement['title']}")
        _api_calls["total"] += 1

        # Create Bedrock client with specified region - important to know if chosen model is region-specific
        bedrock = boto3.client("bedrock-runtime", region_name=region)

        user_service_names = [s["service"] for s in user_services.get("services", [])]
        service_list = ", ".join([f'"{name}"' for name in user_service_names])

        prompt = f"""Analyze this AWS announcement and determine if it's relevant to the user based on the services they use.

        User's AWS Services: {service_list}

        Title: {announcement['title']}
        Description: {announcement.get('description', '')}

        CRITICAL INSTRUCTIONS:
        1. Extract ALL AWS services mentioned BY NAME in the announcement - be thorough (ABSOLUTELY DO NOT JUST DUMP THE User's
          AWS Services if unsure)
        2. For determining relevance:
           - EXTRACT the ROOT SERVICE NAME from the announcement (e.g., "EC2" from "EC2 instances")
           - If the title mentions a service TYPE (like EC2 instance types, S3 features, Lambda functions, Amazon Nova), match
           it to the base service
           - Recognize common AWS service abbreviations as their full names (Elastic Compute Cloud = EC2, Simple Storage
           Service = S3, Relational Database Service = RDS, etc.)
        3. An announcement is relevant ONLY IF it mentions at least one service from the User's AWS Services
           - This includes services that are part of the same product family (EC2 instances are part of EC2)
           - Use broad service family matching (EC2 instances should match EC2 - Other)

        SUMMARY STYLE INSTRUCTIONS:
        - Create an OBJECTIVE, FACTUAL summary that states what the announcement is about
        - Focus on key technical details and specific improvements
        - Use third-person, neutral tone
        - Include specific details like region names, percentages, or capabilities
        - Be direct and clear

        Output format - a valid JSON object with:
        - "relevant": true/false based on service matching
        - "services": [array of ALL AWS service names mentioned in the announcement]
        - "summary": A concise summary if relevant, otherwise empty string

        Format response as valid JSON only with no other text.
        """

        conversation = [{"role": "user", "content": [{"text": prompt}]}]

        response = bedrock.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={"maxTokens": 500, "temperature": 0.1, "topP": 0.1},
        )

        response_text = response["output"]["message"]["content"][0]["text"]

        # Log full response for debugging
        logger.debug(f"Title: {announcement['title']}")
        logger.debug(f"Bedrock response: {response_text}")

        # Parse JSON response
        try:
            # First try direct JSON parsing
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try regex extraction
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not extract JSON from response")

            announcement["services"] = result.get("services", [])
            announcement["relevant"] = result.get("relevant", False)

            if result.get("relevant", False):
                announcement["summary"] = result.get("summary", "")
                logger.debug(f"Relevant announcement found: {announcement['title']}")
            else:
                logger.debug(f"Irrelevant announcement: {announcement['title']}")

            return announcement

        except (json.JSONDecodeError, ValueError) as e:
            _api_calls["errors"] += 1
            logger.error(
                f"Error parsing Bedrock response as JSON: {e}. Response: {response_text}"
            )
            announcement["services"] = []
            announcement["relevant"] = False
            return announcement

    except Exception as e:
        if "ThrottlingException" in str(e):
            _api_calls["throttled"] += 1
            logger.warning(f"Throttled by Bedrock during processing: {e}")
        else:
            _api_calls["errors"] += 1
            logger.error(f"Error calling Bedrock for processing: {e}", exc_info=True)

        announcement["services"] = []
        announcement["relevant"] = False
        return announcement


def process_announcements_in_parallel(
    announcements: List[Dict],
    user_services: Dict,
    model_id: str = None,
    max_workers: int = 3,
    region: str = "us-east-1",
) -> Tuple[List[Dict], List[Dict]]:
    """Process multiple announcements in parallel.

    Args:
        announcements: List of announcements to process
        user_services: Dictionary of user services
        model_id: Bedrock model ID to use
        max_workers: Maximum number of parallel workers
        region: AWS region for Bedrock client

    Returns:
        Tuple of (relevant_announcements, non_relevant_announcements)
    """
    # Reset counters
    for key in _api_calls:
        _api_calls[key] = 0

    logger.debug(
        f"Processing {len(announcements)} announcements with {max_workers} workers"
    )

    # Process in parallel with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        processed_announcements = list(
            executor.map(
                lambda announcement: process_announcement_with_bedrock(
                    announcement, user_services, model_id, region
                ),
                announcements,
            )
        )

    # Separate relevant and non-relevant
    relevant_announcements = []
    non_relevant_announcements = []

    for announcement in processed_announcements:
        if announcement.get("relevant", False):
            relevant_announcements.append(announcement)
        else:
            non_relevant_announcements.append(announcement)

    # Log stats.. could eventually be exported as metrics in a later version
    logger.info(
        f"Bedrock API usage: {_api_calls['total']} total calls "
        f"({len(relevant_announcements)} relevant, {len(non_relevant_announcements)} non-relevant, "
        f"{_api_calls['throttled']} throttled, {_api_calls['errors']} errors)"
    )

    return relevant_announcements, non_relevant_announcements

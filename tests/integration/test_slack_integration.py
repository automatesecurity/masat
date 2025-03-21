"""
Author: Daniel Wood | 2025-03-20
Modular Attack Surface Analysis Tool
License: Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
LinkedIn: https://www.linkedin.com/in/danielewood
GitHub: https://github.com/automatesecurity
"""
import os
import asyncio
import pytest
from utils.slack_integration import send_slack_notification

@pytest.mark.skipif(
    os.getenv("SLACK_WEBHOOK_URL") is None,
    reason="SLACK_WEBHOOK_URL environment variable not set"
)
@pytest.mark.asyncio
async def test_slack_webhook_integration():
    """
    Integration test for the Slack notification feature.
    This test sends a test message to the Slack channel associated with the webhook.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    test_message = "Integration test: MASAT Slack notification working correctly."
    result = await send_slack_notification(webhook_url, test_message, verbose=True)
    assert result is True

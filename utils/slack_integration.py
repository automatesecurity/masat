#!/usr/bin/env python3
"""
Author: Daniel Wood | 2025-03-20
Modular Attack Surface Analysis Tool
License: Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
LinkedIn: https://www.linkedin.com/in/danielewood
GitHub: https://github.com/automatesecurity
"""
import asyncio
import aiohttp
import logging

def format_findings_for_slack(findings):
    """
    Convert the scanner findings dictionary into a formatted string for Slack.
    """
    message_lines = ["*MASAT Scan Report:*"]

    for category, data in findings.items():
        message_lines.append(f"*{category}:*")
        if isinstance(data, dict):
            for item, details in data.items():
                severity = details.get("severity", 0)
                remediation = details.get("remediation", "")
                extra = details.get("details", "")
                message_lines.append(f"• *{item}* (Severity: {severity})")
                if remediation:
                    message_lines.append(f"   - Remediation: {remediation}")
                if extra:
                    message_lines.append(f"   - Details: {extra}")
        else:
            # If data isn't a dict, just print it out.
            message_lines.append(f"• {data}")
        message_lines.append("")  # Add a blank line for spacing

    return "\n".join(message_lines)

async def send_slack_notification(webhook_url, message, verbose=False):
    """
    Send a notification to Slack using an incoming webhook.

    :param webhook_url: Slack incoming webhook URL.
    :param message: The message payload to send (as a string).
    :param verbose: If True, prints status messages.
    :return: True if notification was sent successfully, False otherwise.
    """
    payload = {
        "text": message
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, timeout=10) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"Slack notification failed: {response.status}, {error_text}")
                    return False
                else:
                    if verbose:
                        print("Slack notification sent successfully.")
                    return True
    except Exception as e:
        logging.error(f"Exception sending Slack notification: {e}")
        return False

# Optional: Test the integration if run as a script.
if __name__ == "__main__":
    import os
    test_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/your/webhook/url")
    test_message = "Test message from slack_integration module."
    asyncio.run(send_slack_notification(test_webhook_url, test_message, verbose=True))

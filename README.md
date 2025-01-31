# Slack Notifier

A flexible Slack notification system with logging capabilities. This package provides an easy way to send notifications to Slack with support for different notification levels, progress tracking, and fallback logging.

## Installation

```bash
pip install slack-notifier
```

## Features

- Multiple notification levels (SUCCESS, WARNING, ERROR, INFO, DEBUG)
- Progress tracking with automatic notifications
- Fallback to logging when Slack webhook is not available
- Support for formatted messages with fields and code blocks
- Customizable notification thresholds

## Usage

```python
from slack_notifier import SlackNotifier, NotificationLevel

# Initialize the notifier
notifier = SlackNotifier(
    webhook_url="your_webhook_url",
    system_name="MyService"
)

# Send a simple notification
notifier.send_info("Process started")

# Send a notification with fields
notifier.send_success(
    message="Process completed",
    title="Batch Processing",
    fields={
        "Files Processed": "100",
        "Success Rate": "98%"
    }
)

# Send a notification with code blocks
notifier.send_error(
    message="Error in processing",
    fields_code_block={
        "Stack Trace": "Error: File not found\n  at line 42"
    }
)

# Track progress
notifier = SlackNotifier(
    webhook_url="your_webhook_url",
    total_files=100,
    system_name="MyService"
)

for file in files:
    # Process file
    success = process_file(file)
    notifier.processed_files += 1
    notifier.send_progress_notification(success=success)
```

## Configuration

The notifier can be configured using environment variables:

- `SLACK_WEBHOOK_URL`: Default webhook URL
- `SYSTEM_NAME`: Default system name
- `NOTIFICATION_PERCENTAGES`: Comma-separated list of progress percentages to trigger notifications (default: "20,100")

## License

MIT License - see LICENSE file for details.

## requirements.txt

```
certifi==2025.1.31
charset-normalizer==3.4.1
idna==3.10
requests==2.31.0
-e file:///Users/dipen/projects/_projects/slack-notifier
urllib3==2.0.7
```


## slack notifier message

```bash
curl --location 'YOUR_WEBHOOK_URL' \
--header 'Content-Type: application/json' \
--data-raw '{
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Hello from curl"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*{key}:*\n{value}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "This is a section block with some *markdown* text."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "This is a header block"
            }
        },
        {
            "type": "input",
            "element": {
                "type": "plain_text_input",
                "action_id": "plain_text_input-action"
            },
            "label": {
                "type": "plain_text",
                "text": "Label"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Priority*"
                },
                {
                    "type": "mrkdwn",
                    "text": "*High*"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Assignee*"
                },
                {
                    "type": "mrkdwn",
                    "text": "*@username*"
                }
            ]
        }
    ]
}'
```
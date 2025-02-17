# src/slack_notifier/notifier.py
import os
import logging
import socket
import json

from enum import Enum
from datetime import datetime
from typing import Any, List, Optional, Dict

import requests

class NotificationLogHandler(logging.FileHandler):
    """Custom handler for notification logs with special formatting"""

    def __init__(self, filename):
        super().__init__(filename)
        self.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s\n")
        )


class NotificationLevel(Enum):
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"
    DEBUG = "🔍"


class SlackNotifier:
    """
    notifier = SlackNotifier(
        webhook_url="your_webhook_url",
        system_name="MyService"  # Optional - will use hostname if not provided
    )
    """

    def __init__(
        self,
        notification_log_path: str = None,
        webhook_url: Optional[str] = None,
        total_files=0,
        start_time=datetime.now(),
        system_name: str = None,
    ):
        """
        Initialize the Slack notifier with webhook URL and dedicated notification log.

        Args:
            notification_log_path: Path to the notification log file
            webhook_url: Slack webhook URL. If not provided, will try to get from environment variable
            system_name: Name of the system sending notifications. If not provided, will try to get from environment variable
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.use_logging = not bool(self.webhook_url)
        self.system_name = system_name or os.getenv("SYSTEM_NAME", socket.gethostname())

        # Set default notification log path if not provided
        self.notification_log_path = notification_log_path or "notifications.log"
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.use_logging = not bool(self.webhook_url)

        # Create notification logger
        self.notification_logger = logging.getLogger("notifications")
        self.notification_logger.setLevel(logging.INFO)
        self.notification_logger.propagate = False  # Don't propagate to root logger

        # Add notification handler
        notification_handler = NotificationLogHandler(self.notification_log_path)
        self.notification_logger.addHandler(notification_handler)

        # Get notification percentages from environment or use default
        notification_pcts = os.getenv("NOTIFICATION_PERCENTAGES", "20,100")
        self.notification_percentages = sorted(
            [int(x) for x in notification_pcts.split(",")]
        )
        self.last_notification_pct = 0

        self.start_time = start_time
        self.total_files = total_files
        self.processed_files = 0  # processed_files
        self.error_files = 0  # error_files

        if self.use_logging:
            self.notification_logger.info(
                f"SlackNotifier initialized in logging-only mode (no webhook URL provided) for system: {self.system_name}"
            )
        else:
            self.notification_logger.debug(
                f"SlackNotifier initialized with webhook: {webhook_url} for system: {self.system_name}"
            )

    def _log_notification(
        self,
        level: NotificationLevel,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
    ):
        """Send notification to the dedicated notification log."""
        full_message = []
        if title:
            full_message.append(f"=== {title} ===")

        full_message.append(
            f"{level.value} {level.name}: {message}"
        )
        # full_message.append(
        #     f"[{self.system_name}] {level.value} {level.name}: {message}"
        # )

        fields_str = self._format_fields_for_logging(fields)
        if fields_str:
            full_message.append("Fields:" + fields_str)

        code_blocks_str = self._format_code_blocks_for_logging(fields_code_block)
        if code_blocks_str:
            full_message.append("Code Blocks:" + code_blocks_str)

        complete_message = "\n".join(full_message)

        # Log to notification logger at appropriate level
        if level == NotificationLevel.ERROR:
            self.notification_logger.error(complete_message)
        elif level == NotificationLevel.WARNING:
            self.notification_logger.warning(complete_message)
        elif level == NotificationLevel.DEBUG:
            self.notification_logger.debug(complete_message)
        else:  # SUCCESS and INFO go to info channel
            self.notification_logger.info(complete_message)
    def _create_message_blocks(
        self,
        level: NotificationLevel,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
    ) -> List[Dict]:
        """Create formatted message blocks for Slack."""
        blocks = []

        # Add title block if provided
        if title:
            blocks.append(
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{title}",
                    },
                }
            )
        else:
            pass
            # # Add system name as header if no title provided
            # blocks.append(
            #     {
            #         "type": "header",
            #         "text": {"type": "plain_text", "text": f"[{self.system_name}]"},
            #     }
            # )
            
        # Add main message block
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{level.value} *{level.name}*\n{message}",
                },
            }
        )

        # Add fields if provided
        if fields:
            # Handle nested dictionaries in fields
            formatted_fields = []
            for key, value in fields.items():
                if isinstance(value, dict):
                    # Format nested dictionary as a bulleted list
                    nested_items = [f"• {k}: {v}" for k, v in value.items()]
                    field_value = "\n".join(nested_items)
                else:
                    field_value = str(value)

                formatted_fields.append(
                    {"type": "mrkdwn", "text": f"*{key}:*\n{field_value}"}
                )

            # Split fields into groups of 10 to avoid Slack's limit
            field_groups = [
                formatted_fields[i : i + 10]
                for i in range(0, len(formatted_fields), 10)
            ]
            for group in field_groups:
                blocks.append({"type": "section", "fields": group})

        # Add code block fields if provided
        if fields_code_block:
            if isinstance(fields_code_block, dict):
                for key, value in fields_code_block.items():
                    blocks.append(
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{key}:*\n```{value}```",
                            },
                        }
                    )
            else:
                # handle `fields_code_block` string data type
                try:
                    if isinstance(fields_code_block, str):
                        fields_code_block = json.loads(fields_code_block)
                        for key, value in fields_code_block.items():
                            blocks.append(
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"*{key}:*\n```{value}```",
                                    },
                                }
                            )
                except json.JSONDecodeError:
                    # If not valid JSON, treat as regular string
                    blocks.append(
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"```{fields_code_block}```",
                            },
                        }
                    )

        # Add timestamp and system context in footer
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"System: {self.system_name} | Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    }
                ],
            }
        )

        return blocks
    
    def _format_fields_for_logging(
        self, fields: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format fields dictionary for logging output.

        Args:
            fields: Dictionary of fields to format

        Returns:
            str: Formatted string representation of fields
        """
        if not fields:
            return ""

        formatted = []
        for key, value in fields.items():
            if isinstance(value, dict):
                nested = [f"    {k}: {v}" for k, v in value.items()]
                formatted.append(f"{key}:\n" + "\n".join(nested))
            else:
                formatted.append(f"{key}: {value}")

        return "\n" + "\n".join(formatted)

    def _format_code_blocks_for_logging(
        self, fields_code_block: Optional[Dict[str, str]] = None
    ) -> str:
        """Format code block fields for logging output.

        Args:
            fields_code_block: Dictionary of code blocks to format

        Returns:
            str: Formatted string representation of code blocks
        """
        if not fields_code_block:
            return ""

        formatted = []
        for key, value in fields_code_block.items():
            formatted.append(f"{key}:\n{value}")

        return "\n" + "\n".join(formatted)

    def _send_to_slack(self, blocks: List[Dict]) -> requests.Response:
        """Send formatted message blocks to Slack webhook.

        Args:
            blocks: List of formatted Slack message blocks

        Returns:
            requests.Response: Response from Slack API

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        return requests.post(
            self.webhook_url,
            json={"blocks": blocks},
            headers={"Content-Type": "application/json"},
        )

    def send_notification(
        self,
        level: NotificationLevel,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Send a notification to Slack.

        Args:
            level: NotificationLevel indicating the type of notification
            message: Main notification message
            title: Optional title for the notification
            fields: Optional dictionary of additional fields
            fields_code_block: Optional dictionary of code block fields

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            if self.use_logging:
                self._log_notification(level, message, title, fields, fields_code_block)
                return True

            # Create message blocks for Slack
            blocks = self._create_message_blocks(
                level, message, title, fields, fields_code_block
            )

            # Send to Slack
            response = self._send_to_slack(blocks)

            # Check response
            response.raise_for_status()
            return True

        except Exception as e:
            error_msg = f"Failed to send notification: {str(e)}"
            if not self.use_logging:
                logging.error(error_msg)
            return False

    def should_send_notification(self) -> bool:
        """
        Determine if a notification should be sent based on current progress.

        Returns:
            bool: True if notification should be sent, False otherwise
        """
        if self.total_files == 0:
            return False

        current_pct = (self.processed_files / self.total_files) * 100

        # Check if we've reached a new notification percentage
        for notification_pct in self.notification_percentages:
            if current_pct >= notification_pct > self.last_notification_pct:
                self.last_notification_pct = notification_pct
                return True

        return False

    def send_progress_notification(self, success: bool = True) -> None:
        """
        Send a progress notification if criteria are met.

        Args:
            success (bool): Whether the current file was processed successfully
        """
        if not self.should_send_notification():
            return

        if not success:
            self.error_files += 1

        elapsed_time = (
            datetime.now() - self.start_time
        ).total_seconds() / 3600  # hours
        processing_rate = self.processed_files / elapsed_time if elapsed_time > 0 else 0
        current_pct = self.processed_files / self.total_files * 100

        self.send_info(
            message=f"Processing Progress: {current_pct:.1f}%",
            fields={
                "Files Processed": f"{self.processed_files} / {self.total_files}",
                "Error Files": str(self.error_files),
                "Processing Rate": f"{processing_rate:.1f} files/hour",
                "Elapsed Time": f"{elapsed_time:.2f} hours",
            },
        )

    # Convenience methods for different notification types
    def send_success(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
    ) -> bool:
        return self.send_notification(
            NotificationLevel.SUCCESS, message, title, fields, fields_code_block
        )

    def send_warning(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
    ) -> bool:
        return self.send_notification(
            NotificationLevel.WARNING, message, title, fields, fields_code_block
        )

    def send_error(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
    ) -> bool:
        return self.send_notification(
            NotificationLevel.ERROR, message, title, fields, fields_code_block
        )

    def send_info(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
    ) -> bool:
        return self.send_notification(
            NotificationLevel.INFO, message, title, fields, fields_code_block
        )

    def send_debug(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
    ) -> bool:
        return self.send_notification(
            NotificationLevel.DEBUG, message, title, fields, fields_code_block
        )

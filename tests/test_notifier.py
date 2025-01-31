import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from slack_notifier import SlackNotifier, NotificationLevel


class TestSlackNotifier(unittest.TestCase):
    def setUp(self):
        self.webhook_url = "https://hooks.slack.com/services/TEST"
        self.notifier = SlackNotifier(
            webhook_url=self.webhook_url, system_name="TestSystem"
        )

    @patch("requests.post")
    def test_send_notification(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.notifier.send_info(
            message="Test message", title="Test Title", fields={"key": "value"}
        )

        self.assertTrue(result)
        mock_post.assert_called_once()

    def test_should_send_notification(self):
        notifier = SlackNotifier(webhook_url=self.webhook_url, total_files=100)
        notifier.processed_files = 20  # 20%

        self.assertTrue(notifier.should_send_notification())


if __name__ == "__main__":
    unittest.main()

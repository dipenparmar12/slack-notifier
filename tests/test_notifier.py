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


class TestMultiChannelSupport(unittest.TestCase):
    """Tests for multi-channel notification support."""

    def setUp(self):
        self.channels = {
            "alerts": "https://hooks.slack.com/services/ALERTS",
            "general": "https://hooks.slack.com/services/GENERAL",
            "deploy": "https://hooks.slack.com/services/DEPLOY",
        }

    def test_init_with_channels(self):
        notifier = SlackNotifier(channels=self.channels, system_name="TestSystem")
        self.assertEqual(notifier.channels, self.channels)
        self.assertFalse(notifier.use_logging)

    def test_init_channels_from_env(self):
        import json
        env_val = json.dumps({"ops": "https://hooks.slack.com/services/OPS"})
        with patch.dict("os.environ", {"PY_SLACK_NOTIFI": env_val}):
            notifier = SlackNotifier(system_name="TestSystem")
        self.assertEqual(notifier.channels, {"ops": "https://hooks.slack.com/services/OPS"})

    def test_init_channels_param_overrides_env(self):
        import json
        env_val = json.dumps({"ops": "https://hooks.slack.com/services/OPS"})
        with patch.dict("os.environ", {"PY_SLACK_NOTIFI": env_val}):
            notifier = SlackNotifier(channels=self.channels, system_name="TestSystem")
        self.assertEqual(notifier.channels, self.channels)

    def test_webhook_url_added_as_default_channel(self):
        notifier = SlackNotifier(
            webhook_url="https://hooks.slack.com/services/SINGLE",
            channels=self.channels,
            system_name="TestSystem",
        )
        self.assertIn("default", notifier.channels)
        self.assertEqual(notifier.channels["default"], "https://hooks.slack.com/services/SINGLE")

    def test_webhook_url_only_backward_compat(self):
        notifier = SlackNotifier(
            webhook_url="https://hooks.slack.com/services/SINGLE",
            system_name="TestSystem",
        )
        self.assertEqual(notifier.channels, {"default": "https://hooks.slack.com/services/SINGLE"})

    @patch("requests.post")
    def test_send_to_specific_channels(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        notifier = SlackNotifier(channels=self.channels, system_name="TestSystem")
        result = notifier.send_info(
            message="Deploy started", channels=["alerts", "deploy"]
        )

        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 2)
        called_urls = [call.args[0] for call in mock_post.call_args_list]
        self.assertIn(self.channels["alerts"], called_urls)
        self.assertIn(self.channels["deploy"], called_urls)

    @patch("requests.post")
    def test_send_to_all_channels_by_default(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        notifier = SlackNotifier(channels=self.channels, system_name="TestSystem")
        result = notifier.send_info(message="Broadcast message")

        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, len(self.channels))

    @patch("requests.post")
    def test_send_invalid_channel_name_ignored(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        notifier = SlackNotifier(channels=self.channels, system_name="TestSystem")
        result = notifier.send_info(
            message="Test", channels=["alerts", "nonexistent"]
        )

        self.assertTrue(result)
        # Only the valid channel gets called
        self.assertEqual(mock_post.call_count, 1)

    @patch("requests.post")
    def test_partial_failure_returns_false(self, mock_post):
        """If one channel fails, send_notification returns False."""
        mock_response_ok = MagicMock()
        mock_response_ok.raise_for_status.return_value = None
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = Exception("Slack error")
        mock_post.side_effect = [mock_response_ok, mock_response_fail]

        notifier = SlackNotifier(
            channels={"ch1": "https://hooks.slack.com/services/CH1",
                       "ch2": "https://hooks.slack.com/services/CH2"},
            system_name="TestSystem",
        )
        result = notifier.send_info(message="Test")
        self.assertFalse(result)

    def test_logging_fallback_no_channels_no_webhook(self):
        with patch.dict("os.environ", {}, clear=True):
            notifier = SlackNotifier(system_name="TestSystem")
        self.assertTrue(notifier.use_logging)
        self.assertEqual(notifier.channels, {})


if __name__ == "__main__":
    unittest.main()

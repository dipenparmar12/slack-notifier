# src/slack_notifier/__init__.py
from .notifier import SlackNotifier, NotificationLevel

__version__ = "0.1.2"
__all__ = ["SlackNotifier", "NotificationLevel"]

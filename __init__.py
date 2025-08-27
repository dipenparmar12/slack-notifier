#!/usr/bin/env python3
"""
py-slack-notifier - Enhanced Multi-Channel Slack Notifier Package

A robust, reusable Slack notification system that supports:
- Multiple channels with different webhooks
- Channel-specific routing
- Environment-based configuration
- Rich message formatting
- Progress tracking
- Error resilience
- Project-agnostic design

Usage:
    from enhanced_slack_notifier import SlackNotifier, ChannelConfig
    
    # Simple usage with default channel
    notifier = SlackNotifier(default_webhook_url="https://hooks.slack.com/...")
    notifier.send_info("Hello World!")
    
    # Multi-channel usage
    channels = {
        "system": "https://hooks.slack.com/services/.../system",
        "alerts": "https://hooks.slack.com/services/.../alerts", 
        "logs": "https://hooks.slack.com/services/.../logs"
    }
    notifier = SlackNotifier(channels=channels)
    notifier.send_error("System failure!", channel="alerts")
    notifier.send_info("Processing started", channel="logs")
"""

__version__ = "2.0.0"

import os
import json
import logging
import socket
import sys
import traceback
from enum import Enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None


class NotificationLevel(Enum):
    """Notification level enumeration with emoji icons"""
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"
    DEBUG = "🔍"


class ChannelConfig:
    """Configuration for individual Slack channels"""
    
    def __init__(self, webhook_url: str, name: Optional[str] = None, description: Optional[str] = None):
        self.webhook_url = webhook_url
        self.name = name or "default"
        self.description = description or f"Channel: {self.name}"
        
    def __repr__(self):
        return f"ChannelConfig(name='{self.name}', webhook='{self.webhook_url[:50]}...')"


class SlackNotifier:
    """
    Enhanced Multi-Channel Slack Notifier
    
    Features:
    - Multiple channel support with webhook routing
    - Environment-based configuration
    - Rich message formatting with blocks and code
    - Progress tracking capabilities
    - Graceful error handling
    - Project-agnostic design
    
    Examples:
        # Single channel usage
        notifier = SlackNotifier(default_webhook_url="https://hooks.slack.com/...")
        notifier.send_success("Task completed!")
        
        # Multi-channel usage
        channels = {
            "system": "https://hooks.slack.com/.../system",
            "alerts": "https://hooks.slack.com/.../alerts"
        }
        notifier = SlackNotifier(channels=channels, system_name="MyApp")
        notifier.send_error("Critical error!", channel="alerts")
        notifier.send_info("System status", channel="system")
        
        # Environment-based configuration
        # Set SLACK_CHANNELS='{"logs":"webhook1","alerts":"webhook2"}'
        notifier = SlackNotifier.from_environment()
        notifier.send_warning("Performance issue", channel="alerts")
    """
    
    def __init__(
        self,
        channels: Optional[Dict[str, str]] = None,
        default_webhook_url: Optional[str] = None,
        system_name: Optional[str] = None,
        notification_log_path: Optional[str] = None,
        enable_logging: bool = True,
        fallback_to_logging: bool = True,
        timeout: int = 10
    ):
        """
        Initialize the Enhanced Slack Notifier
        
        Args:
            channels: Dictionary mapping channel names to webhook URLs
            default_webhook_url: Default webhook URL if channels not provided
            system_name: System identifier for notifications
            notification_log_path: Path for notification logs
            enable_logging: Enable file logging of notifications
            fallback_to_logging: Fall back to logging if webhooks fail
            timeout: Request timeout in seconds
        """
        self.channels = self._setup_channels(channels, default_webhook_url)
        self.system_name = system_name or self._get_system_name()
        self.enable_logging = enable_logging
        self.fallback_to_logging = fallback_to_logging
        self.timeout = timeout
        
        # Environment detection
        self.environment_info = self._get_environment_info()
        
        # Setup logging
        self.logger = self._setup_logging(notification_log_path) if enable_logging else None
        
        # Progress tracking
        self.start_time = datetime.now()
        self.total_items = 0
        self.processed_items = 0
        self.error_items = 0
        self.notification_percentages = [20, 40, 60, 80, 100]
        self.last_notification_pct = 0
        
        # Validation
        if not self.channels and not self.fallback_to_logging:
            raise ValueError("No channels configured and fallback_to_logging is disabled")
            
        self._log_info(f"SlackNotifier initialized: {len(self.channels)} channels, system: {self.system_name}")
    
    @classmethod
    def from_environment(cls, system_name: Optional[str] = None, **kwargs) -> 'SlackNotifier':
        """
        Create SlackNotifier from environment variables
        
        Environment Variables:
            SLACK_CHANNELS: JSON string mapping channel names to webhooks
            SLACK_DEFAULT_WEBHOOK: Default webhook URL
            SYSTEM_NAME: System name for notifications
            SLACK_NOTIFICATION_LOG: Path for notification logs
            
        Example:
            export SLACK_CHANNELS='{"system":"webhook1","alerts":"webhook2"}'
            export SYSTEM_NAME="MyApplication"
            
            notifier = SlackNotifier.from_environment()
        """
        # Parse channels from environment
        channels = None
        channels_str = os.getenv("SLACK_CHANNELS")
        if channels_str:
            try:
                channels = json.loads(channels_str)
            except json.JSONDecodeError:
                logging.warning(f"Invalid SLACK_CHANNELS format: {channels_str}")
        
        # Get default webhook
        default_webhook = os.getenv("SLACK_DEFAULT_WEBHOOK") or os.getenv("SLACK_WEBHOOK_URL")
        
        # Get system name
        env_system_name = system_name or os.getenv("SYSTEM_NAME")
        
        # Get notification log path
        notification_log_path = os.getenv("SLACK_NOTIFICATION_LOG")
        
        return cls(
            channels=channels,
            default_webhook_url=default_webhook,
            system_name=env_system_name,
            notification_log_path=notification_log_path,
            **kwargs
        )
    
    def _setup_channels(self, channels: Optional[Dict[str, str]], default_webhook: Optional[str]) -> Dict[str, ChannelConfig]:
        """Setup channel configurations"""
        result = {}
        
        if channels:
            for name, webhook in channels.items():
                result[name] = ChannelConfig(webhook, name)
        elif default_webhook:
            result["default"] = ChannelConfig(default_webhook, "default")
        
        return result
    
    def _get_system_name(self) -> str:
        """Get system name from environment or hostname"""
        return (
            os.getenv("SYSTEM_NAME") or 
            os.getenv("APP_NAME") or 
            socket.gethostname()
        )
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for context"""
        try:
            return {
                "hostname": socket.gethostname(),
                "environment": self._detect_environment(),
                "database": self._detect_database(),
                "timestamp": datetime.now().isoformat(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"
            }
        except Exception:
            return {"hostname": "unknown", "environment": "unknown"}
    
    def _detect_environment(self) -> str:
        """Detect current environment"""
        app_settings = os.getenv("APP_SETTINGS", "")
        if "prod" in app_settings.lower():
            return "production"
        elif "dev" in app_settings.lower():
            return "development"
        elif "test" in app_settings.lower():
            return "testing"
        elif "local" in app_settings.lower():
            return "local"
        return os.getenv("ENVIRONMENT", "unknown")
    
    def _detect_database(self) -> str:
        """Detect database information"""
        db_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
        if db_url and "/" in db_url:
            return db_url.split("/")[-1]
        
        app_settings = os.getenv("APP_SETTINGS", "")
        if app_settings:
            return app_settings.replace(".", "_").replace("config_", "")
        
        return "unknown"
    
    def _setup_logging(self, log_path: Optional[str]) -> logging.Logger:
        """Setup notification logging"""
        logger = logging.getLogger(f"slack_notifier_{id(self)}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            if log_path:
                # Create log directory if needed
                Path(log_path).parent.mkdir(parents=True, exist_ok=True)
                handler = logging.FileHandler(log_path)
            else:
                handler = logging.StreamHandler()
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _log_info(self, message: str):
        """Log informational messages"""
        if self.logger:
            self.logger.info(message)
    
    def _log_error(self, message: str, exc_info: bool = False):
        """Log error messages"""
        if self.logger:
            self.logger.error(message, exc_info=exc_info)
        elif self.fallback_to_logging:
            logging.error(message, exc_info=exc_info)
    
    def get_channel_names(self) -> List[str]:
        """Get list of available channel names"""
        return list(self.channels.keys())
    
    def add_channel(self, name: str, webhook_url: str, description: Optional[str] = None):
        """Add a new channel configuration"""
        self.channels[name] = ChannelConfig(webhook_url, name, description)
        self._log_info(f"Added channel: {name}")
    
    def remove_channel(self, name: str):
        """Remove a channel configuration"""
        if name in self.channels:
            del self.channels[name]
            self._log_info(f"Removed channel: {name}")
    
    def _get_default_channel(self) -> Optional[str]:
        """Get the default channel name"""
        if "default" in self.channels:
            return "default"
        elif self.channels:
            return list(self.channels.keys())[0]
        return None
    
    def _create_message_blocks(
        self,
        level: NotificationLevel,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
        include_environment: bool = True
    ) -> List[Dict]:
        """Create Slack message blocks"""
        blocks = []
        
        # Add title header if provided
        if title:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{title}"
                }
            })
        
        # Add main message with level indicator
        main_text = f"{level.value} *{level.name}*\n{message}"
        if self.system_name and not title:
            main_text = f"🔧 *{self.system_name}*\n{main_text}"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": main_text
            }
        })
        
        # Add fields if provided
        if fields:
            formatted_fields = []
            for key, value in fields.items():
                if isinstance(value, dict):
                    nested_items = [f"• {k}: {v}" for k, v in value.items()]
                    field_value = "\n".join(nested_items)
                else:
                    field_value = str(value)
                
                formatted_fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{field_value}"
                })
            
            # Split into groups of 10 (Slack limit)
            for i in range(0, len(formatted_fields), 10):
                group = formatted_fields[i:i+10]
                blocks.append({
                    "type": "section",
                    "fields": group
                })
        
        # Add code blocks if provided
        if fields_code_block:
            for key, value in fields_code_block.items():
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n```{value}```"
                    }
                })
        
        # Add environment context footer
        if include_environment:
            env_text = (
                f"Environment: {self.environment_info.get('environment', 'unknown')} | "
                f"Database: {self.environment_info.get('database', 'unknown')} | "
                f"Host: {self.environment_info.get('hostname', 'unknown')} | "
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": env_text
                }]
            })
        
        return blocks
    
    def _send_to_slack(self, webhook_url: str, blocks: List[Dict]) -> bool:
        """Send message blocks to Slack webhook"""
        if not requests:
            self._log_error("requests library not available")
            return False
        
        try:
            response = requests.post(
                webhook_url,
                json={"blocks": blocks},
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self._log_error(f"Failed to send to Slack: {e}", exc_info=True)
            return False
    
    def send_notification(
        self,
        level: NotificationLevel,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None,
        include_environment: bool = True
    ) -> bool:
        """
        Send a notification to Slack
        
        Args:
            level: Notification level (SUCCESS, ERROR, WARNING, INFO, DEBUG)
            message: Main message content
            title: Optional title for the notification
            fields: Optional dictionary of structured fields
            fields_code_block: Optional dictionary of code blocks
            channel: Channel name to send to (uses default if not specified)
            include_environment: Whether to include environment context
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Determine target channel
        if not channel:
            channel = self._get_default_channel()
        
        if not channel or channel not in self.channels:
            self._log_error(f"Channel '{channel}' not found. Available: {list(self.channels.keys())}")
            if self.fallback_to_logging:
                self._log_notification_to_file(level, message, title, fields, fields_code_block)
            return False
        
        # Create message blocks
        blocks = self._create_message_blocks(
            level, message, title, fields, fields_code_block, include_environment
        )
        
        # Send to Slack
        webhook_url = self.channels[channel].webhook_url
        success = self._send_to_slack(webhook_url, blocks)
        
        # Log the notification attempt
        status = "SUCCESS" if success else "FAILED"
        self._log_info(f"{status} - {level.name} to {channel}: {message[:100]}...")
        
        # Fallback to file logging if enabled and Slack failed
        if not success and self.fallback_to_logging:
            self._log_notification_to_file(level, message, title, fields, fields_code_block)
        
        return success
    
    def _log_notification_to_file(
        self,
        level: NotificationLevel,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None
    ):
        """Log notification to file as fallback"""
        log_lines = []
        
        if title:
            log_lines.append(f"=== {title} ===")
        
        log_lines.append(f"{level.value} {level.name}: {message}")
        
        if fields:
            log_lines.append("Fields:")
            for key, value in fields.items():
                log_lines.append(f"  {key}: {value}")
        
        if fields_code_block:
            log_lines.append("Code Blocks:")
            for key, value in fields_code_block.items():
                log_lines.append(f"  {key}:\n{value}")
        
        complete_message = "\n".join(log_lines)
        
        if level == NotificationLevel.ERROR:
            self._log_error(complete_message)
        else:
            self._log_info(complete_message)
    
    # Convenience methods for different notification levels
    def send_success(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a success notification"""
        return self.send_notification(
            NotificationLevel.SUCCESS, message, title, fields, fields_code_block, channel
        )
    
    def send_error(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None,
        error: Optional[Exception] = None,
        context: Optional[Dict] = None
    ) -> bool:
        """Send an error notification with optional exception details"""
        error_fields = fields or {}
        
        if error:
            error_fields["Error Type"] = type(error).__name__
            error_fields["Error Message"] = str(error)
            
            # Add stack trace to code block
            if not fields_code_block:
                fields_code_block = {}
            fields_code_block["Stack Trace"] = traceback.format_exc()
        
        if context:
            error_fields["Context"] = context
        
        return self.send_notification(
            NotificationLevel.ERROR, message, title, error_fields, fields_code_block, channel
        )
    
    def send_warning(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a warning notification"""
        return self.send_notification(
            NotificationLevel.WARNING, message, title, fields, fields_code_block, channel
        )
    
    def send_info(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send an info notification"""
        return self.send_notification(
            NotificationLevel.INFO, message, title, fields, fields_code_block, channel
        )
    
    def send_debug(
        self,
        message: str,
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        fields_code_block: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a debug notification"""
        return self.send_notification(
            NotificationLevel.DEBUG, message, title, fields, fields_code_block, channel
        )
    
    # Script lifecycle convenience methods
    def send_script_started(
        self,
        script_name: str,
        script_version: str = "1.0",
        additional_context: Optional[Dict] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a script started notification"""
        context = {
            "Script": script_name,
            "Version": script_version,
            "Start Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "System": self.system_name,
        }
        
        if additional_context:
            context.update(additional_context)
        
        return self.send_info(
            message=f"Script '{script_name}' has started execution",
            title="Script Started",
            fields=context,
            channel=channel
        )
    
    def send_script_completed(
        self,
        script_name: str,
        duration_seconds: float,
        records_processed: int = 0,
        success_count: int = 0,
        error_count: int = 0,
        additional_stats: Optional[Dict] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send a script completion notification"""
        stats = {
            "Script": script_name,
            "Duration": f"{duration_seconds:.2f} seconds",
            "Records Processed": records_processed,
            "Successful": success_count,
            "Errors": error_count,
            "Completion Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        if additional_stats:
            stats.update(additional_stats)
        
        # Choose notification level based on errors
        if error_count > 0:
            return self.send_warning(
                message=f"Script '{script_name}' completed with {error_count} errors",
                title="Script Completed with Errors",
                fields=stats,
                channel=channel
            )
        else:
            return self.send_success(
                message=f"Script '{script_name}' completed successfully",
                title="Script Completed Successfully",
                fields=stats,
                channel=channel
            )
    
    # Progress tracking methods
    def set_total_items(self, total: int):
        """Set total items for progress tracking"""
        self.total_items = total
        self.processed_items = 0
        self.error_items = 0
        self.last_notification_pct = 0
        self.start_time = datetime.now()
    
    def increment_progress(self, success: bool = True, channel: Optional[str] = None) -> bool:
        """Increment progress and send notification if threshold reached"""
        self.processed_items += 1
        if not success:
            self.error_items += 1
        
        if self.should_send_progress_notification():
            return self.send_progress_notification(channel)
        
        return True
    
    def should_send_progress_notification(self) -> bool:
        """Check if progress notification should be sent"""
        if self.total_items == 0:
            return False
        
        current_pct = (self.processed_items / self.total_items) * 100
        
        for notification_pct in self.notification_percentages:
            if current_pct >= notification_pct > self.last_notification_pct:
                self.last_notification_pct = notification_pct
                return True
        
        return False
    
    def send_progress_notification(self, channel: Optional[str] = None) -> bool:
        """Send a progress notification"""
        if self.total_items == 0:
            return False
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        current_pct = (self.processed_items / self.total_items) * 100
        rate = self.processed_items / elapsed_time if elapsed_time > 0 else 0
        
        eta_seconds = (self.total_items - self.processed_items) / rate if rate > 0 else 0
        eta_formatted = f"{eta_seconds/60:.1f} minutes" if eta_seconds > 60 else f"{eta_seconds:.0f} seconds"
        
        progress_fields = {
            "Progress": f"{current_pct:.1f}%",
            "Processed": f"{self.processed_items} / {self.total_items}",
            "Errors": self.error_items,
            "Rate": f"{rate:.1f} items/second",
            "Elapsed Time": f"{elapsed_time/60:.1f} minutes",
            "ETA": eta_formatted
        }
        
        return self.send_info(
            message=f"Processing progress: {current_pct:.1f}% complete",
            title="Progress Update",
            fields=progress_fields,
            channel=channel
        )


# Convenience factory functions
def create_single_channel_notifier(webhook_url: str, system_name: Optional[str] = None) -> SlackNotifier:
    """Create a single-channel notifier"""
    return SlackNotifier(default_webhook_url=webhook_url, system_name=system_name)


def create_multi_channel_notifier(channels: Dict[str, str], system_name: Optional[str] = None) -> SlackNotifier:
    """Create a multi-channel notifier"""
    return SlackNotifier(channels=channels, system_name=system_name)


# Default instance for backward compatibility
_default_notifier = None


def get_default_notifier() -> SlackNotifier:
    """Get or create default notifier from environment"""
    global _default_notifier
    if _default_notifier is None:
        _default_notifier = SlackNotifier.from_environment()
    return _default_notifier


# Convenience functions using default notifier
def send_success(message: str, channel: Optional[str] = None, **kwargs) -> bool:
    """Send success notification using default notifier"""
    return get_default_notifier().send_success(message, channel=channel, **kwargs)


def send_error(message: str, channel: Optional[str] = None, **kwargs) -> bool:
    """Send error notification using default notifier"""
    return get_default_notifier().send_error(message, channel=channel, **kwargs)


def send_warning(message: str, channel: Optional[str] = None, **kwargs) -> bool:
    """Send warning notification using default notifier"""
    return get_default_notifier().send_warning(message, channel=channel, **kwargs)


def send_info(message: str, channel: Optional[str] = None, **kwargs) -> bool:
    """Send info notification using default notifier"""
    return get_default_notifier().send_info(message, channel=channel, **kwargs)

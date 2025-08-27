# py-slack-notifier

A robust, reusable Python package for sending rich notifications to multiple Slack channels with advanced features like environment detection, progress tracking, and flexible configuration.

## Features

- **Multi-Channel Support**: Route different notifications to different Slack channels
- **Rich Message Formatting**: Support for code blocks, structured fields, and emoji indicators
- **Environment Detection**: Automatically detects database, hostname, and environment information
- **Progress Tracking**: Built-in progress notifications for long-running processes
- **Error Resilience**: Graceful fallback to logging when Slack is unavailable
- **Flexible Configuration**: Environment variables, direct configuration, or code-based setup
- **Script Lifecycle Support**: Specialized notifications for script start/completion
- **Project Agnostic**: Designed to work with any Python project
- **Python 3.7+ Support**: Compatible with Python 3.7 through 3.13+

## Installation

```bash
pip install py-slack-notifier
```

## Quick Start

### Single Channel Usage

```python
from enhanced_slack_notifier import SlackNotifier

# Simple single-channel setup
notifier = SlackNotifier(
    default_webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    system_name="MyApp"
)

# Send notifications
notifier.send_success("Task completed successfully!")
notifier.send_error("Something went wrong!", error=exception)
notifier.send_warning("Performance degraded")
notifier.send_info("System status update")
```

### Multi-Channel Usage

```python
from enhanced_slack_notifier import SlackNotifier

# Configure multiple channels
channels = {
    "system": "https://hooks.slack.com/services/.../system-channel",
    "alerts": "https://hooks.slack.com/services/.../alerts-channel",
    "logs": "https://hooks.slack.com/services/.../logs-channel"
}

notifier = SlackNotifier(channels=channels, system_name="MyApp")

# Route notifications to specific channels
notifier.send_error("Critical system failure!", channel="alerts")
notifier.send_info("Daily backup completed", channel="system")
notifier.send_debug("Processing batch 5", channel="logs")
```

### Environment-Based Configuration

```bash
# Set environment variables
export SLACK_CHANNELS='{"system":"webhook1","alerts":"webhook2","logs":"webhook3"}'
export SYSTEM_NAME="MyApplication"
export SLACK_NOTIFICATION_LOG="./logs/notifications.log"
```

```python
from enhanced_slack_notifier import SlackNotifier

# Auto-configure from environment
notifier = SlackNotifier.from_environment()

# Use with automatic channel routing
notifier.send_success("Started successfully", channel="system")
notifier.send_error("Database connection failed", channel="alerts")
```

## Advanced Features

### Rich Message Formatting

```python
# Send with structured fields
notifier.send_success(
    message="Database backup completed",
    title="Backup Process",
    fields={
        "Database": "production_db",
        "Size": "2.5 GB",
        "Duration": "15 minutes",
        "Performance": {
            "Compression Ratio": "75%",
            "Transfer Speed": "10 MB/s"
        }
    },
    channel="system"
)

# Send with code blocks
notifier.send_error(
    message="Script execution failed",
    title="Processing Error",
    fields={
        "Script": "data_processor.py",
        "Batch": "batch_20250827"
    },
    fields_code_block={
        "Error Details": "ValueError: Invalid input format\n  at line 142",
        "Configuration": "batch_size: 1000\nretry_count: 3"
    },
    channel="alerts"
)
```

### Script Lifecycle Notifications

```python
# Script started notification
notifier.send_script_started(
    script_name="data_processor",
    script_version="2.1",
    additional_context={
        "Environment": "production",
        "Batch Size": 1000,
        "Input Files": 150
    },
    channel="logs"
)

# Script completion notification
notifier.send_script_completed(
    script_name="data_processor",
    duration_seconds=1205.5,
    records_processed=50000,
    success_count=49850,
    error_count=150,
    additional_stats={
        "Performance": "41.5 records/second",
        "Output Files": "processed_data_20250827.json"
    },
    channel="logs"
)
```

### Progress Tracking

```python
# Set up progress tracking
notifier.set_total_items(10000)

# In your processing loop
for item in items:
    # Process item
    success = process_item(item)
    
    # This will automatically send progress notifications at 20%, 40%, 60%, 80%, 100%
    notifier.increment_progress(success=success, channel="logs")
```

### Error Handling with Context

```python
try:
    risky_operation()
except Exception as e:
    notifier.send_error(
        message="Operation failed",
        title="Critical Error",
        error=e,  # Automatically includes exception details and stack trace
        context={
            "operation": "data_transformation",
            "batch_id": "B20250827_001",
            "retry_count": 3
        },
        channel="alerts"
    )
```

## Configuration Options

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SLACK_CHANNELS` | JSON mapping of channel names to webhooks | `'{"alerts":"webhook1","logs":"webhook2"}'` |
| `SLACK_DEFAULT_WEBHOOK` | Default webhook URL | `https://hooks.slack.com/services/...` |
| `SYSTEM_NAME` | System identifier for notifications | `MyApplication` |
| `SLACK_NOTIFICATION_LOG` | Path for notification logs | `./logs/notifications.log` |
| `APP_SETTINGS` | Application environment settings | `myapp.config.production` |
| `DATABASE_URL` | Database connection URL (auto-detected) | `postgresql://...` |

### Programmatic Configuration

```python
# Create with full configuration
notifier = SlackNotifier(
    channels={
        "system": "webhook_url_1",
        "alerts": "webhook_url_2",
        "logs": "webhook_url_3"
    },
    system_name="MyApplication",
    notification_log_path="./logs/slack_notifications.log",
    enable_logging=True,
    fallback_to_logging=True,  # Fallback to file logging if Slack fails
    timeout=10  # Request timeout in seconds
)
```

## Integration Examples

### Database Scripts

```python
from enhanced_slack_notifier import SlackNotifier

def main():
    notifier = SlackNotifier.from_environment()
    
    # Script started
    notifier.send_script_started(
        script_name="database_migration",
        additional_context={
            "Environment": os.getenv("APP_SETTINGS"),
            "Tables": ["users", "orders", "products"]
        },
        channel="system"
    )
    
    try:
        # Your database operations
        run_migrations()
        
        # Success notification
        notifier.send_script_completed(
            script_name="database_migration",
            duration_seconds=time.time() - start_time,
            records_processed=migration_count,
            channel="system"
        )
    except Exception as e:
        # Error notification
        notifier.send_error(
            message="Database migration failed",
            error=e,
            context={"stage": "migration", "current_table": current_table},
            channel="alerts"
        )
        raise
```

### Web Application Integration

```python
from enhanced_slack_notifier import SlackNotifier
from flask import Flask

app = Flask(__name__)
notifier = SlackNotifier.from_environment()

@app.errorhandler(500)
def handle_server_error(error):
    notifier.send_error(
        message="Server error occurred",
        title="Application Error",
        error=error,
        context={
            "endpoint": request.endpoint,
            "method": request.method,
            "user_id": get_current_user_id()
        },
        channel="alerts"
    )
    return "Internal Server Error", 500

@app.route('/api/process')
def process_data():
    notifier.send_info(
        message="Data processing started",
        fields={"user": get_current_user(), "timestamp": datetime.now()},
        channel="logs"
    )
    # Process data...
```

### Background Job Monitoring

```python
from enhanced_slack_notifier import SlackNotifier
import celery

notifier = SlackNotifier.from_environment()

@celery.task(bind=True)
def process_large_dataset(self, dataset_id):
    notifier.send_info(
        message=f"Processing dataset {dataset_id}",
        title="Background Job Started",
        channel="jobs"
    )
    
    try:
        # Set up progress tracking
        total_records = get_record_count(dataset_id)
        notifier.set_total_items(total_records)
        
        for record in get_records(dataset_id):
            success = process_record(record)
            notifier.increment_progress(success=success, channel="jobs")
            
    except Exception as e:
        notifier.send_error(
            message="Background job failed",
            error=e,
            context={"task_id": self.request.id, "dataset_id": dataset_id},
            channel="alerts"
        )
        raise
```

## Channel Routing Strategy

### Recommended Channel Setup

```python
channels = {
    "system": "webhook_for_system_events",     # System lifecycle, deployments
    "alerts": "webhook_for_critical_alerts",   # Errors, failures, critical issues
    "logs": "webhook_for_general_logs",        # General information, debug info
    "performance": "webhook_for_performance",  # Performance metrics, slow queries
    "security": "webhook_for_security"         # Security events, access logs
}

notifier = SlackNotifier(channels=channels)

# Route appropriately
notifier.send_error("Database down!", channel="alerts")
notifier.send_info("Deployment started", channel="system")
notifier.send_debug("Query took 2.5s", channel="performance")
```

## Error Handling and Resilience

The package is designed to be resilient:

- **Network failures**: Automatically falls back to file logging
- **Invalid webhooks**: Logs errors and continues operation
- **Rate limiting**: Respects Slack's rate limits
- **Timeout protection**: Configurable request timeouts
- **Graceful degradation**: Never breaks your application

## Message Format

All notifications include:

- **Level indicator**: Emoji-based visual indicators (✅ ❌ ⚠️ ℹ️ 🔍)
- **System identification**: Shows which system/application sent the message
- **Environment context**: Database, hostname, environment information
- **Timestamp**: When the notification was sent
- **Rich formatting**: Code blocks, structured fields, proper formatting

## API Reference

### SlackNotifier Class

#### Constructor
```python
SlackNotifier(
    channels: Optional[Dict[str, str]] = None,
    default_webhook_url: Optional[str] = None,
    system_name: Optional[str] = None,
    notification_log_path: Optional[str] = None,
    enable_logging: bool = True,
    fallback_to_logging: bool = True,
    timeout: int = 10
)
```

#### Core Methods
- `send_success(message, title=None, fields=None, fields_code_block=None, channel=None)`
- `send_error(message, title=None, fields=None, fields_code_block=None, channel=None, error=None, context=None)`
- `send_warning(message, title=None, fields=None, fields_code_block=None, channel=None)`
- `send_info(message, title=None, fields=None, fields_code_block=None, channel=None)`
- `send_debug(message, title=None, fields=None, fields_code_block=None, channel=None)`

#### Lifecycle Methods
- `send_script_started(script_name, script_version="1.0", additional_context=None, channel=None)`
- `send_script_completed(script_name, duration_seconds, records_processed=0, success_count=0, error_count=0, additional_stats=None, channel=None)`

#### Progress Tracking
- `set_total_items(total)`
- `increment_progress(success=True, channel=None)`
- `send_progress_notification(channel=None)`

#### Channel Management
- `get_channel_names()`
- `add_channel(name, webhook_url, description=None)`
- `remove_channel(name)`

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/dipenparmar12/py-slack-notifier/issues
- Documentation: https://github.com/dipenparmar12/py-slack-notifier/blob/main/README.md

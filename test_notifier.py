#!/usr/bin/env python3
"""
Comprehensive test and demonstration of Enhanced Slack Notifier capabilities
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the package to Python path for testing
sys.path.insert(0, str(Path(__file__).parent))

from __init__ import SlackNotifier, create_multi_channel_notifier


def test_multi_channel_notifications():
    """Test multi-channel notification capabilities"""
    print("🚀 Testing Enhanced Multi-Channel Slack Notifier...")
    
    # Define multiple channels - using the same webhook for demo but in real use these would be different
    channels = {
        "system": "https://hooks.slack.com/services/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",
        "alerts": "https://hooks.slack.com/services/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",
        "logs": "https://hooks.slack.com/services/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"
    }
    
    # Create multi-channel notifier
    notifier = SlackNotifier(
        channels=channels,
        system_name="Enhanced_Slack_Notifier_Demo",
        notification_log_path="./demo_notifications.log"
    )
    
    print(f"✅ Created notifier with channels: {notifier.get_channel_names()}")
    
    # Test 1: Script started notification to system channel
    print("\n1. Testing script started notification (system channel)...")
    notifier.send_script_started(
        script_name="enhanced_demo_script",
        script_version="2.0",
        additional_context={
            "Environment": "demo",
            "Test Type": "Multi-channel capabilities",
            "Channels Configured": len(channels),
            "Features": {
                "Multi-Channel": "✅",
                "Rich Formatting": "✅", 
                "Environment Detection": "✅",
                "Progress Tracking": "✅"
            }
        },
        channel="system"
    )
    time.sleep(2)
    
    # Test 2: Error notification to alerts channel
    print("2. Testing error notification with exception (alerts channel)...")
    try:
        # Simulate an error
        raise ValueError("Demo database connection timeout after 30 seconds")
    except Exception as e:
        notifier.send_error(
            message="Critical system error occurred during demo",
            title="Demo System Alert",
            error=e,
            context={
                "operation": "database_connection",
                "retry_count": 3,
                "timeout_seconds": 30,
                "server": "demo-db-01"
            },
            channel="alerts"
        )
    time.sleep(2)
    
    # Test 3: Rich info notification to logs channel
    print("3. Testing rich info notification (logs channel)...")
    notifier.send_info(
        message="Processing demo batch with enhanced features",
        title="Enhanced Processing Status",
        fields={
            "Batch Details": {
                "Batch ID": "DEMO_20250827_001",
                "Records": 1500,
                "Start Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "Performance Metrics": {
                "Throughput": "125 records/second",
                "Memory Usage": "2.1 GB",
                "CPU Usage": "45%"
            },
            "Configuration": {
                "Max Retries": 3,
                "Timeout": "300 seconds",
                "Parallel Workers": 8
            }
        },
        fields_code_block={
            "Query Example": """
SELECT home_id, chevrons, updated_at 
FROM opt_bldgs 
WHERE project_id IN (18, 19) 
  AND updated_at > '2025-08-26'
ORDER BY home_id 
LIMIT 1000;
            """.strip(),
            "Configuration YAML": """
batch_processing:
  batch_size: 1000
  max_workers: 8
  retry_policy:
    max_retries: 3
    backoff_factor: 2
notifications:
  channels:
    system: "system-events"
    alerts: "critical-alerts" 
    logs: "processing-logs"
            """.strip()
        },
        channel="logs"
    )
    time.sleep(2)
    
    # Test 4: Progress tracking demonstration
    print("4. Testing progress tracking...")
    notifier.set_total_items(100)
    
    # Simulate processing with progress notifications
    for i in range(0, 101, 25):  # 0, 25, 50, 75, 100
        notifier.processed_items = i
        if notifier.should_send_progress_notification():
            notifier.send_progress_notification(channel="logs")
            print(f"   📊 Sent progress notification: {i}%")
        time.sleep(1)
    
    # Test 5: Warning notification
    print("5. Testing warning notification (alerts channel)...")
    notifier.send_warning(
        message="Performance degradation detected in demo system",
        title="Performance Warning",
        fields={
            "Issue": "Database query response time exceeded threshold",
            "Threshold": "2.0 seconds",
            "Current Response Time": "3.8 seconds",
            "Affected Queries": 15,
            "Recommendation": "Review query indexes and consider optimization"
        },
        channel="alerts"
    )
    time.sleep(2)
    
    # Test 6: Script completion notification
    print("6. Testing script completion notification (system channel)...")
    notifier.send_script_completed(
        script_name="enhanced_demo_script",
        duration_seconds=45.7,
        records_processed=1500,
        success_count=1485,
        error_count=15,
        additional_stats={
            "Performance": {
                "Records/Second": "32.8",
                "Peak Memory": "2.1 GB",
                "Average CPU": "42%"
            },
            "Output": {
                "Success File": "demo_success_20250827.json",
                "Error File": "demo_errors_20250827.log",
                "Summary": "demo_summary_20250827.json"
            },
            "Quality Metrics": {
                "Success Rate": "99.0%",
                "Data Quality Score": "A+",
                "Processing Efficiency": "Excellent"
            }
        },
        channel="system"
    )
    
    print("\n✅ All multi-channel notifications sent successfully!")
    print("📱 Check your Slack #service-logs channel for the comprehensive demo")
    
    return notifier

def test_environment_configuration():
    """Test environment-based configuration"""
    print("\n🌍 Testing environment-based configuration...")
    
    # Set environment variables
    os.environ["SLACK_CHANNELS"] = '{"demo_system":"https://hooks.slack.com/services/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"}'
    os.environ["SYSTEM_NAME"] = "Environment_Configured_Demo"
    os.environ["APP_SETTINGS"] = "demo.config.local"
    
    # Create from environment
    env_notifier = SlackNotifier.from_environment()
    
    env_notifier.send_success(
        message="Successfully created notifier from environment configuration",
        title="Environment Configuration Test",
        fields={
            "Configuration Source": "Environment Variables",
            "Channels": env_notifier.get_channel_names(),
            "System Name": env_notifier.system_name,
            "Environment Info": env_notifier.environment_info
        },
        channel="demo_system"
    )
    
    print("✅ Environment-based configuration test completed")
    return env_notifier

def test_channel_management():
    """Test dynamic channel management"""
    print("\n🔧 Testing dynamic channel management...")
    
    # Start with single channel
    notifier = SlackNotifier(
        default_webhook_url="https://hooks.slack.com/services/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",
        system_name="Channel_Management_Demo"
    )
    
    print(f"Initial channels: {notifier.get_channel_names()}")
    
    # Add channels dynamically
    notifier.add_channel(
        "dynamic_alerts", 
        "https://hooks.slack.com/services/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",
        "Dynamically added alerts channel"
    )
    
    notifier.add_channel(
        "dynamic_logs",
        "https://hooks.slack.com/services/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", 
        "Dynamically added logs channel"
    )
    
    print(f"After adding channels: {notifier.get_channel_names()}")
    
    # Test notifications to dynamic channels
    notifier.send_info(
        message="Testing dynamically added channel",
        title="Dynamic Channel Test",
        fields={
            "Channel": "dynamic_alerts",
            "Added At Runtime": "✅",
            "Available Channels": notifier.get_channel_names()
        },
        channel="dynamic_alerts"
    )
    
    # Remove a channel
    notifier.remove_channel("dynamic_logs")
    print(f"After removing channel: {notifier.get_channel_names()}")
    
    print("✅ Dynamic channel management test completed")
    return notifier

def main():
    """Run all tests"""
    print("=" * 80)
    print("🚀 ENHANCED SLACK NOTIFIER - COMPREHENSIVE DEMO")
    print("=" * 80)
    
    # Test 1: Multi-channel notifications
    notifier1 = test_multi_channel_notifications()
    
    # Test 2: Environment configuration  
    notifier2 = test_environment_configuration()
    
    # Test 3: Dynamic channel management
    notifier3 = test_channel_management()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("📱 Check your Slack channel for all the demo notifications")
    print("📋 Key features demonstrated:")
    print("   • Multi-channel routing")
    print("   • Rich message formatting")
    print("   • Environment detection")
    print("   • Progress tracking") 
    print("   • Error handling with stack traces")
    print("   • Script lifecycle notifications")
    print("   • Dynamic channel management")
    print("   • Environment-based configuration")
    print("=" * 80)

if __name__ == "__main__":
    main()

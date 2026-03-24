#!/usr/bin/env python3
"""
PyPI Upload Script for py-slack-notifier Package
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Check if required tools are installed"""
    required_tools = ['twine', 'build']
    missing_tools = []
    
    for tool in required_tools:
        try:
            subprocess.run([sys.executable, '-m', tool, '--help'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing required tools: {', '.join(missing_tools)}")
        print("Installing missing tools...")
        for tool in missing_tools:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', tool], check=True)
            except subprocess.CalledProcessError:
                # Fallback to uv if pip is not available
                subprocess.run(['uv', 'pip', 'install', tool], check=True)
        print("✅ Required tools installed")
    else:
        print("✅ All required tools are available")

def clean_build_artifacts():
    """Clean previous build artifacts"""
    artifacts = ['dist', 'build', '*.egg-info']
    for artifact in artifacts:
        if '*' in artifact:
            # Handle glob patterns
            import glob
            for path in glob.glob(artifact):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"🧹 Removed {path}")
        else:
            if os.path.exists(artifact):
                if os.path.isdir(artifact):
                    shutil.rmtree(artifact)
                else:
                    os.remove(artifact)
                print(f"🧹 Removed {artifact}")

def build_package():
    """Build the package"""
    print("🔨 Building package...")
    result = subprocess.run([
        sys.executable, '-m', 'build'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Build failed:")
        print(result.stderr)
        return False
    
    print("✅ Package built successfully")
    print(result.stdout)
    return True

def upload_to_pypi(test=True):
    """Upload package to PyPI"""
    repository = "testpypi" if test else "pypi"
    print(f"📤 Uploading to {repository}...")
    
    # Check for API token
    token_env = f"PYPI_API_TOKEN" if not test else "TEST_PYPI_API_TOKEN"
    if not os.getenv(token_env):
        print(f"❌ {token_env} environment variable not set")
        print(f"Please set your PyPI API token: export {token_env}=your_token_here")
        return False
    
    cmd = [
        sys.executable, '-m', 'twine', 'upload',
        '--repository', repository,
        '--username', '__token__',
        '--password', os.getenv(token_env),
        'dist/*'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Upload failed:")
        print(result.stderr)
        return False
    
    print(f"✅ Package uploaded successfully to {repository}")
    print(result.stdout)
    return True

def verify_package():
    """Verify package metadata using twine check"""
    print("🔍 Verifying package...")

    result = subprocess.run(
        f'{sys.executable} -m twine check dist/*',
        capture_output=True, text=True, shell=True
    )

    if result.returncode != 0:
        print(f"❌ Package verification failed:")
        print(result.stderr or result.stdout)
        return False

    print("✅ Package verification passed")
    return True

def show_installation_instructions():
    """Show installation instructions"""
    print("\n" + "=" * 60)
    print("📦 PACKAGE DISTRIBUTION COMPLETE")
    print("=" * 60)
    print("\n🎉 Your py-slack-notifier package is now available!")
    print("\n📥 Installation instructions:")
    print("   pip install py-slack-notifier")
    print("\n🚀 Quick start usage:")
    print("""
from slack_notifier import SlackNotifier

# Single channel setup
notifier = SlackNotifier(
    webhook_url="your_webhook_url",
    system_name="Your System"
)

# Multi-channel setup
notifier = SlackNotifier(
    channels={
        "alerts": "webhook_url_1",
        "logs": "webhook_url_2",
    }
)

# Send notifications
notifier.send_success("Operation completed!")
notifier.send_error("Something went wrong!")
notifier.send_info("Status update", channels=["logs"])
""")
    print("=" * 60)

def main():
    """Main upload process"""
    print("🚀 py-slack-notifier - PyPI Upload Process")
    print("=" * 60)
    
    # Change to package directory
    package_dir = Path(__file__).parent
    os.chdir(package_dir)
    print(f"📁 Working directory: {package_dir}")
    
    # Step 1: Check requirements
    check_requirements()
    
    # Step 2: Clean build artifacts
    clean_build_artifacts()
    
    # Step 3: Build package
    if not build_package():
        return 1
    
    # Step 4: Verify package
    if not verify_package():
        return 1
    
    # Step 5: Upload to PyPI
    print("\n🤔 Upload options:")
    print("1. Test PyPI (recommended for first upload)")
    print("2. Production PyPI")
    
    choice = input("Choose upload destination (1 or 2): ").strip()
    
    if choice == "1":
        if upload_to_pypi(test=True):
            print("\n✅ Uploaded to Test PyPI successfully!")
            print("🔗 View at: https://test.pypi.org/project/py-slack-notifier/")
            print("📥 Test install: pip install -i https://test.pypi.org/simple/ py-slack-notifier")
        else:
            return 1
    elif choice == "2":
        confirm = input("⚠️  Upload to PRODUCTION PyPI? This cannot be undone! (yes/no): ")
        if confirm.lower() == "yes":
            if upload_to_pypi(test=False):
                show_installation_instructions()
            else:
                return 1
        else:
            print("❌ Upload cancelled")
            return 1
    else:
        print("❌ Invalid choice")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

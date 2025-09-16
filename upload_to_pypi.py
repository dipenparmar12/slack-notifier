#!/usr/bin/env python3
"""
PyPI Upload Script for py-slack-notifier Package
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import re
import urllib.request
import urllib.error
from typing import Optional, Tuple


def _load_dotenv_if_exists(dotenv_path: str = ".env"):
    """Load simple .env file into environment if present (KEY=VALUE lines)."""
    if not os.path.exists(dotenv_path):
        return

    try:
        with open(dotenv_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # Do not overwrite already-exported environment variables
                if key not in os.environ:
                    os.environ[key] = val
    except Exception:
        # Silently ignore parse errors; environment variables may already be set
        pass

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
            subprocess.run([sys.executable, '-m', 'pip', 'install', tool], check=True)
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
    # Load .env if present so local tokens are picked up
    _load_dotenv_if_exists()

    # Candidate environment variable names to look for (priority order)
    if test:
        candidates = [
            "TEST_PYPI_API_TOKEN",
            "TEST_TWINE_PASSWORD",
            "TWINE_PASSWORD",
            "PYPI_API_TOKEN",
        ]
    else:
        candidates = [
            "PYPI_API_TOKEN",
            "TWINE_PASSWORD",
            "TWINE_API_TOKEN",
            "TWINE_PASSWORD",
            "PYPI_TOKEN",
        ]

    token = None
    for name in candidates:
        token = os.getenv(name)
        if token:
            token_env = name
            break

    if not token:
        print(f"❌ No PyPI API token found in environment. Tried: {', '.join(candidates)}")
        print("Please set your PyPI API token as an environment variable or in a local .env file.")
        print("Example: export PYPI_API_TOKEN=your_token_here")
        return False

    # Use environment variables for twine credentials (safer than passing on CLI)
    env_vars = os.environ.copy()
    env_vars["TWINE_USERNAME"] = "__token__"
    env_vars["TWINE_PASSWORD"] = token

    cmd = [
        sys.executable, '-m', 'twine', 'upload',
        '--repository', repository,
        '--non-interactive',
        '--skip-existing',
        'dist/*'
    ]

    result = subprocess.run(cmd, env=env_vars, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Upload failed (exit code {result.returncode}):")
        if result.stdout:
            print("--- stdout ---")
            print(result.stdout)
        if result.stderr:
            print("--- stderr ---")
            print(result.stderr)
        # Detect common 'file already exists' case and give clear guidance
        stderr = (result.stderr or "") + (result.stdout or "")
        if "File already exists" in stderr or "file already exists" in stderr:
            print("It looks like some or all files already exist on PyPI for this version.")
            print("Options:")
            print("  - Bump the package version in setup.py/pyproject.toml and rebuild/retry")
            print("  - Use --skip-existing (the script already passes this flag) to skip existing files")
            print("  - If you need to replace a file, upload a new version (PyPI does not allow overwriting files)")
        # Provide a helpful hint
        print("Hint: ensure your token is valid, exported in the current shell, and has the correct PyPI scope.")
        return False
    
    print(f"✅ Package uploaded successfully to {repository}")
    print(result.stdout)
    return True


def read_project_name_version() -> Tuple[Optional[str], Optional[str]]:
    """Read package name and version from pyproject.toml (fallback to setup.py)."""
    name = None
    version = None
    try:
        data = open("pyproject.toml", "r", encoding="utf-8").read()
        # crude parsing: look for 'name = "..."' and 'version = "..."' under [project]
        m_name = re.search(r'^name\s*=\s*"([^"]+)"', data, flags=re.M)
        m_version = re.search(r'^version\s*=\s*"([^"]+)"', data, flags=re.M)
        if m_name:
            name = m_name.group(1).strip()
        if m_version:
            version = m_version.group(1).strip()
    except FileNotFoundError:
        pass

    if not name or not version:
        # fallback to setup.py
        try:
            s = open("setup.py", "r", encoding="utf-8").read()
            m_name = re.search(r'name\s*=\s*"([^"]+)"', s)
            m_version = re.search(r'version\s*=\s*"([^"]+)"', s)
            if m_name and not name:
                name = m_name.group(1).strip()
            if m_version and not version:
                version = m_version.group(1).strip()
        except FileNotFoundError:
            pass

    return name, version


def version_exists_on_index(package_name: str, version: str, test: bool) -> bool:
    """Check if a given package version exists on TestPyPI or PyPI using the JSON API."""
    if not package_name or not version:
        return False
    base = "https://test.pypi.org/pypi" if test else "https://pypi.org/pypi"
    url = f"{base}/{package_name}/{version}/json"
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        # For other errors, assume not exists (network issues will show later)
        return False
    except Exception:
        return False


def bump_version_string(current: str, new_version: Optional[str] = None) -> Optional[str]:
    """Return bumped version. If new_version provided, return that. Otherwise increment patch."""
    if new_version:
        return new_version
    # simple semver bump: increase patch
    parts = current.split(".")
    try:
        if len(parts) >= 3:
            parts[-1] = str(int(parts[-1]) + 1)
        elif len(parts) == 2:
            parts.append("1")
        else:
            parts = [parts[0], "0", "1"]
        return ".".join(parts)
    except Exception:
        return None


def write_new_version(new_version: str) -> bool:
    """Update version in pyproject.toml and setup.py in-place. Returns True on success."""
    success = False
    try:
        p = Path("pyproject.toml")
        if p.exists():
            text = p.read_text(encoding="utf-8")
            new_text, n = re.subn(r'(^version\s*=\s*")([^"]+)(" )?', r"\1" + new_version + r"\3", text, flags=re.M)
            if n == 0:
                # try different pattern
                new_text, n = re.subn(r'(^version\s*=\s*")([^"]+)(")', r"\1" + new_version + r"\3", text, flags=re.M)
            if n > 0:
                p.write_text(new_text, encoding="utf-8")
                success = True
    except Exception:
        success = False

    try:
        p2 = Path("setup.py")
        if p2.exists():
            text = p2.read_text(encoding="utf-8")
            new_text, n = re.subn(r'(version\s*=\s*")([^"]+)(")', r"\1" + new_version + r"\3", text)
            if n > 0:
                p2.write_text(new_text, encoding="utf-8")
                success = True
    except Exception:
        success = success or False

    return success

def verify_package():
    """Verify package metadata"""
    print("🔍 Verifying package...")
    
    # Check if setup.py is valid
    result = subprocess.run([
        sys.executable, 'setup.py', 'check'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Package verification failed:")
        print(result.stderr)
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
from enhanced_slack_notifier import SlackNotifier

# Single channel setup
notifier = SlackNotifier(
    default_webhook_url="your_webhook_url",
    system_name="Your System"
)

# Multi-channel setup
channels = {
    "alerts": "webhook_url_1",
    "logs": "webhook_url_2"
}
notifier = SlackNotifier(channels=channels)

# Send notifications
notifier.send_success("Operation completed!")
notifier.send_error("Something went wrong!")
notifier.send_info("Status update", channel="logs")
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
    
    # Step 3: Verify package
    if not verify_package():
        return 1
    
    # Step 4: Build package
    if not build_package():
        return 1
    
    # Step 5: Upload to PyPI
    # CLI flags supported:
    #   --publish <test|prod>
    #   --bump-version <auto|X.Y.Z>
    #   --promote  (if true, after successful test upload, promote to prod)
    #   --dry-run  (don't actually upload; show planned actions)
    args = sys.argv[1:]
    publish_arg = None
    bump_version_arg = None
    promote_arg = False
    dry_run = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--publish" and i + 1 < len(args):
            publish_arg = args[i + 1]
            i += 2
            continue
        if a == "--bump-version" and i + 1 < len(args):
            bump_version_arg = args[i + 1]
            i += 2
            continue
        if a == "--promote":
            promote_arg = True
            i += 1
            continue
        if a == "--dry-run":
            dry_run = True
            i += 1
            continue
        i += 1

    target = publish_arg.lower() if publish_arg else None

    # Default interactive behavior if no publish_arg provided
    if not target:
        print("\n🤔 Upload options:")
        print("1. Test PyPI (recommended for first upload)")
        print("2. Production PyPI")
        choice = input("Choose upload destination (1 or 2): ").strip()
        if choice == "1":
            target = "test"
        elif choice == "2":
            target = "prod"
        else:
            print("❌ Invalid choice")
            return 1

    # Read current package name and version
    pkg_name, current_version = read_project_name_version()
    if not pkg_name or not current_version:
        print("❌ Could not determine package name/version from pyproject.toml or setup.py")
        return 1

    print(f"Detected package: {pkg_name}, version: {current_version}")

    # If bump requested, decide new version
    new_version = None
    if bump_version_arg:
        if bump_version_arg == "auto":
            new_version = bump_version_string(current_version, None)
            if not new_version:
                print("❌ Failed to auto-bump version")
                return 1
        else:
            new_version = bump_version_string(current_version, bump_version_arg)

    # If dry-run, just show what would happen
    if dry_run:
        print("DRY RUN: the script will perform the following actions:")
        if new_version:
            print(f" - Update project version {current_version} -> {new_version}")
        print(f" - Build the package")
        idx = True if target in ("test", "testpypi") else False
        exists = version_exists_on_index(pkg_name, new_version or current_version, idx)
        print(f" - Check if version exists on {'TestPyPI' if idx else 'PyPI'}: {exists}")
        if exists and not new_version:
            print(" - Detected existing version; you may choose to bump the version before uploading")
        print(" - Would call upload_to_pypi(test=...) with the chosen target")
        if promote_arg:
            print(" - After successful test upload the script would promote to production")
        return 0

    # If we need to bump/update files
    if new_version:
        print(f"Updating project version to {new_version}...")
        ok = write_new_version(new_version)
        if not ok:
            print("❌ Failed to write new version to project files")
            return 1
        # Rebuild (clean/build)
        clean_build_artifacts()
        if not build_package():
            return 1

    # Now check whether version exists on the target index
    target_is_test = target in ("test", "testpypi")
    exists = version_exists_on_index(pkg_name, new_version or current_version, target_is_test)
    if exists and not new_version:
        print(f"Version {current_version} already exists on {'TestPyPI' if target_is_test else 'PyPI'}.")
        # Offer to auto-bump
        auto_bump = input("Would you like to auto-bump the version (patch) and proceed? (yes/no): ").strip().lower()
        if auto_bump == "yes":
            new_version = bump_version_string(current_version, None)
            if not new_version:
                print("❌ Failed to auto-bump version")
                return 1
            print(f"Bumping to {new_version} and rebuilding...")
            ok = write_new_version(new_version)
            if not ok:
                print("❌ Failed to write new version to project files")
                return 1
            clean_build_artifacts()
            if not build_package():
                return 1
        else:
            print("Aborting due to existing version")
            return 1

    # Final upload step
    if target_is_test:
        if upload_to_pypi(test=True):
            print("\n✅ Uploaded to Test PyPI successfully!")
            print("🔗 View at: https://test.pypi.org/project/py-slack-notifier/")
            print("📥 Test install: pip install -i https://test.pypi.org/simple/ py-slack-notifier")
            if promote_arg:
                print("Promoting to production as requested...")
                # promote: upload to production
                if upload_to_pypi(test=False):
                    show_installation_instructions()
                else:
                    return 1
        else:
            return 1
    else:
        confirm = input("⚠️  Upload to PRODUCTION PyPI? This cannot be undone! (yes/no): ")
        if confirm.lower() == "yes":
            if upload_to_pypi(test=False):
                show_installation_instructions()
            else:
                return 1
        else:
            print("❌ Upload cancelled")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

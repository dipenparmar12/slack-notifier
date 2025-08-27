from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="py-slack-notifier",
    version="2.0.0",
    author="dipenparmar12",
    author_email="dipensavji@gmail.com",
    description="Enhanced multi-channel Slack notification system with rich formatting and environment detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dipenparmar12/py-slack-notifier",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    keywords="slack, notifications, monitoring, alerts, multi-channel, webhook",
    project_urls={
        "Bug Reports": "https://github.com/dipenparmar12/py-slack-notifier/issues",
        "Source": "https://github.com/dipenparmar12/py-slack-notifier",
        "Documentation": "https://github.com/dipenparmar12/py-slack-notifier/blob/main/README.md",
    },
)

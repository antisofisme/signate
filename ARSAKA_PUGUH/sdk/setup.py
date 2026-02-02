"""
Infra SDK Setup

THIN CLIENT - No business logic, just an adapter to Core API.
"""

from setuptools import setup, find_packages

setup(
    name="infra-sdk",
    version="1.0.0",
    description="ARSAKA_PUGUH Infra SDK - Thin client for Core API",
    author="ARSAKA_PUGUH Team",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24.0",  # Async HTTP client
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

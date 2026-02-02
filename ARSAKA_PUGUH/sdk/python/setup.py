"""
ARSAKA_PUGUH Core Service SDK - Python Package

Setup configuration for distribution.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="arsaka-puguh-sdk",
    version="1.0.0",
    author="ARSAKA_PUGUH Team",
    author_email="dev@arsaka-puguh.com",
    description="Python SDK for ARSAKA_PUGUH Core Service API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arsaka-puguh/core-service-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=[
        "httpx>=0.27.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "black>=24.0.0",
            "mypy>=1.8.0",
        ],
    },
)

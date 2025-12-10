"""
Setup script for No-Driver GPM Package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = ""
readme_file = this_directory / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# Read requirements
requirements = []
req_file = this_directory / "requirements.txt"
if req_file.exists():
    with open(req_file, "r", encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f
            if
            line.strip() and not line.startswith("#") and not line.startswith("python-dotenv") and not line.startswith(
                "PySocks")
        ]

# Optional dependencies
optional_requirements = []
if req_file.exists():
    with open(req_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and (line.startswith("python-dotenv") or line.startswith("PySocks")):
                optional_requirements.append(line.split("#")[0].strip())

setup(
    name="nodrive-gpm-package",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Browser Profile Management with Anti-Detection using GPM and nodriver",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nodrive-gpm-package",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "optional": optional_requirements,
    },
    keywords="gpm browser automation anti-detection nodriver selenium chrome",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/nodrive-gpm-package/issues",
        "Source": "https://github.com/yourusername/nodrive-gpm-package",
    },
)

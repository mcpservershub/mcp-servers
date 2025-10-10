"""Setup script for Universal CTags MCP Server."""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="universal-ctags-mcp-server",
    version="1.0.0",
    author="Universal CTags MCP Team",
    description="MCP Server for Universal CTags integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/universal-ctags-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "mcp[cli]>=1.0.0",
        "python-ctags3>=1.6.0",
        "pydantic>=2.5.0",
        "aiofiles>=23.2.1",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "black>=24.1.0",
            "ruff>=0.2.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ctags-mcp=ctags_mcp.server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Indexing",
    ],
)
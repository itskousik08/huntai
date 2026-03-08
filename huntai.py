#!/usr/bin/env python3
"""
HuntAI - Local AI Lead Generation & Outreach Agent
Main Entry Point
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from cli.interface import HuntAICLI
from database.db import init_database
from config.manager import ConfigManager


def check_dependencies():
    """Check if required dependencies are available."""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
    
    # Check if Ollama is running
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code != 200:
            issues.append("Ollama is not responding — run: ollama serve")
    except Exception:
        issues.append("Ollama is not running — run: ollama serve")
    
    return issues


def main():
    """Main entry point."""
    # Initialize database
    init_database()
    
    # Load config
    config = ConfigManager()
    
    # Start CLI
    cli = HuntAICLI(config)
    cli.run()


if __name__ == "__main__":
    main()

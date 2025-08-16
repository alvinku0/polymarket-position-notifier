#!/usr/bin/env python3
"""
Discord Integration Tests
Quick test for Discord webhook functionality
"""

import os
import sys
import uuid
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.discordService.discordNotifier import DiscordNotifier


def test_discord_notifier():
    """Send a test message to the Discord webhook."""
    load_dotenv()
    
    # Initialize Discord notifier
    notifier = DiscordNotifier()

    # Create unique identifier for this test
    unique = uuid.uuid4().hex[:8]
    
    # Test real message
    ok = notifier.send_notification(f"Integration test: live test ping {unique}")

    assert ok is True


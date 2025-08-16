#!/usr/bin/env python3
"""
Polymarket Integration Tests
Tests real Polymarket API connectivity and functionality
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.polymarketConnector.polymarketNotificationFetcher import PolymarketNotificationFetcher
from src.config.config_manager import get_config


def test_polymarket_connection():
    """Test Polymarket API connection"""
    load_dotenv()
    config = get_config()
    
    private_key = config.get("polymarket.private_key")
    proxy_address = config.get("polymarket.proxy_address")
    signature_type = config.get("polymarket.signature_type")
    
    assert private_key, "Missing PRIVATE_KEY in configuration"
    
    # Initialize Polymarket client
    polymarket_fetcher = PolymarketNotificationFetcher(
        key=private_key,
        signature_type=signature_type,
        POLYMARKET_PROXY_ADDRESS=proxy_address
    )
    
    # Test connection by getting server time
    server_time = polymarket_fetcher.client.get_server_time()
    assert server_time is not None

    polymarket_fetcher.client.assert_level_2_auth()
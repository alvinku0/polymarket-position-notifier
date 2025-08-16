"""Discord webhook notification client.

Provides a lightweight client for posting messages to a Discord channel via
an incoming webhook URL. The client is configured with connection pooling,
retries with backoff, and per-request timeouts. A webhook URL can be supplied
explicitly or sourced from the ``DISCORD_WEBHOOK_URL`` environment variable.

Typical usage example:

    notifier = DiscordNotifier()
    notifier.send_notification("System started")

This module contains no long-lived background threads and performs network
I/O only when a notification method is invoked.
"""

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from ..config import get_config

class DiscordNotifier:
    """Discord webhook notifier with retries and timeouts.

    The notifier wraps a ``requests.Session`` configured with retry policy for
    transient failures and a default per-request timeout. It is safe to reuse a
    single instance across your application.

    Args:
        webhook_url: Explicit webhook URL. If ``None``, the value is read from
            the ``DISCORD_WEBHOOK_URL`` environment variable.
        timeout: Default per-request deadline in seconds.
        max_retries: Retry attempts applied to connect, read, and selected
            HTTP status failures.

    Raises:
        RuntimeError: If a webhook URL cannot be resolved from arguments or the
            ``DISCORD_WEBHOOK_URL`` environment variable.

    Attributes:
        webhook_url: The effective webhook URL used for requests.
        _timeout: Default per-request timeout in seconds.
        _session: Underlying ``requests.Session`` with retry-enabled adapters.
    """

    def __init__(self, timeout: float = 3.0, max_retries: int = 3) -> None:
        

        config = get_config()
        self.webhook_url = config.get("discord.webhook_url")
            
        if not self.webhook_url:
            raise RuntimeError("Missing discord.webhook_url in configuration or DISCORD_WEBHOOK_URL environment variable")

        self._timeout = timeout

        retry_config = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"POST"}),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_config, pool_connections=10, pool_maxsize=20)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        self._session = session

    def send_notification(self, message: str, username: str = "Polymarket Notification Bot", timeout: float | None = None) -> bool:
        """Send a message to the configured Discord webhook.

        Args:
            message: Text content to post.
            username: Display name for the sender.
            timeout: Per-call deadline in seconds. Defaults to instance setting.

        Returns:
            True if accepted (HTTP 200/204), else False.
        """
        if not message:
            return False

        payload = {"content": message, "username": username}

        try:
            response = self._session.post(self.webhook_url, json=payload, timeout=timeout or self._timeout)
            return response.status_code in (200, 204)
        except requests.Timeout:
            return False
        except requests.RequestException:
            return False


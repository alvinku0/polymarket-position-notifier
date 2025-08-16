import os
from typing import Dict, List, Any, Optional
from .polymarketClient import PolymarketClient
from py_clob_client.clob_types import DropNotificationParams
from dotenv import load_dotenv


class PolymarketNotificationFetcher(PolymarketClient):
    """Notification fetcher for Polymarket CLOB API.
    
    Extends PolymarketClient to provide notification-specific functionality
    for fetching and managing notifications from the Polymarket platform.
    """
    
    def _fetch_new_notification(self) -> List[Dict[str, Any]]:
        """Fetch new notifications from Polymarket.
        
        Returns:
            List[Dict[str, Any]]: List of notification objects.
            
        Raises:
            Exception: If an API communication error occurs.
        """
        try:
            notifications = self.client.get_notifications()
            return notifications
        except Exception as e:
            raise Exception(f"Failed to fetch notifications: {e}")
    
    def _drop_notifications(self, notification_ids: List[str]) -> bool:
        """Drop/dismiss multiple notifications.
        
        Args:
            notification_ids (List[str]): List of notification IDs to be dropped.
            
        Returns:
            bool: True if all notifications were successfully dropped, False otherwise.
            
        Raises:
            ValueError: If notification_ids is empty.
            Exception: If there's an API communication error.
        """
        if not notification_ids:
            raise ValueError("notification_ids cannot be empty")
        try:
            params = DropNotificationParams(ids=notification_ids)
            response = self.client.drop_notifications(params)
            return response == "OK"
        except Exception as e:
            raise Exception(f"Failed to drop notifications {notification_ids}: {e}")

    def fetch_and_drop_notifications(self) -> List[Dict[str, Any]]:
        notifications = self._fetch_new_notification()
        if notifications:
            notification_ids = [str(notification['id']) for notification in notifications]
            self._drop_notifications(notification_ids)
            return [notification['payload'] for notification in notifications]
        return []


if __name__ == "__main__":
    
    load_dotenv()
    noti = PolymarketNotificationFetcher(
        key=os.getenv("PRIVATE_KEY"),
        signature_type=2,
        POLYMARKET_PROXY_ADDRESS=os.getenv("POLYMARKET_PROXY_ADDRESS")
    )

    new_notifications = noti.fetch_new_notification()
    print(new_notifications)
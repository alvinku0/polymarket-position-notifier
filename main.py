from src.polymarketConnector.polymarketNotificationFetcher import PolymarketNotificationFetcher
from src.discordService.discordNotifier import DiscordNotifier
from src.db.notification_operation import NotificationOperation
from src.config import get_config
from logging_config import setup_file_logging, setup_console_logging
from dotenv import load_dotenv
from typing import List, Dict, Any
import schedule
import time
import signal
import sys


class PolymarketNotificationService:
    """Main service class for managing Polymarket notifications.
    
    This class handles the complete workflow of fetching notifications from Polymarket,
    saving them to a database, and sending them to Discord.
    """
    
    def __init__(self):
        load_dotenv()
        self.config = get_config()
        self.logger = setup_file_logging("PolymarketNotificationService")
        self.logger = setup_console_logging(self.logger)
        self.notification_fetcher = self._initialize_noti_fetcher()
        self.db_operations = NotificationOperation()
        self.discord_notifier = DiscordNotifier()
    
    def _initialize_noti_fetcher(self) -> PolymarketNotificationFetcher:
        """Initialize the Polymarket notification fetcher with configuration.
        
        Returns:
            PolymarketNotificationFetcher: Configured notification fetcher instance.
            
        Raises:
            ValueError: If required configuration parameters are missing.
            Exception: If initialization fails for any other reason.
        """
        try:
            private_key = self.config.get("polymarket.private_key")
            proxy_address = self.config.get("polymarket.proxy_address")
            signature_type = self.config.get("polymarket.signature_type")
            
            if not private_key:
                self.logger.error("Missing required configuration: polymarket.private_key")
                raise ValueError("Missing required configuration: polymarket.private_key")
            
            return PolymarketNotificationFetcher(
                key=private_key,
                signature_type=signature_type,
                POLYMARKET_PROXY_ADDRESS=proxy_address
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize notification fetcher: {e}")
            raise
    
    def fetch_notifications(self) -> List[Dict[str, Any]]:
        """Fetch notifications from Polymarket.
        
        Returns:
            List[Dict[str, Any]]: List of notification dictionaries fetched from Polymarket.
                                 Returns empty list if fetching fails.
        """
        try:
            notifications = self.notification_fetcher.fetch_and_drop_notifications()
            if notifications:
                self.logger.info(f"Fetched {len(notifications)} notifications from Polymarket")
            else:
                self.logger.debug("No new notifications available from Polymarket")
            return notifications
        except Exception as e:
            self.logger.error(f"Error fetching notifications: {e}")
            return []
    
    def save_notifications(self, notifications: List[Dict[str, Any]]) -> List[str]:
        """Save notifications to database.
        
        Args:
            notifications (List[Dict[str, Any]]): List of notification dictionaries to save.
            
        Returns:
            List[str]: List of saved notification IDs. Returns empty list if saving fails
                      or no notifications provided.
        """
        if not notifications:
            self.logger.info("No notifications to save")
            return []
        
        try:
            saved_ids = self.db_operations.save_notifications(notifications)
            self.logger.info(f"Saved {len(saved_ids)} notifications to database")
            return saved_ids
        except Exception as e:
            self.logger.error(f"Error saving notifications: {e}")
            return []
    
    def send_discord_notifications(self, notifications: List[Dict[str, Any]]) -> bool:
        """Send notifications to Discord.
        
        Args:
            notifications (List[Dict[str, Any]]): List of notification dictionaries to send.
            
        Returns:
            bool: True if all notifications were sent successfully, False otherwise.
        """
        if not notifications:
            self.logger.info("No notifications to send to Discord")
            return False
        
        try:
            for noti in notifications:
                msg = f'''{noti.get("question")}\nSide:{noti.get("side")} Matched Size:{noti.get("matched_size")} At Price:{noti.get("price")}'''
                self.discord_notifier.send_notification(msg)
            self.logger.info(f"Sent {len(notifications)} notifications to Discord")
            return True
        except Exception as e:
            self.logger.error(f"Error sending Discord notifications: {e}")
            return False
    
    def process_notifications(self, send_to_discord: bool = None) -> None:
        """Main method to process notifications: fetch, save, and optionally send to Discord.
        
        This method orchestrates the complete notification workflow:
        1. Fetches notifications from Polymarket
        2. Saves them to the database
        3. Optionally sends them to Discord
        
        Args:
            send_to_discord (bool, optional): Whether to send notifications to Discord.
                                             If None, uses config value. Defaults to None.
        """
        self.logger.info("Starting notification processing...")
        
        # Use config value if not explicitly provided
        if send_to_discord is None:
            send_to_discord = self.config.get("application.send_to_discord", True)
        
        # Fetch notifications
        notifications = self.fetch_notifications()
        
        if notifications:
            # Save to database
            self.save_notifications(notifications)
            
            # Send to Discord if requested
            if send_to_discord:
                self.send_discord_notifications(notifications)
        
        self.logger.info("Notification processing completed")
    
    def run_scheduler(self) -> None:
        """Run the scheduler to process notifications at configured intervals.
        
        Reads the fetch frequency from configuration and schedules the notification
        processing to run at that interval. Runs indefinitely until interrupted.
        """
        # Get fetch frequency from config (default to 60 seconds)
        fetch_frequency = self.config.get("application.fetch_frequency_seconds", 60)
        
        self.logger.info(f"Starting scheduler with {fetch_frequency} second intervals")
        
        # Schedule the job
        schedule.every(fetch_frequency).seconds.do(self.process_notifications)
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            self.logger.info("Received interrupt signal, shutting down gracefully...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Run initial processing immediately
            self.logger.info("Running initial notification processing...")
            self.process_notifications()
            
            # Keep the scheduler running
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            raise


def main():
    """Main entry point for the application.
    
    Creates a PolymarketNotificationService instance and starts the scheduler
    to process notifications at configured intervals.
    Handles and prints any application-level errors.
    """
    try:
        service = PolymarketNotificationService()
        service.run_scheduler()
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    main()
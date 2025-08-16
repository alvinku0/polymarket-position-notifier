from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from py_clob_client.client import ClobClient

class PolymarketClient:
    """Client for interacting with Polymarket CLOB API.
    
    Provides functionality to connect to Polymarket's Central Limit Order Book (CLOB)
    and perform various trading operations.
    
    Attributes:
        host (str): CLOB server host URL.
        chain_id (int): Blockchain chain ID (137 for Polygon).
        key (str | None): Private key for signing transactions.
        signature_type (int | None): Signature type for the CLOB client.
        proxy_address (str | None): Proxy address for transaction funding.
        client (ClobClient): Initialized CLOB client instance.
    """
    
    def __init__(
            self,
            key: str | None = None,
            signature_type: int | None = None,
            POLYMARKET_PROXY_ADDRESS: str | None = None
        ):

        self.host = "https://clob.polymarket.com"
        self.chain_id = 137
        self.key = key
        self.signature_type = signature_type
        self.proxy_address = POLYMARKET_PROXY_ADDRESS
        
        if signature_type is not None:
            self.client = ClobClient(
                host=self.host,
                chain_id=self.chain_id,
                key=self.key,
                signature_type=self.signature_type,
                funder=self.proxy_address
            )
        else:
            self.client = ClobClient(host="https://clob.polymarket.com", chain_id=137, key=key)
        
        if key:
            self.client.set_api_creds(self.client.create_or_derive_api_creds())

        if not self.client.get_ok():
            raise Exception("Failed to connect to Polymarket CLOB")
    
    def get_server_time_ET(self) -> datetime:
        """Return CLOB server time as US/Eastern.

        Falls back to system UTC converted to Eastern on failure.

        Returns:
            datetime: Timezone-aware datetime in US/Eastern.
        """
        try:
            server_timestamp: int = self.client.get_server_time()
            return datetime.fromtimestamp(server_timestamp, ZoneInfo("US/Eastern"))
        except Exception as e:
            # Fall back to system UTC time converted to Eastern
            utc_now = datetime.now(timezone.utc)
            return utc_now.astimezone(ZoneInfo("US/Eastern"))
    
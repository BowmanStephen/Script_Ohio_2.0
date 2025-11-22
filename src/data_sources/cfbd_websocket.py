"""
CFBD WebSocket Client for Real-time Subscriptions
=================================================

Handles GraphQL WebSocket connections for real-time game events.
"""

import asyncio
import logging
import os
from typing import AsyncIterator, Dict, Any, Optional

try:
    from gql import Client, gql
    from gql.transport.websockets import WebsocketsTransport
    GQL_AVAILABLE = True
except ImportError:
    GQL_AVAILABLE = False

logger = logging.getLogger(__name__)

class CFBDWebSocketClient:
    """
    WebSocket client for CollegeFootballData.com GraphQL API.
    
    Handles:
    - Connection management
    - Authentication
    - Automatic reconnection
    - Subscription event yielding
    """
    
    def __init__(self, api_key: str, host: str = "production"):
        """
        Initialize WebSocket client.
        
        Args:
            api_key: CFBD API Key
            host: 'production' or 'apinext' (default: production)
        """
        if not GQL_AVAILABLE:
            raise ImportError("gql[websockets] library required for WebSocket support")
            
        self.api_key = api_key
        self.host = host
        
        if host == "apinext":
            self.endpoint = "wss://apinext.collegefootballdata.com/v1/graphql"
        else:
            self.endpoint = "wss://graphql.collegefootballdata.com/v1/graphql"
            
        self.client: Optional[Client] = None
        self.transport: Optional[WebsocketsTransport] = None
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 8.0
        
    def _build_transport(self) -> WebsocketsTransport:
        """Create WebSocket transport with auth headers."""
        return WebsocketsTransport(
            url=self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "ScriptOhio2.0/CFBD-WebSocket"
            },
            ping_interval=20,
            connect_timeout=10,
            close_timeout=10
        )
        
    async def connect(self):
        """Establish WebSocket connection."""
        try:
            self.transport = self._build_transport()
            self.client = Client(
                transport=self.transport,
                fetch_schema_from_transport=False
            )
            # Note: Client context manager handles actual connection
            logger.info(f"WebSocket client configured for {self.endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to configure WebSocket client: {e}")
            raise

    async def subscribe(self, query: str, variables: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        """
        Subscribe to a GraphQL query.
        
        Args:
            query: GraphQL subscription query string
            variables: Query variables
            
        Yields:
            Dict containing event data
        """
        if not self.client:
            await self.connect()
            
        backoff = self._reconnect_delay
        
        while True:
            try:
                # Determine if query is subscription or query (gql client handles both, but we want subscribe)
                # We assume usage in async context
                document = gql(query)
                
                logger.info("Establishing WebSocket subscription...")
                
                async with self.client as session:
                    async for result in session.subscribe(document, variable_values=variables):
                        # Reset backoff on successful message
                        backoff = self._reconnect_delay
                        yield result
                        
            except asyncio.CancelledError:
                logger.info("Subscription cancelled")
                break
            except Exception as e:
                logger.warning(f"WebSocket connection lost: {e}. Reconnecting in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self._max_reconnect_delay)
                
                # Rebuild transport to ensure fresh connection state
                self.transport = self._build_transport()
                self.client = Client(transport=self.transport, fetch_schema_from_transport=False)

    async def disconnect(self):
        """Close connection."""
        if self.transport:
            await self.transport.close()
            logger.info("WebSocket disconnected")


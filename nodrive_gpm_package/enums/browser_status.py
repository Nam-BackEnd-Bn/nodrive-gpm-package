"""Browser status enumeration"""

from enum import Enum


class BrowserStatus(str, Enum):
    """Browser connection status"""
    
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    STARTING = "starting"
    CLOSING = "closing"
    ERROR = "error"


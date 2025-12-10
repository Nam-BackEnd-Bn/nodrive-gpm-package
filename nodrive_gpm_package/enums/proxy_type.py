"""Proxy type enumeration"""

from enum import Enum


class ProxyType(str, Enum):
    """Supported proxy types"""
    
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"
    SOCKS4 = "socks4"
    
    def format_proxy(self, proxy_string: str) -> str:
        """
        Format proxy string with protocol prefix
        
        Args:
            proxy_string: Proxy in format IP:Port:User:Pass or IP:Port
            
        Returns:
            Formatted proxy string with protocol
        """
        if self in [ProxyType.HTTP, ProxyType.HTTPS]:
            return proxy_string
        else:
            return f"{self.value}://{proxy_string}"


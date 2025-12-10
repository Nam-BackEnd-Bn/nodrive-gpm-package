"""Proxy-related Pydantic schemas"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from ..enums import ProxyType


class ProxyConfig(BaseModel):
    """Proxy configuration schema"""
    
    proxy_type: ProxyType = Field(..., description="Proxy protocol type")
    host: str = Field(..., description="Proxy host/IP")
    port: int = Field(..., description="Proxy port")
    username: Optional[str] = Field(None, description="Proxy username")
    password: Optional[str] = Field(None, description="Proxy password")
    
    @validator("port")
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    def to_string(self) -> str:
        """
        Convert to proxy string format
        
        Returns:
            Proxy string in format IP:Port:User:Pass or IP:Port
        """
        if self.username and self.password:
            return f"{self.host}:{self.port}:{self.username}:{self.password}"
        return f"{self.host}:{self.port}"
    
    def to_raw_proxy(self) -> str:
        """
        Convert to raw proxy format for GPM API
        
        Returns:
            Formatted proxy string with protocol prefix if needed
        """
        proxy_str = self.to_string()
        return self.proxy_type.format_proxy(proxy_str)
    
    @classmethod
    def from_string(cls, proxy_string: str, proxy_type: ProxyType = ProxyType.HTTP) -> "ProxyConfig":
        """
        Parse proxy from string format
        
        Args:
            proxy_string: Proxy in format IP:Port:User:Pass or IP:Port
            proxy_type: Proxy protocol type
            
        Returns:
            ProxyConfig instance
        """
        parts = proxy_string.split(":")
        
        if len(parts) == 2:
            return cls(
                proxy_type=proxy_type,
                host=parts[0],
                port=int(parts[1])
            )
        elif len(parts) == 4:
            return cls(
                proxy_type=proxy_type,
                host=parts[0],
                port=int(parts[1]),
                username=parts[2],
                password=parts[3]
            )
        else:
            raise ValueError(f"Invalid proxy format: {proxy_string}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "proxy_type": "socks5",
                "host": "123.45.67.89",
                "port": 1080,
                "username": "user",
                "password": "pass"
            }
        }

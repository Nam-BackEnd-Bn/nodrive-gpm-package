"""Browser-related Pydantic schemas"""

from typing import Optional
from pydantic import BaseModel, Field
from ..enums import ProxyType


class BrowserLaunchRequest(BaseModel):
    """Request schema for launching a browser"""
    
    profile_name: str = Field(..., description="Profile name to launch")
    proxy_type: Optional[ProxyType] = Field(None, description="Proxy type")
    proxy_string: Optional[str] = Field(None, description="Proxy in format IP:Port:User:Pass")
    max_retries: int = Field(3, description="Maximum retry attempts")
    persistent_position: int = Field(0, description="Browser window position index")
    window_width: Optional[int] = Field(None, description="Browser window width")
    window_height: Optional[int] = Field(None, description="Browser window height")
    window_x: Optional[int] = Field(None, description="Browser window X position")
    window_y: Optional[int] = Field(None, description="Browser window Y position")
    window_scale: Optional[float] = Field(None, description="Browser window scale")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_name": "my_profile",
                "proxy_type": "socks5",
                "proxy_string": "123.45.67.89:1080:user:pass",
                "persistent_position": 0
            }
        }


class BrowserConnectionInfo(BaseModel):
    """Browser connection information"""
    
    host: str = Field(..., description="Chrome DevTools host")
    port: int = Field(..., description="Chrome DevTools port")
    profile_id: str = Field(..., description="Profile ID")
    profile_name: str = Field(..., description="Profile name")
    remote_debugging_address: str = Field(..., description="Full debugging address")
    browser_location: str = Field(..., description="Browser executable path")
    
    class Config:
        from_attributes = True

"""Profile-related Pydantic schemas"""

from typing import Optional, List, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ProfileCreateRequest(BaseModel):
    """Request schema for creating a new profile"""
    
    profile_name: str = Field(..., description="Name of the profile")
    browser_name: Optional[str] = Field(None, description="Browser name")
    group_name: Optional[str] = Field(None, description="Group name")
    browser_core: Optional[str] = Field(None, description="Browser core (e.g., chromium)")
    browser_version: Optional[str] = Field(None, description="Browser version")
    is_random_browser_version: bool = Field(False, description="Use random browser version")
    raw_proxy: Optional[str] = Field(None, description="Proxy string (IP:Port:User:Pass)")
    startup_urls: Optional[str] = Field(None, description="Comma-separated startup URLs")
    
    # Anti-detection settings
    is_masked_font: bool = Field(True, description="Mask font fingerprint")
    is_noise_canvas: bool = Field(True, description="Add canvas noise")
    is_noise_webgl: bool = Field(True, description="Add WebGL noise")
    is_noise_client_rect: bool = Field(True, description="Add client rect noise")
    is_noise_audio_context: bool = Field(True, description="Add audio context noise")
    is_random_screen: bool = Field(False, description="Randomize screen resolution")
    is_masked_webgl_data: bool = Field(False, description="Mask WebGL data")
    is_masked_media_device: bool = Field(False, description="Mask media devices")
    is_random_os: bool = Field(False, description="Randomize OS")
    os: Optional[str] = Field(None, description="Operating system")
    webrtc_mode: int = Field(0, description="WebRTC mode")
    user_agent: Optional[str] = Field(None, description="Custom user agent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_name": "my_profile",
                "is_masked_font": True,
                "is_noise_canvas": True,
                "is_noise_webgl": True,
                "raw_proxy": "123.45.67.89:8080:username:password"
            }
        }


class ProfileUpdateRequest(BaseModel):
    """Request schema for updating a profile"""
    
    profile_name: Optional[str] = Field(None, description="New profile name")
    group_id: Optional[int] = Field(None, description="Group ID")
    raw_proxy: Optional[str] = Field(None, description="Proxy string")
    startup_urls: Optional[str] = Field(None, description="Startup URLs")
    note: Optional[str] = Field(None, description="Profile notes")
    color: Optional[str] = Field(None, description="Profile color tag")
    user_agent: Optional[str] = Field(None, description="User agent")


class ProfileResponse(BaseModel):
    """Response schema for profile data"""
    
    id: Union[str, int] = Field(..., description="Profile ID")
    name: str = Field(..., description="Profile name")
    profile_path: str = Field(..., description="Profile storage path")
    browser_type: Optional[str] = Field(None, description="Browser type")
    browser_version: Optional[str] = Field(None, description="Browser version")
    raw_proxy: Optional[str] = Field(None, description="Proxy configuration")
    note: Optional[str] = Field(None, description="Profile notes")
    group_id: Optional[Union[str, int]] = Field(None, description="Group ID")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    status: Optional[str] = Field(None, description="Current status")
    
    @field_validator('id', 'group_id', mode='before')
    @classmethod
    def convert_to_str(cls, v):
        """Convert numeric fields to string"""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class ProfileOpenResponse(BaseModel):
    """Response schema when opening a profile"""
    
    profile_id: Union[str, int] = Field(..., description="Profile ID")
    browser_location: str = Field(..., description="Browser executable path")
    remote_debugging_address: str = Field(..., description="Chrome DevTools Protocol address")
    driver_path: Optional[str] = Field(None, description="WebDriver path")
    process_id: Optional[Union[str, int]] = Field(None, description="Browser process ID")
    
    @field_validator('profile_id', 'process_id', mode='before')
    @classmethod
    def convert_to_str(cls, v):
        """Convert numeric fields to string"""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v
    
    @property
    def host(self) -> str:
        """Extract host from debugging address"""
        return self.remote_debugging_address.split(":")[0]
    
    @property
    def port(self) -> int:
        """Extract port from debugging address"""
        return int(self.remote_debugging_address.split(":")[1])


class ProfileListResponse(BaseModel):
    """Response schema for profile list"""
    
    profiles: List[ProfileResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total number of profiles")


class ProfileStatusResponse(BaseModel):
    """Response schema for profile status check"""
    
    profile_name: str = Field(..., description="Profile name")
    status: str = Field(..., description="Profile status (stopped/running/pending)")
    is_running: bool = Field(..., description="Whether profile is running")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    process_id: Optional[int] = Field(None, description="Process ID if running")

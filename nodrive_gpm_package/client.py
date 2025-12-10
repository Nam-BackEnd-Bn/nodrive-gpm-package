"""
Easy-to-use GPM Client Interface
Simplified API for common use cases
"""

from typing import Optional, List
import asyncio
import nodriver as nd

from .config import GPMConfig, get_config
from .services import GPMService
from .enums import ProxyType, ProfileStatus
from .schemas import ProfileResponse


class GPMClient:
    """
    Easy-to-use GPM Client
    
    This is the main entry point for using the GPM package.
    It provides a simple, intuitive interface for common operations.
    
    Examples:
        # Basic usage - launch a browser
        ```python
        from nodrive_gpm_package import GPMClient
        
        client = GPMClient()
        browser = await client.launch("my_profile")
        ```
        
        # With proxy
        ```python
        browser = await client.launch(
            "my_profile",
            proxy_type="socks5",
            proxy="123.45.67.89:1080:user:pass"
        )
        ```
        
        # With custom configuration
        ```python
        from nodrive_gpm_package import GPMClient, GPMConfig
        
        config = GPMConfig(
            gpm_api_base_url="http://localhost:12003/api/v3",
            browser_width=1200,
            browser_height=800
        )
        
        client = GPMClient(config=config)
        browser = await client.launch("my_profile")
        ```
        
        # Check profile status
        ```python
        status = client.get_status("my_profile")
        print(f"Profile status: {status}")
        ```
        
        # Close profile
        ```python
        client.close("my_profile")
        ```
    """
    
    def __init__(self, config: Optional[GPMConfig] = None):
        """
        Initialize GPM Client
        
        Args:
            config: Optional configuration. If not provided, uses defaults from environment.
        """
        self.config = config or get_config()
        self.service = GPMService(config=self.config)
    
    async def launch(
        self,
        profile_name: str,
        proxy_type: Optional[str] = None,
        proxy: Optional[str] = None,
        position: int = 0,
        **kwargs
    ) -> Optional[nd.Browser]:
        """
        Launch a browser with the specified profile
        
        This is the main method for launching browsers. It handles everything:
        - Creating profile if it doesn't exist
        - Configuring proxy
        - Checking and cleaning up existing instances
        - Connecting to the browser
        
        Args:
            profile_name: Name of the profile to launch
            proxy_type: Proxy type ("http", "socks5", etc.)
            proxy: Proxy string in format "IP:Port:User:Pass" or "IP:Port"
            position: Window position index (0, 1, 2, ...)
            **kwargs: Additional arguments (window_width, window_height, window_scale, max_retries)
            
        Returns:
            nodriver Browser instance or None if failed
            
        Example:
            ```python
            # Simple launch
            browser = await client.launch("profile1")
            
            # With proxy
            browser = await client.launch(
                "profile2",
                proxy_type="socks5",
                proxy="123.45.67.89:1080:user:pass"
            )
            
            # Custom window size
            browser = await client.launch(
                "profile3",
                window_width=1920,
                window_height=1080,
                position=0
            )
            ```
        """
        # Convert proxy_type string to enum
        proxy_type_enum = None
        if proxy_type:
            try:
                proxy_type_enum = ProxyType(proxy_type.lower())
            except ValueError:
                print(f"⚠️ Invalid proxy type: {proxy_type}, ignoring proxy")
                proxy = None
        
        return await self.service.launch_browser(
            profile_name=profile_name,
            proxy_type=proxy_type_enum,
            proxy_string=proxy,
            persistent_position=position,
            **kwargs
        )
    
    def close(self, profile_name: str) -> bool:
        """
        Close a running profile
        
        Args:
            profile_name: Name of the profile to close
            
        Returns:
            True if successfully closed, False otherwise
            
        Example:
            ```python
            client.close("my_profile")
            ```
        """
        return self.service.close_profile(profile_name)
    
    def get_status(self, profile_name: str) -> ProfileStatus:
        """
        Get the current status of a profile
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            ProfileStatus enum (STOPPED, RUNNING, PENDING, or UNKNOWN)
            
        Example:
            ```python
            status = client.get_status("my_profile")
            
            if status == ProfileStatus.RUNNING:
                print("Profile is running")
            elif status == ProfileStatus.STOPPED:
                print("Profile is stopped")
            ```
        """
        return self.service.get_profile_status(profile_name)
    
    def get_profiles(self) -> List[ProfileResponse]:
        """
        Get list of all profiles
        
        Returns:
            List of ProfileResponse objects
            
        Example:
            ```python
            profiles = client.get_profiles()
            
            for profile in profiles:
                print(f"Profile: {profile.name}, ID: {profile.id}")
            ```
        """
        return self.service.api_client.get_profiles()
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile by name
        
        Args:
            profile_name: Name of the profile to delete
            
        Returns:
            True if successfully deleted
            
        Example:
            ```python
            client.delete_profile("old_profile")
            ```
        """
        return self.service.api_client.delete_profile_by_name(profile_name)
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.service.__exit__(exc_type, exc_val, exc_tb)


# Convenience function for quick usage
async def launch_browser(
    profile_name: str,
    proxy_type: Optional[str] = None,
    proxy: Optional[str] = None,
    **kwargs
) -> Optional[nd.Browser]:
    """
    Quick function to launch a browser (convenience wrapper)
    
    Args:
        profile_name: Name of the profile
        proxy_type: Proxy type ("http", "socks5", etc.)
        proxy: Proxy string
        **kwargs: Additional arguments
        
    Returns:
        nodriver Browser instance
        
    Example:
        ```python
        from nodrive_gpm_package import launch_browser
        
        browser = await launch_browser("my_profile")
        ```
    """
    client = GPMClient()
    return await client.launch(profile_name, proxy_type, proxy, **kwargs)

"""
Easy-to-use GPM Client Interface
Simplified API for common use cases
"""

from typing import Optional, List, Tuple
import asyncio
import nodriver as nd
import sys

from .config import GPMConfig, get_config
from .services import GPMService
from .enums import ProxyType, ProfileStatus
from .schemas import ProfileResponse


def get_screen_size() -> Tuple[int, int]:
    """
    Get the primary screen size (width, height).
    Uses screeninfo library if available, with fallback methods.
    
    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        # Try using screeninfo first (most accurate)
        try:
            from screeninfo import get_monitors
            monitors = get_monitors()
            if monitors:
                # Get primary monitor (usually first one)
                primary_monitor = monitors[0]
                return (primary_monitor.width, primary_monitor.height)
        except ImportError:
            # screeninfo not installed, use fallback
            pass
        except Exception as e:
            print(f"Error using screeninfo: {e}, using fallback")
        
        # Fallback 1: Windows API
        if sys.platform == 'win32':
            import ctypes
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            return (width, height)
        
        # Fallback 2: tkinter (cross-platform)
        try:
            import tkinter as tk
            root = tk.Tk()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return (width, height)
        except:
            pass
        
        # Final fallback
        return (1920, 1080)
    except Exception as e:
        print(f"Error getting screen size: {e}, using default")
        return (1920, 1080)


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
        grid_row: Optional[int] = None,
        grid_col: Optional[int] = None,
        grid_rows: Optional[int] = None,
        grid_cols: Optional[int] = None,
        **kwargs
    ) -> Optional[nd.Browser]:
        """
        Launch a browser with the specified profile
        
        This is the main method for launching browsers. It handles everything:
        - Creating profile if it doesn't exist
        - Configuring proxy
        - Checking and cleaning up existing instances
        - Connecting to the browser
        - Calculating window dimensions and position based on grid layout
        
        Args:
            profile_name: Name of the profile to launch
            proxy_type: Proxy type ("http", "socks5", etc.)
            proxy: Proxy string in format "IP:Port:User:Pass" or "IP:Port"
            position: Window position index (0, 1, 2, ...) - used if grid parameters not provided
            grid_row: Row index in the grid (0-based)
            grid_col: Column index in the grid (0-based)
            grid_rows: Total number of rows in the grid
            grid_cols: Total number of columns in the grid
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
            
            # With grid layout (automatically calculates window size and position)
            browser = await client.launch(
                "profile3",
                grid_row=0,
                grid_col=0,
                grid_rows=2,
                grid_cols=5
            )
            
            # Custom window size (overrides grid calculation)
            browser = await client.launch(
                "profile4",
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
        
        # Calculate window dimensions and position from grid if provided
        # Store grid info for post-launch positioning
        grid_info = None
        if grid_row is not None and grid_col is not None and grid_rows is not None and grid_cols is not None:
            screen_width, screen_height = get_screen_size()
            
            # Calculate window dimensions to fill full screen divided by grid (no margins)
            window_width = screen_width // grid_cols
            window_height = screen_height // grid_rows
            
            # Calculate window position based on grid position
            window_x = grid_col * window_width
            window_y = grid_row * window_height
            
            # Store grid info for post-launch positioning
            grid_info = {
                'x': window_x,
                'y': window_y,
                'width': window_width,
                'height': window_height
            }
            
            # Override kwargs with calculated dimensions if not explicitly provided
            if 'window_width' not in kwargs:
                kwargs['window_width'] = window_width
            if 'window_height' not in kwargs:
                kwargs['window_height'] = window_height
            if 'window_x' not in kwargs:
                kwargs['window_x'] = window_x
            if 'window_y' not in kwargs:
                kwargs['window_y'] = window_y
            
            print(f"📐 [{profile_name}] Grid layout: row={grid_row}, col={grid_col}, "
                  f"window_size=({window_width}x{window_height}), position=({window_x}, {window_y})")
        
        browser = await self.service.launch_browser(
            profile_name=profile_name,
            proxy_type=proxy_type_enum,
            proxy_string=proxy,
            persistent_position=position,
            **kwargs
        )
        
        return browser
    
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


"""
Main GPM Service with Dependency Injection
Combines profile management, browser control, and monitoring
"""

import asyncio
from typing import Optional
import nodriver as nd

from ..config import GPMConfig, get_config
from ..api.gpm_client import GPMApiClient, GPMApiException
from ..services.profile_monitor import ProfileMonitor
from ..schemas import (
    ProfileCreateRequest,
    ProfileResponse,
    BrowserLaunchRequest,
    BrowserConnectionInfo,
)
from ..enums import ProxyType, ProfileStatus


class GPMService:
    """
    Main GPM Service with Dependency Injection
    
    This service provides high-level operations for browser profile management
    with automatic profile creation, status monitoring, and browser launching.
    
    Usage:
        # Basic usage with defaults
        service = GPMService()
        browser = await service.launch_browser("my_profile")
        
        # With custom config
        config = GPMConfig(gpm_api_base_url="http://localhost:12003/api/v3")
        service = GPMService(config=config)
        
        # With dependency injection
        api_client = GPMApiClient(config)
        monitor = ProfileMonitor(config)
        service = GPMService(config=config, api_client=api_client, monitor=monitor)
    """
    
    def __init__(
        self,
        config: Optional[GPMConfig] = None,
        api_client: Optional[GPMApiClient] = None,
        monitor: Optional[ProfileMonitor] = None,
    ):
        """
        Initialize GPM Service
        
        Args:
            config: Optional configuration. If not provided, uses global config.
            api_client: Optional API client. If not provided, creates new one.
            monitor: Optional profile monitor. If not provided, creates new one.
        """
        self.config = config or get_config()
        self.api_client = api_client or GPMApiClient(self.config)
        self.monitor = monitor or ProfileMonitor(self.config)
    
    async def launch_browser(
        self,
        profile_name: str,
        proxy_type: Optional[ProxyType] = None,
        proxy_string: Optional[str] = None,
        max_retries: Optional[int] = None,
        persistent_position: int = 0,
        window_width: Optional[int] = None,
        window_height: Optional[int] = None,
        window_x: Optional[int] = None,
        window_y: Optional[int] = None,
        window_scale: Optional[float] = None,
    ) -> Optional[nd.Browser]:
        """
        Launch browser with profile (high-level method)
        
        This method handles:
        - Profile creation if doesn't exist
        - Proxy configuration
        - Status checking and cleanup
        - Browser connection with retries
        
        Args:
            profile_name: Profile name
            proxy_type: Proxy protocol type
            proxy_string: Proxy in format IP:Port:User:Pass
            max_retries: Maximum retry attempts (default from config)
            persistent_position: Browser window position index
            window_width: Browser window width (default from config)
            window_height: Browser window height (default from config)
            window_scale: Browser window scale (default from config)
            
        Returns:
            nodriver Browser instance or None if failed
        """
        request = BrowserLaunchRequest(
            profile_name=profile_name,
            proxy_type=proxy_type,
            proxy_string=proxy_string,
            max_retries=max_retries or self.config.max_retries,
            persistent_position=persistent_position,
            window_width=window_width or self.config.browser_width,
            window_height=window_height or self.config.browser_height,
            window_x=window_x,
            window_y=window_y,
            window_scale=window_scale or self.config.browser_scale,
        )
        
        for attempt in range(request.max_retries):
            try:
                print(f"🔧 [{profile_name}] Attempt {attempt + 1}/{request.max_retries}")
                
                # Step 1: Get or create profile
                profile = await self._ensure_profile_exists(
                    profile_name=profile_name,
                    proxy_type=proxy_type,
                    proxy_string=proxy_string,
                )
                
                if not profile:
                    raise Exception("Failed to get or create profile")
                
                # Step 2: Check and handle profile status
                browser = await self._handle_profile_status(
                    profile=profile,
                    request=request,
                )
                
                if browser:
                    return browser
                
                # If we get here, status handling didn't return a browser
                # Continue to retry
                
            except Exception as e:
                print(f"❌ [{profile_name}] Attempt {attempt + 1} failed: {e}")
                
                if attempt < request.max_retries - 1:
                    wait_time = self.config.retry_delay * (attempt + 1)
                    print(f"⏳ [{profile_name}] Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"💀 [{profile_name}] All attempts exhausted")
                    return None
        
        return None
    
    async def _ensure_profile_exists(
        self,
        profile_name: str,
        proxy_type: Optional[ProxyType],
        proxy_string: Optional[str],
    ) -> Optional[ProfileResponse]:
        """Get existing profile or create new one"""
        
        # Try to get existing profile
        profile = self.api_client.get_profile_by_name(profile_name)
        
        if profile:
            print(f"✅ [{profile_name}] Profile found")
            return profile
        
        # Create new profile
        print(f"🍣 [{profile_name}] Creating new profile...")
        
        # Prepare proxy
        raw_proxy = None
        if proxy_type and proxy_string:
            if proxy_type == ProxyType.HTTP:
                raw_proxy = proxy_string
            else:
                raw_proxy = f"{proxy_type.value}://{proxy_string}"
        
        # Create profile request
        create_request = ProfileCreateRequest(
            profile_name=profile_name,
            is_masked_font=True,
            is_noise_canvas=True,
            is_noise_webgl=True,
            is_noise_client_rect=True,
            is_noise_audio_context=True,
            raw_proxy=raw_proxy,
        )
        
        try:
            profile = self.api_client.create_profile(create_request)
            print(f"✅ [{profile_name}] Profile created successfully")
            await asyncio.sleep(self.config.connection_wait_time)
            return profile
        except GPMApiException as e:
            print(f"❌ [{profile_name}] Profile creation failed: {e}")
            return None
    
    async def _handle_profile_status(
        self,
        profile: ProfileResponse,
        request: BrowserLaunchRequest,
    ) -> Optional[nd.Browser]:
        """Check profile status and handle accordingly"""
        
        profile_name = request.profile_name
        profile_path = profile.profile_path
        
        # Check status
        status_result = self.monitor.check_all_profiles_status()
        
        is_running = status_result.is_running(profile_path)
        is_pending = status_result.is_pending(profile_path)
        
        print(f"🔍 [{profile_name}] Status - Running: {is_running}, Pending: {is_pending}")
        
        # Handle pending profiles
        if is_pending:
            print(f"⬇️ [{profile_name}] Closing pending profile...")
            self.api_client.close_profile_by_name(profile_name)
            await asyncio.sleep(self.config.retry_delay)
            
            # Recheck status
            status_result = self.monitor.check_all_profiles_status()
            is_running = status_result.is_running(profile_path)
            is_pending = status_result.is_pending(profile_path)
        
        # Handle running profiles - try to connect
        if is_running:
            print(f"🔗 [{profile_name}] Profile already running, attempting to connect...")
            
            try:
                # Get connection info
                profiles = self.api_client.get_profiles()
                current_profile = None
                
                for p in profiles:
                    if p.name == profile_name and p.status == "running":
                        current_profile = p
                        break
                
                if current_profile and hasattr(current_profile, "remote_debugging_address"):
                    # Use schema properties for robust parsing
                    host = current_profile.host
                    port = current_profile.port
                    
                    if host and port:
                        browser = await self._connect_to_browser(host, port, profile_name)

                        if browser:
                            return browser
                
                # Connection failed, close and restart
                print(f"🔄 [{profile_name}] Connection failed, restarting...")
                self.api_client.close_profile_by_name(profile_name)
                await asyncio.sleep(self.config.retry_delay)
                is_running = False
                
            except Exception as e:
                print(f"⚠️ [{profile_name}] Error connecting: {e}")
                self.api_client.close_profile_by_name(profile_name)
                await asyncio.sleep(self.config.retry_delay)
                is_running = False
        
        # Start new profile if not running
        if not is_running:
            return await self._start_new_profile(profile, request)
        
        return None
    
    async def _start_new_profile(
        self,
        profile: ProfileResponse,
        request: BrowserLaunchRequest,
    ) -> Optional[nd.Browser]:
        """Start a new profile and connect to it"""
        
        profile_name = request.profile_name
        
        print(f"🚀 [{profile_name}] Starting new profile...")
        
        # Calculate window position
        if request.window_x is not None and request.window_y is not None:
            pos_x = request.window_x
            pos_y = request.window_y
        else:
            row = request.persistent_position // self.config.max_browsers_per_line
            col = request.persistent_position % self.config.max_browsers_per_line
            
            pos_x = col * request.window_width
            pos_y = row * request.window_height
        
        try:
            # Start profile via API
            open_response = self.api_client.start_profile(
                profile_id=profile.id,
                window_size=f"{request.window_width},{request.window_height}",
                window_pos=f"{pos_x},{pos_y}",
                window_scale=request.window_scale,
            )
            
            print(f"📔 [{profile_name}] Profile started: {open_response.remote_debugging_address}")
            
            await asyncio.sleep(self.config.connection_wait_time)
            
            # Connect to browser
            browser = await self._connect_to_browser(
                open_response.host,
                open_response.port,
                profile_name,
            )
            
            if not browser:
                raise Exception("Failed to connect to browser")
            
            # Verify browser works
            try:
                page = await browser.get()
                print(f"✅ [{profile_name}] Browser ready! URL: {page.url}")
                return browser
            except Exception as e:
                print(f"❌ [{profile_name}] Browser verification failed: {e}")
                await browser.stop()
                raise
                
        except Exception as e:
            print(f"❌ [{profile_name}] Failed to start profile: {e}")
            return None
    
    async def _connect_to_browser(
        self,
        host: str,
        port: int,
        profile_name: str,
    ) -> Optional[nd.Browser]:
        """Connect to existing Chrome instance via nodriver"""
        
        try:
            print(f"🔌 [{profile_name}] Connecting to {host}:{port}...")
            
            browser = await nd.start(
                headless=False,
                sandbox=False,
                host=host,
                port=port,
                browser_args=[
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            
            if browser:
                print(f"✅ [{profile_name}] Connected to browser")
                return browser
            
            return None
            
        except Exception as e:
            print(f"❌ [{profile_name}] Connection failed: {e}")
            return None
    
    def close_profile(self, profile_name: str) -> bool:
        """
        Close a running profile
        
        Args:
            profile_name: Profile name
            
        Returns:
            True if successful
        """
        return self.api_client.close_profile_by_name(profile_name)
    
    def get_profile_status(self, profile_name: str) -> ProfileStatus:
        """
        Get current status of a profile
        
        Args:
            profile_name: Profile name
            
        Returns:
            ProfileStatus enum
        """
        status_result = self.monitor.check_all_profiles_status()
        return status_result.get_status(profile_name)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.api_client.__exit__(exc_type, exc_val, exc_tb)

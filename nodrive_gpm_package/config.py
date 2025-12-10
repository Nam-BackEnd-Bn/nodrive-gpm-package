"""
Configuration module for GPM Package
Handles environment variables and default settings
"""

import os
from typing import Optional

class GPMConfig:
    """
    GPM Configuration using environment variables or constructor arguments
    
    Constructor arguments take precedence over environment variables.

    Usage:
        # Using environment variables:
        # export GPM_API_BASE_URL=http://127.0.0.1:12003/api/v3
        config = GPMConfig()
        
        # Using constructor arguments:
        config = GPMConfig(
            gpm_api_base_url="http://127.0.0.1:12003/api/v3",
            browser_width=1920,
            browser_height=1080,
            debug=True
        )
        
        # Mix of both (constructor args override env vars):
        config = GPMConfig(browser_width=1920)  # Other settings from env
    """

    def __init__(
        self,
        gpm_api_base_url: Optional[str] = None,
        gpm_api_timeout: Optional[int] = None,
        gpm_profiles_dir: Optional[str] = None,
        browser_width: Optional[int] = None,
        browser_height: Optional[int] = None,
        browser_scale: Optional[float] = None,
        max_browsers_per_line: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        connection_wait_time: Optional[int] = None,
        cpu_threshold: Optional[float] = None,
        cpu_check_interval: Optional[float] = None,
        debug: Optional[bool] = None,
    ):
        # API Settings (constructor args take precedence)
        self.gpm_api_base_url: str = (
            gpm_api_base_url if gpm_api_base_url is not None 
            else os.getenv("GPM_API_BASE_URL", "http://127.0.0.1:12003/api/v3")
        )
        self.gpm_api_timeout: int = (
            gpm_api_timeout if gpm_api_timeout is not None
            else int(os.getenv("GPM_API_TIMEOUT", "30"))
        )

        # Profile Storage
        env_profiles_dir = os.getenv("GPM_PROFILES_DIR")
        self.gpm_profiles_dir: Optional[str] = (
            gpm_profiles_dir if gpm_profiles_dir is not None
            else (env_profiles_dir if env_profiles_dir else None)
        )

        # Browser Settings
        self.browser_width: int = (
            browser_width if browser_width is not None
            else int(os.getenv("BROWSER_WIDTH", "1000"))
        )
        self.browser_height: int = (
            browser_height if browser_height is not None
            else int(os.getenv("BROWSER_HEIGHT", "700"))
        )
        self.browser_scale: float = (
            browser_scale if browser_scale is not None
            else float(os.getenv("BROWSER_SCALE", "0.8"))
        )
        self.max_browsers_per_line: int = (
            max_browsers_per_line if max_browsers_per_line is not None
            else int(os.getenv("MAX_BROWSERS_PER_LINE", "4"))
        )

        # Retry Settings
        self.max_retries: int = (
            max_retries if max_retries is not None
            else int(os.getenv("MAX_RETRIES", "3"))
        )
        self.retry_delay: int = (
            retry_delay if retry_delay is not None
            else int(os.getenv("RETRY_DELAY", "5"))
        )
        self.connection_wait_time: int = (
            connection_wait_time if connection_wait_time is not None
            else int(os.getenv("CONNECTION_WAIT_TIME", "3"))
        )

        # CPU Detection Settings
        self.cpu_threshold: float = (
            cpu_threshold if cpu_threshold is not None
            else float(os.getenv("CPU_THRESHOLD", "2.0"))
        )
        self.cpu_check_interval: float = (
            cpu_check_interval if cpu_check_interval is not None
            else float(os.getenv("CPU_CHECK_INTERVAL", "1.5"))
        )

        # Debugging
        self.debug: bool = (
            debug if debug is not None
            else os.getenv("DEBUG", "False").lower() in ("true", "1", "y")
        )

    @property
    def profiles_directory(self) -> str:
        """Get profiles directory, with fallback to default Windows location"""
        if self.gpm_profiles_dir:
            return self.gpm_profiles_dir

        user_profile = os.getenv("USERPROFILE")
        if not user_profile:
            raise ValueError("USERPROFILE environment variable not set")
        return os.path.join(user_profile, "profiles")

    def validate_config(self) -> bool:
        """Validate configuration"""
        if not os.path.exists(self.profiles_directory):
            raise ValueError(f"Profiles directory does not exist: {self.profiles_directory}")
        return True

# Global config instance
_config: Optional[GPMConfig] = None

def get_config() -> GPMConfig:
    """Get or create global config instance"""
    global _config
    if _config is None:
        _config = GPMConfig()
    return _config

def set_config(config: GPMConfig) -> None:
    """Set global config instance"""
    global _config
    _config = config


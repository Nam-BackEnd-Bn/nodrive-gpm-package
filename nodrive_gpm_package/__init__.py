"""
No-Driver GPM Package
Browser Profile Management with Anti-Detection
"""

__version__ = "1.0.0"

# Main exports
from .client import GPMClient
from .config import GPMConfig, get_config, set_config
from .services import (
    GPMService,
    ProfileMonitor,
    GoogleDriveService,
    GoogleDriveServiceException,
    UploadFileResult,
    FileInfo,
    StorageInfo,
    GoogleSheetService,
    GoogleSheetServiceException,
    GoogleSheetOAuth,
    GoogleSheetOAuthException,
    HelperGGSheet,
    SheetChildrenInfo,
    SheetInfo,
    SheetValUpdateCell,
    ExportType,
    CaptchaService,
    CaptchaServiceException,
    CaptchaSolution,
    RecaptchaVerification,
)
from .api.gpm_client import GPMApiClient, GPMApiException

# Enums
from .enums import ProxyType, ProfileStatus, BrowserStatus

# Schemas
from .schemas import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
    BrowserLaunchRequest,
    ProxyConfig,
)

__all__ = [
    # Main client
    "GPMClient",
    
    # Configuration
    "GPMConfig",
    "get_config",
    "set_config",
    
    # Services
    "GPMService",
    "GPMApiClient",
    "ProfileMonitor",
    "GPMApiException",
    "GoogleDriveService",
    "GoogleDriveServiceException",
    "UploadFileResult",
    "FileInfo",
    "StorageInfo",
    "GoogleSheetService",
    "GoogleSheetServiceException",
    "GoogleSheetOAuth",
    "GoogleSheetOAuthException",
    "HelperGGSheet",
    "SheetChildrenInfo",
    "SheetInfo",
    "SheetValUpdateCell",
    "ExportType",
    "CaptchaService",
    "CaptchaServiceException",
    "CaptchaSolution",
    "RecaptchaVerification",
    
    # Enums
    "ProxyType",
    "ProfileStatus",
    "BrowserStatus",
    
    # Schemas
    "ProfileCreateRequest",
    "ProfileUpdateRequest",
    "ProfileResponse",
    "BrowserLaunchRequest",
    "ProxyConfig",
]

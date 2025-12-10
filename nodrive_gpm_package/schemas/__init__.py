"""Pydantic schemas for GPM Package"""

from .profile import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
    ProfileOpenResponse,
    ProfileListResponse,
    ProfileStatusResponse,
)
from .browser import (
    BrowserLaunchRequest,
    BrowserConnectionInfo,
)
from .proxy import ProxyConfig

__all__ = [
    "ProfileCreateRequest",
    "ProfileUpdateRequest",
    "ProfileResponse",
    "ProfileOpenResponse",
    "ProfileListResponse",
    "ProfileStatusResponse",
    "BrowserLaunchRequest",
    "BrowserConnectionInfo",
    "ProxyConfig",
]

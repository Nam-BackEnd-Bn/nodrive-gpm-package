"""
Refactored GPM API Client with dependency injection
"""

import requests
from typing import List, Optional, Dict, Any
from requests.exceptions import RequestException, Timeout

from ..config import GPMConfig, get_config
from ..schemas import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
    ProfileOpenResponse,
)


class GPMApiException(Exception):
    """Custom exception for GPM API errors"""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class GPMApiClient:
    """
    GPM API Client with dependency injection
    
    This class handles all communication with the GPM API server.
    
    Usage:
        # With default config
        client = GPMApiClient()
        
        # With custom config
        config = GPMConfig(gpm_api_base_url="http://localhost:12003/api/v3")
        client = GPMApiClient(config=config)
    """

    def __init__(self, config: Optional[GPMConfig] = None):
        """
        Initialize GPM API Client
        
        Args:
            config: Optional GPMConfig instance. If not provided, uses global config.
        """
        self.config = config or get_config()
        self.base_url = self.config.gpm_api_base_url
        self.timeout = self.config.gpm_api_timeout
        self.session = requests.Session()

    def _make_request(
            self,
            method: str,
            endpoint: str,
            json: Optional[Dict] = None,
            params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to GPM API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /profiles)
            json: JSON payload for POST requests
            params: Query parameters
            
        Returns:
            Response data dictionary
            
        Raises:
            GPMApiException: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                timeout=self.timeout,
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            if self.config.debug:
                print(f"✅ API {method} {endpoint}: {response.status_code}")
                print(f"📦 Response: {result}")

            # Extract data from response
            data = result.get("data", result)
            
            # Handle None response
            if data is None:
                raise GPMApiException(
                    f"API returned None/empty data for {method} {endpoint}. Response: {result}",
                    status_code=response.status_code
                )
            
            return data

        except Timeout:
            raise GPMApiException(
                f"Request timeout after {self.timeout}s: {method} {url}",
                status_code=408,
            )
        except RequestException as e:
            status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            raise GPMApiException(
                f"API request failed: {str(e)}",
                status_code=status_code,
            )
        except Exception as e:
            raise GPMApiException(f"Unexpected error: {str(e)}")

    # ==================== Profile Management ====================

    def create_profile(self, request: ProfileCreateRequest) -> ProfileResponse:
        """
        Create a new browser profile
        
        Args:
            request: Profile creation request
            
        Returns:
            Created profile information
        """
        data = self._make_request(
            method="POST",
            endpoint="/profiles/create",
            json=request.model_dump(exclude_none=True),
        )
        return ProfileResponse(**data)

    def get_profiles(self) -> List[ProfileResponse]:
        """
        Get list of all profiles
        
        Returns:
            List of profiles
        """
        data = self._make_request(method="GET", endpoint="/profiles")

        if isinstance(data, list):
            return [ProfileResponse(**profile) for profile in data]
        return []

    def get_profile_by_id(self, profile_id: str) -> Optional[ProfileResponse]:
        """
        Get profile by ID
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Profile information or None if not found
        """
        try:
            data = self._make_request(method="GET", endpoint=f"/profiles/{profile_id}")
            return ProfileResponse(**data)
        except GPMApiException:
            return None

    def get_profile_by_name(self, profile_name: str) -> Optional[ProfileResponse]:
        """
        Get profile by name
        
        Args:
            profile_name: Profile name
            
        Returns:
            Profile information or None if not found
        """
        profiles = self.get_profiles()

        for profile in profiles:
            if profile.name == profile_name:
                return profile

        return None

    def update_profile(
            self,
            profile_id: str,
            request: ProfileUpdateRequest,
    ) -> ProfileResponse:
        """
        Update profile by ID
        
        Args:
            profile_id: Profile ID
            request: Update request
            
        Returns:
            Updated profile information
        """
        data = self._make_request(
            method="POST",
            endpoint=f"/profiles/update/{profile_id}",
            json=request.model_dump(exclude_none=True),
        )
        return ProfileResponse(**data)

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete profile by ID
        
        Args:
            profile_id: Profile ID
            
        Returns:
            True if successful
        """
        try:
            self._make_request(method="GET", endpoint=f"/profiles/delete/{profile_id}")
            return True
        except GPMApiException:
            return False

    def delete_profile_by_name(self, profile_name: str) -> bool:
        """
        Delete profile by name
        
        Args:
            profile_name: Profile name
            
        Returns:
            True if successful
        """
        profile = self.get_profile_by_name(profile_name)
        if not profile:
            return False

        return self.delete_profile(profile.id)

    # ==================== Profile Operations ====================

    def start_profile(
            self,
            profile_id: str,
            window_size: Optional[str] = None,
            window_pos: Optional[str] = None,
            window_scale: Optional[float] = None,
            additional_args: Optional[str] = None,
    ) -> ProfileOpenResponse:
        """
        Start a browser profile
        
        Args:
            profile_id: Profile ID
            window_size: Window size (e.g., "1000,700")
            window_pos: Window position (e.g., "0,0")
            window_scale: Window scale (e.g., 0.8)
            additional_args: Additional Chrome arguments
            
        Returns:
            Profile open response with debugging address
        """
        params = {}
        if window_size:
            params["win_size"] = window_size
        if window_pos:
            params["win_pos"] = window_pos
        if window_scale:
            params["win_scale"] = window_scale
        if additional_args:
            params["additional_args"] = additional_args

        data = self._make_request(
            method="GET",
            endpoint=f"/profiles/start/{profile_id}",
            params=params,
        )
        return ProfileOpenResponse(**data)

    def close_profile(self, profile_id: str) -> bool:
        """
        Close a running profile
        
        Args:
            profile_id: Profile ID
            
        Returns:
            True if successful
        """
        try:
            self._make_request(method="GET", endpoint=f"/profiles/close/{profile_id}")
            return True
        except GPMApiException:
            return False

    def close_profile_by_name(self, profile_name: str) -> bool:
        """
        Close a running profile by name
        
        Args:
            profile_name: Profile name
            
        Returns:
            True if successful
        """
        profile = self.get_profile_by_name(profile_name)
        if not profile:
            return False

        return self.close_profile(profile.id)

    # ==================== Group Management ====================

    def create_group(self, name: str, sort: int = 0) -> Dict[str, Any]:
        """
        Create a profile group
        
        Args:
            name: Group name
            sort: Sort order
            
        Returns:
            Created group information
        """
        return self._make_request(
            method="POST",
            endpoint="/groups/create",
            json={"name": name, "sort": sort},
        )

    def get_groups(self) -> List[Dict[str, Any]]:
        """
        Get list of all groups
        
        Returns:
            List of groups
        """
        data = self._make_request(method="GET", endpoint="/groups")

        if isinstance(data, list):
            return data
        return []

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.session.close()

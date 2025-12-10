"""
Captcha Service
Provides reCAPTCHA solving capabilities using AchiCaptcha API.
"""

import time
import logging
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass

try:
    import requests
except ImportError:
    raise ImportError(
        "Requests library not installed. Install with: pip install requests"
    )


logger = logging.getLogger(__name__)


class CaptchaServiceException(Exception):
    """Exception raised for Captcha service errors"""
    pass


@dataclass
class CaptchaSolution:
    """Result of captcha solving"""
    task_id: str
    token: str
    status: str
    cost: Optional[float] = None
    ip: Optional[str] = None
    create_time: Optional[int] = None
    end_time: Optional[int] = None
    solve_count: Optional[int] = None


@dataclass
class RecaptchaVerification:
    """Result of reCAPTCHA verification"""
    success: bool
    challenge_ts: Optional[str] = None
    hostname: Optional[str] = None
    error_codes: Optional[list] = None
    score: Optional[float] = None
    action: Optional[str] = None


class CaptchaService:
    """
    Captcha solving service using AchiCaptcha API
    
    This service provides automated captcha solving for reCAPTCHA v2 and v3
    using the AchiCaptcha API service.
    
    Features:
        - reCAPTCHA v2 solving (with and without proxy)
        - reCAPTCHA v3 solving
        - Token verification
        - Automatic polling for results
        - Configurable timeouts and retry logic
    
    Usage:
        # Initialize service
        service = CaptchaService(
            client_key='your_achicaptcha_api_key',
            google_secret_key='your_google_recaptcha_secret'  # Optional for verification
        )
        
        # Solve reCAPTCHA v2
        solution = service.solve_recaptcha_v2(
            website_url='https://example.com',
            website_key='6Le-wvkSAAAAAPBMRTvw0Q...'
        )
        
        print(f"Captcha token: {solution.token}")
        
        # Verify solution (optional)
        verification = service.verify_recaptcha(solution.token)
        if verification.success:
            print("Captcha verified successfully")
    """
    
    API_BASE_URL = "https://api.achicaptcha.com"
    GOOGLE_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
    
    def __init__(
        self,
        client_key: Optional[str] = None,
        google_secret_key: Optional[str] = None,
        default_timeout: int = 120,
        poll_interval: int = 3,
        debug: bool = False
    ):
        """
        Initialize Captcha Service
        
        Args:
            client_key: AchiCaptcha API client key
            google_secret_key: Google reCAPTCHA secret key (for verification)
            default_timeout: Maximum time to wait for captcha solution (seconds)
            poll_interval: Time between polling requests (seconds)
            debug: Enable debug logging
        """
        self.client_key = client_key
        self.google_secret_key = google_secret_key
        self.default_timeout = default_timeout
        self.poll_interval = poll_interval
        self.debug = debug
        
        if debug:
            logger.setLevel(logging.DEBUG)
        
        if not self.client_key:
            logger.warning("No AchiCaptcha client key provided. Set via constructor or environment.")
    
    def solve_recaptcha_v2(
        self,
        website_url: str,
        website_key: str,
        timeout: Optional[int] = None,
        proxy: Optional[str] = None,
        user_agent: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None
    ) -> CaptchaSolution:
        """
        Solve reCAPTCHA v2 challenge
        
        Args:
            website_url: URL of the website with captcha
            website_key: reCAPTCHA site key
            timeout: Maximum time to wait for solution (default: 120s)
            proxy: Proxy string in format "ip:port:user:pass" (optional)
            user_agent: User agent string (optional)
            cookies: Cookies dictionary (optional)
        
        Returns:
            CaptchaSolution object with token
        
        Raises:
            CaptchaServiceException: If captcha solving fails
        
        Example:
            >>> service = CaptchaService(client_key='your_key')
            >>> solution = service.solve_recaptcha_v2(
            ...     website_url='https://example.com',
            ...     website_key='6Le-wvkSAAAAAPBMRTvw0Q...'
            ... )
            >>> print(solution.token)
        """
        if not self.client_key:
            raise CaptchaServiceException("AchiCaptcha client key not set")
        
        logger.info(f"🔐 Starting reCAPTCHA v2 solve for {website_url}")
        
        # Build task payload
        task = {
            "type": "RecaptchaV2TaskProxyless",
            "websiteURL": website_url,
            "websiteKey": website_key,
        }
        
        # Add optional parameters
        if proxy:
            task["type"] = "RecaptchaV2Task"
            task["proxyType"] = "http"  # or "socks5"
            task["proxyAddress"] = proxy.split(":")[0]
            task["proxyPort"] = int(proxy.split(":")[1])
            if len(proxy.split(":")) > 2:
                task["proxyLogin"] = proxy.split(":")[2]
                task["proxyPassword"] = proxy.split(":")[3]
        
        if user_agent:
            task["userAgent"] = user_agent
        
        if cookies:
            task["cookies"] = ";".join([f"{k}={v}" for k, v in cookies.items()])
        
        # Create task
        task_id = self._create_task(task)
        
        # Poll for result
        timeout_val = timeout or self.default_timeout
        solution = self._get_task_result(task_id, timeout_val)
        
        logger.info(f"✅ reCAPTCHA v2 solved successfully")
        return solution
    
    def solve_recaptcha_v3(
        self,
        website_url: str,
        website_key: str,
        action: str = "verify",
        min_score: float = 0.3,
        timeout: Optional[int] = None,
        proxy: Optional[str] = None
    ) -> CaptchaSolution:
        """
        Solve reCAPTCHA v3 challenge
        
        Args:
            website_url: URL of the website with captcha
            website_key: reCAPTCHA site key
            action: Action name for reCAPTCHA v3
            min_score: Minimum score required (0.0 - 1.0)
            timeout: Maximum time to wait for solution
            proxy: Proxy string (optional)
        
        Returns:
            CaptchaSolution object with token
        
        Raises:
            CaptchaServiceException: If captcha solving fails
        """
        if not self.client_key:
            raise CaptchaServiceException("AchiCaptcha client key not set")
        
        logger.info(f"🔐 Starting reCAPTCHA v3 solve for {website_url}")
        
        task = {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": website_url,
            "websiteKey": website_key,
            "pageAction": action,
            "minScore": min_score
        }
        
        if proxy:
            task["type"] = "RecaptchaV3Task"
            # Add proxy configuration similar to v2
        
        task_id = self._create_task(task)
        timeout_val = timeout or self.default_timeout
        solution = self._get_task_result(task_id, timeout_val)
        
        logger.info(f"✅ reCAPTCHA v3 solved successfully")
        return solution
    
    def _create_task(self, task: Dict[str, Any]) -> str:
        """
        Create captcha solving task
        
        Args:
            task: Task configuration dictionary
        
        Returns:
            Task ID string
        
        Raises:
            CaptchaServiceException: If task creation fails
        """
        url = f"{self.API_BASE_URL}/createTask"
        headers = {"Content-Type": "application/json"}
        payload = {
            "clientKey": self.client_key,
            "task": task
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error creating task: {e}")
            raise CaptchaServiceException(f"HTTP error creating captcha task: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error creating task: {e}")
            raise CaptchaServiceException(f"Request error creating captcha task: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating task: {e}")
            raise CaptchaServiceException(f"Unexpected error creating captcha task: {e}")
        
        # Check for errors
        error_id = result.get("errorId", -1)
        if error_id != 0:
            error_code = result.get("errorCode", "unknown")
            error_desc = result.get("errorDescription", "No description")
            logger.error(f"Task creation failed: {error_code} - {error_desc}")
            raise CaptchaServiceException(f"Task creation failed: {error_code} - {error_desc}")
        
        task_id = result.get("taskId")
        if not task_id:
            raise CaptchaServiceException("No task ID returned from API")
        
        logger.debug(f"Task created successfully: {task_id}")
        return task_id
    
    def _get_task_result(self, task_id: str, timeout: int) -> CaptchaSolution:
        """
        Poll for task result
        
        Args:
            task_id: Task ID to poll
            timeout: Maximum time to wait (seconds)
        
        Returns:
            CaptchaSolution object
        
        Raises:
            CaptchaServiceException: If polling fails or times out
        """
        url = f"{self.API_BASE_URL}/getTaskResult"
        headers = {"Content-Type": "application/json"}
        payload = {
            "clientKey": self.client_key,
            "taskId": task_id
        }
        
        start_time = time.time()
        attempts = 0
        
        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.error(f"Timeout waiting for captcha solution (>{timeout}s)")
                raise CaptchaServiceException(f"Timeout waiting for captcha solution after {timeout}s")
            
            attempts += 1
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error polling task result (attempt {attempts}): {e}")
                time.sleep(self.poll_interval)
                continue
            
            if self.debug:
                logger.debug(f"Poll result (attempt {attempts}): {result}")
            
            # Check for errors
            error_id = result.get("errorId", -1)
            if error_id != 0:
                error_code = result.get("errorCode", "unknown")
                error_desc = result.get("errorDescription", "No description")
                logger.error(f"Task failed: {error_code} - {error_desc}")
                raise CaptchaServiceException(f"Task failed: {error_code} - {error_desc}")
            
            status = result.get("status")
            
            if status == "ready":
                solution_data = result.get("solution", {})
                token = solution_data.get("gRecaptchaResponse")
                
                if not token:
                    raise CaptchaServiceException("No captcha token in solution")
                
                logger.info(f"✅ Captcha solved in {elapsed:.1f}s ({attempts} attempts)")
                
                return CaptchaSolution(
                    task_id=task_id,
                    token=token,
                    status="ready",
                    cost=result.get("cost"),
                    ip=result.get("ip"),
                    create_time=result.get("createTime"),
                    end_time=result.get("endTime"),
                    solve_count=result.get("solveCount")
                )
            
            elif status == "processing":
                logger.debug(f"Captcha processing... ({elapsed:.1f}s elapsed)")
                time.sleep(self.poll_interval)
            
            else:
                logger.warning(f"Unknown status: {status}")
                time.sleep(self.poll_interval)
    
    def verify_recaptcha(
        self,
        token: str,
        remote_ip: Optional[str] = None
    ) -> RecaptchaVerification:
        """
        Verify reCAPTCHA token with Google
        
        Args:
            token: reCAPTCHA response token to verify
            remote_ip: User's IP address (optional)
        
        Returns:
            RecaptchaVerification object with verification result
        
        Raises:
            CaptchaServiceException: If verification request fails
        
        Example:
            >>> service = CaptchaService(
            ...     client_key='your_key',
            ...     google_secret_key='your_secret'
            ... )
            >>> verification = service.verify_recaptcha(token)
            >>> if verification.success:
            ...     print("Valid captcha!")
        """
        if not self.google_secret_key:
            raise CaptchaServiceException("Google reCAPTCHA secret key not set")
        
        logger.info("🔍 Verifying reCAPTCHA token with Google")
        
        data = {
            "secret": self.google_secret_key,
            "response": token
        }
        
        if remote_ip:
            data["remoteip"] = remote_ip
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            response = requests.post(
                self.GOOGLE_VERIFY_URL,
                data=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying captcha: {e}")
            raise CaptchaServiceException(f"Error verifying captcha: {e}")
        
        if self.debug:
            logger.debug(f"Verification result: {result}")
        
        success = result.get("success", False)
        
        if success:
            logger.info("✅ reCAPTCHA verification successful")
        else:
            error_codes = result.get("error-codes", [])
            logger.warning(f"❌ reCAPTCHA verification failed: {error_codes}")
        
        return RecaptchaVerification(
            success=success,
            challenge_ts=result.get("challenge_ts"),
            hostname=result.get("hostname"),
            error_codes=result.get("error-codes"),
            score=result.get("score"),
            action=result.get("action")
        )
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance from AchiCaptcha
        
        Returns:
            Dictionary with balance information
        
        Raises:
            CaptchaServiceException: If request fails
        """
        if not self.client_key:
            raise CaptchaServiceException("AchiCaptcha client key not set")
        
        url = f"{self.API_BASE_URL}/getBalance"
        headers = {"Content-Type": "application/json"}
        payload = {"clientKey": self.client_key}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise CaptchaServiceException(f"Error getting balance: {e}")
        
        error_id = result.get("errorId", -1)
        if error_id != 0:
            error_code = result.get("errorCode", "unknown")
            raise CaptchaServiceException(f"Get balance failed: {error_code}")
        
        balance = result.get("balance", 0)
        logger.info(f"💰 Account balance: {balance}")
        
        return {
            "balance": balance,
            "currency": "USD"
        }


# Backward compatibility alias
decodeCaptcha = CaptchaService.solve_recaptcha_v2
verifyRecaptcha = CaptchaService.verify_recaptcha


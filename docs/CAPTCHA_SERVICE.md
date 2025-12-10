## Captcha Service

Automated reCAPTCHA solving using the AchiCaptcha API.

## Overview

The `CaptchaService` provides automated solving for reCAPTCHA v2 and v3 challenges using the AchiCaptcha API service. Perfect for automation tasks that require bypassing reCAPTCHA verification.

### Features

- ✅ **reCAPTCHA v2** - Solve standard checkbox captchas
- ✅ **reCAPTCHA v3** - Solve invisible captchas with score
- ✅ **Proxy Support** - Use proxies for solving
- ✅ **Token Verification** - Verify solutions with Google
- ✅ **Balance Checking** - Monitor account balance
- ✅ **Automatic Polling** - Auto-check for solutions
- ✅ **Timeout Protection** - Configurable timeouts
- ✅ **Debug Mode** - Detailed logging

## Installation

The captcha service is included in the package:

```bash
pip install nodrive-gpm-package
```

Or install just the required dependency:

```bash
pip install requests
```

## Setup

### 1. Get AchiCaptcha API Key

1. Sign up at [AchiCaptcha](https://achicaptcha.com)
2. Add funds to your account
3. Get your API client key from dashboard

### 2. Get Google reCAPTCHA Secret (Optional)

Only needed if you want to verify solutions:

1. Go to [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Register your site
3. Get the secret key

## Basic Usage

### Initialize Service

```python
from nodrive_gpm_package import CaptchaService

# Basic initialization
service = CaptchaService(
    client_key='your_achicaptcha_api_key'
)

# With Google secret for verification
service = CaptchaService(
    client_key='your_achicaptcha_api_key',
    google_secret_key='your_google_secret_key'
)

# With custom settings
service = CaptchaService(
    client_key='your_achicaptcha_api_key',
    default_timeout=120,    # Maximum wait time (seconds)
    poll_interval=3,        # Check interval (seconds)
    debug=True             # Enable debug logging
)
```

### Solve reCAPTCHA v2

```python
# Solve standard reCAPTCHA
solution = service.solve_recaptcha_v2(
    website_url='https://example.com',
    website_key='6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-'
)

print(f"Captcha token: {solution.token}")
print(f"Task ID: {solution.task_id}")
print(f"Cost: ${solution.cost}")
```

### Solve with Proxy

```python
solution = service.solve_recaptcha_v2(
    website_url='https://example.com',
    website_key='6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-',
    proxy='123.45.67.89:8080:username:password'
)
```

### Solve reCAPTCHA v3

```python
solution = service.solve_recaptcha_v3(
    website_url='https://example.com',
    website_key='6LcR_okUAAAAAPYrPe-HK_0RULO1aZM15ENyM-Mf',
    action='homepage',
    min_score=0.7
)
```

### Verify Solution

```python
# Verify token with Google
verification = service.verify_recaptcha(solution.token)

if verification.success:
    print("✅ Token is valid!")
    print(f"Hostname: {verification.hostname}")
    print(f"Challenge time: {verification.challenge_ts}")
else:
    print("❌ Token is invalid")
    print(f"Errors: {verification.error_codes}")
```

### Check Balance

```python
balance = service.get_balance()
print(f"Balance: ${balance['balance']}")
```

## API Reference

### `CaptchaService`

Main class for captcha solving operations.

#### Constructor

```python
CaptchaService(
    client_key: Optional[str] = None,
    google_secret_key: Optional[str] = None,
    default_timeout: int = 120,
    poll_interval: int = 3,
    debug: bool = False
)
```

**Parameters:**
- `client_key`: AchiCaptcha API client key
- `google_secret_key`: Google reCAPTCHA secret key (for verification)
- `default_timeout`: Maximum wait time for solution (seconds)
- `poll_interval`: Time between status checks (seconds)
- `debug`: Enable debug logging

---

#### `solve_recaptcha_v2()`

Solve reCAPTCHA v2 challenge.

```python
solve_recaptcha_v2(
    website_url: str,
    website_key: str,
    timeout: Optional[int] = None,
    proxy: Optional[str] = None,
    user_agent: Optional[str] = None,
    cookies: Optional[Dict[str, str]] = None
) -> CaptchaSolution
```

**Parameters:**
- `website_url`: URL of the page with captcha
- `website_key`: reCAPTCHA site key
- `timeout`: Override default timeout
- `proxy`: Proxy in format "ip:port:user:pass"
- `user_agent`: Custom user agent string
- `cookies`: Cookies dictionary

**Returns:** `CaptchaSolution` object

**Raises:** `CaptchaServiceException`

**Example:**
```python
solution = service.solve_recaptcha_v2(
    website_url='https://example.com',
    website_key='6Le-wvkSAA...',
    timeout=60,
    proxy='123.45.67.89:8080',
    user_agent='Mozilla/5.0...'
)
```

---

#### `solve_recaptcha_v3()`

Solve reCAPTCHA v3 challenge.

```python
solve_recaptcha_v3(
    website_url: str,
    website_key: str,
    action: str = "verify",
    min_score: float = 0.3,
    timeout: Optional[int] = None,
    proxy: Optional[str] = None
) -> CaptchaSolution
```

**Parameters:**
- `website_url`: URL of the page with captcha
- `website_key`: reCAPTCHA site key
- `action`: Action name for v3
- `min_score`: Minimum score required (0.0 - 1.0)
- `timeout`: Override default timeout
- `proxy`: Proxy string

**Returns:** `CaptchaSolution` object

**Example:**
```python
solution = service.solve_recaptcha_v3(
    website_url='https://example.com',
    website_key='6LcR_okUAA...',
    action='login',
    min_score=0.7
)
```

---

#### `verify_recaptcha()`

Verify reCAPTCHA token with Google.

```python
verify_recaptcha(
    token: str,
    remote_ip: Optional[str] = None
) -> RecaptchaVerification
```

**Parameters:**
- `token`: reCAPTCHA response token
- `remote_ip`: User's IP address (optional)

**Returns:** `RecaptchaVerification` object

**Example:**
```python
verification = service.verify_recaptcha(
    token='03AGdBq26...',
    remote_ip='123.45.67.89'
)

if verification.success:
    print("Valid!")
```

---

#### `get_balance()`

Get account balance.

```python
get_balance() -> Dict[str, Any]
```

**Returns:** Dictionary with balance info

**Example:**
```python
balance = service.get_balance()
print(f"Balance: ${balance['balance']}")
```

---

### Data Classes

#### `CaptchaSolution`

Result of captcha solving.

```python
@dataclass
class CaptchaSolution:
    task_id: str                    # Task ID
    token: str                      # Captcha solution token
    status: str                     # Status ("ready")
    cost: Optional[float]           # Cost in USD
    ip: Optional[str]               # Solver IP
    create_time: Optional[int]      # Creation timestamp
    end_time: Optional[int]         # Completion timestamp
    solve_count: Optional[int]      # Attempt count
```

**Usage:**
```python
solution = service.solve_recaptcha_v2(...)
print(f"Token: {solution.token}")
print(f"Cost: ${solution.cost}")
```

---

#### `RecaptchaVerification`

Result of token verification.

```python
@dataclass
class RecaptchaVerification:
    success: bool                       # Verification result
    challenge_ts: Optional[str]         # Challenge timestamp
    hostname: Optional[str]             # Site hostname
    error_codes: Optional[list]         # Error codes if failed
    score: Optional[float]              # Score for v3 (0.0-1.0)
    action: Optional[str]               # Action for v3
```

**Usage:**
```python
verification = service.verify_recaptcha(token)
if verification.success:
    print(f"Hostname: {verification.hostname}")
    if verification.score:
        print(f"Score: {verification.score}")
```

---

### Exception

#### `CaptchaServiceException`

Raised when captcha operations fail.

```python
try:
    solution = service.solve_recaptcha_v2(...)
except CaptchaServiceException as e:
    print(f"Error: {e}")
```

## Advanced Usage

### Integration with Browser Automation

```python
import asyncio
from nodrive_gpm_package import GPMClient, CaptchaService

async def main():
    # Initialize services
    captcha_service = CaptchaService(client_key='your_key')
    gpm_client = GPMClient()
    
    # Launch browser
    browser = await gpm_client.launch("profile_name")
    page = await browser.get("https://example.com/captcha-page")
    
    # Get captcha details from page
    website_key = "6Le-wvkSAA..."  # Extract from page
    website_url = page.url
    
    # Solve captcha
    solution = captcha_service.solve_recaptcha_v2(
        website_url=website_url,
        website_key=website_key
    )
    
    # Inject token into page
    script = f"""
    document.getElementById('g-recaptcha-response').innerHTML = '{solution.token}';
    """
    await page.evaluate(script)
    
    # Submit form or continue automation...
    
    gpm_client.close("profile_name")

asyncio.run(main())
```

### Batch Solving

```python
# Solve multiple captchas
captchas = [
    {"url": "https://site1.com", "key": "6Le..."},
    {"url": "https://site2.com", "key": "6Lc..."},
    {"url": "https://site3.com", "key": "6Ld..."},
]

results = []
for captcha in captchas:
    try:
        solution = service.solve_recaptcha_v2(
            website_url=captcha["url"],
            website_key=captcha["key"]
        )
        results.append({"success": True, "token": solution.token})
    except CaptchaServiceException as e:
        results.append({"success": False, "error": str(e)})

# Process results
successful = sum(1 for r in results if r["success"])
print(f"Solved {successful}/{len(results)} captchas")
```

### With Custom Timeout

```python
service = CaptchaService(
    client_key='your_key',
    default_timeout=180,  # 3 minutes default
    poll_interval=5       # Check every 5 seconds
)

# Override for specific request
solution = service.solve_recaptcha_v2(
    website_url='https://example.com',
    website_key='6Le-wvkSAA...',
    timeout=60  # 1 minute for this one
)
```

### Error Handling

```python
from nodrive_gpm_package import CaptchaService, CaptchaServiceException

service = CaptchaService(client_key='your_key')

try:
    solution = service.solve_recaptcha_v2(
        website_url='https://example.com',
        website_key='6Le-wvkSAA...'
    )
    print(f"Success: {solution.token}")
    
except CaptchaServiceException as e:
    if "timeout" in str(e).lower():
        print("Captcha solving timed out, retry")
    elif "balance" in str(e).lower():
        print("Insufficient balance")
    else:
        print(f"Error: {e}")
```

## Environment Variables

You can set API keys via environment variables:

```bash
# .env file
ACHICAPTCHA_CLIENT_KEY=your_achicaptcha_key
GOOGLE_RECAPTCHA_SECRET=your_google_secret
```

```python
import os
from dotenv import load_dotenv

load_dotenv()

service = CaptchaService(
    client_key=os.getenv('ACHICAPTCHA_CLIENT_KEY'),
    google_secret_key=os.getenv('GOOGLE_RECAPTCHA_SECRET')
)
```

## Cost Estimation

AchiCaptcha pricing (approximate):
- **reCAPTCHA v2**: ~$0.0010 per solve
- **reCAPTCHA v3**: ~$0.0020 per solve

Example cost calculation:

```python
# Solve 1000 captchas
captchas_to_solve = 1000
cost_per_captcha = 0.0010

total_cost = captchas_to_solve * cost_per_captcha
print(f"Estimated cost: ${total_cost:.2f}")  # $1.00
```

## Best Practices

### 1. Use Appropriate Timeouts

```python
# For fast sites
service = CaptchaService(client_key='key', default_timeout=60)

# For slower sites or complex captchas
service = CaptchaService(client_key='key', default_timeout=180)
```

### 2. Check Balance Regularly

```python
balance = service.get_balance()
if balance['balance'] < 1.0:
    print("Low balance warning!")
    # Send notification or pause operations
```

### 3. Verify Solutions When Critical

```python
solution = service.solve_recaptcha_v2(...)

# Verify before using
verification = service.verify_recaptcha(solution.token)
if not verification.success:
    # Retry solving
    solution = service.solve_recaptcha_v2(...)
```

### 4. Handle Errors Gracefully

```python
MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    try:
        solution = service.solve_recaptcha_v2(...)
        break
    except CaptchaServiceException as e:
        if attempt == MAX_RETRIES - 1:
            raise
        print(f"Retry {attempt + 1}/{MAX_RETRIES}")
        time.sleep(5)
```

### 5. Use Proxies for Geo-Restrictions

```python
# Use proxy from same region as target site
solution = service.solve_recaptcha_v2(
    website_url='https://us-only-site.com',
    website_key='6Le...',
    proxy='us-proxy-ip:port:user:pass'
)
```

## Troubleshooting

### Invalid Client Key

**Error:** `Task creation failed: ERROR_KEY_DOES_NOT_EXIST`

**Solution:**
- Verify your API key is correct
- Check if account is active
- Ensure sufficient balance

### Timeout Errors

**Error:** `Timeout waiting for captcha solution`

**Solution:**
- Increase timeout: `default_timeout=180`
- Reduce poll interval: `poll_interval=2`
- Check AchiCaptcha service status

### Invalid Site Key

**Error:** `Task failed: ERROR_WRONG_SITEKEY`

**Solution:**
- Verify the site key from the target website
- Ensure you're using the correct reCAPTCHA version (v2 vs v3)

### Verification Fails

**Issue:** Solution token doesn't verify

**Solution:**
- Use proxy from same region as target site
- Verify website_url matches exactly
- Check if token expired (valid for ~2 minutes)

## Comparison: Manual vs Automated

| Aspect | Manual Solving | CaptchaService |
|--------|---------------|----------------|
| Speed | 10-30 seconds | 5-15 seconds |
| Cost | Free (time) | ~$0.001 per solve |
| Scale | 1-10/hour | 1000+/hour |
| Accuracy | 99%+ | 95%+ |
| Automation | No | Yes |

## See Also

- [Example: Captcha Usage](../examples/captcha_usage.py)
- [GPM Browser Automation](QUICKSTART.md)
- [AchiCaptcha API Documentation](https://achicaptcha.com/docs)
- [Google reCAPTCHA Documentation](https://developers.google.com/recaptcha)


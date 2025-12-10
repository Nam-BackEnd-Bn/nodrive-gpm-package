# Complete Usage Guide

Comprehensive guide for using the No-Driver GPM Package.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Usage](#basic-usage)
3. [Configuration](#configuration)
4. [Proxy Configuration](#proxy-configuration)
5. [Profile Management](#profile-management)
6. [Multiple Browsers](#multiple-browsers)
7. [Advanced Usage](#advanced-usage)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Quick Start

### 1. Install Package

```bash
cd tool_package/nodrive_gpm_package
pip install -e .
```

### 2. Launch Your First Browser

```python
import asyncio
from nodrive_gpm_package import GPMClient

async def main():
    client = GPMClient()
    browser = await client.launch("my_profile")
    
    if browser:
        page = await browser.get("https://www.google.com")
        print(f"Page title: {page.title}")
        
        await asyncio.sleep(5)
        client.close("my_profile")

asyncio.run(main())
```

---

## Basic Usage

### Creating a Client

```python
from nodrive_gpm_package import GPMClient

# Default configuration
client = GPMClient()

# Custom configuration
from nodrive_gpm_package import GPMConfig

config = GPMConfig(
    browser_width=1920,
    browser_height=1080,
    debug=True
)
client = GPMClient(config=config)
```

### Launching a Browser

```python
# Simple launch
browser = await client.launch("profile_name")

# With position
browser = await client.launch("profile_name", position=0)

# With custom window size
browser = await client.launch(
    "profile_name",
    window_width=1920,
    window_height=1080,
    window_scale=1.0
)
```

### Using the Browser

```python
if browser:
    # Navigate to URL
    page = await browser.get("https://www.example.com")
    
    # Get page title
    print(page.title)
    
    # Get current URL
    print(page.url)
    
    # Find elements
    element = await page.find("input[name='q']")
    await element.send_keys("search query")
    
    # Wait
    await asyncio.sleep(5)
```

### Closing a Browser

```python
# Close specific profile
client.close("profile_name")

# Or close via browser
await browser.stop()
```

---

## Configuration

### Method 1: Environment Variables (.env file)

Create `.env` file:

```env
# API Configuration
GPM_API_BASE_URL=http://127.0.0.1:12003/api/v3
GPM_API_TIMEOUT=30

# Profile Directory
GPM_PROFILES_DIR=C:/Users/YourName/profiles

# Browser Settings
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
BROWSER_SCALE=0.8
MAX_BROWSERS_PER_LINE=4

# Retry Settings
MAX_RETRIES=5
RETRY_DELAY=10
CONNECTION_WAIT_TIME=3

# Debug
DEBUG=true
```

Use in code:

```python
from nodrive_gpm_package import GPMClient

# Automatically loads from .env
client = GPMClient()
```

### Method 2: Direct Configuration

```python
from nodrive_gpm_package import GPMConfig, GPMClient

config = GPMConfig(
    gpm_api_base_url="http://127.0.0.1:12003/api/v3",
    browser_width=1920,
    browser_height=1080,
    browser_scale=1.0,
    max_browsers_per_line=3,
    max_retries=5,
    retry_delay=10,
    debug=True
)

client = GPMClient(config=config)
```

### Method 3: Global Configuration

```python
from nodrive_gpm_package import GPMConfig, set_config, GPMClient

# Set global config
config = GPMConfig(browser_width=1920)
set_config(config)

# All clients use this config
client1 = GPMClient()
client2 = GPMClient()
```

---

## Proxy Configuration

### HTTP Proxy

```python
browser = await client.launch(
    "profile_name",
    proxy_type="http",
    proxy="123.45.67.89:8080:username:password"
)

# Without authentication
browser = await client.launch(
    "profile_name",
    proxy_type="http",
    proxy="123.45.67.89:8080"
)
```

### SOCKS5 Proxy

```python
browser = await client.launch(
    "profile_name",
    proxy_type="socks5",
    proxy="123.45.67.89:1080:username:password"
)
```

### Using ProxyConfig Schema

```python
from nodrive_gpm_package import ProxyConfig, ProxyType

# Create proxy config
proxy_config = ProxyConfig(
    proxy_type=ProxyType.SOCKS5,
    host="123.45.67.89",
    port=1080,
    username="user",
    password="pass"
)

# Convert to string
proxy_string = proxy_config.to_string()
# Output: "123.45.67.89:1080:user:pass"

# Use with client
browser = await client.launch(
    "profile_name",
    proxy_type="socks5",
    proxy=proxy_string
)
```

### Proxy from String

```python
from nodrive_gpm_package import ProxyConfig, ProxyType

# Parse proxy string
proxy = ProxyConfig.from_string(
    "123.45.67.89:1080:user:pass",
    proxy_type=ProxyType.SOCKS5
)

print(proxy.host)      # "123.45.67.89"
print(proxy.port)      # 1080
print(proxy.username)  # "user"
```

---

## Profile Management

### List All Profiles

```python
profiles = client.get_profiles()

for profile in profiles:
    print(f"Name: {profile.name}")
    print(f"ID: {profile.id}")
    print(f"Status: {profile.status}")
    print(f"Proxy: {profile.raw_proxy}")
    print("---")
```

### Check Profile Status

```python
from nodrive_gpm_package import ProfileStatus

status = client.get_status("my_profile")

if status == ProfileStatus.RUNNING:
    print("Profile is actively running")
elif status == ProfileStatus.STOPPED:
    print("Profile is stopped")
elif status == ProfileStatus.PENDING:
    print("Profile process exists but idle")
else:
    print("Status unknown")
```

### Close Profile

```python
success = client.close("my_profile")

if success:
    print("Profile closed successfully")
else:
    print("Failed to close profile")
```

### Delete Profile

```python
success = client.delete_profile("old_profile")

if success:
    print("Profile deleted")
```

---

## Multiple Browsers

### Launch Multiple Browsers Sequentially

```python
async def launch_multiple():
    client = GPMClient()
    
    browsers = []
    for i in range(4):
        browser = await client.launch(
            f"profile_{i}",
            position=i  # Auto-arranges in grid
        )
        browsers.append(browser)
    
    return browsers
```

### Launch Multiple Browsers in Parallel

```python
async def launch_parallel():
    client = GPMClient()
    
    # Create tasks
    tasks = [
        client.launch(f"profile_{i}", position=i)
        for i in range(4)
    ]
    
    # Launch all at once
    browsers = await asyncio.gather(*tasks)
    
    return browsers
```

### Use Different Proxies

```python
proxies = [
    ("socks5", "proxy1:1080:user:pass"),
    ("socks5", "proxy2:1080:user:pass"),
    ("http", "proxy3:8080:user:pass"),
]

browsers = []
for i, (proxy_type, proxy) in enumerate(proxies):
    browser = await client.launch(
        f"profile_{i}",
        proxy_type=proxy_type,
        proxy=proxy,
        position=i
    )
    browsers.append(browser)
```

### Manage Multiple Browsers

```python
class BrowserManager:
    def __init__(self):
        self.client = GPMClient()
        self.browsers = {}
    
    async def launch(self, profile_name, **kwargs):
        browser = await self.client.launch(profile_name, **kwargs)
        self.browsers[profile_name] = browser
        return browser
    
    def close(self, profile_name):
        if profile_name in self.browsers:
            self.client.close(profile_name)
            del self.browsers[profile_name]
    
    def close_all(self):
        for profile_name in list(self.browsers.keys()):
            self.close(profile_name)

# Usage
manager = BrowserManager()
await manager.launch("profile_1")
await manager.launch("profile_2")
manager.close_all()
```

---

## Advanced Usage

### Using Low-Level API Client

```python
from nodrive_gpm_package import GPMApiClient, ProfileCreateRequest

# Create API client
api = GPMApiClient()

# Create profile manually
request = ProfileCreateRequest(
    profile_name="custom_profile",
    is_masked_font=True,
    is_noise_canvas=True,
    raw_proxy="socks5://proxy:1080:user:pass"
)

profile = api.create_profile(request)
print(f"Created profile: {profile.id}")

# Start profile
response = api.start_profile(
    profile_id=profile.id,
    window_size="1920,1080",
    window_pos="0,0",
    window_scale=1.0
)

print(f"Debugging address: {response.remote_debugging_address}")
```

### Using Service Layer

```python
from nodrive_gpm_package import GPMService, ProxyType

service = GPMService()

browser = await service.launch_browser(
    profile_name="my_profile",
    proxy_type=ProxyType.SOCKS5,
    proxy_string="proxy:1080:user:pass",
    persistent_position=0,
    window_width=1920,
    window_height=1080
)
```

### Dependency Injection

```python
from nodrive_gpm_package import (
    GPMConfig,
    GPMApiClient,
    ProfileMonitor,
    GPMService
)

# Create dependencies
config = GPMConfig(debug=True)
api_client = GPMApiClient(config=config)
monitor = ProfileMonitor(config=config)

# Inject into service
service = GPMService(
    config=config,
    api_client=api_client,
    monitor=monitor
)

# Use service
browser = await service.launch_browser("my_profile")
```

### Custom Error Handling

```python
from nodrive_gpm_package import GPMClient, GPMApiException

client = GPMClient()

try:
    browser = await client.launch("my_profile")
except GPMApiException as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Context Manager

```python
from nodrive_gpm_package import GPMClient

with GPMClient() as client:
    browser = await client.launch("my_profile")
    # Use browser...
    client.close("my_profile")
# Resources automatically cleaned up
```

---

## Best Practices

### 1. Use Environment Variables

```python
# ✅ Good - configurable
client = GPMClient()

# ❌ Bad - hardcoded
config = GPMConfig(browser_width=1920)  # Use .env instead
```

### 2. Always Close Profiles

```python
# ✅ Good
try:
    browser = await client.launch("profile")
    # Use browser...
finally:
    client.close("profile")

# ❌ Bad - leaks resources
browser = await client.launch("profile")
# Never closed
```

### 3. Handle Errors

```python
# ✅ Good
try:
    browser = await client.launch("profile")
    if browser:
        # Use browser
    else:
        print("Failed to launch")
except Exception as e:
    print(f"Error: {e}")

# ❌ Bad - no error handling
browser = await client.launch("profile")
page = await browser.get("url")  # Might fail if browser is None
```

### 4. Use Type Hints

```python
# ✅ Good
from nodrive_gpm_package import GPMClient
import nodriver as nd

async def launch_browser(profile: str) -> nd.Browser | None:
    client = GPMClient()
    return await client.launch(profile)

# ❌ Bad - no types
async def launch_browser(profile):
    client = GPMClient()
    return await client.launch(profile)
```

### 5. Reuse Client Instance

```python
# ✅ Good - one client for all operations
client = GPMClient()
browser1 = await client.launch("profile1")
browser2 = await client.launch("profile2")

# ❌ Bad - creates new client each time
browser1 = await GPMClient().launch("profile1")
browser2 = await GPMClient().launch("profile2")
```

---

## Troubleshooting

### Browser Won't Launch

**Check:**
1. GPM is running: `http://127.0.0.1:12003`
2. Profile name is correct
3. No other instance is running

```python
# Check status first
status = client.get_status("profile")
print(f"Current status: {status}")

# Force close if needed
client.close("profile")
await asyncio.sleep(5)

# Try again
browser = await client.launch("profile")
```

### Proxy Not Working

```python
# Test proxy format
from nodrive_gpm_package import ProxyConfig, ProxyType

try:
    proxy = ProxyConfig.from_string(
        "123.45.67.89:1080:user:pass",
        ProxyType.SOCKS5
    )
    print(f"Proxy valid: {proxy.to_raw_proxy()}")
except Exception as e:
    print(f"Invalid proxy: {e}")
```

### Multiple Launches Fail

```python
# Add delays between launches
for i in range(4):
    browser = await client.launch(f"profile_{i}", position=i)
    await asyncio.sleep(2)  # Wait between launches
```

### Configuration Not Loading

```python
# Check config
from nodrive_gpm_package import get_config

config = get_config()
print(f"API URL: {config.gpm_api_base_url}")
print(f"Profiles dir: {config.profiles_directory}")
print(f"Browser size: {config.browser_width}x{config.browser_height}")
```

---

## API Reference

### GPMClient

```python
class GPMClient:
    def __init__(config: Optional[GPMConfig] = None)
    
    async def launch(
        profile_name: str,
        proxy_type: Optional[str] = None,
        proxy: Optional[str] = None,
        position: int = 0,
        **kwargs
    ) -> Optional[nd.Browser]
    
    def close(profile_name: str) -> bool
    def get_status(profile_name: str) -> ProfileStatus
    def get_profiles() -> List[ProfileResponse]
    def delete_profile(profile_name: str) -> bool
```

### GPMConfig

```python
class GPMConfig:
    gpm_api_base_url: str = "http://127.0.0.1:12003/api/v3"
    gpm_api_timeout: int = 30
    gpm_profiles_dir: Optional[str] = None
    browser_width: int = 1000
    browser_height: int = 700
    browser_scale: float = 0.8
    max_browsers_per_line: int = 4
    max_retries: int = 3
    retry_delay: int = 5
    connection_wait_time: int = 3
    cpu_threshold: float = 2.0
    cpu_check_interval: float = 1.5
    debug: bool = False
```

### ProxyType Enum

```python
class ProxyType(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"
    SOCKS4 = "socks4"
```

### ProfileStatus Enum

```python
class ProfileStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PENDING = "pending"
    UNKNOWN = "unknown"
```

---

## Additional Resources

- [README.md](../README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start
- [INSTALL.md](INSTALL.md) - Installation
- [MIGRATION.md](MIGRATION.md) - Migration guide
- [examples/](examples/) - Code examples

---

**Happy coding! 🚀**

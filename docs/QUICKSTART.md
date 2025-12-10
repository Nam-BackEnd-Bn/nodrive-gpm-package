# Quick Start Guide

Get started with No-Driver GPM Package in 5 minutes!

## Prerequisites

1. **Windows OS** (Required)
2. **Python 3.8+** (Required)
3. **GPM (Gologin Profile Manager)** running on `http://127.0.0.1:12003` (Required)

## Installation

### Option 1: From Source (Development)

```bash
cd tool_package/nodrive_gpm_package
pip install -e .
```

### Option 2: From PyPI (when published)

```bash
pip install nodrive-gpm-package
```

## 30-Second Example

Create a file `test.py`:

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

Run it:

```bash
python test.py
```

## Common Use Cases

### Use Case 1: Simple Browser Launch

```python
from nodrive_gpm_package import GPMClient

async def simple():
    client = GPMClient()
    browser = await client.launch("profile_name")
    # Use browser...
    client.close("profile_name")
```

### Use Case 2: With Proxy

```python
from nodrive_gpm_package import GPMClient

async def with_proxy():
    client = GPMClient()
    
    browser = await client.launch(
        profile_name="my_profile",
        proxy_type="socks5",
        proxy="123.45.67.89:1080:user:pass"
    )
    # Use browser...
```

### Use Case 3: Multiple Browsers

```python
from nodrive_gpm_package import GPMClient

async def multiple():
    client = GPMClient()
    
    # Launch 4 browsers in parallel
    browsers = await asyncio.gather(*[
        client.launch(f"profile_{i}", position=i)
        for i in range(4)
    ])
    
    # Use browsers...
```

### Use Case 4: Custom Configuration

```python
from nodrive_gpm_package import GPMClient, GPMConfig

async def custom():
    config = GPMConfig(
        browser_width=1920,
        browser_height=1080,
        max_retries=5
    )
    
    client = GPMClient(config=config)
    browser = await client.launch("my_profile")
```

## Configuration

### Method 1: Environment Variables (Recommended)

Create `.env` file:

```env
GPM_API_BASE_URL=http://127.0.0.1:12003/api/v3
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
MAX_RETRIES=5
DEBUG=true
```

### Method 2: Direct Configuration

```python
from nodrive_gpm_package import GPMConfig, set_config

config = GPMConfig(
    browser_width=1920,
    browser_height=1080
)

set_config(config)  # Set global config
```

## Troubleshooting

### Error: Cannot connect to GPM API

**Problem**: GPM is not running

**Solution**: 
1. Start GPM application
2. Verify it's running on `http://127.0.0.1:12003`
3. Check firewall settings

### Error: Profile already running

**Problem**: Profile is already open in another window

**Solution**: The package will automatically handle this - it will either connect to the existing instance or restart it.

### Error: ModuleNotFoundError

**Problem**: Package not installed

**Solution**:
```bash
pip install -e .
```

## Next Steps

1. **Read Full Documentation**: Check [README.md](../README.md)
2. **Explore Examples**: See [examples/](examples/) directory
3. **Learn DI Pattern**: Review [examples/advanced_di.py](../examples/advanced_di.py)
4. **Check API Reference**: See API documentation in README.md

## Getting Help

- 📖 Full docs: [README.md](../README.md)
- 💡 Examples: [examples/](examples/)
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

## Core Concepts

### 1. GPMClient
The main entry point - simple and easy to use.

### 2. Profile
A browser profile with saved cookies, cache, and settings.

### 3. Proxy
Optional proxy configuration (HTTP, SOCKS5) for the browser.

### 4. Configuration
Environment-based settings for customizing behavior.

### 5. Dependency Injection
Advanced pattern for maximum control and testability.

---

**That's it!** You're ready to start automating browsers with anti-detection. 🚀

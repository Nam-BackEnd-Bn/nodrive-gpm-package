# Examples

This directory contains examples demonstrating various features of the No-Driver GPM Package.

## Running Examples

Make sure you have:
1. GPM (Gologin Profile Manager) running locally on `http://127.0.0.1:12003`
2. The package installed: `pip install -e .`
3. Python 3.8+ with asyncio support

Then run any example:

```bash
python examples/basic_usage.py
```

## Available Examples

### 1. basic_usage.py
**Simple browser launching**

Learn how to:
- Create a GPM client
- Launch a browser with a profile
- Navigate to a webpage
- Close the profile

```bash
python examples/basic_usage.py
```

### 2. proxy_usage.py
**Using proxies (HTTP and SOCKS5)**

Learn how to:
- Configure HTTP proxy
- Configure SOCKS5 proxy
- Launch multiple browsers with different proxies
- Position browsers automatically

```bash
python examples/proxy_usage.py
```

### 3. custom_config.py
**Custom configuration**

Learn how to:
- Create custom GPMConfig
- Set browser dimensions and scale
- Configure retry behavior
- Enable debug mode

```bash
python examples/custom_config.py
```

### 4. multiple_browsers.py
**Launch multiple browsers in parallel**

Learn how to:
- Launch multiple browsers concurrently
- Use asyncio.gather() for parallel operations
- Auto-arrange browsers in grid layout
- Manage multiple profiles

```bash
python examples/multiple_browsers.py
```

### 5. profile_management.py
**Profile management operations**

Learn how to:
- List all profiles
- Check profile status
- Close profiles
- Delete profiles (optional)

```bash
python examples/profile_management.py
```

### 6. advanced_di.py
**Advanced dependency injection**

Learn how to:
- Create custom configuration
- Initialize components separately
- Inject dependencies manually
- Use low-level API directly
- Access profile monitor

```bash
python examples/advanced_di.py
```

## Environment Configuration

You can create a `.env` file in the root directory:

```env
# API Configuration
GPM_API_BASE_URL=http://127.0.0.1:12003/api/v3
GPM_API_TIMEOUT=30

# Profile Storage
GPM_PROFILES_DIR=C:/Users/YourUser/profiles

# Browser Settings
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
BROWSER_SCALE=0.8
MAX_BROWSERS_PER_LINE=4

# Retry Settings
MAX_RETRIES=3
RETRY_DELAY=5
CONNECTION_WAIT_TIME=3

# Debug
DEBUG=true
```

## Tips

1. **Start Simple**: Begin with `basic_usage.py` to understand the fundamentals
2. **Proxy Testing**: Use `proxy_usage.py` to verify your proxy configuration
3. **Scaling Up**: Use `multiple_browsers.py` to see how to handle multiple instances
4. **Custom Needs**: Check `advanced_di.py` for maximum control and customization

## Troubleshooting

### GPM not running
```
Error: Connection refused on http://127.0.0.1:12003
```
**Solution**: Make sure GPM is running on your system

### Profile already running
```
Profile already running, attempting to connect...
```
**Solution**: This is normal - the package will attempt to connect or restart

### Import errors
```
ModuleNotFoundError: No module named 'nodrive_gpm_package'
```
**Solution**: Install the package: `pip install -e .`

## Need Help?

- Check the main [README.md](../README.md) for full documentation
- Review the source code for detailed implementation
- Open an issue on GitHub for bugs or questions

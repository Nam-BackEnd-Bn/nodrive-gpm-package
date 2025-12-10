# No-Driver GPM Package

Professional browser profile management with anti-detection features using GPM (Gologin Profile Manager) and nodriver.

## Features

### Browser Profile Management
✨ **Easy to Use** - Simple, intuitive API with sensible defaults  
🔒 **Anti-Detection** - Built-in fingerprint masking and noise injection  
🌐 **Proxy Support** - HTTP, HTTPS, SOCKS4, SOCKS5 proxies  
⚙️ **Configuration** - Environment-based configuration with `.env` support  
🏗️ **Dependency Injection** - Clean architecture with DI pattern  
📦 **Type Safe** - Full Pydantic schema validation  
🔄 **Auto-Retry** - Automatic retry logic with exponential backoff  
📊 **Status Monitoring** - Real-time profile status detection

### Google Drive Integration
☁️ **File Upload** - Upload files with automatic folder creation  
📁 **Folder Management** - Create nested folder structures  
🤝 **Sharing** - Share files/folders with role-based permissions  
👑 **Ownership Transfer** - Transfer ownership to other accounts  
💾 **Storage Info** - Monitor storage quota and usage  
🌍 **Public Links** - Make files accessible to anyone with link

### Google Sheets Integration
📊 **Read/Write Operations** - Read and update sheet data efficiently  
🔄 **Service Account Rotation** - Automatic rotation across 10 service accounts  
⚡ **Rate Limiting** - Smart rate limit handling (300 read/100 write per minute)  
📦 **Batch Operations** - Redis-based queue for bulk updates  
🔒 **Sheet Locking** - Prevent concurrent modifications  
📈 **Export Functionality** - Append or overwrite data with ease  
🎯 **Smart Updates** - Multi-cell, row, column, and matrix updates  

## Installation

### From PyPI (when published)

```bash
pip install nodrive-gpm-package
```

### From Source

```bash
cd tool_package/nodrive_gpm_package
pip install -e .
```

### Requirements

- Python 3.8+
- Windows OS
- GPM (Gologin Profile Manager) running locally

## Quick Start

### Basic Usage

```python
import asyncio
from nodrive_gpm_package import GPMClient

async def main():
    # Create client
    client = GPMClient()
    
    # Launch browser with profile
    browser = await client.launch("my_profile")
    
    if browser:
        # Use the browser
        page = await browser.get("https://www.google.com")
        print(f"Page title: {page.title}")
        
        # Close when done
        client.close("my_profile")

asyncio.run(main())
```

### With Proxy

```python
import asyncio
from nodrive_gpm_package import GPMClient

async def main():
    client = GPMClient()
    
    # Launch with SOCKS5 proxy
    browser = await client.launch(
        profile_name="my_profile",
        proxy_type="socks5",
        proxy="123.45.67.89:1080:username:password"
    )
    
    if browser:
        page = await browser.get("https://ipinfo.io")
        # Your proxy IP should be shown

asyncio.run(main())
```

### With Custom Configuration

```python
from nodrive_gpm_package import GPMClient, GPMConfig

# Create custom config
config = GPMConfig(
    gpm_api_base_url="http://127.0.0.1:12003/api/v3",
    browser_width=1920,
    browser_height=1080,
    max_retries=5,
    debug=True
)

# Use custom config
client = GPMClient(config=config)
```

### Using Environment Variables

Set environment variables directly or use a `.env` file with `python-dotenv`:

**Option 1: Set environment variables**
```bash
# Windows
set GPM_API_BASE_URL=http://127.0.0.1:12003/api/v3
set BROWSER_WIDTH=1920

# Linux/Mac
export GPM_API_BASE_URL=http://127.0.0.1:12003/api/v3
export BROWSER_WIDTH=1920
```

**Option 2: Use .env file (requires python-dotenv)**
```bash
pip install python-dotenv
```

Create `.env` file:
```env
GPM_API_BASE_URL=http://127.0.0.1:12003/api/v3
GPM_PROFILES_DIR=C:/Users/YourUser/profiles
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
MAX_RETRIES=5
DEBUG=true
```

Load in code:
```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file

from nodrive_gpm_package import GPMClient
client = GPMClient()  # Uses environment variables
```

## Advanced Usage

### Dependency Injection

```python
from nodrive_gpm_package import (
    GPMConfig,
    GPMApiClient,
    ProfileMonitor,
    GPMService
)

# Create dependencies
config = GPMConfig()
api_client = GPMApiClient(config=config)
monitor = ProfileMonitor(config=config)

# Inject dependencies
service = GPMService(
    config=config,
    api_client=api_client,
    monitor=monitor
)

# Use service
browser = await service.launch_browser("my_profile")
```

### Profile Management

```python
from nodrive_gpm_package import GPMClient

client = GPMClient()

# Get all profiles
profiles = client.get_profiles()
for profile in profiles:
    print(f"Profile: {profile.name}, Status: {profile.status}")

# Check profile status
from nodrive_gpm_package import ProfileStatus

status = client.get_status("my_profile")

if status == ProfileStatus.RUNNING:
    print("Profile is running")
elif status == ProfileStatus.STOPPED:
    print("Profile is stopped")
elif status == ProfileStatus.PENDING:
    print("Profile is idle")

# Close profile
client.close("my_profile")

# Delete profile
client.delete_profile("old_profile")
```

### Multiple Browsers

```python
import asyncio
from nodrive_gpm_package import GPMClient

async def main():
    client = GPMClient()
    
    # Launch multiple browsers at different positions
    browsers = []
    
    for i in range(4):
        browser = await client.launch(
            profile_name=f"profile_{i}",
            position=i  # Auto-arranges in grid
        )
        browsers.append(browser)
    
    # Use browsers...
    
    # Close all
    for i in range(4):
        client.close(f"profile_{i}")

asyncio.run(main())
```

### Using Low-Level API

```python
from nodrive_gpm_package import (
    GPMApiClient,
    ProfileCreateRequest,
    ProxyType
)

client = GPMApiClient()

# Create profile with full control
request = ProfileCreateRequest(
    profile_name="custom_profile",
    is_masked_font=True,
    is_noise_canvas=True,
    is_noise_webgl=True,
    is_noise_client_rect=True,
    is_noise_audio_context=True,
    is_random_screen=True,
    raw_proxy="socks5://123.45.67.89:1080:user:pass"
)

profile = client.create_profile(request)
print(f"Created profile: {profile.id}")

# Start profile
response = client.start_profile(
    profile_id=profile.id,
    window_size="1920,1080",
    window_pos="0,0",
    window_scale=1.0
)

print(f"Debug address: {response.remote_debugging_address}")
```

## Google Drive Integration

The package includes a comprehensive Google Drive service for file management and cloud storage operations.

### Quick Start - Google Drive

```python
from nodrive_gpm_package import GoogleDriveService

# Initialize with service account credentials
service = GoogleDriveService(key_file='tokens/drive.json')

# Upload a file
result = service.upload_file(
    file_path_upload='document.pdf',
    folder_store='MyFolder/SubFolder',
    file_name='report.pdf'  # Optional
)

print(f"Uploaded: {result.name}")
print(f"View Link: {result.web_view_link}")

# Get storage info
storage = service.get_storage_info()
print(f"Storage: {storage.formatted_used} / {storage.formatted_total}")
```

### Upload and Share

```python
# Upload and automatically share with email
result = service.upload_file_and_share(
    file_path_upload='document.pdf',
    folder_store='SharedFolder',
    share_with_email='colleague@example.com',
    role='reader'  # Options: 'reader', 'writer', 'owner'
)
```

### Folder Operations

```python
# Get folder ID by path (creates if doesn't exist)
folder_id = service.get_folder_id_by_path('Projects/2024/Reports')

# List files in folder
files = service.list_files_in_folder(folder_id)
for file in files:
    print(f"{file.name} - {file.mime_type}")

# Share folder with permissions
service.share_folder_with_email(
    folder_id=folder_id,
    email_address='team@example.com',
    role='writer'
)
```

### Google Drive Documentation

- 📘 **[Complete Guide](docs/GOOGLE_DRIVE_SERVICE.md)** - Full API reference and examples
- 🚀 **[Quick Start](docs/GOOGLE_DRIVE_QUICKSTART.md)** - Get started in 5 minutes
- 💻 **[Usage Examples](examples/google_drive_usage.py)** - Comprehensive code examples

**Setup Requirements:**
1. Google Cloud Project with Drive API enabled
2. Service Account credentials (JSON key file)
3. Credentials saved as `tokens/drive.json`

See the [Quick Start Guide](docs/GOOGLE_DRIVE_QUICKSTART.md) for detailed setup instructions.

## Google Sheets Integration

The package includes a powerful Google Sheets service with enterprise-grade features like service account rotation, rate limiting, and batch operations.

### Quick Start - Google Sheets

```python
from nodrive_gpm_package import GoogleSheetService, SheetValUpdateCell, ExportType

# Initialize with service accounts directory
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    redis_host='localhost',  # For queue functionality
    enable_queue=True
)

# Read sheet values
values = service.get_values(
    sheet_url='https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit',
    sheet_name='Sheet1'
)

print(f"Read {len(values)} rows")
print(f"Headers: {values[0]}")

# Convert to dictionaries
data = service.convert_value_sheet(values, row_offset=0)
for row in data:
    print(row)  # {'Name': 'John', 'Email': 'john@example.com', ...}
```

### Update Cells

```python
# Update multiple cells at once
cells = [
    SheetValUpdateCell(idx_row=0, idx_col=0, content='Name 1'),
    SheetValUpdateCell(idx_row=0, idx_col=1, content='Value 1'),
    SheetValUpdateCell(idx_row=1, idx_col=0, content='Name 2'),
]

service.update_values_multi_cells(
    sheet_url='https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit',
    sheet_name='Sheet1',
    sheet_val=cells,
    immediate=True  # Or False to queue for batch processing
)
```

### Export Data

```python
# Prepare data
headers = ['ID', 'Name', 'Email', 'Status']
data = [
    ['1', 'John Doe', 'john@example.com', 'Active'],
    ['2', 'Jane Smith', 'jane@example.com', 'Active'],
]

# Export with Overwrite (clear and write from row 1)
service.export(
    sheet_url='https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit',
    sheet_name='Export_Sheet',
    list_cols=headers,
    vals_export=data,
    type_export=ExportType.OVERWRITE
)

# Or Append to existing data
service.export(
    sheet_url='https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit',
    sheet_name='Export_Sheet',
    list_cols=headers,
    vals_export=data,
    type_export=ExportType.APPEND
)
```

### Batch Operations with Queue

```python
# Enable queue for efficient batch processing
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    redis_host='localhost',
    enable_queue=True
)

# Add updates to queue (not executed immediately)
for i in range(100):
    service.update_values_multi_cells(
        sheet_url=sheet_url,
        sheet_name=sheet_name,
        sheet_val=[
            SheetValUpdateCell(idx_row=i, idx_col=0, content=f'Value {i}')
        ],
        immediate=False  # Queue for batch processing
    )

# Process all queued operations at once
service.process_queued_operations()
```

### Service Account Rotation

The service automatically rotates between multiple service accounts to handle Google's rate limits:

```python
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    service_account_files=[
        'automationservice-v1.json',
        'automationservice-v2.json',
        'automationservice-v3.json',
        # ... up to v10
    ],
    redis_host='localhost',
    enable_queue=True
)

# Perform many operations - automatic rotation handles rate limits
for i in range(1000):
    values = service.get_values(sheet_url, sheet_name)
    # Service automatically switches accounts to avoid rate limits
```

**Rate Limits per Service Account:**
- **Read**: 300 requests/minute
- **Write**: 100 requests/minute
- Accounts automatically blocked for 65 seconds when limit reached

### Google Sheets Documentation

- 📘 **[Quick Start Guide](docs/GOOGLE_SHEETS_QUICKSTART.md)** - Complete setup and usage guide
- 💻 **[Usage Examples](examples/google_sheets_usage.py)** - 15+ comprehensive examples
- 🔧 **Setup**: 3-10 service accounts with Sheets API enabled

**Key Features:**
- ✅ Service account rotation with automatic rate limiting
- ✅ Redis-based queue for batch operations
- ✅ Sheet locking to prevent concurrent modifications
- ✅ Timeout protection for heavy calculations
- ✅ Row offset support for flexible header positioning
- ✅ Export with Append/Overwrite modes
- ✅ Column name/index conversion utilities

**Setup Requirements:**
1. Google Cloud Project with Sheets API enabled
2. 3-10 Service Account credentials (JSON key files)
3. Service accounts saved in `tokens/service-account/` directory
4. Redis server (optional, for queue functionality)
5. Share target sheets with all service account emails

See the [Google Sheets Quick Start Guide](docs/GOOGLE_SHEETS_QUICKSTART.md) for detailed setup instructions.

## Configuration Options

All configuration can be set via environment variables (using `os.getenv`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GPM_API_BASE_URL` | `http://127.0.0.1:12003/api/v3` | GPM API base URL |
| `GPM_API_TIMEOUT` | `30` | API request timeout (seconds) |
| `GPM_PROFILES_DIR` | `%USERPROFILE%/profiles` | Profiles directory |
| `BROWSER_WIDTH` | `1000` | Browser window width |
| `BROWSER_HEIGHT` | `700` | Browser window height |
| `BROWSER_SCALE` | `0.8` | Browser window scale |
| `MAX_BROWSERS_PER_LINE` | `4` | Browsers per row in grid layout |
| `MAX_RETRIES` | `3` | Maximum retry attempts |
| `RETRY_DELAY` | `5` | Delay between retries (seconds) |
| `CONNECTION_WAIT_TIME` | `3` | Wait time after starting profile |
| `CPU_THRESHOLD` | `2.0` | CPU usage threshold for detection |
| `CPU_CHECK_INTERVAL` | `1.5` | CPU check interval (seconds) |
| `DEBUG` | `false` | Enable debug logging |

## API Reference

### GPMClient

Main client class for easy usage.

**Methods:**
- `launch(profile_name, proxy_type=None, proxy=None, position=0, **kwargs)` - Launch browser
- `close(profile_name)` - Close profile
- `get_status(profile_name)` - Get profile status
- `get_profiles()` - List all profiles
- `delete_profile(profile_name)` - Delete profile

### GPMService

Service layer with full control.

**Methods:**
- `launch_browser(...)` - Launch browser with full options
- `close_profile(profile_name)` - Close profile
- `get_profile_status(profile_name)` - Get status

### GPMApiClient

Low-level API client.

**Methods:**
- `create_profile(request)` - Create profile
- `get_profiles()` - List profiles
- `get_profile_by_name(name)` - Get profile
- `start_profile(profile_id, **params)` - Start profile
- `close_profile(profile_id)` - Close profile
- `delete_profile(profile_id)` - Delete profile

### Enums

- `ProxyType` - HTTP, HTTPS, SOCKS4, SOCKS5
- `ProfileStatus` - STOPPED, RUNNING, PENDING, UNKNOWN
- `BrowserStatus` - CONNECTED, DISCONNECTED, STARTING, CLOSING, ERROR

## Architecture

```
nodrive_gpm_package/
├── client.py              # High-level easy-to-use interface
├── config.py              # Configuration management
├── enums/                 # Enumerations
│   ├── proxy_type.py
│   ├── profile_status.py
│   └── browser_status.py
├── schemas/               # Pydantic schemas
│   ├── profile.py
│   ├── browser.py
│   └── proxy.py
├── api/                   # API clients
│   └── gpm_client.py
└── services/              # Business logic
    ├── gpm_service.py
    ├── profile_monitor.py
    ├── google_drive_service.py   # Google Drive integration
    └── google_sheet_service.py   # Google Sheets integration
```

## Error Handling

```python
from nodrive_gpm_package import GPMClient, GPMApiException

client = GPMClient()

try:
    browser = await client.launch("my_profile")
except GPMApiException as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/nodrive-gpm-package/issues
- Documentation: https://github.com/yourusername/nodrive-gpm-package

## Changelog

### Version 1.0.0
- Initial release
- Full GPM API integration
- Profile management with anti-detection
- Proxy support (HTTP, SOCKS5)
- Environment-based configuration
- Dependency injection architecture
- Type-safe Pydantic schemas
- **NEW:** Google Drive service integration
  - File upload with folder hierarchy
  - Sharing and permissions management
  - Ownership transfer
  - Storage quota monitoring
  - Public link generation
- **NEW:** Google Sheets service integration
  - Service account rotation (up to 10 accounts)
  - Automatic rate limiting (300 read/100 write per minute)
  - Redis-based queue for batch operations
  - Sheet locking mechanism
  - Read/write operations with row offset support
  - Export functionality (Append/Overwrite)
  - Timeout protection for heavy calculations
#   n o d r i v e - g p m - p a c k a g e 
 
 #   n o d r i v e - g p m - p a c k a g e 
 
 #   n o d r i v e - g p m - p a c k a g e 
 
 

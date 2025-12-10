# Google Sheets Service - Quick Start Guide

Complete guide to using the Google Sheets Service with service account rotation, rate limiting, and batch operations.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Setup](#setup)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The `GoogleSheetService` provides a robust Python interface for Google Sheets operations with enterprise-grade features:

- **Service Account Rotation**: Automatically rotate between multiple service accounts to handle rate limits
- **Rate Limiting**: Smart rate limit detection and automatic blocking (300 read/100 write per minute per account)
- **Queue System**: Redis-based queue for batch operations
- **Sheet Locking**: Prevent concurrent modifications
- **Row Offset Support**: Flexible header positioning

## Features

### Core Operations
- ✅ Read sheet values
- ✅ Update single/multiple cells
- ✅ Export data (Append/Overwrite modes)
- ✅ Delete rows
- ✅ Find rows by value
- ✅ Bulk matrix updates

### Advanced Features
- ✅ Service account rotation with automatic failover
- ✅ Redis-based queue for batch processing
- ✅ Sheet locking mechanism
- ✅ Timeout protection for heavy calculations
- ✅ Column name/index conversion utilities

## Installation

### 1. Install Python Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Install Redis (Optional - for queue functionality)

```bash
pip install redis
```

**Windows:**
- Download Redis for Windows from [https://github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases)
- Or use Docker: `docker run -d -p 6379:6379 redis`

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Mac
brew install redis
```

### 3. Install the Package

```bash
pip install -e .
```

## Setup

### 1. Service Account Setup

#### Create Service Accounts in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Sheets API**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

4. Create Service Accounts:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it (e.g., `automation-service-v1`)
   - Click "Create and Continue"
   - Click "Done"

5. Create Keys:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON"
   - Download the key file

6. Repeat steps 4-5 to create multiple service accounts (recommended: 3-10 accounts)

#### Organize Service Account Files

Create directory structure:

```
your_project/
├── tokens/
│   └── service-account/
│       ├── automationservice-v1.json
│       ├── automationservice-v2.json
│       ├── automationservice-v3.json
│       └── ... (up to v10)
```

### 2. Share Google Sheets with Service Accounts

For each Google Sheet you want to access:

1. Open the Google Sheet
2. Click "Share" button
3. Add each service account email (found in JSON files):
   - `automation-service-v1@your-project.iam.gserviceaccount.com`
   - Give "Editor" permission
4. Repeat for all service accounts

### 3. Redis Setup (Optional)

If using queue functionality:

```bash
# Start Redis server
redis-server

# Or with Docker
docker run -d -p 6379:6379 --name redis redis

# Test connection
redis-cli ping
# Should return: PONG
```

## Basic Usage

### 1. Initialize Service

```python
from nodrive_gpm_package.services import GoogleSheetService

# Basic initialization (no queue)
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    enable_queue=False
)

# With Redis queue enabled
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    redis_host='localhost',
    redis_port=6379,
    enable_queue=True
)
```

### 2. Read Sheet Data

```python
# Read all values
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

### 3. Update Cells

```python
from nodrive_gpm_package.services import SheetValUpdateCell

# Update single cell
service.update_values_multi_cells(
    sheet_url='https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit',
    sheet_name='Sheet1',
    sheet_val=[
        SheetValUpdateCell(idx_row=0, idx_col=0, content='Updated Value')
    ],
    immediate=True  # Execute immediately
)

# Update multiple cells
cells = [
    SheetValUpdateCell(idx_row=0, idx_col=0, content='Name 1'),
    SheetValUpdateCell(idx_row=0, idx_col=1, content='Value 1'),
    SheetValUpdateCell(idx_row=1, idx_col=0, content='Name 2'),
    SheetValUpdateCell(idx_row=1, idx_col=1, content='Value 2'),
]

service.update_values_multi_cells(
    sheet_url='https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit',
    sheet_name='Sheet1',
    sheet_val=cells,
    immediate=True
)
```

### 4. Export Data

```python
from nodrive_gpm_package.services import ExportType

# Prepare data
headers = ['ID', 'Name', 'Email', 'Status']
data = [
    ['1', 'John Doe', 'john@example.com', 'Active'],
    ['2', 'Jane Smith', 'jane@example.com', 'Active'],
    ['3', 'Bob Johnson', 'bob@example.com', 'Inactive'],
]

# Overwrite mode (clear and write from row 1)
service.export(
    sheet_url='https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit',
    sheet_name='Export_Sheet',
    list_cols=headers,
    vals_export=data,
    type_export=ExportType.OVERWRITE
)

# Append mode (add to existing data)
service.export(
    sheet_url='https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit',
    sheet_name='Export_Sheet',
    list_cols=headers,
    vals_export=data,
    type_export=ExportType.APPEND
)
```

## Advanced Features

### 1. Service Account Rotation

The service automatically rotates between service accounts based on usage:

```python
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    service_account_files=[
        'automationservice-v1.json',
        'automationservice-v2.json',
        'automationservice-v3.json',
    ],
    redis_host='localhost',
    enable_queue=True,
    debug=True  # See which account is being used
)

# Perform multiple operations - automatic rotation
for i in range(100):
    values = service.get_values(sheet_url=url, sheet_name=name)
    # Service automatically switches accounts to avoid rate limits
```

**Rate Limits:**
- **Read operations**: 300 requests/minute per service account
- **Write operations**: 100 requests/minute per service account
- Accounts automatically blocked for 65 seconds when limit reached
- Service switches to next available account

### 2. Queue-Based Batch Operations

Queue operations for batch processing (reduces API calls):

```python
# Enable queue
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    redis_host='localhost',
    enable_queue=True
)

# Add multiple updates to queue (not executed immediately)
for i in range(100):
    service.update_values_multi_cells(
        sheet_url=sheet_url,
        sheet_name=sheet_name,
        sheet_val=[
            SheetValUpdateCell(idx_row=i, idx_col=0, content=f'Value {i}')
        ],
        immediate=False  # Add to queue
    )

# Process all queued operations in batch
service.process_queued_operations()
```

**Benefits:**
- Reduces API calls by batching operations
- More efficient for bulk updates
- Automatic retry on failures
- Can be scheduled with cron jobs

### 3. Sheet Locking

Prevent concurrent modifications:

```python
# Lock sheet for 10 seconds during update
service.update_values_multi_cells(
    sheet_url=sheet_url,
    sheet_name=sheet_name,
    sheet_val=[...],
    immediate=True,
    time_lock_sheet=10  # Lock for 10 seconds
)

# Other operations on this sheet will be blocked during lock period
```

### 4. Row Offset Support

Handle sheets with custom header positions:

```python
# Standard: Header at row 1, data starts at row 2
service.update_values_multi_cells(
    sheet_url=sheet_url,
    sheet_name=sheet_name,
    sheet_val=[SheetValUpdateCell(idx_row=0, idx_col=0, content='Value')],
    row_offset=0  # Row 0 → writes to row 2
)

# Custom: Header at row 1, skip row 2, data starts at row 3
service.update_values_multi_cells(
    sheet_url=sheet_url,
    sheet_name=sheet_name,
    sheet_val=[SheetValUpdateCell(idx_row=0, idx_col=0, content='Value')],
    row_offset=1  # Row 0 → writes to row 3
)
```

### 5. Bulk Matrix Updates

Update large ranges efficiently:

```python
# Update a 10x5 matrix
matrix_data = [
    ['A1', 'B1', 'C1', 'D1', 'E1'],
    ['A2', 'B2', 'C2', 'D2', 'E2'],
    # ... 10 rows
]

service.update_values_multi_rows_multi_cols(
    sheet_url=sheet_url,
    sheet_name=sheet_name,
    values=matrix_data,
    start_row=0,      # Start at row 0 (data row, becomes row 2)
    start_col=0,      # Start at column A
    immediate=True
)
```

### 6. Timeout Protection

Automatically detect sheets with heavy calculations:

```python
# Enable timeout check
values = service.get_values(
    sheet_url=sheet_url,
    sheet_name=sheet_name,
    is_check_timeout=True  # Check if sheet is responsive
)

# If sheet takes >10 seconds to respond, it will be locked for 30 seconds
# and an exception will be raised
```

## API Reference

### GoogleSheetService

#### Constructor

```python
GoogleSheetService(
    service_accounts_dir: Optional[str] = None,
    service_account_files: Optional[List[str]] = None,
    redis_host: str = 'localhost',
    redis_port: int = 6379,
    redis_db: int = 0,
    redis_password: Optional[str] = None,
    enable_queue: bool = True,
    debug: bool = False
)
```

#### Key Methods

##### Read Operations

```python
get_sheet_info(sheet_url: str) -> SheetInfo
```
Get spreadsheet metadata and all sheet tabs.

```python
get_values(
    sheet_url: str,
    sheet_name: str,
    end_row: Optional[int] = None,
    is_check_timeout: bool = False
) -> List[List[str]]
```
Read all values from sheet.

```python
get_idx_row(
    sheet_url: str,
    sheet_name: str,
    col_name: str,
    val: str,
    is_check_timeout: bool = False
) -> int
```
Find row index by searching for value in column.

##### Write Operations

```python
update_values_multi_cells(
    sheet_url: str,
    sheet_name: str,
    sheet_val: List[SheetValUpdateCell],
    row_offset: int = 0,
    immediate: bool = False,
    time_lock_sheet: int = 0
) -> bool
```
Update multiple cells.

```python
update_values_multi_rows_multi_cols(
    sheet_url: str,
    sheet_name: str,
    values: List[List[str]],
    start_row: int = 0,
    end_row: Optional[int] = None,
    start_col: int = 0,
    row_offset: int = 0,
    immediate: bool = False,
    time_lock_sheet: int = 0
) -> bool
```
Update matrix of values.

```python
export(
    sheet_url: str,
    sheet_name: str,
    list_cols: List[str],
    vals_export: List[List[str]],
    type_export: ExportType,
    immediate: bool = True,
    time_lock_sheet: int = 0
) -> bool
```
Export data with Append or Overwrite mode.

```python
delete_row_sheet(
    sheet_url: str,
    sheet_name: str,
    sheet_row: Union[int, str],
    row_offset: int = 0
) -> bool
```
Delete a row from sheet.

##### Utility Methods

```python
convert_index_to_column_name(index_col: int) -> str
```
Convert column index (0-based) to name (A, B, ..., AA, AB, ...).

```python
convert_column_name_to_index(column_name: str) -> int
```
Convert column name to index (0-based).

```python
convert_value_sheet(
    vals: Optional[List[List[str]]],
    row_offset: int = 0
) -> Optional[List[Dict[str, Any]]]
```
Convert sheet values to list of dictionaries.

```python
process_queued_operations()
```
Process all queued operations (call periodically or via cron).

### Data Classes

#### SheetValUpdateCell

```python
@dataclass
class SheetValUpdateCell:
    idx_row: Union[int, str]    # Row index (0-based)
    idx_col: Union[int, str]    # Column index (0-based)
    content: str                # Cell content
    actual_col: Optional[str] = None
    actual_row: Optional[int] = None
```

#### SheetInfo

```python
@dataclass
class SheetInfo:
    spreadsheet_title: str
    sheets: List[SheetChildrenInfo]
```

#### SheetChildrenInfo

```python
@dataclass
class SheetChildrenInfo:
    title: str
    sheet_id: int
    row_count: int
    column_count: int
```

#### ExportType

```python
class ExportType(str, Enum):
    APPEND = "Append"      # Append to existing data
    OVERWRITE = "Overwrite"  # Clear and write from row 1
```

## Best Practices

### 1. Service Account Management

- **Use 3-10 service accounts** for production
- Name them consistently: `automationservice-v1.json`, `automationservice-v2.json`, etc.
- Share all sheets with all service accounts
- Monitor usage in Google Cloud Console

### 2. Rate Limiting

- Let the service handle rotation automatically
- Don't override rate limits manually
- Use queue for bulk operations
- Monitor Redis for blocked accounts

### 3. Queue Operations

```python
# Good: Use queue for bulk updates
for i in range(1000):
    service.update_values_multi_cells(..., immediate=False)
service.process_queued_operations()

# Bad: 1000 immediate API calls
for i in range(1000):
    service.update_values_multi_cells(..., immediate=True)
```

### 4. Error Handling

```python
from nodrive_gpm_package.services import GoogleSheetServiceException

try:
    values = service.get_values(sheet_url, sheet_name)
except GoogleSheetServiceException as e:
    logger.error(f"Sheet error: {e}")
    # Handle error appropriately
```

### 5. Sheet Locking

```python
# Use locks for critical operations
service.update_values_multi_cells(
    ...,
    time_lock_sheet=30  # Lock for 30 seconds
)
```

### 6. Scheduled Queue Processing

For production, process queues regularly:

```python
# Schedule with APScheduler, cron, or similar
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', seconds=30)
def process_sheets_queue():
    service.process_queued_operations()

scheduler.start()
```

## Troubleshooting

### Common Issues

#### 1. "Invalid Google Sheet URL"

**Problem**: Sheet ID not extracted from URL

**Solution**:
```python
# Correct URL format
url = 'https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit'

# Extract ID
sheet_id = service.get_sheet_id(url)
print(f"Sheet ID: {sheet_id}")
```

#### 2. "Permission denied" or "File not found"

**Problem**: Service accounts don't have access

**Solution**:
1. Open Google Sheet
2. Click "Share"
3. Add ALL service account emails
4. Give "Editor" permission

#### 3. "Redis connection failed"

**Problem**: Redis not running or wrong configuration

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server

# Or disable queue functionality
service = GoogleSheetService(..., enable_queue=False)
```

#### 4. "All service accounts blocked or at limit"

**Problem**: All accounts hit rate limits

**Solution**:
- Add more service accounts
- Use queue to batch operations
- Wait for cooldown (65 seconds)

#### 5. "Sheet is locked, please wait"

**Problem**: Sheet is being updated by another process

**Solution**:
- Wait for lock to expire
- Check Redis: `redis-cli keys "key_store_lock_sheet:*"`
- Manually clear lock if needed: `redis-cli del "key_store_lock_sheet:..."`

### Debug Mode

Enable debug logging to troubleshoot:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    debug=True
)

# Will log:
# - Service account selection
# - Rate limit tracking
# - Queue operations
# - API responses
```

### Performance Tips

1. **Batch operations**: Use queue for bulk updates
2. **Use matrix updates**: More efficient than cell-by-cell
3. **Limit read ranges**: Specify `end_row` when possible
4. **Monitor rate limits**: Check Redis usage keys
5. **Pre-warm service accounts**: Make test calls before production

## Examples

See complete examples in `examples/google_sheets_usage.py`:

- Basic read/write operations
- Export with Append/Overwrite
- Queue-based batch processing
- Service account rotation
- Sheet locking
- Column utilities
- Row finding and deletion

## Support

For issues and questions:
- Check this documentation
- Review examples in `examples/`
- Enable debug mode for detailed logs
- Check Redis for queue status

## License

Same as package license.


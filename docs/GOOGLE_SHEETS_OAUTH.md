# Google Sheets OAuth Helper

Simple OAuth2-based Google Sheets operations for personal and small-scale use.

## Overview

The `GoogleSheetOAuth` helper provides a simpler alternative to the service-account-based `GoogleSheetService`. It's perfect for:

- **Personal projects** - Working with your own Google Sheets
- **Small-scale applications** - No need for multiple service accounts
- **Quick prototyping** - Faster setup with OAuth2 credentials
- **Simple operations** - Read and write without complex configurations

For production applications with heavy usage, consider using `GoogleSheetService` which provides service account rotation, rate limiting, and Redis-based queuing.

## Setup

### 1. Enable Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Go to **APIs & Services > Credentials**

### 2. Create OAuth2 Credentials

1. Click **Create Credentials > OAuth client ID**
2. Choose **Desktop app** as application type
3. Give it a name (e.g., "Google Sheets OAuth")
4. Download the credentials JSON file

### 3. Setup Credentials

```bash
# Create directories
mkdir -p certs tokens

# Save downloaded credentials as oauth.json
mv ~/Downloads/client_secret_*.json certs/oauth.json
```

### 4. First Run Authentication

On first run, the helper will:
1. Open your default browser
2. Ask you to sign in with Google
3. Request permission to access Google Sheets
4. Cache credentials in `tokens/sheet.token`

Subsequent runs will use the cached credentials.

## Installation

The OAuth helper is included in the package. Make sure you have the required dependencies:

```bash
pip install nodrive-gpm-package
```

Or install just the Google Sheets dependencies:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Basic Usage

### Initialize Helper

```python
from nodrive_gpm_package import GoogleSheetOAuth

# Default paths: certs/oauth.json and tokens/sheet.token
helper = GoogleSheetOAuth()

# Or with custom paths
helper = GoogleSheetOAuth(
    credentials_file="path/to/oauth.json",
    token_file="path/to/token.pickle"
)
```

### Read Sheet Data

```python
# Read entire sheet
data = helper.read_sheet(
    sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit",
    sheet_name="Sheet1"
)

# Returns list of dictionaries
# Example: [
#   {'Name': 'John', 'Age': '25', 'City': 'NYC'},
#   {'Name': 'Jane', 'Age': '30', 'City': 'LA'}
# ]

for row in data:
    print(f"Name: {row['Name']}, Age: {row['Age']}")
```

### Write to Single Cell

```python
# Write to cell A2 (row 0 becomes row 2 in sheet)
result = helper.write_sheet(
    sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit",
    sheet_name="Sheet1",
    row=0,      # 0-based index (row 0 = sheet row 2)
    col="A",    # Column name
    value="Hello World"
)

print(f"Updated {result.get('updatedCells', 0)} cells")
```

### Write Multiple Values (Range)

```python
# Prepare data as 2D array
data = [
    ["Name", "Age", "City"],
    ["John", "25", "NYC"],
    ["Jane", "30", "LA"],
    ["Bob", "35", "SF"]
]

# Write range starting at A2
result = helper.write_range(
    sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit",
    sheet_name="Sheet1",
    start_row=0,    # 0-based (becomes row 2)
    start_col="A",
    values=data
)

print(f"Updated {result.get('updatedCells', 0)} cells")
```

## API Reference

### `GoogleSheetOAuth`

Main class for OAuth2-based Google Sheets operations.

#### Constructor

```python
GoogleSheetOAuth(
    credentials_file: Optional[str] = None,  # Path to oauth.json
    token_file: Optional[str] = None         # Path to token cache
)
```

**Parameters:**
- `credentials_file`: Path to OAuth2 credentials JSON file (default: `certs/oauth.json`)
- `token_file`: Path to token cache file (default: `tokens/sheet.token`)

#### Methods

##### `read_sheet(sheet_url, sheet_name)`

Read data from a Google Sheet.

**Parameters:**
- `sheet_url` (str): Google Sheets URL
- `sheet_name` (str): Name of the sheet tab

**Returns:**
- List[Dict[str, Any]]: List of dictionaries with column headers as keys
- Empty list if error or sheet is empty

**Example:**
```python
data = helper.read_sheet(
    sheet_url="https://docs.google.com/spreadsheets/d/ABC123/edit",
    sheet_name="Sheet1"
)
```

##### `write_sheet(sheet_url, sheet_name, row, col, value)`

Write value to a specific cell.

**Parameters:**
- `sheet_url` (str): Google Sheets URL
- `sheet_name` (str): Name of the sheet tab
- `row` (int): Row index (0-based, row 0 becomes sheet row 2)
- `col` (str): Column name (e.g., 'A', 'B', 'AA')
- `value` (str): Value to write

**Returns:**
- Dict[str, Any]: Update result information
- Empty dict if error

**Example:**
```python
result = helper.write_sheet(
    sheet_url="https://docs.google.com/spreadsheets/d/ABC123/edit",
    sheet_name="Sheet1",
    row=0,
    col="A",
    value="Updated"
)
```

##### `write_range(sheet_url, sheet_name, start_row, start_col, values)`

Write multiple values to a range.

**Parameters:**
- `sheet_url` (str): Google Sheets URL
- `sheet_name` (str): Name of the sheet tab
- `start_row` (int): Starting row index (0-based)
- `start_col` (str): Starting column name
- `values` (List[List[str]]): 2D array of values

**Returns:**
- Dict[str, Any]: Update result information
- Empty dict if error

**Example:**
```python
result = helper.write_range(
    sheet_url="https://docs.google.com/spreadsheets/d/ABC123/edit",
    sheet_name="Sheet1",
    start_row=0,
    start_col="A",
    values=[
        ["Name", "Age"],
        ["John", "25"]
    ]
)
```

##### `get_column_name(index_col)`

Convert column index to column name.

**Parameters:**
- `index_col` (int): Column index (0-based)

**Returns:**
- str: Column name (e.g., 'A', 'Z', 'AA')

**Example:**
```python
col_name = helper.get_column_name(0)   # 'A'
col_name = helper.get_column_name(25)  # 'Z'
col_name = helper.get_column_name(26)  # 'AA'
```

## Row Index Offset

**Important:** The helper uses a row offset of +2 for write operations:

- `row=0` writes to sheet row 2
- `row=1` writes to sheet row 3
- etc.

This is designed to preserve row 1 as a header row.

### Example

```python
# This writes to cell A2 (not A1)
helper.write_sheet(
    sheet_url=SHEET_URL,
    sheet_name="Sheet1",
    row=0,  # Becomes row 2
    col="A",
    value="Data"
)

# To write to actual row 1, you would need to modify the helper
# or use the Google Sheets API directly
```

## Column Name Conversions

The helper provides utilities for column name/index conversions:

```python
# Index to name
helper.get_column_name(0)    # 'A'
helper.get_column_name(25)   # 'Z'
helper.get_column_name(26)   # 'AA'
helper.get_column_name(701)  # 'ZZ'

# Name to index (internal method)
helper._column_name_to_index('A')   # 0
helper._column_name_to_index('Z')   # 25
helper._column_name_to_index('AA')  # 26
```

## Error Handling

The helper catches exceptions and returns empty results:

```python
# Invalid URL
data = helper.read_sheet(
    sheet_url="invalid-url",
    sheet_name="Sheet1"
)
# Returns: []
# Prints error message

# Non-existent sheet
data = helper.read_sheet(
    sheet_url=VALID_URL,
    sheet_name="NonExistentSheet"
)
# Returns: []
# Prints error message

# Service unavailable (503)
data = helper.read_sheet(
    sheet_url=VALID_URL,
    sheet_name="Sheet1"
)
# Returns: []
# Prints: "Google Sheets service temporarily unavailable"
```

For more robust error handling, wrap calls in try-except:

```python
from nodrive_gpm_package import GoogleSheetOAuth, GoogleSheetOAuthException

try:
    helper = GoogleSheetOAuth(
        credentials_file="missing.json"
    )
except GoogleSheetOAuthException as e:
    print(f"Failed to initialize: {e}")
```

## Backward Compatibility

For backward compatibility with existing code, `HelperGGSheet` is provided as an alias:

```python
from nodrive_gpm_package import HelperGGSheet

# This is the same as GoogleSheetOAuth
helper = HelperGGSheet()

data = helper.read_sheet(
    sheet_url=SHEET_URL,
    sheet_name="Sheet1"
)
```

## Comparison: OAuth vs Service Account

| Feature | GoogleSheetOAuth | GoogleSheetService |
|---------|------------------|-------------------|
| Setup Complexity | ✅ Simple (OAuth2) | ⚠️ Complex (Service Accounts) |
| Authentication | User OAuth | Service Account JSON |
| Rate Limiting | ❌ Manual | ✅ Automatic |
| Account Rotation | ❌ No | ✅ Up to 10 accounts |
| Queue System | ❌ No | ✅ Redis-based |
| Best For | Personal/Small | Production/Heavy |
| First Run | Browser consent | No interaction |
| Credentials Cache | Local pickle | N/A |

**Use OAuth helper when:**
- Working with your personal sheets
- Small-scale applications (<100 requests/min)
- Quick prototypes and scripts
- Simple read/write operations

**Use Service Account service when:**
- Production applications
- Heavy usage (>100 requests/min)
- Need rate limiting and rotation
- Batch operations with queuing
- No user interaction required

## Complete Example

```python
from nodrive_gpm_package import GoogleSheetOAuth

# Initialize
helper = GoogleSheetOAuth()

# Your sheet details
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
SHEET_NAME = "Sheet1"

# Read existing data
print("Reading data...")
data = helper.read_sheet(
    sheet_url=SHEET_URL,
    sheet_name=SHEET_NAME
)

print(f"Found {len(data)} rows")
for i, row in enumerate(data[:5], 1):
    print(f"Row {i}: {row}")

# Write new data
print("\nWriting data...")
new_data = [
    ["Product", "Price", "Stock"],
    ["Laptop", "999.99", "15"],
    ["Mouse", "29.99", "50"],
    ["Keyboard", "79.99", "30"]
]

result = helper.write_range(
    sheet_url=SHEET_URL,
    sheet_name=SHEET_NAME,
    start_row=0,
    start_col="A",
    values=new_data
)

print(f"Updated {result.get('updatedCells', 0)} cells")

# Update specific cell
print("\nUpdating cell...")
helper.write_sheet(
    sheet_url=SHEET_URL,
    sheet_name=SHEET_NAME,
    row=1,
    col="C",
    value="25"
)

print("Done!")
```

## Troubleshooting

### OAuth Consent Screen

**Issue:** Browser doesn't open for OAuth consent

**Solution:**
1. Check firewall/antivirus settings
2. Try manually navigating to the URL shown in console
3. Ensure port 0 (random port) is available

### Invalid Credentials

**Issue:** `GoogleSheetOAuthException: OAuth credentials file not found`

**Solution:**
1. Download OAuth2 credentials from Google Cloud Console
2. Save as `certs/oauth.json` or specify custom path
3. Ensure file is valid JSON format

### Token Expired

**Issue:** Token refresh fails

**Solution:**
1. Delete `tokens/sheet.token`
2. Run script again to re-authenticate
3. Grant all requested permissions

### Permission Denied

**Issue:** Error 403 or insufficient permissions

**Solution:**
1. Ensure Google Sheets API is enabled
2. Check OAuth scopes include spreadsheets access
3. Verify you own or have access to the sheet

### Service Unavailable (503)

**Issue:** "The service is currently unavailable"

**Solution:**
1. This is a temporary Google issue
2. Implement retry logic with exponential backoff
3. Wait a few minutes and try again

## Advanced Usage

### Custom Token Storage

```python
import pickle
from google.oauth2.credentials import Credentials

# Load credentials manually
with open('custom/path/token.pickle', 'rb') as f:
    creds = pickle.load(f)

# Use with helper (requires modification)
# Or build service directly
from googleapiclient.discovery import build
service = build('sheets', 'v4', credentials=creds)
```

### Bulk Operations

```python
# Read multiple sheets
sheets = ["Sheet1", "Sheet2", "Sheet3"]
all_data = {}

for sheet_name in sheets:
    data = helper.read_sheet(
        sheet_url=SHEET_URL,
        sheet_name=sheet_name
    )
    all_data[sheet_name] = data

# Write to multiple locations
updates = [
    ("Sheet1", 0, "A", "Value1"),
    ("Sheet1", 1, "A", "Value2"),
    ("Sheet2", 0, "B", "Value3"),
]

for sheet, row, col, value in updates:
    helper.write_sheet(
        sheet_url=SHEET_URL,
        sheet_name=sheet,
        row=row,
        col=col,
        value=value
    )
```

## See Also

- [Google Sheets Service Account Setup](GOOGLE_SHEETS_SETUP.md)
- [Google Sheets Service Usage](GOOGLE_SHEETS_USAGE.md)
- [Google Sheets API Reference](GOOGLE_SHEETS_QUICK_REFERENCE.md)
- [Example: OAuth Demo](../examples/google_sheets_oauth_demo.py)
- [Example: Service Account Usage](../examples/google_sheets_usage.py)


# Google Sheets Service - Quick Reference Card

One-page reference for common operations.

## Quick Start

```python
from nodrive_gpm_package.services import (
    GoogleSheetService, 
    SheetValUpdateCell,
    ExportType
)

# Initialize
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    redis_host='localhost',
    enable_queue=True  # False if no Redis
)
```

## Read Operations

```python
# Get sheet info
info = service.get_sheet_info(sheet_url)
print(f"Title: {info.spreadsheet_title}")
for sheet in info.sheets:
    print(f"- {sheet.title}: {sheet.row_count}x{sheet.column_count}")

# Read all values
values = service.get_values(sheet_url, 'Sheet1')

# Read with limit
values = service.get_values(sheet_url, 'Sheet1', end_row=100)

# Convert to dictionaries
data = service.convert_value_sheet(values, row_offset=0)

# Find row by value
row_idx = service.get_idx_row(
    sheet_url=sheet_url,
    sheet_name='Sheet1',
    col_name='A',
    val='John Doe'
)
```

## Write Operations

### Update Single Cell
```python
service.update_values_multi_cells(
    sheet_url=sheet_url,
    sheet_name='Sheet1',
    sheet_val=[
        SheetValUpdateCell(idx_row=0, idx_col=0, content='Value')
    ],
    immediate=True
)
```

### Update Multiple Cells
```python
cells = [
    SheetValUpdateCell(idx_row=0, idx_col=0, content='A1'),
    SheetValUpdateCell(idx_row=0, idx_col=1, content='B1'),
    SheetValUpdateCell(idx_row=1, idx_col=0, content='A2'),
]
service.update_values_multi_cells(
    sheet_url=sheet_url,
    sheet_name='Sheet1',
    sheet_val=cells,
    immediate=True
)
```

### Update Matrix
```python
matrix = [
    ['A1', 'B1', 'C1'],
    ['A2', 'B2', 'C2'],
    ['A3', 'B3', 'C3'],
]
service.update_values_multi_rows_multi_cols(
    sheet_url=sheet_url,
    sheet_name='Sheet1',
    values=matrix,
    start_row=0,
    start_col=0,
    immediate=True
)
```

### Delete Row
```python
service.delete_row_sheet(
    sheet_url=sheet_url,
    sheet_name='Sheet1',
    sheet_row=5  # Delete row 5
)
```

## Export Operations

### Overwrite Mode
```python
headers = ['ID', 'Name', 'Email']
data = [
    ['1', 'John', 'john@example.com'],
    ['2', 'Jane', 'jane@example.com'],
]

service.export(
    sheet_url=sheet_url,
    sheet_name='Export',
    list_cols=headers,
    vals_export=data,
    type_export=ExportType.OVERWRITE
)
```

### Append Mode
```python
service.export(
    sheet_url=sheet_url,
    sheet_name='Export',
    list_cols=headers,
    vals_export=data,
    type_export=ExportType.APPEND
)
```

## Queue Operations

### Add to Queue
```python
# Queue multiple updates
for i in range(100):
    service.update_values_multi_cells(
        sheet_url=sheet_url,
        sheet_name='Sheet1',
        sheet_val=[
            SheetValUpdateCell(idx_row=i, idx_col=0, content=f'Val {i}')
        ],
        immediate=False  # Queue it
    )
```

### Process Queue
```python
# Process all queued operations
service.process_queued_operations()
```

## Utilities

### Column Conversions
```python
# Index to name
col_name = service.convert_index_to_column_name(0)   # 'A'
col_name = service.convert_index_to_column_name(26)  # 'AA'

# Name to index
idx = service.convert_column_name_to_index('A')   # 0
idx = service.convert_column_name_to_index('AA')  # 26
```

### Row Offset
```python
# Standard: Header at row 1, data starts at row 2
service.update_values_multi_cells(..., row_offset=0)

# Custom: Header at row 1, skip row 2, data starts at row 3
service.update_values_multi_cells(..., row_offset=1)
```

### Sheet Locking
```python
# Lock sheet for 10 seconds
service.update_values_multi_cells(
    ...,
    time_lock_sheet=10
)
```

## Error Handling

```python
from nodrive_gpm_package.services import GoogleSheetServiceException

try:
    values = service.get_values(sheet_url, 'Sheet1')
except GoogleSheetServiceException as e:
    print(f"Error: {e}")
```

## Rate Limits

- **Read**: 300 requests/minute per service account
- **Write**: 100 requests/minute per service account
- Automatic rotation and blocking

## Common Patterns

### Read and Process
```python
values = service.get_values(sheet_url, 'Sheet1')
data = service.convert_value_sheet(values, row_offset=0)

for row in data:
    print(f"Name: {row['Name']}, Email: {row['Email']}")
```

### Bulk Update
```python
cells = []
for i, value in enumerate(my_data):
    cells.append(SheetValUpdateCell(
        idx_row=i,
        idx_col=0,
        content=value
    ))

service.update_values_multi_cells(
    sheet_url=sheet_url,
    sheet_name='Sheet1',
    sheet_val=cells,
    immediate=False  # Queue
)

service.process_queued_operations()
```

### Read, Modify, Write
```python
# Read
values = service.get_values(sheet_url, 'Sheet1')

# Modify
for row in values[1:]:  # Skip header
    row[2] = 'Updated'   # Update column C

# Write back
service.update_values_multi_rows_multi_cols(
    sheet_url=sheet_url,
    sheet_name='Sheet1',
    values=values[1:],
    start_row=0,
    start_col=0,
    immediate=True
)
```

## Configuration Options

```python
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    service_account_files=[...],  # Optional: custom files
    redis_host='localhost',
    redis_port=6379,
    redis_db=0,
    redis_password=None,
    enable_queue=True,
    debug=False
)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid Google Sheet URL" | Check URL format: `https://docs.google.com/spreadsheets/d/ID/edit` |
| "Permission denied" | Share sheet with all service account emails |
| "Redis connection failed" | Start Redis or set `enable_queue=False` |
| "All service accounts blocked" | Wait 65s or add more accounts |
| "Sheet is locked" | Wait for lock to expire |

## Quick Commands

```bash
# Install dependencies
pip install google-auth google-auth-oauthlib google-api-python-client redis

# Start Redis (Docker)
docker run -d -p 6379:6379 redis

# Test Redis
redis-cli ping

# Run demo
python examples/google_sheets_simple_demo.py
```

## Environment Setup

```bash
# Create directory
mkdir -p tokens/service-account

# Move service account files
mv automationservice-*.json tokens/service-account/

# Start Redis
redis-server
```

## Links

- 📖 [Quick Start Guide](GOOGLE_SHEETS_QUICKSTART.md)
- 🔧 [Setup Guide](GOOGLE_SHEETS_SETUP.md)
- 💻 [Examples](../examples/google_sheets_usage.py)

---

**Tip**: Use `debug=True` to see which service account is being used for each operation.


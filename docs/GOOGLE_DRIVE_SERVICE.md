# Google Drive Service Documentation

## Overview

The `GoogleDriveService` provides comprehensive Google Drive operations for Python applications, including file upload/download, folder management, sharing, ownership transfer, and storage quota information.

## Features

- ✅ **File Operations**
  - Upload files to Google Drive
  - Upload with automatic folder hierarchy creation
  - Delete files
  - Check file existence
  - Make files public

- ✅ **Folder Management**
  - Create nested folder structures
  - List files in folders
  - Get folder ID by path
  - Share folders with specific permissions

- ✅ **Sharing & Permissions**
  - Share files with specific emails
  - Share folders with role-based access
  - Transfer file ownership
  - Transfer folder ownership
  - Make files public (anyone with link)

- ✅ **Storage Information**
  - Get storage quota details
  - View used/total storage
  - Human-readable format

## Installation

### 1. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or if using the package's requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Service Account

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your project ID

#### Step 2: Enable Google Drive API

1. In the Cloud Console, go to **APIs & Services > Library**
2. Search for "Google Drive API"
3. Click **Enable**

#### Step 3: Create Service Account

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > Service Account**
3. Fill in service account details:
   - Name: `drive-service-account`
   - Description: "Service account for Drive operations"
4. Click **Create and Continue**
5. Grant role: **Basic > Editor** (or custom role with Drive permissions)
6. Click **Done**

#### Step 4: Create and Download Key

1. In **Credentials**, find your service account
2. Click on the service account email
3. Go to **Keys** tab
4. Click **Add Key > Create New Key**
5. Select **JSON** format
6. Click **Create**
7. Save the downloaded JSON file as `tokens/drive.json` in your project

#### Step 5: Share Drive Folders (Important!)

Since service accounts have their own Drive storage, you need to:

1. Create folders in your personal Google Drive
2. Right-click folder > **Share**
3. Add the service account email (looks like: `name@project-id.iam.gserviceaccount.com`)
4. Grant appropriate permissions (Editor or Owner)

Alternatively, use the service to manage files within the service account's own Drive space.

## Usage

### Basic Initialization

```python
from nodrive_gpm_package import GoogleDriveService

# Initialize with service account credentials
service = GoogleDriveService(key_file='tokens/drive.json')
```

### 1. Get Storage Information

```python
# Get storage quota details
storage = service.get_storage_info()

print(f"Total Storage: {storage.formatted_total}")
print(f"Used Storage: {storage.formatted_used} ({storage.percentage}%)")
print(f"Available: {service._format_bytes(storage.total - storage.used)}")
```

**Output:**
```
📊📊📊 Google Drive Storage Information:
💾 Total Storage: 15.0 GB
📈 Used Storage: 2.5 GB (16.67%)
📁 Used in Drive: 2.3 GB
🆓 Available: 12.5 GB
```

### 2. Upload Files

#### Simple Upload

```python
# Upload to root folder
result = service.upload_file(
    file_path_upload='/path/to/local/file.txt',
    folder_store='',  # Empty string for root
)

print(f"File ID: {result.id}")
print(f"View Link: {result.web_view_link}")
```

#### Upload to Folder

```python
# Upload to specific folder (creates if doesn't exist)
result = service.upload_file(
    file_path_upload='/path/to/local/document.pdf',
    folder_store='MyDocuments',
)
```

#### Upload to Nested Folders

```python
# Upload with nested folder hierarchy (all folders created automatically)
result = service.upload_file(
    file_path_upload='/path/to/local/report.xlsx',
    folder_store='Company/2024/Q1/Reports',
    file_name='q1_report.xlsx'  # Optional: rename file
)
```

**Output:**
```
🔍 Uploading file: /path/to/local/report.xlsx
🔍 File exists: True
✅ Found existing folder: Company (ID: abc123...)
📁 Created new folder: 2024 (ID: def456...)
📁 Created new folder: Q1 (ID: ghi789...)
📁 Created new folder: Reports (ID: jkl012...)
🎯 Folder hierarchy created: Company/2024/Q1/Reports
🚀 Starting upload: q1_report.xlsx to folder: Company/2024/Q1/Reports
🌍 File jkl012... is now public (anyone with link can view)
🚀🚀🚀 File uploaded successfully:
📁 File ID: xyz789...
📄 File Name: q1_report.xlsx
🔗 Web View Link: https://drive.google.com/file/d/xyz789.../view
💾 Web Content Link: https://drive.google.com/uc?id=xyz789...
🌍 Public: Always enabled
```

### 3. Upload and Share

```python
# Upload file and automatically share with specific email
result = service.upload_file_and_share(
    file_path_upload='/path/to/local/file.txt',
    folder_store='SharedFolder',
    share_with_email='colleague@example.com',
    role='reader'  # Options: 'reader', 'writer', 'owner'
)
```

**Roles:**
- `reader`: Can view and download
- `writer`: Can edit, view, and download
- `owner`: Full control (transfers ownership)

### 4. Folder Operations

#### Get Folder ID by Path

```python
# Get or create folder hierarchy and return final folder ID
folder_id = service.get_folder_id_by_path('Projects/2024/Reports')
print(f"Folder ID: {folder_id}")
```

#### List Files in Folder

```python
# List all files in a folder
files = service.list_files_in_folder(folder_id='root')

for file in files:
    print(f"Name: {file.name}")
    print(f"ID: {file.id}")
    print(f"Type: {file.mime_type}")
    print(f"Link: {file.web_view_link}")
    print("---")
```

#### Share Folder

```python
# Share folder with specific email and role
folder_id = service.get_folder_id_by_path('TeamFolder')
service.share_folder_with_email(
    folder_id=folder_id,
    email_address='team@example.com',
    role='writer'
)
```

### 5. File Management

#### Check File Existence

```python
# Check if file exists in folder
folder_id = service.get_folder_id_by_path('MyFolder')
file_id = service.file_exists_in_folder('document.pdf', folder_id)

if file_id:
    print(f"File exists with ID: {file_id}")
else:
    print("File not found")
```

#### Make File Public

```python
# Make file accessible to anyone with link
service.make_file_public(file_id='abc123...')
```

#### Delete File

```python
# Delete file (only owner can delete)
success = service.delete_file(file_id='abc123...')

if success:
    print("File deleted successfully")
```

**Note:** If ownership was transferred, only the new owner can delete the file.

### 6. Ownership Transfer

#### Transfer File Ownership

```python
# Transfer file ownership to another email
service.transfer_file_ownership(
    file_id='abc123...',
    new_owner_email='newowner@example.com',
    role='reader'  # Optional, defaults to 'reader'
)
```

**Important Notes:**
- Ownership transfer is **permanent**
- File now counts against new owner's storage quota
- Notification email is automatically sent (required by Google)
- Original owner loses ability to delete the file

#### Transfer Folder Ownership

```python
# Transfer entire folder ownership
folder_id = service.get_folder_id_by_path('ProjectFolder')
service.transfer_folder_ownership(
    folder_id=folder_id,
    new_owner_email='newowner@example.com'
)
```

### 7. Using Context Manager

```python
# Automatic cleanup with context manager
with GoogleDriveService(key_file='tokens/drive.json') as service:
    storage = service.get_storage_info()
    
    result = service.upload_file(
        file_path_upload='file.txt',
        folder_store='TempFolder'
    )
    
    print(f"File uploaded: {result.name}")
# Service automatically cleaned up
```

### 8. Batch Operations

```python
# Upload multiple files
files_to_upload = [
    {'path': 'file1.txt', 'folder': 'Batch/Set1'},
    {'path': 'file2.pdf', 'folder': 'Batch/Set1'},
    {'path': 'file3.docx', 'folder': 'Batch/Set2'},
]

service = GoogleDriveService(key_file='tokens/drive.json')
results = []

for file_info in files_to_upload:
    try:
        result = service.upload_file(
            file_path_upload=file_info['path'],
            folder_store=file_info['folder']
        )
        results.append(result)
        print(f"✅ Uploaded: {result.name}")
    except Exception as e:
        print(f"❌ Failed: {file_info['path']} - {e}")

print(f"Uploaded {len(results)}/{len(files_to_upload)} files")
```

## API Reference

### GoogleDriveService

#### Constructor

```python
GoogleDriveService(key_file: str)
```

**Parameters:**
- `key_file`: Path to service account JSON credentials

**Raises:**
- `GoogleDriveServiceException`: If credentials file not found

---

#### get_storage_info()

Get Google Drive storage quota information.

**Returns:** `StorageInfo`

**Raises:** `GoogleDriveServiceException`

---

#### upload_file()

Upload file to Google Drive.

```python
upload_file(
    file_path_upload: str,
    folder_store: str,
    file_name: Optional[str] = None
) -> UploadFileResult
```

**Parameters:**
- `file_path_upload`: Absolute path to local file
- `folder_store`: Destination folder path (e.g., "Folder/SubFolder")
- `file_name`: Custom file name (optional)

**Returns:** `UploadFileResult`

**Raises:** `GoogleDriveServiceException`

---

#### upload_file_and_share()

Upload file and automatically share with email.

```python
upload_file_and_share(
    file_path_upload: str,
    folder_store: str,
    file_name: Optional[str] = None,
    share_with_email: str = 'supercanh1@gmail.com',
    role: RoleShare = 'reader'
) -> UploadFileResult
```

**Parameters:**
- `file_path_upload`: Absolute path to local file
- `folder_store`: Destination folder path
- `file_name`: Custom file name (optional)
- `share_with_email`: Email to share with
- `role`: Permission role (`'reader'`, `'writer'`, or `'owner'`)

**Returns:** `UploadFileResult`

**Raises:** `GoogleDriveServiceException`

---

#### delete_file()

Delete file from Google Drive (owner only).

```python
delete_file(file_id: str) -> bool
```

**Parameters:**
- `file_id`: ID of file to delete

**Returns:** `True` if successful

**Raises:** `GoogleDriveServiceException`

---

#### list_files_in_folder()

List all files in a folder.

```python
list_files_in_folder(folder_id: str = 'root') -> List[FileInfo]
```

**Parameters:**
- `folder_id`: Folder ID (default: 'root')

**Returns:** `List[FileInfo]`

**Raises:** `GoogleDriveServiceException`

---

#### make_file_public()

Make file accessible to anyone with link.

```python
make_file_public(file_id: str) -> bool
```

**Parameters:**
- `file_id`: File ID

**Returns:** `True` if successful

**Raises:** `GoogleDriveServiceException`

---

#### transfer_file_ownership()

Transfer file ownership to another email.

```python
transfer_file_ownership(
    file_id: str,
    new_owner_email: str,
    role: RoleShare = 'reader'
) -> bool
```

**Parameters:**
- `file_id`: File ID
- `new_owner_email`: Email of new owner
- `role`: Permission role

**Returns:** `True` if successful

**Raises:** `GoogleDriveServiceException`

---

#### transfer_folder_ownership()

Transfer folder ownership to another email.

```python
transfer_folder_ownership(
    folder_id: str,
    new_owner_email: str
) -> bool
```

**Parameters:**
- `folder_id`: Folder ID
- `new_owner_email`: Email of new owner

**Returns:** `True` if successful

**Raises:** `GoogleDriveServiceException`

---

#### share_folder_with_email()

Share folder with specific email and permissions.

```python
share_folder_with_email(
    folder_id: str,
    email_address: str,
    role: RoleShare = 'writer'
) -> bool
```

**Parameters:**
- `folder_id`: Folder ID
- `email_address`: Email to share with
- `role`: Permission role

**Returns:** `True` if successful

**Raises:** `GoogleDriveServiceException`

---

#### get_folder_id_by_path()

Get folder ID by path (creates if doesn't exist).

```python
get_folder_id_by_path(folder_path: str) -> str
```

**Parameters:**
- `folder_path`: Folder path (e.g., "folder1/folder2")

**Returns:** Folder ID

**Raises:** `GoogleDriveServiceException`

---

#### file_exists_in_folder()

Check if file exists in specific folder.

```python
file_exists_in_folder(
    file_name: str,
    folder_id: str = 'root'
) -> Optional[str]
```

**Parameters:**
- `file_name`: File name to check
- `folder_id`: Folder ID (default: 'root')

**Returns:** File ID if exists, `None` otherwise

**Raises:** `GoogleDriveServiceException`

---

## Data Classes

### UploadFileResult

```python
@dataclass
class UploadFileResult:
    id: str
    name: str
    web_view_link: Optional[str] = None
    web_content_link: Optional[str] = None
```

### FileInfo

```python
@dataclass
class FileInfo:
    id: str
    name: str
    mime_type: str
    web_view_link: Optional[str] = None
    parents: Optional[List[str]] = None
```

### StorageInfo

```python
@dataclass
class StorageInfo:
    used: int
    total: int
    used_in_drive: int
    percentage: float
    formatted_used: str
    formatted_total: str
    formatted_used_in_drive: str
```

## Error Handling

All methods raise `GoogleDriveServiceException` for errors:

```python
from nodrive_gpm_package import GoogleDriveServiceException

try:
    service = GoogleDriveService(key_file='tokens/drive.json')
    result = service.upload_file(
        file_path_upload='file.txt',
        folder_store='MyFolder'
    )
except GoogleDriveServiceException as e:
    print(f"Error: {e}")
except FileNotFoundError:
    print("Credentials file not found")
```

## Best Practices

### 1. Credential Security

- ❌ Never commit `drive.json` to version control
- ✅ Add `tokens/` to `.gitignore`
- ✅ Store credentials securely
- ✅ Use environment variables for sensitive paths

### 2. Error Handling

```python
try:
    service = GoogleDriveService(key_file='tokens/drive.json')
    # ... operations ...
except GoogleDriveServiceException as e:
    logging.error(f"Drive operation failed: {e}")
    # Handle error appropriately
```

### 3. Resource Management

```python
# Use context manager for automatic cleanup
with GoogleDriveService(key_file='tokens/drive.json') as service:
    # ... operations ...
# Automatic cleanup
```

### 4. Batch Operations

For multiple uploads, reuse the service instance:

```python
service = GoogleDriveService(key_file='tokens/drive.json')

for file_path in file_paths:
    try:
        result = service.upload_file(file_path, 'MyFolder')
    except GoogleDriveServiceException as e:
        logging.error(f"Failed to upload {file_path}: {e}")
```

### 5. Ownership Transfer

Be aware of implications:

```python
# Transfer ownership - THIS IS PERMANENT
service.transfer_file_ownership(
    file_id=file_id,
    new_owner_email='newowner@example.com'
)
# You can no longer delete this file!
```

## Common Issues

### Issue: "File not found" Error

**Problem:** File path is incorrect

**Solution:**
```python
from pathlib import Path

# Use absolute paths
file_path = Path('file.txt').resolve()
print(f"Uploading: {file_path}")
print(f"Exists: {file_path.exists()}")

service.upload_file(str(file_path), 'MyFolder')
```

### Issue: "Permission denied" Error

**Problem:** Service account doesn't have access

**Solution:**
1. Share the folder with service account email
2. Or use service account's own Drive space

### Issue: Can't Delete File After Upload

**Problem:** Ownership was transferred

**Solution:**
- Only the current owner can delete
- Check ownership before attempting deletion

### Issue: "Invalid credentials" Error

**Problem:** Service account key is invalid

**Solution:**
1. Verify `drive.json` is correct
2. Ensure Google Drive API is enabled
3. Check service account has proper permissions

## Examples

See `examples/google_drive_usage.py` for comprehensive examples:

```bash
python examples/google_drive_usage.py
```

## Support

For issues or questions:

1. Check this documentation
2. Review examples in `examples/google_drive_usage.py`
3. Check [Google Drive API documentation](https://developers.google.com/drive/api/v3/about-sdk)

## License

This service is part of the nodrive_gpm_package. See LICENSE for details.


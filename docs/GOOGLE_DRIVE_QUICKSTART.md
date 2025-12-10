# Google Drive Service - Quick Start Guide

Get started with Google Drive integration in 5 minutes!

## Prerequisites

- Python 3.7+
- Google Account
- nodrive_gpm_package installed

## Quick Setup (5 Steps)

### Step 1: Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or install all package requirements:

```bash
pip install -r requirements.txt
```

### Step 2: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Create Project**
3. Enter project name (e.g., "my-drive-app")
4. Click **Create**

### Step 3: Enable Google Drive API

1. In your project, go to **APIs & Services > Library**
2. Search for "Google Drive API"
3. Click on it and press **Enable**

### Step 4: Create Service Account Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > Service Account**
3. Enter details:
   - **Name**: `drive-service`
   - **Description**: "Service account for Drive operations"
4. Click **Create and Continue**
5. Grant role: **Editor** or **Owner**
6. Click **Done**
7. Click on the created service account
8. Go to **Keys** tab
9. Click **Add Key > Create New Key**
10. Select **JSON**
11. Click **Create** (file downloads automatically)

### Step 5: Setup Credentials in Project

1. Create a `tokens` directory in your project:
   ```bash
   mkdir tokens
   ```

2. Move the downloaded JSON file to `tokens/drive.json`

3. Add to `.gitignore`:
   ```
   tokens/
   *.json
   ```

## Your First Upload

Create a file `test_drive.py`:

```python
from nodrive_gpm_package import GoogleDriveService

# Initialize service
service = GoogleDriveService(key_file='tokens/drive.json')

# Get storage info
storage = service.get_storage_info()
print(f"Storage: {storage.formatted_used} / {storage.formatted_total}")

# Upload a test file
result = service.upload_file(
    file_path_upload='test.txt',  # Your file
    folder_store='TestFolder',     # Folder in Drive
)

print(f"✅ Uploaded: {result.name}")
print(f"🔗 View: {result.web_view_link}")
```

Run it:

```bash
python test_drive.py
```

## Common First-Time Issues

### ❌ "File not found: tokens/drive.json"

**Solution:** Make sure you:
1. Downloaded the JSON key file
2. Renamed it to `drive.json`
3. Placed it in the `tokens/` directory

---

### ❌ "File does not exist: test.txt"

**Solution:** Create a test file first:

```python
# Create test file
with open('test.txt', 'w') as f:
    f.write('Hello, Google Drive!')

# Then upload it
service.upload_file('test.txt', 'TestFolder')
```

---

### ❌ "Failed to initialize Google Drive client"

**Solution:** 
1. Verify Google Drive API is enabled
2. Check the JSON file is valid (should start with `{"type": "service_account"`)
3. Ensure service account has proper roles

---

## Next Steps

### Upload to Nested Folders

```python
# Creates: MyDocs → 2024 → Reports
result = service.upload_file(
    file_path_upload='report.pdf',
    folder_store='MyDocs/2024/Reports',
)
```

### Share with Email

```python
# Upload and share in one step
result = service.upload_file_and_share(
    file_path_upload='document.pdf',
    folder_store='SharedFolder',
    share_with_email='friend@example.com',
    role='reader',  # Can view only
)
```

### List Files

```python
# List files in folder
folder_id = service.get_folder_id_by_path('MyFolder')
files = service.list_files_in_folder(folder_id)

for file in files:
    print(f"{file.name} - {file.mime_type}")
```

## Full Documentation

For complete API reference and advanced features:

📚 See [GOOGLE_DRIVE_SERVICE.md](./GOOGLE_DRIVE_SERVICE.md)

## Examples

Check out comprehensive examples:

```bash
python examples/google_drive_usage.py
```

## Need Help?

1. **Service account email**: Find it in Google Cloud Console under **IAM & Admin > Service Accounts**
   - Looks like: `name@project-id.iam.gserviceaccount.com`

2. **Share folders**: To access personal Drive folders, share them with the service account email

3. **Permissions**: Grant "Editor" or "Owner" role to the service account

## Tips

✅ **DO:**
- Keep credentials secure (never commit to Git)
- Use absolute paths for files
- Handle exceptions properly
- Reuse service instance for multiple operations

❌ **DON'T:**
- Commit `drive.json` to version control
- Use relative paths without validation
- Transfer ownership without understanding implications
- Share credentials publicly

## Quick Reference

```python
from nodrive_gpm_package import GoogleDriveService

# Initialize
service = GoogleDriveService(key_file='tokens/drive.json')

# Upload file
result = service.upload_file('file.txt', 'Folder')

# Share folder
folder_id = service.get_folder_id_by_path('Folder')
service.share_folder_with_email(folder_id, 'user@example.com', 'reader')

# Get storage
storage = service.get_storage_info()

# List files
files = service.list_files_in_folder('root')

# Delete file
service.delete_file(file_id)
```

---

**Happy uploading! 🚀**


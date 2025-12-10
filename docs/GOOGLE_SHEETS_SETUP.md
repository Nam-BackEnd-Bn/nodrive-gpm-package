# Google Sheets Service - Setup Guide

Step-by-step guide to set up the Google Sheets service with service accounts and Redis.

## Prerequisites

- Python 3.8+
- Google Cloud Console account
- Redis server (optional, for queue functionality)

## Part 1: Google Cloud Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "my-automation-project")
4. Click "Create"

### Step 2: Enable Google Sheets API

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it
4. Click **"Enable"**

### Step 3: Create Service Accounts

You'll need multiple service accounts for rate limit handling. We recommend **3-10 accounts**.

#### Create First Service Account:

1. Go to **"IAM & Admin"** → **"Service Accounts"**
2. Click **"Create Service Account"**
3. Enter details:
   - **Name**: `automation-service-v1`
   - **Description**: `Service account for automation v1`
4. Click **"Create and Continue"**
5. Skip role assignment (click "Continue")
6. Click **"Done"**

#### Create Key for Service Account:

1. Click on the newly created service account
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **"JSON"** format
5. Click **"Create"**
6. The key file will download automatically
7. **Rename the file** to `automationservice-v1.json`

#### Repeat for Multiple Accounts:

Repeat steps above to create more service accounts:
- `automation-service-v2` → `automationservice-v2.json`
- `automation-service-v3` → `automationservice-v3.json`
- ... up to v10

**Important Notes:**
- Each service account has independent rate limits
- More accounts = higher throughput
- Minimum recommended: 3 accounts
- Maximum supported: 10 accounts

### Step 4: Organize Service Account Files

Create directory structure in your project:

```
your_project/
├── tokens/
│   └── service-account/
│       ├── automationservice-v1.json
│       ├── automationservice-v2.json
│       ├── automationservice-v3.json
│       ├── automationservice-v4.json
│       ├── automationservice-v5.json
│       └── ... (up to v10)
```

**On Windows:**
```cmd
mkdir tokens\service-account
move automationservice-*.json tokens\service-account\
```

**On Linux/Mac:**
```bash
mkdir -p tokens/service-account
mv automationservice-*.json tokens/service-account/
```

### Step 5: Share Google Sheets with Service Accounts

For **each Google Sheet** you want to access:

1. Open the Google Sheet
2. Click **"Share"** button (top right)
3. Add each service account email:
   - Find email in JSON file: `"client_email": "automation-service-v1@your-project.iam.gserviceaccount.com"`
   - Or find in Google Cloud Console → Service Accounts
4. Set permission to **"Editor"**
5. **Uncheck** "Notify people" (service accounts don't need notifications)
6. Click **"Share"**
7. Repeat for ALL service accounts (v1, v2, v3, etc.)

**Quick tip:** You can add multiple emails at once, separated by commas.

## Part 2: Redis Setup (Optional but Recommended)

Redis is used for:
- Rate limit tracking
- Service account rotation
- Queue-based batch operations
- Sheet locking

### Option A: Install Redis on Windows

1. Download Redis for Windows:
   - [Official Redis releases](https://github.com/microsoftarchive/redis/releases)
   - Download `Redis-x64-*.zip`

2. Extract and install:
   ```cmd
   cd C:\Redis
   redis-server.exe
   ```

3. Test connection:
   ```cmd
   redis-cli.exe
   > ping
   PONG
   > exit
   ```

### Option B: Use Docker (Recommended)

```bash
# Run Redis in Docker
docker run -d -p 6379:6379 --name redis redis

# Test connection
docker exec -it redis redis-cli ping
# Should return: PONG
```

### Option C: Install on Linux

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**CentOS/RHEL:**
```bash
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis
```

### Option D: Install on macOS

```bash
brew install redis
brew services start redis
```

### Test Redis Connection

```python
import redis

try:
    client = redis.Redis(host='localhost', port=6379)
    client.ping()
    print("✅ Redis connected successfully")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
```

## Part 3: Python Dependencies

### Install Required Packages

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Install Redis (for queue functionality)

```bash
pip install redis
```

### Install the Package

```bash
# From source
cd nodrive_gpm_package
pip install -e .

# Or from PyPI (when published)
pip install nodrive-gpm-package
```

### Verify Installation

```python
from nodrive_gpm_package.services import GoogleSheetService

print("✅ Google Sheets service imported successfully")
```

## Part 4: Configuration

### Basic Configuration (No Queue)

```python
from nodrive_gpm_package.services import GoogleSheetService

service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    enable_queue=False  # Disable queue if Redis not available
)
```

### Full Configuration (With Queue)

```python
from nodrive_gpm_package.services import GoogleSheetService

service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    redis_host='localhost',
    redis_port=6379,
    redis_db=0,
    redis_password=None,  # Set if Redis has password
    enable_queue=True,
    debug=False  # Set True for detailed logs
)
```

### Custom Service Account Files

```python
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    service_account_files=[
        'my-service-account-1.json',
        'my-service-account-2.json',
        'my-service-account-3.json',
    ],
    enable_queue=True
)
```

## Part 5: Verification

### Test Script

Create `test_sheets_setup.py`:

```python
from nodrive_gpm_package.services import GoogleSheetService, GoogleSheetServiceException

# Configuration
SHEET_URL = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
SHEET_NAME = 'Sheet1'

# Initialize service
service = GoogleSheetService(
    service_accounts_dir='./tokens/service-account',
    enable_queue=False,
    debug=True
)

# Test 1: Get sheet info
print("Test 1: Get sheet info...")
try:
    info = service.get_sheet_info(SHEET_URL)
    print(f"✅ Found spreadsheet: {info.spreadsheet_title}")
    print(f"   Sheets: {[s.title for s in info.sheets]}")
except GoogleSheetServiceException as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 2: Read values
print("\nTest 2: Read values...")
try:
    values = service.get_values(SHEET_URL, SHEET_NAME)
    print(f"✅ Read {len(values)} rows")
    if values:
        print(f"   Headers: {values[0]}")
except GoogleSheetServiceException as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 3: Service account rotation
print("\nTest 3: Service account rotation...")
try:
    for i in range(5):
        values = service.get_values(SHEET_URL, SHEET_NAME)
        print(f"   Read #{i+1}: {len(values)} rows")
    print("✅ Service account rotation working")
except GoogleSheetServiceException as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n✅ All tests passed! Setup is complete.")
```

Run the test:
```bash
python test_sheets_setup.py
```

## Part 6: Troubleshooting

### Issue 1: "No valid service account files found"

**Cause:** Service account files not in correct location

**Solution:**
```bash
# Verify files exist
ls tokens/service-account/

# Should show:
# automationservice-v1.json
# automationservice-v2.json
# ...
```

### Issue 2: "Permission denied" or "File not found"

**Cause:** Sheet not shared with service accounts

**Solution:**
1. Open Google Sheet
2. Check sharing settings
3. Verify ALL service account emails are added with Editor permission
4. Service account email format: `service-name@project-id.iam.gserviceaccount.com`

### Issue 3: "Redis connection failed"

**Cause:** Redis not running

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not, start Redis
redis-server

# Or disable queue functionality
service = GoogleSheetService(..., enable_queue=False)
```

### Issue 4: "All service accounts blocked"

**Cause:** Rate limits exceeded on all accounts

**Solution:**
- Add more service accounts
- Use queue for batch operations
- Wait 65 seconds for cooldown

### Issue 5: "Invalid Google Sheet URL"

**Cause:** Incorrect URL format

**Solution:**
```python
# Correct format
url = 'https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit'

# Extract ID to verify
sheet_id = service.get_sheet_id(url)
print(f"Sheet ID: {sheet_id}")  # Should show ID, not None
```

## Part 7: Best Practices

### 1. Service Account Management

✅ **Do:**
- Use 3-10 service accounts for production
- Name consistently: `automationservice-v1.json`, v2, v3, etc.
- Keep credentials secure (add `tokens/` to `.gitignore`)
- Rotate service accounts regularly

❌ **Don't:**
- Use only 1 service account (rate limits)
- Commit service account files to Git
- Share credentials publicly

### 2. Rate Limiting

✅ **Do:**
- Let the service handle rotation automatically
- Use queue for bulk operations
- Monitor Redis for blocked accounts

❌ **Don't:**
- Override rate limits manually
- Make too many immediate calls
- Ignore rate limit warnings

### 3. Queue Usage

✅ **Do:**
```python
# Good: Queue bulk updates
for i in range(1000):
    service.update_values_multi_cells(..., immediate=False)
service.process_queued_operations()
```

❌ **Don't:**
```python
# Bad: 1000 immediate API calls
for i in range(1000):
    service.update_values_multi_cells(..., immediate=True)
```

### 4. Error Handling

✅ **Do:**
```python
from nodrive_gpm_package.services import GoogleSheetServiceException

try:
    values = service.get_values(sheet_url, sheet_name)
except GoogleSheetServiceException as e:
    logger.error(f"Sheet error: {e}")
    # Handle error appropriately
```

### 5. Security

✅ **Do:**
- Store credentials outside of source code
- Use environment variables for sensitive data
- Add `tokens/` to `.gitignore`
- Use service accounts with minimal required permissions

**.gitignore:**
```
tokens/
*.json
!requirements.json
.env
```

## Part 8: Production Deployment

### 1. Environment Variables

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
SERVICE_ACCOUNTS_DIR=/path/to/service-accounts
DEBUG=false
```

### 2. Scheduled Queue Processing

```python
from apscheduler.schedulers.blocking import BlockingScheduler

service = GoogleSheetService(...)

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', seconds=30)
def process_queue():
    service.process_queued_operations()

scheduler.start()
```

### 3. Monitoring

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sheets_service.log'),
        logging.StreamHandler()
    ]
)
```

### 4. Health Checks

```python
def health_check():
    """Check if service is healthy"""
    try:
        # Test Redis connection
        if service.redis_client:
            service.redis_client.ping()
        
        # Test service account access
        service.get_sheet_info(test_sheet_url)
        
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
```

## Next Steps

1. ✅ Complete all setup steps above
2. ✅ Run verification test script
3. ✅ Read [Quick Start Guide](GOOGLE_SHEETS_QUICKSTART.md)
4. ✅ Review [Usage Examples](../examples/google_sheets_usage.py)
5. ✅ Start integrating into your project

## Support

For additional help:
- 📖 [Quick Start Guide](GOOGLE_SHEETS_QUICKSTART.md)
- 💻 [Usage Examples](../examples/google_sheets_usage.py)
- 🐛 [GitHub Issues](https://github.com/yourusername/nodrive-gpm-package/issues)

## Summary Checklist

- [ ] Google Cloud project created
- [ ] Google Sheets API enabled
- [ ] 3-10 service accounts created
- [ ] Service account JSON files downloaded
- [ ] Files organized in `tokens/service-account/`
- [ ] Target sheets shared with all service accounts
- [ ] Redis installed and running (optional)
- [ ] Python dependencies installed
- [ ] Package installed
- [ ] Verification tests passed

**Once all items are checked, you're ready to use the Google Sheets service! 🎉**


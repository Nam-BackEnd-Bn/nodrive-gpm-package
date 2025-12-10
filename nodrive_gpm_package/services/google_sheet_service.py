"""
Google Sheets Service
Provides comprehensive Google Sheets operations including read, write, update, 
export with service account rotation, rate limiting, and queue-based batch processing.
"""

import os
import re
import time
import logging
import asyncio
from typing import Optional, List, Dict, Any, Literal, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request
except ImportError:
    raise ImportError(
        "Google Sheets dependencies not installed. "
        "Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    )

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Queue functionality will be disabled. Install with: pip install redis")


logger = logging.getLogger(__name__)


class ExportType(str, Enum):
    """Export type enumeration"""
    APPEND = "Append"
    OVERWRITE = "Overwrite"


@dataclass
class SheetChildrenInfo:
    """Information about a sheet tab"""
    title: str
    sheet_id: int
    row_count: int
    column_count: int


@dataclass
class SheetInfo:
    """Complete spreadsheet information"""
    spreadsheet_title: str
    sheets: List[SheetChildrenInfo]


@dataclass
class SheetValUpdateCell:
    """Cell update specification"""
    idx_row: Union[int, str]
    idx_col: Union[int, str]
    content: str
    actual_col: Optional[str] = None
    actual_row: Optional[int] = None


@dataclass
class QueueUpdateMultiCells:
    """Queue operation for multi-cell updates"""
    sheet_url: str
    sheet_name: str
    sheet_val: List[SheetValUpdateCell]
    row_offset: int
    timestamp: float


@dataclass
class QueueUpdateMultiColsByRow:
    """Queue operation for multi-column updates by row"""
    sheet_url: str
    sheet_name: str
    sheet_row: Union[int, str]
    sheet_val: List[Dict[str, Any]]
    row_offset: int
    timestamp: float


@dataclass
class QueueUpdateMultiRowsByCol:
    """Queue operation for multi-row updates by column"""
    sheet_url: str
    sheet_name: str
    sheet_col: Union[int, str]
    sheet_val: List[Dict[str, Any]]
    row_offset: int
    timestamp: float


@dataclass
class QueueUpdateMultiRowsMultiCols:
    """Queue operation for multi-row/multi-column updates"""
    sheet_url: str
    sheet_name: str
    values: List[List[str]]
    start_row: int
    end_row: Optional[int]
    start_col: int
    row_offset: int
    timestamp: float


class GoogleSheetServiceException(Exception):
    """Exception raised for Google Sheets service errors"""
    pass


class GoogleSheetService:
    """
    Google Sheets Service with service account rotation, rate limiting, and batch processing
    
    This service provides:
    - Service account rotation (up to 10 accounts) with automatic rate limiting
    - Redis-based queue system for batch operations
    - Sheet locking mechanism to prevent concurrent modifications
    - Read/Write operations with row offset support
    - Export functionality (Append/Overwrite modes)
    - Timeout protection for heavy calculations
    
    Usage:
        # Initialize with service account credentials directory
        service = GoogleSheetService(
            service_accounts_dir='path/to/service_accounts',
            redis_host='localhost',
            redis_port=6379
        )
        
        # Read sheet values
        values = service.get_values(
            sheet_url='https://docs.google.com/spreadsheets/d/...',
            sheet_name='Sheet1'
        )
        
        # Update multiple cells (queued by default)
        service.update_values_multi_cells(
            sheet_url='https://docs.google.com/spreadsheets/d/...',
            sheet_name='Sheet1',
            sheet_val=[
                SheetValUpdateCell(idx_row=0, idx_col=0, content='Value1'),
                SheetValUpdateCell(idx_row=1, idx_col=1, content='Value2')
            ]
        )
        
        # Process queued operations
        service.process_queued_operations()
        
        # Export data
        service.export(
            sheet_url='https://docs.google.com/spreadsheets/d/...',
            sheet_name='Sheet1',
            list_cols=['ID', 'Name', 'Email'],
            vals_export=[['1', 'John', 'john@example.com']],
            type_export=ExportType.APPEND
        )
    """
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    START_ROW_DEFAULT = 1
    NUMBER_OFFSET_ROW_ACTUAL = 2  # Row offset: 0 + 2 = row 2
    
    # Redis keys
    KEY_STORE_QUEUE_UPDATE_MULTI_ROWS_MULTI_COLS = 'key_store_queue_update_multi_rows_multi_cols'
    KEY_STORE_QUEUE_UPDATE_MULTI_ROWS_BY_COL = 'key_store_queue_update_multi_rows_by_col'
    KEY_STORE_QUEUE_UPDATE_MULTI_COLS_BY_ROW = 'key_store_queue_update_multi_cols_by_row'
    KEY_STORE_QUEUE_UPDATE_MULTI_CELLS = 'key_store_queue_update_multi_cells'
    KEY_STORE_LOCK_SHEET = 'key_store_lock_sheet'
    
    REDIS_KEY_CURRENT_INDEX = 'goog-sheet:service_account_current_index'
    REDIS_KEY_USAGE_PREFIX = 'service_account_usage'
    REDIS_KEY_BLOCKED_PREFIX = 'service_account_blocked'
    
    # Rate limits per minute per service account
    READ_LIMIT_PER_MINUTE = 300
    WRITE_LIMIT_PER_MINUTE = 100
    BLOCK_DURATION_SECONDS = 65
    
    def __init__(
        self,
        service_accounts_dir: Optional[str] = None,
        service_account_files: Optional[List[str]] = None,
        redis_host: str = 'localhost',
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        enable_queue: bool = True,
        debug: bool = False
    ):
        """
        Initialize Google Sheets Service
        
        Args:
            service_accounts_dir: Directory containing service account JSON files
            service_account_files: List of service account filenames (relative to dir)
            redis_host: Redis host for queue and rate limiting
            redis_port: Redis port
            redis_db: Redis database number
            redis_password: Redis password (optional)
            enable_queue: Enable queue functionality (requires Redis)
            debug: Enable debug logging
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
        
        # Setup service accounts
        self.service_accounts_dir = service_accounts_dir or os.path.join(
            os.path.dirname(__file__), '../../tokens/service-account'
        )
        
        self.service_account_files = service_account_files or [
            f'automationservice-v{i}.json' for i in range(1, 11)
        ]
        
        # Verify service account files exist
        self._verify_service_accounts()
        
        # Setup Redis if available and enabled
        self.redis_client: Optional[Redis] = None
        self.enable_queue = enable_queue and REDIS_AVAILABLE
        
        if self.enable_queue:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("✅ Redis connection established")
            except Exception as e:
                logger.warning(f"❌ Redis connection failed: {e}. Queue functionality disabled.")
                self.enable_queue = False
                self.redis_client = None
        else:
            if enable_queue and not REDIS_AVAILABLE:
                logger.warning("Queue functionality requested but Redis not available")
    
    def _verify_service_accounts(self):
        """Verify that service account files exist"""
        missing_files = []
        for filename in self.service_account_files:
            file_path = os.path.join(self.service_accounts_dir, filename)
            if not os.path.exists(file_path):
                missing_files.append(filename)
        
        if missing_files:
            logger.warning(f"Missing service account files: {missing_files}")
            # Remove missing files from list
            self.service_account_files = [
                f for f in self.service_account_files 
                if f not in missing_files
            ]
        
        if not self.service_account_files:
            raise GoogleSheetServiceException(
                f"No valid service account files found in {self.service_accounts_dir}"
            )
        
        logger.info(f"✅ Found {len(self.service_account_files)} service account(s)")
    
    # ==================== UTILITY METHODS ====================
    
    def get_sheet_id(self, sheet_url: str) -> Optional[str]:
        """
        Extract sheet ID from URL
        
        Args:
            sheet_url: Google Sheets URL
            
        Returns:
            Sheet ID or None if not found
        """
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, sheet_url)
        return match.group(1) if match else None
    
    def convert_index_to_column_name(self, index_col: int) -> str:
        """
        Convert column index (0-based) to column name (A, B, C, ..., AA, AB, ...)
        
        Args:
            index_col: Column index (0 = A, 1 = B, ...)
            
        Returns:
            Column name (e.g., 'A', 'Z', 'AA', 'AB')
        """
        column_name = ''
        index = index_col
        while index >= 0:
            column_name = chr((index % 26) + ord('A')) + column_name
            index = (index // 26) - 1
        return column_name
    
    def convert_column_name_to_index(self, column_name: str) -> int:
        """
        Convert column name to index (0-based)
        
        Args:
            column_name: Column name (e.g., 'A', 'Z', 'AA')
            
        Returns:
            Column index (A = 0, B = 1, ...)
        """
        upper_name = column_name.upper()
        if not re.match(r'^[A-Z]+$', upper_name):
            raise ValueError("Invalid column name. Only letters A-Z are allowed")
        
        result = 0
        for char in upper_name:
            char_code = ord(char) - ord('A')
            result = result * 26 + (char_code + 1)
        
        return result - 1
    
    def convert_value_sheet(
        self,
        vals: Optional[List[List[str]]],
        row_offset: int = 0
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Convert sheet values to list of dictionaries using first row as keys
        
        Args:
            vals: 2D array of sheet values
            row_offset: Row index for keys (0 = first row)
            
        Returns:
            List of dictionaries or None if vals is None
        """
        if not vals:
            return None
        
        keys = vals[row_offset]
        result = []
        
        for row in vals[row_offset + 1:]:
            row_dict = {}
            for i, key in enumerate(keys):
                row_dict[key] = row[i] if i < len(row) else ''
            result.append(row_dict)
        
        return result
    
    def get_index_col(self, key: str, list_keys: List[str]) -> int:
        """Get column index for a key"""
        try:
            return list_keys.index(key)
        except ValueError:
            return -1
    
    def get_list_cols_and_vals_export(
        self,
        cols_for_sheet: Dict[str, str],
        result_items: List[Dict[str, Any]]
    ) -> tuple[List[str], List[List[str]]]:
        """
        Extract columns and values for export
        
        Args:
            cols_for_sheet: Mapping of field keys to column names
            result_items: List of data items to export
            
        Returns:
            Tuple of (column headers, data rows)
        """
        # Extract column headers
        list_cols = list(cols_for_sheet.values())
        
        # Extract data rows
        vals_export = []
        for item in result_items:
            row = []
            for field_key in cols_for_sheet.keys():
                field_value = item.get(field_key)
                
                # Convert value to string
                if field_value is None:
                    cell_value = ''
                elif isinstance(field_value, datetime):
                    cell_value = field_value.isoformat()
                elif isinstance(field_value, dict):
                    cell_value = str(field_value)
                else:
                    cell_value = str(field_value)
                
                row.append(cell_value)
            vals_export.append(row)
        
        return list_cols, vals_export
    
    # ==================== SERVICE ACCOUNT ROTATION ====================
    
    def _get_file(self, operation_type: Literal['read', 'write'] = 'read') -> str:
        """
        Get service account file with round-robin rotation and rate limiting
        
        Args:
            operation_type: 'read' or 'write' operation
            
        Returns:
            Path to service account JSON file
        """
        if not self.enable_queue or not self.redis_client:
            # Fallback to first service account if Redis not available
            return os.path.join(
                self.service_accounts_dir,
                self.service_account_files[0]
            )
        
        try:
            # Get current index
            current_index = self.redis_client.get(self.REDIS_KEY_CURRENT_INDEX)
            current_index = int(current_index) if current_index else 0
            
            attempts = 0
            max_attempts = len(self.service_account_files)
            
            while attempts < max_attempts:
                filename = self.service_account_files[current_index]
                
                # Check if blocked
                if not self._is_service_account_blocked(filename):
                    # Check usage
                    current_usage = self._get_current_usage(filename, operation_type)
                    limit = self.READ_LIMIT_PER_MINUTE if operation_type == 'read' else self.WRITE_LIMIT_PER_MINUTE
                    
                    if current_usage < limit - 10:  # Buffer of 10 requests
                        # Increment usage
                        self._increment_usage(filename, operation_type)
                        
                        # Update index for next call
                        next_index = (current_index + 1) % len(self.service_account_files)
                        self.redis_client.set(self.REDIS_KEY_CURRENT_INDEX, next_index)
                        
                        file_path = os.path.join(self.service_accounts_dir, filename)
                        if self.debug:
                            logger.debug(f"🔄 Using service account: {filename} ({operation_type})")
                        return file_path
                    else:
                        # Reached limit, block this account
                        logger.warning(f"⚠️ Service account {filename} reached limit, blocking for {self.BLOCK_DURATION_SECONDS}s")
                        self._block_service_account(filename)
                
                # Try next account
                current_index = (current_index + 1) % len(self.service_account_files)
                attempts += 1
            
            # All accounts blocked or at limit, use fallback
            logger.warning("🚨 All service accounts blocked or at limit, using fallback")
            return os.path.join(self.service_accounts_dir, self.service_account_files[0])
            
        except Exception as e:
            logger.error(f"Error in round robin selection: {e}")
            return os.path.join(self.service_accounts_dir, self.service_account_files[0])
    
    def _is_service_account_blocked(self, filename: str) -> bool:
        """Check if service account is blocked"""
        if not self.redis_client:
            return False
        
        block_key = f"{self.REDIS_KEY_BLOCKED_PREFIX}:{filename}"
        blocked_until = self.redis_client.get(block_key)
        
        if blocked_until:
            blocked_until = float(blocked_until)
            if time.time() < blocked_until:
                return True  # Still blocked
            else:
                # Block expired, delete key
                self.redis_client.delete(block_key)
        
        return False
    
    def _block_service_account(self, filename: str):
        """Block service account for BLOCK_DURATION_SECONDS"""
        if not self.redis_client:
            return
        
        block_key = f"{self.REDIS_KEY_BLOCKED_PREFIX}:{filename}"
        block_until = time.time() + self.BLOCK_DURATION_SECONDS
        self.redis_client.setex(block_key, 70, str(block_until))  # TTL 70s to be safe
    
    def _get_current_usage(self, filename: str, operation_type: str) -> int:
        """Get current usage count in current minute"""
        if not self.redis_client:
            return 0
        
        usage_key = f"{self.REDIS_KEY_USAGE_PREFIX}:{filename}:{operation_type}"
        current_minute = int(time.time() / 60)
        minute_key = f"{usage_key}:{current_minute}"
        
        usage = self.redis_client.get(minute_key)
        return int(usage) if usage else 0
    
    def _increment_usage(self, filename: str, operation_type: str):
        """Increment usage count"""
        if not self.redis_client:
            return
        
        usage_key = f"{self.REDIS_KEY_USAGE_PREFIX}:{filename}:{operation_type}"
        current_minute = int(time.time() / 60)
        minute_key = f"{usage_key}:{current_minute}"
        
        current = self._get_current_usage(filename, operation_type)
        self.redis_client.setex(minute_key, 120, current + 1)  # TTL 2 minutes
    
    def _get_file_for_read(self) -> str:
        """Get service account file for read operation"""
        return self._get_file('read')
    
    def _get_file_for_write(self) -> str:
        """Get service account file for write operation"""
        return self._get_file('write')
    
    # ==================== SHEET LOCKING ====================
    
    def _lock_sheet(self, sheet_id: str, sheet_name: str, time_lock_seconds: int):
        """Lock sheet to prevent concurrent modifications"""
        if not self.redis_client:
            return
        
        lock_key = f"{self.KEY_STORE_LOCK_SHEET}:{sheet_id}:{sheet_name}"
        self.redis_client.setex(lock_key, time_lock_seconds, 'true')
        logger.debug(f"🔒 Locked sheet {sheet_name} for {time_lock_seconds}s")
    
    def _is_sheet_locked(self, sheet_id: str, sheet_name: str) -> bool:
        """Check if sheet is locked"""
        if not self.redis_client:
            return False
        
        lock_key = f"{self.KEY_STORE_LOCK_SHEET}:{sheet_id}:{sheet_name}"
        return self.redis_client.exists(lock_key) > 0
    
    # ==================== QUEUE OPERATIONS ====================
    
    def _get_queue_key(self, queue_type: str, sheet_url: str, sheet_name: str) -> str:
        """Generate queue key"""
        sheet_id = self.get_sheet_id(sheet_url)
        return f"{queue_type}:{sheet_id}:{sheet_name}"
    
    def _add_to_queue(self, queue_key: str, operation: Dict[str, Any]):
        """Add operation to queue"""
        if not self.redis_client:
            logger.warning("Queue operation skipped - Redis not available")
            return
        
        try:
            import json
            
            # Get existing queue
            existing_data = self.redis_client.get(queue_key)
            existing_queue = json.loads(existing_data) if existing_data else []
            
            # Add new operation
            existing_queue.append(operation)
            
            # Save with 5-minute TTL
            self.redis_client.setex(queue_key, 300, json.dumps(existing_queue))
            
            logger.debug(f"Added operation to queue: {queue_key}, Total: {len(existing_queue)}")
        except Exception as e:
            logger.error(f"Error adding to queue {queue_key}: {e}")
            raise
    
    def _get_and_clear_queue(self, queue_key: str) -> List[Dict[str, Any]]:
        """Get and clear queue"""
        if not self.redis_client:
            return []
        
        try:
            import json
            
            data = self.redis_client.get(queue_key)
            queue = json.loads(data) if data else []
            
            if queue:
                self.redis_client.delete(queue_key)
                logger.debug(f"Retrieved and cleared queue: {queue_key}, Operations: {len(queue)}")
            
            return queue
        except Exception as e:
            logger.error(f"Error getting queue {queue_key}: {e}")
            return []
    
    # ==================== GOOGLE SHEETS API OPERATIONS ====================
    
    def _get_sheets_service(self, key_file: str):
        """Get authenticated Google Sheets service"""
        credentials = service_account.Credentials.from_service_account_file(
            key_file,
            scopes=self.SCOPES
        )
        return build('sheets', 'v4', credentials=credentials)
    
    def _check_timeout(
        self,
        service,
        sheet_id: str,
        sheet_name: str,
        timeout_seconds: int = 10
    ):
        """
        Check if sheet is responsive (timeout protection for sheets with heavy calculations)
        
        Args:
            service: Google Sheets service instance
            sheet_id: Spreadsheet ID
            sheet_name: Sheet name
            timeout_seconds: Timeout in seconds
            
        Raises:
            GoogleSheetServiceException: If timeout occurs
        """
        timeout_range = f"{sheet_name}!A1:A1"
        
        try:
            logger.debug(f"🔍 Performing timeout check with {timeout_seconds}s limit...")
            
            # Simple timeout implementation
            start_time = time.time()
            try:
                service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=timeout_range
                ).execute()
                
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError()
                
                logger.debug("✅ Timeout check passed - sheet is responsive")
            except TimeoutError:
                raise
            
        except Exception as e:
            # Lock sheet for 30 seconds if timeout
            self._lock_sheet(sheet_id, sheet_name, 30)
            logger.error(f"❌ Timeout check failed: {str(e)}")
            raise GoogleSheetServiceException(
                f"Sheet {sheet_name} is unresponsive or calculating formulas. Please try again later."
            )
    
    # ==================== READ OPERATIONS ====================
    
    def get_sheet_info(self, sheet_url: str) -> SheetInfo:
        """
        Get spreadsheet information including all sheet tabs
        
        Args:
            sheet_url: Google Sheets URL
            
        Returns:
            SheetInfo object with spreadsheet details
        """
        try:
            key_file = self._get_file_for_read()
            service = self._get_sheets_service(key_file)
            
            sheet_id = self.get_sheet_id(sheet_url)
            if not sheet_id:
                raise GoogleSheetServiceException(f"Invalid Google Sheet URL: {sheet_url}")
            
            response = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                includeGridData=False
            ).execute()
            
            spreadsheet_title = response.get('properties', {}).get('title', '')
            
            sheets = []
            for sheet in response.get('sheets', []):
                props = sheet.get('properties', {})
                grid_props = props.get('gridProperties', {})
                
                sheets.append(SheetChildrenInfo(
                    title=props.get('title', ''),
                    sheet_id=props.get('sheetId', 0),
                    row_count=grid_props.get('rowCount', 0),
                    column_count=grid_props.get('columnCount', 0)
                ))
            
            logger.debug(
                f"Sheet information retrieved: {spreadsheet_title} with {len(sheets)} sub-sheets"
            )
            
            return SheetInfo(spreadsheet_title=spreadsheet_title, sheets=sheets)
            
        except Exception as e:
            logger.error(f"Error retrieving sheet information: {str(e)}")
            raise GoogleSheetServiceException(
                f"Failed to get Google Sheet information: {str(e)}"
            )
    
    def get_idx_row(
        self,
        sheet_url: str,
        sheet_name: str,
        col_name: str,
        val: str,
        is_check_timeout: bool = False
    ) -> int:
        """
        Find row index by searching for value in specific column
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Sheet name
            col_name: Column name (e.g., 'A', 'B')
            val: Value to search for
            is_check_timeout: Enable timeout check
            
        Returns:
            Row index (1-based) or -1 if not found
        """
        sheet_id = self.get_sheet_id(sheet_url)
        
        # Check if locked
        if self._is_sheet_locked(sheet_id, sheet_name):
            raise GoogleSheetServiceException(
                f"Sheet {sheet_name} is locked, please try again"
            )
        
        try:
            sheet_info = self.get_sheet_info(sheet_url)
            sheet = next((s for s in sheet_info.sheets if s.title == sheet_name), None)
            
            if not sheet:
                raise GoogleSheetServiceException(f"Sheet {sheet_name} not found")
            
            key_file = self._get_file_for_read()
            service = self._get_sheets_service(key_file)
            
            if is_check_timeout:
                self._check_timeout(service, sheet_id, sheet_name)
            
            range_str = f"{sheet_name}!{col_name}{self.START_ROW_DEFAULT}:{col_name}{sheet.row_count}"
            
            start_time = time.time()
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_str
            ).execute()
            
            elapsed = time.time() - start_time
            logger.debug(f"⌛ TIME READ: {elapsed:.3f}s")
            
            values = result.get('values', [])
            
            for idx, row in enumerate(values):
                if row and row[0] == val:
                    return idx + 1
            
            return -1
            
        except Exception as e:
            logger.warning(f"Error finding row index: {str(e)}")
            raise GoogleSheetServiceException(
                f"Your google sheet is invalid: {sheet_name} {sheet_url}"
            )
    
    def get_values(
        self,
        sheet_url: str,
        sheet_name: str,
        end_row: Optional[int] = None,
        is_check_timeout: bool = False
    ) -> List[List[str]]:
        """
        Get all values from a sheet
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Sheet name
            end_row: Optional end row limit
            is_check_timeout: Enable timeout check
            
        Returns:
            2D array of cell values
        """
        sheet_id = self.get_sheet_id(sheet_url)
        
        # Check if locked
        if self._is_sheet_locked(sheet_id, sheet_name):
            raise GoogleSheetServiceException(
                f"Sheet {sheet_name} is locking, please wait..."
            )
        
        logger.info(f"📰 Reading sheet: {sheet_name}")
        logger.info(f"🔗 Sheet URL: {sheet_url}")
        
        try:
            sheet_info = self.get_sheet_info(sheet_url)
            sheet = next((s for s in sheet_info.sheets if s.title == sheet_name), None)
            
            if not sheet:
                raise GoogleSheetServiceException(f"Sheet {sheet_name} not found")
            
            key_file = self._get_file_for_read()
            service = self._get_sheets_service(key_file)
            
            if is_check_timeout:
                self._check_timeout(service, sheet_id, sheet_name)
            
            # Determine range
            start_col = 'A'
            end_col = self.convert_index_to_column_name(sheet.column_count - 1)
            
            if end_row:
                range_str = f"{sheet_name}!{start_col}{self.START_ROW_DEFAULT}:{end_col}{end_row}"
            else:
                range_str = sheet_name
            
            start_time = time.time()
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_str
            ).execute()
            
            elapsed = time.time() - start_time
            logger.info(f"⌛ TIME READ: {elapsed:.3f}s")
            
            return result.get('values', [])
            
        except Exception as e:
            logger.warning(f"Error reading values: {str(e)}")
            raise GoogleSheetServiceException(
                "Sheet URL or name is invalid, please check again!"
            )
    
    # ==================== EXPORT OPERATIONS ====================
    
    def export(
        self,
        sheet_url: str,
        sheet_name: str,
        list_cols: List[str],
        vals_export: List[List[str]],
        type_export: ExportType,
        immediate: bool = True,
        time_lock_sheet: int = 0
    ) -> bool:
        """
        Export data to Google Sheet with Append or Overwrite mode
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Sheet name
            list_cols: Column headers
            vals_export: Data rows
            type_export: Export type (Append or Overwrite)
            immediate: Execute immediately (default True)
            time_lock_sheet: Lock duration in seconds
            
        Returns:
            True if successful
        """
        logger.info(f"🚀 Starting export: {sheet_name}, Type: {type_export}")
        logger.info(f"📊 Columns: {len(list_cols)}, Rows: {len(vals_export)}")
        
        sheet_id = self.get_sheet_id(sheet_url)
        if time_lock_sheet > 0:
            self._lock_sheet(sheet_id, sheet_name, time_lock_sheet)
        
        return self._execute_export(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            list_cols=list_cols,
            vals_export=vals_export,
            type_export=type_export
        )
    
    def _execute_export(
        self,
        sheet_url: str,
        sheet_name: str,
        list_cols: List[str],
        vals_export: List[List[str]],
        type_export: ExportType
    ) -> bool:
        """Internal method to execute export"""
        try:
            key_file = self._get_file_for_write()
            service = self._get_sheets_service(key_file)
            
            sheet_id = self.get_sheet_id(sheet_url)
            if not sheet_id:
                raise GoogleSheetServiceException(f"Invalid Google Sheet URL: {sheet_url}")
            
            if type_export == ExportType.OVERWRITE:
                return self._execute_overwrite_export(
                    service=service,
                    sheet_id=sheet_id,
                    sheet_name=sheet_name,
                    list_cols=list_cols,
                    vals_export=vals_export
                )
            elif type_export == ExportType.APPEND:
                return self._execute_append_export(
                    service=service,
                    sheet_id=sheet_id,
                    sheet_name=sheet_name,
                    list_cols=list_cols,
                    vals_export=vals_export
                )
            else:
                raise GoogleSheetServiceException(f"Invalid export type: {type_export}")
                
        except Exception as e:
            logger.error(f"Error during export: {str(e)}")
            raise GoogleSheetServiceException(
                f"Failed to export data to Google Sheet: {str(e)}"
            )
    
    def _execute_overwrite_export(
        self,
        service,
        sheet_id: str,
        sheet_name: str,
        list_cols: List[str],
        vals_export: List[List[str]]
    ) -> bool:
        """Execute OVERWRITE export - write headers and data from row 1"""
        try:
            # Prepare data: headers + data rows
            export_data = [list_cols] + vals_export
            
            num_cols = len(list_cols)
            num_rows = len(export_data)
            
            start_col = 'A'
            end_col = self.convert_index_to_column_name(num_cols - 1)
            start_row = 1
            end_row = num_rows
            
            range_str = f"{sheet_name}!{start_col}{start_row}:{end_col}{end_row}"
            
            logger.info(f"📝 OVERWRITE mode - Writing to range: {range_str}")
            logger.info(f"📝 Data matrix: {num_rows} rows x {num_cols} cols")
            
            response = service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': [
                        {
                            'range': range_str,
                            'values': export_data
                        }
                    ]
                }
            ).execute()
            
            logger.info("✅ OVERWRITE export completed successfully")
            logger.info(f"📊 Exported {len(vals_export)} data rows with headers")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ OVERWRITE export failed: {str(e)}")
            raise
    
    def _execute_append_export(
        self,
        service,
        sheet_id: str,
        sheet_name: str,
        list_cols: List[str],
        vals_export: List[List[str]]
    ) -> bool:
        """Execute APPEND export - find empty rows and append data"""
        try:
            logger.info("🔍 APPEND mode - Finding empty rows...")
            
            # Get sheet info
            sheet_info = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                ranges=[sheet_name],
                includeGridData=False
            ).execute()
            
            sheet = next(
                (s for s in sheet_info.get('sheets', []) 
                 if s.get('properties', {}).get('title') == sheet_name),
                None
            )
            
            if not sheet:
                raise GoogleSheetServiceException(f"Sheet {sheet_name} not found")
            
            max_rows = sheet.get('properties', {}).get('gridProperties', {}).get('rowCount', 1000)
            
            # Read column A to find last used row
            read_range = f"{sheet_name}!A1:A{max_rows}"
            read_response = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=read_range
            ).execute()
            
            current_data = read_response.get('values', [])
            
            # Find last non-empty row
            start_row = 1
            if current_data:
                last_used_row = 0
                for i in range(len(current_data) - 1, -1, -1):
                    if current_data[i] and len(current_data[i]) > 0 and current_data[i][0].strip():
                        last_used_row = i + 1
                        break
                start_row = last_used_row + 1
            
            logger.info(f"📍 Append position: row {start_row}")
            
            # Determine if we need headers
            data_to_write = vals_export
            write_start_row = start_row
            
            if start_row == 1:
                # Include headers
                data_to_write = [list_cols] + vals_export
                logger.info("📝 Including headers (sheet is empty)")
            else:
                # Verify existing headers
                header_range = f"{sheet_name}!A1:{self.convert_index_to_column_name(len(list_cols) - 1)}1"
                header_response = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=header_range
                ).execute()
                
                existing_headers = header_response.get('values', [[]])[0] if header_response.get('values') else []
                
                if existing_headers:
                    headers_match = all(
                        i < len(existing_headers) and existing_headers[i] == col 
                        for i, col in enumerate(list_cols)
                    )
                    if not headers_match:
                        logger.warning("⚠️ Headers mismatch detected")
                        logger.warning(f"Expected: {list_cols}")
                        logger.warning(f"Existing: {existing_headers}")
                
                logger.info("📝 Appending data only (headers exist)")
            
            # Calculate write range
            num_cols = len(list_cols)
            num_rows = len(data_to_write)
            start_col = 'A'
            end_col = self.convert_index_to_column_name(num_cols - 1)
            end_row = write_start_row + num_rows - 1
            
            write_range = f"{sheet_name}!{start_col}{write_start_row}:{end_col}{end_row}"
            
            logger.info(f"📝 APPEND mode - Writing to range: {write_range}")
            
            response = service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': [
                        {
                            'range': write_range,
                            'values': data_to_write
                        }
                    ]
                }
            ).execute()
            
            logger.info("✅ APPEND export completed successfully")
            logger.info(f"📊 Appended {len(vals_export)} data rows at row {write_start_row}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ APPEND export failed: {str(e)}")
            raise
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update_values_multi_cells(
        self,
        sheet_url: str,
        sheet_name: str,
        sheet_val: List[SheetValUpdateCell],
        row_offset: int = 0,
        immediate: bool = False,
        time_lock_sheet: int = 0
    ) -> bool:
        """
        Update multiple cells with specific positions
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Sheet name
            sheet_val: List of cell updates
            row_offset: Row offset (0 = data starts at row 2)
            immediate: Execute immediately (default False - queued)
            time_lock_sheet: Lock duration in seconds
            
        Returns:
            True if successful (or queued)
        """
        sheet_id = self.get_sheet_id(sheet_url)
        
        if time_lock_sheet > 0:
            self._lock_sheet(sheet_id, sheet_name, time_lock_sheet)
        
        if immediate or not self.enable_queue:
            return self._execute_update_values_multi_cells(
                sheet_url=sheet_url,
                sheet_name=sheet_name,
                sheet_val=sheet_val,
                row_offset=row_offset
            )
        
        # Add to queue
        queue_key = self._get_queue_key(
            self.KEY_STORE_QUEUE_UPDATE_MULTI_CELLS,
            sheet_url,
            sheet_name
        )
        
        operation = {
            'sheet_url': sheet_url,
            'sheet_name': sheet_name,
            'sheet_val': [
                {
                    'idx_row': cell.idx_row,
                    'idx_col': cell.idx_col,
                    'content': cell.content
                }
                for cell in sheet_val
            ],
            'row_offset': row_offset,
            'timestamp': time.time()
        }
        
        self._add_to_queue(queue_key, operation)
        logger.debug(f"Queued updateValuesMultiCells operation for {sheet_name}")
        
        return True
    
    def _execute_update_values_multi_cells(
        self,
        sheet_url: str,
        sheet_name: str,
        sheet_val: List[SheetValUpdateCell],
        row_offset: int = 0
    ) -> bool:
        """Internal method to execute multi-cell update"""
        try:
            key_file = self._get_file_for_write()
            service = self._get_sheets_service(key_file)
            
            sheet_id = self.get_sheet_id(sheet_url)
            if not sheet_id:
                raise GoogleSheetServiceException(f"Invalid Google Sheet URL: {sheet_url}")
            
            if not sheet_val:
                raise GoogleSheetServiceException("No values provided for update")
            
            # Create batch update requests
            requests = []
            for cell in sheet_val:
                row_num = int(cell.idx_row) if isinstance(cell.idx_row, str) else cell.idx_row
                col_num = int(cell.idx_col) if isinstance(cell.idx_col, str) else cell.idx_col
                
                if row_num < 0 or col_num < 0:
                    raise GoogleSheetServiceException(
                        f"Row and column must be non-negative: row={row_num}, col={col_num}"
                    )
                
                col_name = self.convert_index_to_column_name(col_num)
                actual_row = row_num + self.NUMBER_OFFSET_ROW_ACTUAL + row_offset
                
                sheet_range = f"{sheet_name}!{col_name}{actual_row}"
                
                requests.append({
                    'range': sheet_range,
                    'values': [[cell.content]]
                })
            
            # Execute batch update
            response = service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': requests
                }
            ).execute()
            
            logger.info(f"📓 Updated {len(sheet_val)} cells in {sheet_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating multiple cells: {str(e)}")
            raise GoogleSheetServiceException(
                f"Failed to update multiple cells: {str(e)}"
            )
    
    def update_values_multi_rows_multi_cols(
        self,
        sheet_url: str,
        sheet_name: str,
        values: List[List[str]],
        start_row: int = 0,
        end_row: Optional[int] = None,
        start_col: int = 0,
        row_offset: int = 0,
        immediate: bool = False,
        time_lock_sheet: int = 0
    ) -> bool:
        """
        Update multiple rows and columns (matrix update)
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Sheet name
            values: 2D array of values
            start_row: Start row index (0-based)
            end_row: End row index (optional)
            start_col: Start column index (0-based)
            row_offset: Row offset
            immediate: Execute immediately (default False)
            time_lock_sheet: Lock duration in seconds
            
        Returns:
            True if successful
        """
        sheet_id = self.get_sheet_id(sheet_url)
        
        if time_lock_sheet > 0:
            self._lock_sheet(sheet_id, sheet_name, time_lock_sheet)
        
        if immediate or not self.enable_queue:
            return self._execute_update_values_multi_rows_multi_cols(
                sheet_url=sheet_url,
                sheet_name=sheet_name,
                values=values,
                start_row=start_row,
                end_row=end_row,
                start_col=start_col,
                row_offset=row_offset
            )
        
        # Add to queue
        queue_key = self._get_queue_key(
            self.KEY_STORE_QUEUE_UPDATE_MULTI_ROWS_MULTI_COLS,
            sheet_url,
            sheet_name
        )
        
        operation = {
            'sheet_url': sheet_url,
            'sheet_name': sheet_name,
            'values': values,
            'start_row': start_row,
            'end_row': end_row,
            'start_col': start_col,
            'row_offset': row_offset,
            'timestamp': time.time()
        }
        
        self._add_to_queue(queue_key, operation)
        logger.debug(f"Queued updateValuesMultiRowsMultiCols for {sheet_name}")
        
        return True
    
    def _execute_update_values_multi_rows_multi_cols(
        self,
        sheet_url: str,
        sheet_name: str,
        values: List[List[str]],
        start_row: int = 0,
        end_row: Optional[int] = None,
        start_col: int = 0,
        row_offset: int = 0
    ) -> bool:
        """Internal method to execute multi-row/multi-col update"""
        try:
            key_file = self._get_file_for_write()
            service = self._get_sheets_service(key_file)
            
            sheet_id = self.get_sheet_id(sheet_url)
            
            if not values or not values[0]:
                raise GoogleSheetServiceException("Invalid values matrix")
            
            num_rows = len(values)
            num_cols = len(values[0])
            
            start_col_name = self.convert_index_to_column_name(start_col)
            end_col_name = self.convert_index_to_column_name(start_col + num_cols - 1)
            
            start_row_idx = start_row + self.NUMBER_OFFSET_ROW_ACTUAL + row_offset
            
            if end_row:
                end_row_idx = end_row + self.NUMBER_OFFSET_ROW_ACTUAL + row_offset
            else:
                end_row_idx = start_row + num_rows + 1 + row_offset
            
            sheet_range = f"{sheet_name}!{start_col_name}{start_row_idx}:{end_col_name}{end_row_idx}"
            
            response = service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': [
                        {
                            'range': sheet_range,
                            'values': values
                        }
                    ]
                }
            ).execute()
            
            logger.info(f"📓 Updated range {sheet_range} in {sheet_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during multi-row/multi-col update: {str(e)}")
            return False
    
    def delete_row_sheet(
        self,
        sheet_url: str,
        sheet_name: str,
        sheet_row: Union[int, str],
        row_offset: int = 0
    ) -> bool:
        """
        Delete a row from sheet
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Sheet name
            sheet_row: Row index to delete (0-based)
            row_offset: Row offset
            
        Returns:
            True if successful
        """
        try:
            key_file = self._get_file_for_write()
            service = self._get_sheets_service(key_file)
            
            sheet_id_str = self.get_sheet_id(sheet_url)
            
            # Get sheet ID (numeric)
            sheet_info = service.spreadsheets().get(
                spreadsheetId=sheet_id_str,
                ranges=[sheet_name],
                includeGridData=False
            ).execute()
            
            sheet = next(
                (s for s in sheet_info.get('sheets', [])
                 if s.get('properties', {}).get('title') == sheet_name),
                None
            )
            
            if not sheet:
                raise GoogleSheetServiceException(f"Sheet {sheet_name} not found")
            
            numeric_sheet_id = sheet.get('properties', {}).get('sheetId')
            
            if numeric_sheet_id is None:
                raise GoogleSheetServiceException("Could not get sheet ID")
            
            row_num = int(sheet_row) if isinstance(sheet_row, str) else sheet_row
            actual_row_idx = row_num + 1 + row_offset
            
            request = {
                'deleteDimension': {
                    'range': {
                        'sheetId': numeric_sheet_id,
                        'dimension': 'ROWS',
                        'startIndex': actual_row_idx,
                        'endIndex': actual_row_idx + 1
                    }
                }
            }
            
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id_str,
                body={'requests': [request]}
            ).execute()
            
            logger.info(f"📓 Deleted row {actual_row_idx} from {sheet_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting row: {str(e)}")
            return False
    
    # ==================== QUEUE PROCESSING ====================
    
    def process_queued_operations(self):
        """
        Process all queued operations
        Call this method periodically (e.g., via cron job or scheduler)
        """
        if not self.enable_queue:
            logger.warning("Queue processing skipped - queue not enabled")
            return
        
        logger.info("⏰ Starting queue processing")
        
        total_processed = 0
        
        # Process each queue type
        total_processed += self._process_multi_cells_queue()
        total_processed += self._process_multi_rows_multi_cols_queue()
        
        if total_processed > 0:
            logger.info(f"🎯 Queue processing completed: {total_processed} operations processed")
        else:
            logger.debug("No queued operations to process")
    
    def _process_multi_cells_queue(self) -> int:
        """Process multi-cell update queue"""
        try:
            # Get all queue keys for this operation type
            pattern = f"{self.KEY_STORE_QUEUE_UPDATE_MULTI_CELLS}:*"
            all_keys = self.redis_client.keys(pattern) if self.redis_client else []
            
            total_processed = 0
            
            for queue_key in all_keys:
                operations = self._get_and_clear_queue(queue_key)
                if not operations:
                    continue
                
                # Merge operations for same sheet
                merged_cells = []
                latest_row_offset = 0
                sheet_url = ''
                sheet_name = ''
                
                for op in operations:
                    sheet_url = op['sheet_url']
                    sheet_name = op['sheet_name']
                    latest_row_offset = op['row_offset']
                    
                    # Convert dict to SheetValUpdateCell
                    for cell_dict in op['sheet_val']:
                        merged_cells.append(SheetValUpdateCell(
                            idx_row=cell_dict['idx_row'],
                            idx_col=cell_dict['idx_col'],
                            content=cell_dict['content']
                        ))
                
                # Execute merged update
                if merged_cells:
                    try:
                        self._execute_update_values_multi_cells(
                            sheet_url=sheet_url,
                            sheet_name=sheet_name,
                            sheet_val=merged_cells,
                            row_offset=latest_row_offset
                        )
                        total_processed += len(merged_cells)
                        logger.debug(f"✅ Processed {len(merged_cells)} cells for {sheet_name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to process queue for {sheet_name}: {str(e)}")
            
            return total_processed
            
        except Exception as e:
            logger.error(f"❌ Error processing multi-cells queue: {str(e)}")
            return 0
    
    def _process_multi_rows_multi_cols_queue(self) -> int:
        """Process multi-row/multi-col update queue"""
        try:
            pattern = f"{self.KEY_STORE_QUEUE_UPDATE_MULTI_ROWS_MULTI_COLS}:*"
            all_keys = self.redis_client.keys(pattern) if self.redis_client else []
            
            total_processed = 0
            
            for queue_key in all_keys:
                operations = self._get_and_clear_queue(queue_key)
                if not operations:
                    continue
                
                # Process each operation separately (different ranges)
                for op in operations:
                    try:
                        self._execute_update_values_multi_rows_multi_cols(
                            sheet_url=op['sheet_url'],
                            sheet_name=op['sheet_name'],
                            values=op['values'],
                            start_row=op['start_row'],
                            end_row=op.get('end_row'),
                            start_col=op['start_col'],
                            row_offset=op['row_offset']
                        )
                        total_processed += 1
                        logger.debug(f"✅ Processed multi-rows-multi-cols for {op['sheet_name']}")
                    except Exception as e:
                        logger.error(f"❌ Failed to process operation for {op['sheet_name']}: {str(e)}")
            
            return total_processed
            
        except Exception as e:
            logger.error(f"❌ Error processing multi-rows-multi-cols queue: {str(e)}")
            return 0


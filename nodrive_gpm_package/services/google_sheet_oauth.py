"""
Google Sheets OAuth2 Helper
Simple OAuth2-based Google Sheets operations for personal/small-scale use.

This is a lighter alternative to GoogleSheetService which uses service accounts.
Use this helper when:
- Working with personal Google Sheets
- Don't need service account rotation or rate limiting
- Want simpler setup with OAuth2 credentials

For production/heavy usage, use GoogleSheetService instead.
"""

import os
import pickle
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    raise ImportError(
        "Google Sheets OAuth dependencies not installed. "
        "Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    )


class GoogleSheetOAuthException(Exception):
    """Exception raised for Google Sheets OAuth helper errors"""
    pass


class GoogleSheetOAuth:
    """
    Simple Google Sheets helper using OAuth2 authentication
    
    This class provides basic read/write operations for Google Sheets using
    OAuth2 user credentials. Perfect for personal projects and small-scale usage.
    
    Setup:
        1. Create OAuth2 credentials in Google Cloud Console
        2. Download credentials as 'oauth.json'
        3. Place in 'certs' directory or specify custom path
    
    Usage:
        # Initialize helper
        helper = GoogleSheetOAuth()
        
        # Read sheet data
        data = helper.read_sheet(
            sheet_url='https://docs.google.com/spreadsheets/d/...',
            sheet_name='Sheet1'
        )
        
        # Write to specific cell
        helper.write_sheet(
            sheet_url='https://docs.google.com/spreadsheets/d/...',
            sheet_name='Sheet1',
            row=0,  # 0-based index
            col='A',
            value='Hello World'
        )
    
    Notes:
        - First run will open browser for OAuth2 consent
        - Credentials are cached in tokens/sheet.token
        - For production/heavy usage, consider using GoogleSheetService
    """
    
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    
    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None
    ):
        """
        Initialize Google Sheets OAuth helper
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file.
                            Defaults to 'certs/oauth.json'
            token_file: Path to token cache file.
                       Defaults to 'tokens/sheet.token'
        """
        # Set default paths
        if credentials_file is None:
            credentials_file = os.path.join(os.getcwd(), "certs", "oauth.json")
        
        if token_file is None:
            token_file = os.path.join(os.getcwd(), "tokens", "sheet.token")
        
        self.credentials_file = credentials_file
        self.token_file = token_file
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        
        # Authenticate and build service
        self.svc = self._authenticate()
    
    def _authenticate(self):
        """
        Authenticate with Google Sheets API using OAuth2
        
        Returns:
            Google Sheets service instance
        """
        creds = None
        
        # Load cached credentials
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "rb") as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"Warning: Failed to load token file: {e}")
                creds = None
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Warning: Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                # Check if credentials file exists
                if not os.path.exists(self.credentials_file):
                    raise GoogleSheetOAuthException(
                        f"OAuth credentials file not found: {self.credentials_file}\n"
                        f"Please download OAuth2 credentials from Google Cloud Console "
                        f"and save as '{self.credentials_file}'"
                    )
                
                # Run OAuth2 flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file,
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            try:
                with open(self.token_file, "wb") as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"Warning: Failed to save token: {e}")
        
        # Build and return service
        return build("sheets", "v4", credentials=creds)
    
    def read_sheet(
        self,
        sheet_url: str,
        sheet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Read data from a Google Sheet and return as list of dictionaries
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Name of the sheet tab to read
        
        Returns:
            List of dictionaries with column headers as keys
            Empty list if error occurs or sheet is empty
        
        Example:
            >>> helper = GoogleSheetOAuth()
            >>> data = helper.read_sheet(
            ...     sheet_url='https://docs.google.com/spreadsheets/d/...',
            ...     sheet_name='Sheet1'
            ... )
            >>> print(data)
            [
                {'Name': 'John', 'Age': '25', 'City': 'NYC'},
                {'Name': 'Jane', 'Age': '30', 'City': 'LA'}
            ]
        """
        sheet_id = self._get_sheet_id(sheet_url)
        
        if not sheet_id:
            raise GoogleSheetOAuthException(f"Invalid Google Sheets URL: {sheet_url}")
        
        try:
            result = (
                self.svc.spreadsheets()
                .values()
                .get(spreadsheetId=sheet_id, range=sheet_name)
                .execute()
            )
            
            if not result or 'values' not in result:
                return []
            
            values = result['values']
            
            if not values or len(values) < 2:
                return []
            
            # Extract headers (first row) and remove whitespace
            headers = [str(item).replace(" ", "") for item in values[0]]
            
            # Convert data rows to dictionaries
            payload = []
            for row in values[1:]:
                item = {}
                for index, header in enumerate(headers):
                    if index < len(row):
                        item[header] = row[index]
                    else:
                        item[header] = ""
                payload.append(item)
            
            return payload
        
        except HttpError as e:
            if e.resp.status == 503:
                print(f"Google Sheets service temporarily unavailable: {str(e)}")
            else:
                print(f"HTTP error reading sheet: {str(e)}")
            return []
        
        except Exception as e:
            print(f"Error reading sheet '{sheet_name}': {str(e)}")
            return []
    
    def write_sheet(
        self,
        sheet_url: str,
        sheet_name: str,
        row: int,
        col: str,
        value: str
    ) -> Dict[str, Any]:
        """
        Write value to a specific cell in Google Sheet
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Name of the sheet tab
            row: Row index (0-based). Note: row 0 becomes sheet row 2
            col: Column name (e.g., 'A', 'B', 'AA')
            value: Value to write to the cell
        
        Returns:
            Dictionary with update result information
            Empty dict if error occurs
        
        Example:
            >>> helper = GoogleSheetOAuth()
            >>> result = helper.write_sheet(
            ...     sheet_url='https://docs.google.com/spreadsheets/d/...',
            ...     sheet_name='Sheet1',
            ...     row=0,
            ...     col='A',
            ...     value='Updated Value'
            ... )
            >>> print(result)
            {'updatedCells': 1, 'updatedRows': 1, ...}
        """
        sheet_id = self._get_sheet_id(sheet_url)
        
        if not sheet_id:
            raise GoogleSheetOAuthException(f"Invalid Google Sheets URL: {sheet_url}")
        
        # Convert 0-based row to actual sheet row (row 0 = sheet row 2)
        actual_row = row + 2
        
        print(
            f"Updating cell: Sheet='{sheet_name}', "
            f"Cell={col}{actual_row}, Value='{value}'"
        )
        
        try:
            # Build cell range (e.g., 'Sheet1!A2')
            range_name = f"{sheet_name}!{col}{actual_row}"
            
            # Prepare value
            body = {"values": [[value]]}
            
            # Execute update
            result = (
                self.svc.spreadsheets()
                .values()
                .update(
                    spreadsheetId=sheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body=body,
                )
                .execute()
            )
            
            updated_cells = result.get('updatedCells', 0)
            print(f"✅ Successfully updated {updated_cells} cell(s)")
            
            return result
        
        except HttpError as e:
            print(f"HTTP error writing to sheet: {str(e)}")
            return {}
        
        except Exception as e:
            print(f"Error writing to sheet '{sheet_name}': {str(e)}")
            return {}
    
    def write_range(
        self,
        sheet_url: str,
        sheet_name: str,
        start_row: int,
        start_col: str,
        values: List[List[str]]
    ) -> Dict[str, Any]:
        """
        Write multiple values to a range in Google Sheet
        
        Args:
            sheet_url: Google Sheets URL
            sheet_name: Name of the sheet tab
            start_row: Starting row index (0-based)
            start_col: Starting column name (e.g., 'A', 'B')
            values: 2D array of values to write
        
        Returns:
            Dictionary with update result information
        
        Example:
            >>> helper = GoogleSheetOAuth()
            >>> result = helper.write_range(
            ...     sheet_url='https://docs.google.com/spreadsheets/d/...',
            ...     sheet_name='Sheet1',
            ...     start_row=0,
            ...     start_col='A',
            ...     values=[
            ...         ['Name', 'Age', 'City'],
            ...         ['John', '25', 'NYC'],
            ...         ['Jane', '30', 'LA']
            ...     ]
            ... )
        """
        sheet_id = self._get_sheet_id(sheet_url)
        
        if not sheet_id:
            raise GoogleSheetOAuthException(f"Invalid Google Sheets URL: {sheet_url}")
        
        if not values:
            raise GoogleSheetOAuthException("No values provided to write")
        
        # Calculate range
        actual_start_row = start_row + 2
        num_rows = len(values)
        num_cols = len(values[0]) if values else 0
        
        # Calculate end column
        start_col_idx = self._column_name_to_index(start_col)
        end_col_idx = start_col_idx + num_cols - 1
        end_col = self.get_column_name(end_col_idx)
        
        # Build range
        range_name = f"{sheet_name}!{start_col}{actual_start_row}:{end_col}{actual_start_row + num_rows - 1}"
        
        print(f"Writing range: {range_name}")
        
        try:
            body = {"values": values}
            
            result = (
                self.svc.spreadsheets()
                .values()
                .update(
                    spreadsheetId=sheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body=body,
                )
                .execute()
            )
            
            updated_cells = result.get('updatedCells', 0)
            print(f"✅ Successfully updated {updated_cells} cell(s)")
            
            return result
        
        except Exception as e:
            print(f"Error writing range to sheet '{sheet_name}': {str(e)}")
            return {}
    
    def get_column_name(self, index_col: int) -> str:
        """
        Convert column index (0-based) to column name
        
        Args:
            index_col: Column index (0 = A, 1 = B, 25 = Z, 26 = AA)
        
        Returns:
            Column name (e.g., 'A', 'B', 'AA', 'AB')
        
        Example:
            >>> helper = GoogleSheetOAuth()
            >>> helper.get_column_name(0)
            'A'
            >>> helper.get_column_name(25)
            'Z'
            >>> helper.get_column_name(26)
            'AA'
        """
        return self._index_to_column_name(index_col)
    
    def _get_sheet_id(self, url: str) -> Optional[str]:
        """
        Extract spreadsheet ID from Google Sheets URL
        
        Args:
            url: Google Sheets URL
        
        Returns:
            Spreadsheet ID or None if not found
        """
        pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def _index_to_column_name(self, index: int) -> str:
        """
        Convert 0-based column index to Excel-style column name
        
        Args:
            index: Column index (0-based)
        
        Returns:
            Column name (e.g., 'A', 'B', 'AA')
        """
        column_name = ""
        while index >= 0:
            column_name = chr(index % 26 + ord("A")) + column_name
            index = index // 26 - 1
        return column_name
    
    def _column_name_to_index(self, column_name: str) -> int:
        """
        Convert Excel-style column name to 0-based index
        
        Args:
            column_name: Column name (e.g., 'A', 'B', 'AA')
        
        Returns:
            Column index (0-based)
        """
        column_name = column_name.upper()
        result = 0
        for char in column_name:
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result - 1
    
    def _get_column_names(self, length: int) -> List[str]:
        """
        Get list of column names from 0 to length
        
        Args:
            length: Number of columns
        
        Returns:
            List of column names
        """
        return [self._index_to_column_name(i) for i in range(length)]


# Backward compatibility alias
HelperGGSheet = GoogleSheetOAuth


"""
Google Sheets Service Usage Examples

This example demonstrates how to use the GoogleSheetService for:
1. Reading sheet data
2. Writing/updating cells
3. Exporting data (Append/Overwrite)
4. Service account rotation with rate limiting
5. Queue-based batch operations
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodrive_gpm_package.services import (
    GoogleSheetService,
    GoogleSheetServiceException,
    SheetValUpdateCell,
    ExportType
)


def example_basic_read():
    """Example 1: Basic sheet reading"""
    print("\n" + "="*60)
    print("Example 1: Basic Sheet Reading")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account',
        enable_queue=False  # Disable queue for immediate execution
    )
    
    # Read sheet values
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        values = service.get_values(
            sheet_url=sheet_url,
            sheet_name=sheet_name
        )
        
        print(f"✅ Read {len(values)} rows")
        if values:
            print(f"First row (headers): {values[0]}")
            if len(values) > 1:
                print(f"Second row (data): {values[1]}")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_get_sheet_info():
    """Example 2: Get sheet information"""
    print("\n" + "="*60)
    print("Example 2: Get Sheet Information")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    
    try:
        info = service.get_sheet_info(sheet_url)
        
        print(f"📊 Spreadsheet: {info.spreadsheet_title}")
        print(f"📄 Number of sheets: {len(info.sheets)}")
        
        for sheet in info.sheets:
            print(f"\n  Sheet: {sheet.title}")
            print(f"    ID: {sheet.sheet_id}")
            print(f"    Rows: {sheet.row_count}")
            print(f"    Columns: {sheet.column_count}")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_convert_values():
    """Example 3: Convert sheet values to dictionaries"""
    print("\n" + "="*60)
    print("Example 3: Convert Sheet Values to Dictionaries")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        # Read values
        values = service.get_values(sheet_url=sheet_url, sheet_name=sheet_name)
        
        # Convert to list of dictionaries (using first row as keys)
        data = service.convert_value_sheet(values, row_offset=0)
        
        print(f"✅ Converted {len(data)} rows to dictionaries")
        if data:
            print(f"\nFirst record: {data[0]}")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_update_single_cell():
    """Example 4: Update single cell (immediate)"""
    print("\n" + "="*60)
    print("Example 4: Update Single Cell (Immediate)")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        # Update cell at row 0, column 0 (will write to A2 due to header offset)
        result = service.update_values_multi_cells(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            sheet_val=[
                SheetValUpdateCell(idx_row=0, idx_col=0, content='Updated Value')
            ],
            immediate=True  # Execute immediately, don't queue
        )
        
        if result:
            print("✅ Cell updated successfully")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_update_multiple_cells():
    """Example 5: Update multiple cells at once"""
    print("\n" + "="*60)
    print("Example 5: Update Multiple Cells")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        # Update multiple cells
        cells_to_update = [
            SheetValUpdateCell(idx_row=0, idx_col=0, content='Name 1'),
            SheetValUpdateCell(idx_row=0, idx_col=1, content='Value 1'),
            SheetValUpdateCell(idx_row=1, idx_col=0, content='Name 2'),
            SheetValUpdateCell(idx_row=1, idx_col=1, content='Value 2'),
        ]
        
        result = service.update_values_multi_cells(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            sheet_val=cells_to_update,
            immediate=True
        )
        
        if result:
            print(f"✅ Updated {len(cells_to_update)} cells successfully")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_export_overwrite():
    """Example 6: Export data with Overwrite mode"""
    print("\n" + "="*60)
    print("Example 6: Export Data (Overwrite Mode)")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Export_Test'
    
    # Prepare data
    headers = ['ID', 'Name', 'Email', 'Status']
    data = [
        ['1', 'John Doe', 'john@example.com', 'Active'],
        ['2', 'Jane Smith', 'jane@example.com', 'Active'],
        ['3', 'Bob Johnson', 'bob@example.com', 'Inactive'],
    ]
    
    try:
        result = service.export(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            list_cols=headers,
            vals_export=data,
            type_export=ExportType.OVERWRITE
        )
        
        if result:
            print(f"✅ Exported {len(data)} rows with OVERWRITE mode")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_export_append():
    """Example 7: Export data with Append mode"""
    print("\n" + "="*60)
    print("Example 7: Export Data (Append Mode)")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Export_Test'
    
    # Prepare data (will be appended to existing data)
    headers = ['ID', 'Name', 'Email', 'Status']
    data = [
        ['4', 'Alice Brown', 'alice@example.com', 'Active'],
        ['5', 'Charlie Wilson', 'charlie@example.com', 'Active'],
    ]
    
    try:
        result = service.export(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            list_cols=headers,
            vals_export=data,
            type_export=ExportType.APPEND
        )
        
        if result:
            print(f"✅ Appended {len(data)} rows")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_update_with_row_offset():
    """Example 8: Update with row offset (skip rows)"""
    print("\n" + "="*60)
    print("Example 8: Update with Row Offset")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        # With row_offset=1, row 0 will actually write to row 3
        # (header at row 1, skip row 2, data starts at row 3)
        result = service.update_values_multi_cells(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            sheet_val=[
                SheetValUpdateCell(idx_row=0, idx_col=0, content='Offset Test')
            ],
            row_offset=1,  # Skip one row after header
            immediate=True
        )
        
        if result:
            print("✅ Cell updated with row offset")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_queue_based_updates():
    """Example 9: Queue-based batch updates"""
    print("\n" + "="*60)
    print("Example 9: Queue-based Batch Updates")
    print("="*60)
    
    # Initialize service with Redis queue enabled
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account',
        redis_host='localhost',
        redis_port=6379,
        enable_queue=True
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        print("Adding updates to queue...")
        
        # Add multiple updates to queue (not executed immediately)
        for i in range(5):
            service.update_values_multi_cells(
                sheet_url=sheet_url,
                sheet_name=sheet_name,
                sheet_val=[
                    SheetValUpdateCell(idx_row=i, idx_col=0, content=f'Queued {i}')
                ],
                immediate=False  # Add to queue
            )
        
        print("✅ Added 5 updates to queue")
        
        # Process all queued operations
        print("\nProcessing queued operations...")
        service.process_queued_operations()
        
        print("✅ Queue processing complete")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_service_account_rotation():
    """Example 10: Service account rotation with rate limiting"""
    print("\n" + "="*60)
    print("Example 10: Service Account Rotation")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account',
        service_account_files=[
            'automationservice-v1.json',
            'automationservice-v2.json',
            'automationservice-v3.json',
        ],
        redis_host='localhost',
        enable_queue=True,
        debug=True  # Enable debug logging to see rotation
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    print("Performing multiple read operations to test rotation...")
    
    try:
        # Perform multiple reads - service will automatically rotate accounts
        for i in range(10):
            values = service.get_values(sheet_url=sheet_url, sheet_name=sheet_name)
            print(f"  Read #{i+1}: {len(values)} rows")
            time.sleep(0.1)
        
        print("✅ Service account rotation working")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_column_utilities():
    """Example 11: Column name/index conversion utilities"""
    print("\n" + "="*60)
    print("Example 11: Column Utilities")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    # Index to column name
    print("\nColumn Index to Name:")
    for idx in [0, 1, 25, 26, 27, 701, 702]:
        col_name = service.convert_index_to_column_name(idx)
        print(f"  Index {idx} → Column {col_name}")
    
    # Column name to index
    print("\nColumn Name to Index:")
    for col_name in ['A', 'B', 'Z', 'AA', 'AB', 'ZZ', 'AAA']:
        idx = service.convert_column_name_to_index(col_name)
        print(f"  Column {col_name} → Index {idx}")


def example_find_row_by_value():
    """Example 12: Find row index by searching for value"""
    print("\n" + "="*60)
    print("Example 12: Find Row by Value")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        # Find row where column A contains "John Doe"
        row_idx = service.get_idx_row(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            col_name='A',  # Search in column A
            val='John Doe'
        )
        
        if row_idx > 0:
            print(f"✅ Found 'John Doe' at row {row_idx}")
        else:
            print("❌ Value not found")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_delete_row():
    """Example 13: Delete a row from sheet"""
    print("\n" + "="*60)
    print("Example 13: Delete Row")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        # Delete row at index 2 (3rd data row, row 4 in sheet including header)
        result = service.delete_row_sheet(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            sheet_row=2,
            row_offset=0
        )
        
        if result:
            print("✅ Row deleted successfully")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_bulk_update_matrix():
    """Example 14: Bulk update (matrix of values)"""
    print("\n" + "="*60)
    print("Example 14: Bulk Update Matrix")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account'
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        # Update a 3x3 matrix starting at row 0, column 0
        matrix_data = [
            ['A1', 'B1', 'C1'],
            ['A2', 'B2', 'C2'],
            ['A3', 'B3', 'C3'],
        ]
        
        result = service.update_values_multi_rows_multi_cols(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            values=matrix_data,
            start_row=0,
            start_col=0,
            immediate=True
        )
        
        if result:
            print(f"✅ Updated 3x3 matrix successfully")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def example_with_sheet_locking():
    """Example 15: Update with sheet locking"""
    print("\n" + "="*60)
    print("Example 15: Update with Sheet Locking")
    print("="*60)
    
    service = GoogleSheetService(
        service_accounts_dir='./tokens/service-account',
        redis_host='localhost',
        enable_queue=True
    )
    
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    sheet_name = 'Sheet1'
    
    try:
        # Lock sheet for 10 seconds during update
        result = service.update_values_multi_cells(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            sheet_val=[
                SheetValUpdateCell(idx_row=0, idx_col=0, content='Locked Update')
            ],
            immediate=True,
            time_lock_sheet=10  # Lock for 10 seconds
        )
        
        if result:
            print("✅ Update completed with sheet lock (10s)")
    
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples"""
    print("="*60)
    print("Google Sheets Service - Usage Examples")
    print("="*60)
    print("\nNote: Update sheet URLs and ensure service account files exist")
    print("before running these examples.\n")
    
    # Uncomment the examples you want to run:
    
    # Basic operations
    # example_basic_read()
    # example_get_sheet_info()
    # example_convert_values()
    
    # Update operations
    # example_update_single_cell()
    # example_update_multiple_cells()
    # example_update_with_row_offset()
    # example_bulk_update_matrix()
    
    # Export operations
    # example_export_overwrite()
    # example_export_append()
    
    # Advanced features
    # example_queue_based_updates()
    # example_service_account_rotation()
    # example_with_sheet_locking()
    
    # Utilities
    example_column_utilities()
    # example_find_row_by_value()
    # example_delete_row()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()


"""
Simple Google Sheets Demo
A minimal example to test the Google Sheets service
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodrive_gpm_package.services import (
    GoogleSheetService,
    GoogleSheetServiceException,
    SheetValUpdateCell,
    ExportType
)


def main():
    """Simple demo of Google Sheets functionality"""
    
    print("="*70)
    print("Google Sheets Service - Simple Demo")
    print("="*70)
    
    # ========== CONFIGURATION ==========
    # Update these values before running
    SHEET_URL = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
    SHEET_NAME = 'Sheet1'
    SERVICE_ACCOUNTS_DIR = './tokens/service-account'
    
    print("\n📝 Configuration:")
    print(f"  Service Accounts Dir: {SERVICE_ACCOUNTS_DIR}")
    print(f"  Sheet URL: {SHEET_URL}")
    print(f"  Sheet Name: {SHEET_NAME}")
    
    # Initialize service (without Redis/queue for simplicity)
    print("\n🔧 Initializing service...")
    try:
        service = GoogleSheetService(
            service_accounts_dir=SERVICE_ACCOUNTS_DIR,
            enable_queue=False,  # Disable queue for this demo
            debug=True
        )
        print("✅ Service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return
    
    # ========== TEST 1: Get Sheet Info ==========
    print("\n" + "="*70)
    print("TEST 1: Get Sheet Information")
    print("="*70)
    try:
        info = service.get_sheet_info(SHEET_URL)
        print(f"✅ Spreadsheet: {info.spreadsheet_title}")
        print(f"   Number of sheets: {len(info.sheets)}")
        for sheet in info.sheets:
            print(f"   - {sheet.title}: {sheet.row_count} rows x {sheet.column_count} cols")
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")
        return
    
    # ========== TEST 2: Read Values ==========
    print("\n" + "="*70)
    print("TEST 2: Read Sheet Values")
    print("="*70)
    try:
        values = service.get_values(
            sheet_url=SHEET_URL,
            sheet_name=SHEET_NAME
        )
        print(f"✅ Read {len(values)} rows")
        if values:
            print(f"   First row (headers): {values[0]}")
            if len(values) > 1:
                print(f"   Second row (data): {values[1]}")
        else:
            print("   ⚠️ Sheet is empty")
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")
        return
    
    # ========== TEST 3: Convert to Dictionaries ==========
    print("\n" + "="*70)
    print("TEST 3: Convert Values to Dictionaries")
    print("="*70)
    if values and len(values) > 1:
        try:
            data = service.convert_value_sheet(values, row_offset=0)
            print(f"✅ Converted {len(data)} rows to dictionaries")
            if data:
                print(f"   First record: {data[0]}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("⏭️ Skipped (not enough data)")
    
    # ========== TEST 4: Column Utilities ==========
    print("\n" + "="*70)
    print("TEST 4: Column Utilities")
    print("="*70)
    
    print("Column Index to Name:")
    for idx in [0, 1, 25, 26]:
        col_name = service.convert_index_to_column_name(idx)
        print(f"  Index {idx:3d} → Column '{col_name}'")
    
    print("\nColumn Name to Index:")
    for col_name in ['A', 'B', 'Z', 'AA']:
        idx = service.convert_column_name_to_index(col_name)
        print(f"  Column '{col_name:2s}' → Index {idx}")
    
    # ========== TEST 5: Update Cell (Optional) ==========
    print("\n" + "="*70)
    print("TEST 5: Update Cell (Optional - Uncomment to enable)")
    print("="*70)
    
    # Uncomment the code below to test cell update
    """
    try:
        result = service.update_values_multi_cells(
            sheet_url=SHEET_URL,
            sheet_name=SHEET_NAME,
            sheet_val=[
                SheetValUpdateCell(idx_row=0, idx_col=0, content='Test Update')
            ],
            immediate=True
        )
        if result:
            print("✅ Cell updated successfully")
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")
    """
    print("⏭️ Skipped (uncomment code to enable)")
    
    # ========== TEST 6: Export Data (Optional) ==========
    print("\n" + "="*70)
    print("TEST 6: Export Data (Optional - Uncomment to enable)")
    print("="*70)
    
    # Uncomment the code below to test export
    """
    headers = ['ID', 'Name', 'Value', 'Status']
    data = [
        ['1', 'Test 1', '100', 'Active'],
        ['2', 'Test 2', '200', 'Active'],
    ]
    
    try:
        result = service.export(
            sheet_url=SHEET_URL,
            sheet_name='TestExport',  # Change to your test sheet
            list_cols=headers,
            vals_export=data,
            type_export=ExportType.OVERWRITE
        )
        if result:
            print(f"✅ Exported {len(data)} rows")
    except GoogleSheetServiceException as e:
        print(f"❌ Error: {e}")
    """
    print("⏭️ Skipped (uncomment code to enable)")
    
    # ========== SUMMARY ==========
    print("\n" + "="*70)
    print("Demo Completed!")
    print("="*70)
    print("\n✅ Basic read operations tested successfully")
    print("💡 To test write operations:")
    print("   1. Uncomment TEST 5 or TEST 6 in the code")
    print("   2. Ensure your service account has edit permissions")
    print("   3. Run the script again")
    print("\n📚 For more examples, see: examples/google_sheets_usage.py")
    print("📖 For complete guide, see: docs/GOOGLE_SHEETS_QUICKSTART.md")
    print("="*70)


if __name__ == "__main__":
    main()


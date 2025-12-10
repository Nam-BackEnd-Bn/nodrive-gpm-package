"""
Google Sheets OAuth Helper Demo
Simple example showing OAuth2-based Google Sheets operations

This example demonstrates the simpler OAuth2-based helper for personal use.
For production/heavy usage with service accounts, see google_sheets_usage.py
"""

from nodrive_gpm_package import GoogleSheetOAuth, HelperGGSheet

# Example Google Sheets URL (replace with your own)
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
SHEET_NAME = "Sheet1"


def example_basic_read_write():
    """Basic read and write operations"""
    print("=" * 60)
    print("Example 1: Basic Read/Write Operations")
    print("=" * 60)
    
    # Initialize helper (will open browser for OAuth consent on first run)
    helper = GoogleSheetOAuth()
    
    # Read data from sheet
    print("\n📖 Reading sheet data...")
    data = helper.read_sheet(
        sheet_url=SHEET_URL,
        sheet_name=SHEET_NAME
    )
    
    if data:
        print(f"✅ Read {len(data)} rows")
        print("First 3 rows:")
        for i, row in enumerate(data[:3], 1):
            print(f"  Row {i}: {row}")
    else:
        print("❌ No data found or sheet is empty")
    
    # Write to specific cell
    print("\n✍️ Writing to cell...")
    result = helper.write_sheet(
        sheet_url=SHEET_URL,
        sheet_name=SHEET_NAME,
        row=0,  # 0-based index (becomes row 2 in sheet)
        col="A",
        value="Updated Value"
    )
    
    if result:
        print(f"✅ Cell updated successfully")
    else:
        print("❌ Failed to update cell")


def example_write_multiple_cells():
    """Write to multiple cells"""
    print("\n" + "=" * 60)
    print("Example 2: Write Multiple Cells")
    print("=" * 60)
    
    helper = GoogleSheetOAuth()
    
    # Write to different cells
    cells_to_update = [
        (0, "A", "Name"),
        (0, "B", "Age"),
        (0, "C", "City"),
        (1, "A", "John"),
        (1, "B", "25"),
        (1, "C", "New York"),
    ]
    
    print("\n✍️ Writing multiple cells...")
    for row, col, value in cells_to_update:
        helper.write_sheet(
            sheet_url=SHEET_URL,
            sheet_name=SHEET_NAME,
            row=row,
            col=col,
            value=value
        )
    
    print("✅ All cells updated")


def example_write_range():
    """Write data in bulk using write_range"""
    print("\n" + "=" * 60)
    print("Example 3: Write Range (Bulk Data)")
    print("=" * 60)
    
    helper = GoogleSheetOAuth()
    
    # Prepare data as 2D array
    data = [
        ["Product", "Price", "Stock", "Category"],
        ["Laptop", "999.99", "15", "Electronics"],
        ["Mouse", "29.99", "50", "Electronics"],
        ["Desk", "299.99", "8", "Furniture"],
        ["Chair", "199.99", "12", "Furniture"],
    ]
    
    print(f"\n✍️ Writing {len(data)} rows to sheet...")
    result = helper.write_range(
        sheet_url=SHEET_URL,
        sheet_name=SHEET_NAME,
        start_row=0,  # 0-based (becomes row 2 in sheet)
        start_col="A",
        values=data
    )
    
    if result:
        print(f"✅ Range written successfully")
        print(f"   Updated {result.get('updatedCells', 0)} cells")
    else:
        print("❌ Failed to write range")


def example_column_helpers():
    """Demonstrate column name conversion utilities"""
    print("\n" + "=" * 60)
    print("Example 4: Column Name Utilities")
    print("=" * 60)
    
    helper = GoogleSheetOAuth()
    
    print("\n📊 Column index to name conversion:")
    for i in [0, 1, 25, 26, 27, 51, 52, 701, 702]:
        col_name = helper.get_column_name(i)
        print(f"   Index {i:4d} -> Column '{col_name}'")
    
    print("\n📊 Column name to index conversion:")
    for col_name in ["A", "B", "Z", "AA", "AB", "AZ", "BA", "ZZ"]:
        idx = helper._column_name_to_index(col_name)
        print(f"   Column '{col_name:3s}' -> Index {idx}")


def example_with_custom_paths():
    """Initialize helper with custom credential paths"""
    print("\n" + "=" * 60)
    print("Example 5: Custom Credential Paths")
    print("=" * 60)
    
    # Initialize with custom paths
    helper = GoogleSheetOAuth(
        credentials_file="path/to/custom/oauth.json",
        token_file="path/to/custom/token.pickle"
    )
    
    print("✅ Helper initialized with custom paths")
    print(f"   Credentials: {helper.credentials_file}")
    print(f"   Token cache: {helper.token_file}")


def example_backward_compatibility():
    """Using the HelperGGSheet alias (backward compatibility)"""
    print("\n" + "=" * 60)
    print("Example 6: Backward Compatibility (HelperGGSheet)")
    print("=" * 60)
    
    # Use old class name (alias for GoogleSheetOAuth)
    helper = HelperGGSheet()
    
    print("✅ HelperGGSheet is an alias for GoogleSheetOAuth")
    print(f"   Class type: {type(helper).__name__}")
    
    # All methods work the same
    data = helper.read_sheet(
        sheet_url=SHEET_URL,
        sheet_name=SHEET_NAME
    )
    
    print(f"✅ Read {len(data) if data else 0} rows using HelperGGSheet alias")


def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "=" * 60)
    print("Example 7: Error Handling")
    print("=" * 60)
    
    helper = GoogleSheetOAuth()
    
    print("\n🧪 Testing with invalid sheet URL...")
    data = helper.read_sheet(
        sheet_url="https://invalid-url.com",
        sheet_name="Sheet1"
    )
    print(f"   Result: {data}")  # Should return empty list
    
    print("\n🧪 Testing with non-existent sheet name...")
    data = helper.read_sheet(
        sheet_url=SHEET_URL,
        sheet_name="NonExistentSheet"
    )
    print(f"   Result: {data}")  # Should return empty list and print error


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("🚀 Google Sheets OAuth Helper Demo")
    print("=" * 60)
    print("\nIMPORTANT: Before running, update SHEET_URL with your sheet ID")
    print("=" * 60)
    
    # Uncomment the examples you want to run
    
    # example_basic_read_write()
    # example_write_multiple_cells()
    # example_write_range()
    # example_column_helpers()
    # example_with_custom_paths()
    # example_backward_compatibility()
    # example_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ Demo completed")
    print("=" * 60)


if __name__ == "__main__":
    main()


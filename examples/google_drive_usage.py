"""
Google Drive Service Usage Examples
Demonstrates file upload, folder management, sharing, and storage operations
"""

import os
from pathlib import Path
from nodrive_gpm_package import (
    GoogleDriveService,
    GoogleDriveServiceException,
)


def example_basic_operations():
    """
    Example 1: Basic file upload and storage info
    """
    print("=" * 60)
    print("Example 1: Basic File Upload and Storage Info")
    print("=" * 60)
    
    try:
        # Initialize service with credentials
        # Place your service account JSON file in 'tokens/drive.json'
        service = GoogleDriveService(key_file='tokens/drive.json')
        
        # Get storage information
        print("\n📊 Getting storage information...")
        storage = service.get_storage_info()
        print(f"✅ Storage retrieved: {storage.formatted_used} / {storage.formatted_total}")
        
        # Upload a file
        print("\n📤 Uploading file...")
        result = service.upload_file(
            file_path_upload='path/to/your/file.txt',
            folder_store='TestFolder',
            file_name='my_file.txt'  # Optional: rename file
        )
        
        print(f"✅ File uploaded successfully!")
        print(f"   File ID: {result.id}")
        print(f"   View Link: {result.web_view_link}")
        
    except GoogleDriveServiceException as e:
        print(f"❌ Error: {e}")
    except FileNotFoundError:
        print("❌ Please create 'tokens/drive.json' with your service account credentials")


def example_folder_hierarchy():
    """
    Example 2: Upload to nested folder structure
    """
    print("\n" + "=" * 60)
    print("Example 2: Upload to Nested Folders")
    print("=" * 60)
    
    try:
        service = GoogleDriveService(key_file='tokens/drive.json')
        
        # Upload to nested folder structure (will be created automatically)
        print("\n📤 Uploading to nested folders...")
        result = service.upload_file(
            file_path_upload='path/to/your/document.pdf',
            folder_store='Projects/2024/Reports',  # Creates hierarchy
            file_name='annual_report.pdf'
        )
        
        print(f"✅ File uploaded to nested structure!")
        print(f"   Folder structure: Projects → 2024 → Reports")
        
    except GoogleDriveServiceException as e:
        print(f"❌ Error: {e}")


def example_share_operations():
    """
    Example 3: Upload and share with email
    """
    print("\n" + "=" * 60)
    print("Example 3: Upload and Share with Email")
    print("=" * 60)
    
    try:
        service = GoogleDriveService(key_file='tokens/drive.json')
        
        # Upload and share with specific email
        print("\n📤 Uploading and sharing file...")
        result = service.upload_file_and_share(
            file_path_upload='path/to/your/file.txt',
            folder_store='SharedFolder',
            share_with_email='colleague@example.com',
            role='reader'  # Options: 'reader', 'writer', 'owner'
        )
        
        print(f"✅ File uploaded and shared!")
        print(f"   Shared with: colleague@example.com")
        print(f"   Permission: reader")
        
        # Share an existing folder
        print("\n📁 Sharing existing folder...")
        folder_id = service.get_folder_id_by_path('SharedFolder')
        service.share_folder_with_email(
            folder_id=folder_id,
            email_address='team@example.com',
            role='writer'
        )
        
        print(f"✅ Folder shared with team@example.com as writer")
        
    except GoogleDriveServiceException as e:
        print(f"❌ Error: {e}")


def example_list_and_manage():
    """
    Example 4: List files and manage them
    """
    print("\n" + "=" * 60)
    print("Example 4: List and Manage Files")
    print("=" * 60)
    
    try:
        service = GoogleDriveService(key_file='tokens/drive.json')
        
        # List files in root
        print("\n📂 Listing files in root folder...")
        files = service.list_files_in_folder('root')
        
        print(f"✅ Found {len(files)} items in root")
        for file in files[:5]:  # Show first 5
            print(f"   - {file.name} ({file.mime_type})")
        
        # Check if file exists
        print("\n🔍 Checking if file exists...")
        folder_id = service.get_folder_id_by_path('TestFolder')
        file_id = service.file_exists_in_folder('my_file.txt', folder_id)
        
        if file_id:
            print(f"✅ File exists with ID: {file_id}")
            
            # Make it public
            print("\n🌍 Making file public...")
            service.make_file_public(file_id)
            print("✅ File is now public (anyone with link can view)")
        else:
            print("❌ File not found")
        
    except GoogleDriveServiceException as e:
        print(f"❌ Error: {e}")


def example_ownership_transfer():
    """
    Example 5: Transfer ownership
    """
    print("\n" + "=" * 60)
    print("Example 5: Transfer Ownership")
    print("=" * 60)
    
    try:
        service = GoogleDriveService(key_file='tokens/drive.json')
        
        # Upload a file
        print("\n📤 Uploading file...")
        result = service.upload_file(
            file_path_upload='path/to/your/file.txt',
            folder_store='TransferTest'
        )
        
        # Transfer file ownership
        print("\n👑 Transferring file ownership...")
        service.transfer_file_ownership(
            file_id=result.id,
            new_owner_email='newowner@example.com'
        )
        
        print(f"✅ File ownership transferred!")
        print(f"   New owner: newowner@example.com")
        print(f"   Note: File now counts against their storage quota")
        
        # Transfer folder ownership
        print("\n👑 Transferring folder ownership...")
        folder_id = service.get_folder_id_by_path('TransferTest')
        service.transfer_folder_ownership(
            folder_id=folder_id,
            new_owner_email='newowner@example.com'
        )
        
        print(f"✅ Folder ownership transferred!")
        
    except GoogleDriveServiceException as e:
        print(f"❌ Error: {e}")


def example_context_manager():
    """
    Example 6: Using context manager
    """
    print("\n" + "=" * 60)
    print("Example 6: Using Context Manager")
    print("=" * 60)
    
    try:
        # Use with context manager for automatic cleanup
        with GoogleDriveService(key_file='tokens/drive.json') as service:
            storage = service.get_storage_info()
            print(f"✅ Storage: {storage.formatted_used} / {storage.formatted_total}")
            
            # Upload file
            result = service.upload_file(
                file_path_upload='path/to/your/file.txt',
                folder_store='ContextTest'
            )
            
            print(f"✅ File uploaded: {result.name}")
        
        print("✅ Context manager closed automatically")
        
    except GoogleDriveServiceException as e:
        print(f"❌ Error: {e}")


def example_batch_upload():
    """
    Example 7: Batch upload multiple files
    """
    print("\n" + "=" * 60)
    print("Example 7: Batch Upload Multiple Files")
    print("=" * 60)
    
    try:
        service = GoogleDriveService(key_file='tokens/drive.json')
        
        # List of files to upload
        files_to_upload = [
            {'path': 'file1.txt', 'folder': 'Batch/Set1'},
            {'path': 'file2.pdf', 'folder': 'Batch/Set1'},
            {'path': 'file3.docx', 'folder': 'Batch/Set2'},
        ]
        
        print(f"\n📤 Uploading {len(files_to_upload)} files...")
        
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
                print(f"❌ Failed to upload {file_info['path']}: {e}")
        
        print(f"\n✅ Successfully uploaded {len(results)}/{len(files_to_upload)} files")
        
    except GoogleDriveServiceException as e:
        print(f"❌ Error: {e}")


def example_delete_file():
    """
    Example 8: Delete a file
    """
    print("\n" + "=" * 60)
    print("Example 8: Delete File")
    print("=" * 60)
    
    try:
        service = GoogleDriveService(key_file='tokens/drive.json')
        
        # Check if file exists first
        folder_id = service.get_folder_id_by_path('TestFolder')
        file_id = service.file_exists_in_folder('my_file.txt', folder_id)
        
        if file_id:
            print(f"\n🗑️ Deleting file with ID: {file_id}")
            service.delete_file(file_id)
            print("✅ File deleted successfully")
        else:
            print("❌ File not found")
            
        # Note: Only the owner can delete files
        # If ownership was transferred, the original service account cannot delete
        
    except GoogleDriveServiceException as e:
        print(f"❌ Error: {e}")


def main():
    """
    Run all examples
    """
    print("\n🚀 Google Drive Service Examples\n")
    
    # Check if credentials file exists
    creds_path = Path('tokens/drive.json')
    if not creds_path.exists():
        print("=" * 60)
        print("⚠️  SETUP REQUIRED")
        print("=" * 60)
        print("\nTo use Google Drive Service, you need:")
        print("1. Create a Google Cloud Project")
        print("2. Enable Google Drive API")
        print("3. Create a Service Account")
        print("4. Download the service account JSON key")
        print("5. Save it as 'tokens/drive.json'")
        print("\nFor detailed instructions, visit:")
        print("https://cloud.google.com/iam/docs/creating-managing-service-account-keys")
        print("=" * 60)
        return
    
    # Run examples (comment out examples you don't want to run)
    try:
        example_basic_operations()
        # example_folder_hierarchy()
        # example_share_operations()
        # example_list_and_manage()
        # example_ownership_transfer()
        # example_context_manager()
        # example_batch_upload()
        # example_delete_file()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()


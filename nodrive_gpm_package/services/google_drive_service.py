"""
Google Drive Service
Provides comprehensive Google Drive operations including file upload, download, 
folder management, sharing, and storage information.
"""

import os
import math
from typing import Optional, List, Dict, Any, Literal
from pathlib import Path
from dataclasses import dataclass

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
except ImportError:
    raise ImportError(
        "Google Drive dependencies not installed. "
        "Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    )


@dataclass
class UploadFileResult:
    """Result of file upload operation"""
    id: str
    name: str
    web_view_link: Optional[str] = None
    web_content_link: Optional[str] = None


@dataclass
class FileInfo:
    """Information about a file in Google Drive"""
    id: str
    name: str
    mime_type: str
    web_view_link: Optional[str] = None
    parents: Optional[List[str]] = None


@dataclass
class StorageInfo:
    """Storage quota information"""
    used: int
    total: int
    used_in_drive: int
    percentage: float
    formatted_used: str
    formatted_total: str
    formatted_used_in_drive: str


RoleShare = Literal['reader', 'writer', 'owner']


class GoogleDriveServiceException(Exception):
    """Exception raised for Google Drive service errors"""
    pass


class GoogleDriveService:
    """
    Google Drive Service with comprehensive file and folder management
    
    This service provides:
    - File upload/download operations
    - Folder creation and hierarchy management
    - File and folder sharing with permissions
    - Storage quota information
    - Ownership transfer capabilities
    
    Usage:
        # Initialize with service account credentials
        service = GoogleDriveService(key_file='path/to/service_account.json')
        
        # Upload a file
        result = service.upload_file(
            file_path_upload='local/file.txt',
            folder_store='MyFolder/SubFolder',
            file_name='renamed_file.txt'  # Optional
        )
        
        # Upload and share with email
        result = service.upload_file_and_share(
            file_path_upload='local/file.txt',
            folder_store='MyFolder',
            share_with_email='user@example.com',
            role='reader'
        )
        
        # Get storage info
        storage = service.get_storage_info()
        print(f"Used: {storage.formatted_used} / {storage.formatted_total}")
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
    ]
    
    def __init__(self, key_file: str):
        """
        Initialize Google Drive Service
        
        Args:
            key_file: Path to service account JSON credentials file
            
        Raises:
            GoogleDriveServiceException: If credentials file not found or invalid
        """
        self.key_file = Path(key_file)
        
        if not self.key_file.exists():
            raise GoogleDriveServiceException(
                f"Service account key file not found: {key_file}"
            )
        
        self._drive_service = None
    
    def _get_drive_client(self):
        """
        Get or create Google Drive API client
        
        Returns:
            Google Drive API service instance
        """
        if self._drive_service is None:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    str(self.key_file),
                    scopes=self.SCOPES
                )
                self._drive_service = build('drive', 'v3', credentials=credentials)
            except Exception as e:
                raise GoogleDriveServiceException(
                    f"Failed to initialize Google Drive client: {e}"
                )
        
        return self._drive_service
    
    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """
        Format bytes to human-readable format
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string (e.g., "1.5 GB")
        """
        if bytes_value == 0:
            return '0 Bytes'
        
        k = 1024
        sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
        i = math.floor(math.log(bytes_value) / math.log(k))
        
        return f"{round(bytes_value / math.pow(k, i), 2)} {sizes[i]}"
    
    def get_storage_info(self) -> StorageInfo:
        """
        Get Google Drive storage quota information
        
        Returns:
            StorageInfo object with storage details
            
        Raises:
            GoogleDriveServiceException: If unable to retrieve storage info
        """
        try:
            drive = self._get_drive_client()
            
            response = drive.about().get(fields='storageQuota').execute()
            quota = response.get('storageQuota', {})
            
            if not quota:
                raise GoogleDriveServiceException(
                    'Unable to retrieve storage quota information'
                )
            
            used = int(quota.get('usage', 0))
            total = int(quota.get('limit', 0))
            used_in_drive = int(quota.get('usageInDrive', 0))
            
            percentage = (used / total * 100) if total > 0 else 0
            
            storage_info = StorageInfo(
                used=used,
                total=total,
                used_in_drive=used_in_drive,
                percentage=round(percentage, 2),
                formatted_used=self._format_bytes(used),
                formatted_total=self._format_bytes(total),
                formatted_used_in_drive=self._format_bytes(used_in_drive)
            )
            
            print('📊📊📊 Google Drive Storage Information:')
            print(f'💾 Total Storage: {storage_info.formatted_total}')
            print(f'📈 Used Storage: {storage_info.formatted_used} ({storage_info.percentage}%)')
            print(f'📁 Used in Drive: {storage_info.formatted_used_in_drive}')
            print(f'🆓 Available: {self._format_bytes(total - used)}')
            
            return storage_info
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to get storage information: {e}"
            )
    
    def _get_or_create_folder(self, folder_name: str, parent_id: str = 'root') -> str:
        """
        Get existing folder or create new one
        
        Args:
            folder_name: Name of the folder
            parent_id: ID of parent folder (default: 'root')
            
        Returns:
            Folder ID
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            drive = self._get_drive_client()
            
            # Search for existing folder
            query = (
                f"name='{folder_name}' and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"'{parent_id}' in parents and "
                f"trashed=false"
            )
            
            response = drive.files().list(
                q=query,
                fields='files(id, name)',
                spaces='drive'
            ).execute()
            
            folders = response.get('files', [])
            
            if folders:
                # Folder exists
                folder_id = folders[0]['id']
                print(f"✅ Found existing folder: {folder_name} (ID: {folder_id})")
                return folder_id
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = drive.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder['id']
            print(f"📁 Created new folder: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to get or create folder '{folder_name}': {e}"
            )
    
    def _create_folder_hierarchy(self, folder_path: str) -> str:
        """
        Create folder hierarchy from path string
        
        Args:
            folder_path: Folder path (e.g., "folder1/folder2/folder3")
            
        Returns:
            ID of the final folder in hierarchy
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            if not folder_path or folder_path in ('/', ''):
                return 'root'
            
            # Split path into folder names
            folders = [f.strip() for f in folder_path.split('/') if f.strip()]
            current_parent_id = 'root'
            
            # Create each folder in hierarchy
            for folder_name in folders:
                current_parent_id = self._get_or_create_folder(
                    folder_name,
                    current_parent_id
                )
            
            print(f"🎯 Folder hierarchy created: {folder_path} (Final ID: {current_parent_id})")
            return current_parent_id
            
        except Exception as e:
            raise GoogleDriveServiceException(
                f"Failed to create folder hierarchy '{folder_path}': {e}"
            )
    
    def upload_file(
        self,
        file_path_upload: str,
        folder_store: str,
        file_name: Optional[str] = None
    ) -> UploadFileResult:
        """
        Upload file to Google Drive
        
        Args:
            file_path_upload: Absolute path to local file
            folder_store: Destination folder path on Google Drive (e.g., "Test/SubFolder")
            file_name: Custom file name (optional, uses original name if not provided)
            
        Returns:
            UploadFileResult with file information
            
        Raises:
            GoogleDriveServiceException: If upload fails
        """
        try:
            # Normalize and validate path
            file_path = Path(file_path_upload).resolve()
            
            print(f'🔍 Uploading file: {file_path}')
            print(f'🔍 File exists: {file_path.exists()}')
            
            if not file_path.exists():
                # Debug information
                print(f'🔍 Directory: {file_path.parent}')
                print(f'🔍 Filename: {file_path.name}')
                print(f'🔍 Directory exists: {file_path.parent.exists()}')
                
                if file_path.parent.exists():
                    files_in_dir = list(file_path.parent.iterdir())
                    print(f'🔍 Files in directory: {files_in_dir}')
                
                raise GoogleDriveServiceException(
                    f"File does not exist: {file_path}. "
                    f"Please check the file path and ensure the file exists."
                )
            
            # Use original filename if not provided
            final_file_name = file_name or file_path.name
            
            drive = self._get_drive_client()
            
            # Create folder hierarchy
            folder_id = self._create_folder_hierarchy(folder_store)
            
            # File metadata
            file_metadata = {
                'name': final_file_name,
                'parents': [folder_id]
            }
            
            # Create media upload
            media = MediaFileUpload(
                str(file_path),
                mimetype='application/octet-stream',
                resumable=True
            )
            
            print(f'🚀 Starting upload: {final_file_name} to folder: {folder_store}')
            
            # Upload file
            file = drive.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()
            
            result = UploadFileResult(
                id=file['id'],
                name=file['name'],
                web_view_link=file.get('webViewLink'),
                web_content_link=file.get('webContentLink')
            )
            
            # Always make file public
            self.make_file_public(result.id)
            
            print('🚀🚀🚀 File uploaded successfully:')
            print(f'📁 File ID: {result.id}')
            print(f'📄 File Name: {result.name}')
            print(f'🔗 Web View Link: {result.web_view_link}')
            print(f'💾 Web Content Link: {result.web_content_link}')
            print(f'🌍 Public: Always enabled')
            
            return result
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to upload file to Google Drive: {e}"
            )
        except Exception as e:
            raise GoogleDriveServiceException(
                f"Failed to upload file: {e}"
            )
    
    def upload_file_and_share(
        self,
        file_path_upload: str,
        folder_store: str,
        file_name: Optional[str] = None,
        share_with_email: str = 'supercanh1@gmail.com',
        role: RoleShare = 'reader'
    ) -> UploadFileResult:
        """
        Upload file and automatically share with specified email
        
        Args:
            file_path_upload: Absolute path to local file
            folder_store: Destination folder path on Google Drive
            file_name: Custom file name (optional)
            share_with_email: Email to share with (default: 'supercanh1@gmail.com')
            role: Permission role ('reader', 'writer', or 'owner')
            
        Returns:
            UploadFileResult with file information
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            # Upload file normally
            result = self.upload_file(
                file_path_upload=file_path_upload,
                folder_store=folder_store,
                file_name=file_name
            )
            
            # Get folder ID and share it
            folder_id = self.get_folder_id_by_path(folder_store)
            self.share_folder_with_email(folder_id, share_with_email, role)
            
            return result
            
        except Exception as e:
            raise GoogleDriveServiceException(
                f"Failed to upload and share: {e}"
            )
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from Google Drive (only owner can delete)
        
        Args:
            file_id: ID of file to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            GoogleDriveServiceException: If deletion fails
        """
        try:
            drive = self._get_drive_client()
            
            drive.files().delete(fileId=file_id).execute()
            
            print(f'🗑️🗑️🗑️ File with ID {file_id} deleted successfully')
            return True
            
        except HttpError as e:
            error_msg = str(e)
            print(f'❌ Error deleting file with ID {file_id}: {error_msg}')
            
            if 'forbidden' in error_msg.lower() or 'permission' in error_msg.lower():
                print(
                    '💡 Hint: File ownership may have been transferred. '
                    'Only the current owner can delete this file.'
                )
            
            raise GoogleDriveServiceException(
                f"Failed to delete file from Google Drive: {e}"
            )
    
    def list_files_in_folder(self, folder_id: str = 'root') -> List[FileInfo]:
        """
        List all files in a specific folder
        
        Args:
            folder_id: ID of folder to list (default: 'root')
            
        Returns:
            List of FileInfo objects
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            drive = self._get_drive_client()
            
            query = f"'{folder_id}' in parents and trashed=false"
            
            response = drive.files().list(
                q=query,
                fields='files(id, name, mimeType, webViewLink, parents)',
                orderBy='name'
            ).execute()
            
            files = response.get('files', [])
            
            result = [
                FileInfo(
                    id=file['id'],
                    name=file['name'],
                    mime_type=file['mimeType'],
                    web_view_link=file.get('webViewLink'),
                    parents=file.get('parents')
                )
                for file in files
            ]
            
            print(f'📂 Found {len(result)} items in folder ID: {folder_id}')
            
            if not result:
                print(f'📂 No files or folders found in folder ID: {folder_id}')
            else:
                print(f'📂📂📂 Files and folders in folder ID {folder_id}:')
                for item in result:
                    print(f'📄 Name: {item.name}')
                    print(f'🆔 ID: {item.id}')
                    print(f'📋 Type: {item.mime_type}')
                    print(f'🔗 Link: {item.web_view_link or "No link"}')
                    print(f'📁 Parents: {", ".join(item.parents) if item.parents else "Root"}')
                    print('---')
            
            return result
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to list files in Google Drive folder: {e}"
            )
    
    def make_file_public(self, file_id: str) -> bool:
        """
        Make file public (anyone with link can view)
        
        Args:
            file_id: ID of file to make public
            
        Returns:
            True if successful
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            drive = self._get_drive_client()
            
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            drive.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            print(f'🌍 File {file_id} is now public (anyone with link can view)')
            return True
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to make file public: {e}"
            )
    
    def transfer_file_ownership(
        self,
        file_id: str,
        new_owner_email: str,
        role: RoleShare = 'reader'
    ) -> bool:
        """
        Transfer file ownership to another email
        
        Args:
            file_id: ID of file to transfer
            new_owner_email: Email of new owner
            role: Permission role (default: 'reader')
            
        Returns:
            True if successful
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            drive = self._get_drive_client()
            
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': new_owner_email
            }
            
            drive.permissions().create(
                fileId=file_id,
                body=permission,
                transferOwnership=True,
                sendNotificationEmail=True  # Required for ownership transfer
            ).execute()
            
            print(f'👑 File {file_id} ownership transferred to {new_owner_email}')
            print(f'💾 File now counts against {new_owner_email}\'s storage quota')
            print(f'📧 Notification email sent to {new_owner_email} (required for ownership transfer)')
            
            return True
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to transfer file ownership: {e}"
            )
    
    def transfer_folder_ownership(self, folder_id: str, new_owner_email: str) -> bool:
        """
        Transfer folder ownership to another email
        
        Args:
            folder_id: ID of folder to transfer
            new_owner_email: Email of new owner
            
        Returns:
            True if successful
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            drive = self._get_drive_client()
            
            permission = {
                'type': 'user',
                'role': 'owner',
                'emailAddress': new_owner_email
            }
            
            drive.permissions().create(
                fileId=folder_id,
                body=permission,
                transferOwnership=True,
                sendNotificationEmail=True  # Required for ownership transfer
            ).execute()
            
            print(f'👑 Folder {folder_id} ownership transferred to {new_owner_email}')
            print(f'📧 Notification email sent to {new_owner_email} (required for ownership transfer)')
            
            return True
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to transfer folder ownership: {e}"
            )
    
    def share_folder_with_email(
        self,
        folder_id: str,
        email_address: str,
        role: RoleShare = 'writer'
    ) -> bool:
        """
        Share folder with specified email
        
        Args:
            folder_id: ID of folder to share
            email_address: Email to share with
            role: Permission role ('reader', 'writer', or 'owner')
            
        Returns:
            True if successful
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            drive = self._get_drive_client()
            
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email_address
            }
            
            # Configure based on role
            if role == 'owner':
                # Ownership transfer requires notification
                drive.permissions().create(
                    fileId=folder_id,
                    body=permission,
                    transferOwnership=True,
                    sendNotificationEmail=True
                ).execute()
                
                print(f'✅ Folder {folder_id} shared with {email_address} as {role}')
                print(f'👑 Ownership transferred - folder now counts against {email_address}\'s quota')
                print(f'📧 Notification email sent to {email_address} (required for ownership transfer)')
            else:
                # Other roles don't need notification
                drive.permissions().create(
                    fileId=folder_id,
                    body=permission,
                    sendNotificationEmail=False
                ).execute()
                
                print(f'✅ Folder {folder_id} shared with {email_address} as {role}')
            
            return True
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to share folder: {e}"
            )
    
    def get_folder_id_by_path(self, folder_path: str) -> str:
        """
        Get folder ID by path (utility method)
        
        Args:
            folder_path: Folder path (e.g., "folder1/folder2/folder3")
            
        Returns:
            Folder ID
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            return self._create_folder_hierarchy(folder_path)
        except Exception as e:
            raise GoogleDriveServiceException(
                f"Failed to get folder ID: {e}"
            )
    
    def file_exists_in_folder(
        self,
        file_name: str,
        folder_id: str = 'root'
    ) -> Optional[str]:
        """
        Check if file exists in specific folder
        
        Args:
            file_name: Name of file to check
            folder_id: ID of folder to check (default: 'root')
            
        Returns:
            File ID if exists, None otherwise
            
        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            drive = self._get_drive_client()
            
            query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
            
            response = drive.files().list(
                q=query,
                fields='files(id, name)'
            ).execute()
            
            files = response.get('files', [])
            
            if files:
                file_id = files[0]['id']
                print(f'✅ File exists: {file_name} (ID: {file_id})')
                return file_id
            
            return None
            
        except HttpError as e:
            raise GoogleDriveServiceException(
                f"Failed to check file existence: {e}"
            )
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self._drive_service = None


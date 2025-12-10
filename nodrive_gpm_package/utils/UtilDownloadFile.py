import shutil
import base64
import os
from typing import Optional
import uuid
import re
from datetime import datetime
from urllib.parse import urlparse, unquote
from pathlib import Path
import nodriver as nd


class UniversalDownloader:
    """
    Universal downloader for all file types and URL types
    """

    # Mapping MIME types to file extensions
    MIME_TO_EXT = {
        # Images
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "image/bmp": ".bmp",
        "image/ico": ".ico",
        "image/tiff": ".tiff",
        # Videos
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/ogg": ".ogg",
        "video/avi": ".avi",
        "video/mov": ".mov",
        "video/wmv": ".wmv",
        "video/flv": ".flv",
        "video/mkv": ".mkv",
        "video/m4v": ".m4v",
        "video/3gp": ".3gp",
        # Audio
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "audio/ogg": ".ogg",
        "audio/aac": ".aac",
        "audio/flac": ".flac",
        "audio/m4a": ".m4a",
        "audio/wma": ".wma",
        "audio/opus": ".opus",
        # Documents
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.ms-powerpoint": ".ppt",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        "text/plain": ".txt",
        "text/html": ".html",
        "text/css": ".css",
        "text/javascript": ".js",
        "application/javascript": ".js",
        "application/json": ".json",
        "application/xml": ".xml",
        "text/xml": ".xml",
        # Archives
        "application/zip": ".zip",
        "application/x-rar-compressed": ".rar",
        "application/x-7z-compressed": ".7z",
        "application/x-tar": ".tar",
        "application/gzip": ".gz",
        # Others
        "application/octet-stream": ".bin",
        "application/x-executable": ".exe",
        "application/x-msi": ".msi",
        "application/x-deb": ".deb",
        "application/x-rpm": ".rpm",
    }

    @staticmethod
    def detect_url_type(url: str) -> str:
        """
        Detect URL type
        """
        url_lower = url.lower().strip()

        if url_lower.startswith("data:"):
            return "base64"
        elif url_lower.startswith("blob:"):
            return "blob"
        elif url_lower.startswith(("http://", "https://")):
            return "http"
        elif url_lower.startswith("ftp://"):
            return "ftp"
        elif url_lower.startswith("file://"):
            return "file"
        else:
            return "unknown"

    @staticmethod
    def extract_filename_from_url(url: str) -> str:
        """
        Extract filename from URL
        """
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path)
            filename = os.path.basename(path)

            if filename and "." in filename:
                return filename

            # If no filename in URL, generate one
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            return f"downloaded_{timestamp}_{unique_id}"

        except Exception:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            return f"downloaded_{timestamp}_{unique_id}"

    @staticmethod
    def get_file_extension(content_type: str, url: str = None) -> str:
        """
        Get file extension from content type or URL
        """
        if content_type and content_type in UniversalDownloader.MIME_TO_EXT:
            return UniversalDownloader.MIME_TO_EXT[content_type]

        if url:
            # Try to get extension from URL
            parsed = urlparse(url)
            path = unquote(parsed.path)
            _, ext = os.path.splitext(path)
            if ext:
                return ext.lower()

        # Default extension
        return ".bin"

    @staticmethod
    async def download_http_url(url: str, dir_store: str) -> str:
        """
        Download HTTP/HTTPS URL using requests
        """
        import requests

        try:
            # Get filename from URL
            filename = UniversalDownloader.extract_filename_from_url(url)

            # Download file
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Get content type and determine extension
            content_type = (
                response.headers.get("content-type", "").split(";")[0].strip()
            )
            extension = UniversalDownloader.get_file_extension(content_type, url)

            # Ensure filename has extension
            if not filename.endswith(extension):
                filename = filename + extension

            file_path = os.path.join(dir_store, filename)

            # Write file
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = os.path.getsize(file_path)
            # print(f"✅ HTTP download successful: {file_path} ({file_size} bytes)")
            return file_path

        except Exception as e:
            raise Exception(f"HTTP download failed: {e}")

    @staticmethod
    async def download_base64_url(url: str, dir_store: str) -> str:
        """
        Download data URL (base64)
        """
        try:
            # Parse data URL: data:mime_type;base64,data
            if not url.startswith("data:"):
                raise Exception("Invalid data URL format")

            # Split header and data
            header, data = url.split(",", 1)

            # Extract mime type
            mime_match = re.search(r"data:([^;]+)", header)
            mime_type = (
                mime_match.group(1) if mime_match else "application/octet-stream"
            )

            # Get extension
            extension = UniversalDownloader.get_file_extension(mime_type)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"base64_{timestamp}_{unique_id}{extension}"
            file_path = os.path.join(dir_store, filename)

            # Decode base64
            file_data = base64.b64decode(data)

            # Write file
            with open(file_path, "wb") as f:
                f.write(file_data)

            # print(
            #     f"✅ Base64 download successful: {file_path} ({len(file_data)} bytes)"
            # )
            return file_path

        except Exception as e:
            raise Exception(f"Base64 download failed: {e}")

    @staticmethod
    async def download_image_blog(tab, blob_url: str, dir_store: str):
        """
        Phương pháp đã sửa lại cho nodriver - sử dụng Promise thay vì async callback
        """
        try:
            os.makedirs(dir_store, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"blob_image_{timestamp}_{unique_id}.jpg"
            file_path = os.path.join(dir_store, filename)

            print(f"Downloading blob: {blob_url}")

            # JavaScript sử dụng Promise thay vì callback (nodriver style)
            js_code = f"""
            (async () => {{
                const toBase64 = function(buffer) {{
                    const bytes = new Uint8Array(buffer);
                    const binary = Array.from(bytes).map(b => String.fromCharCode(b)).join('');
                    return btoa(binary);
                }};
                
                try {{
                    const response = await fetch('{blob_url}');
                    if (!response.ok) {{
                        throw new Error('HTTP ' + response.status);
                    }}
                    
                    const arrayBuffer = await response.arrayBuffer();
                    return toBase64(arrayBuffer);
                }} catch (error) {{
                    throw error;
                }}
            }})()
            """

            # Sử dụng await_promise=True để chờ Promise resolve
            result = await tab.evaluate(js_code, await_promise=True)

            # Kiểm tra kết quả
            if not result or not isinstance(result, str):
                raise Exception(f"Invalid result: {result}")

            # Decode base64 và lưu file
            try:
                image_data = base64.b64decode(result)

                with open(file_path, "wb") as f:
                    f.write(image_data)

                print(f"✅ Downloaded successfully: {file_path}")
                print(f"File size: {len(image_data)} bytes")
                return file_path

            except Exception as decode_error:
                raise Exception(f"Failed to decode base64: {decode_error}")

        except Exception as e:
            print(f"❌ Error downloading blob: {e}")
            raise e


# async def download(tab: nd.Tab, url: str, dir_store: str, new_name_file: str) -> str:
#     """
#     Universal download function for all file types and URL types

#     Args:
#         tab: nodriver tab object (can be None for HTTP/Base64 downloads)
#         url: URL to download (HTTP, HTTPS, blob, data URL)
#         dir_store: Directory to store the downloaded file

#     Returns:
#         str: Path to the downloaded file

#     Raises:
#         Exception: If download fails
#     """
#     try:
#         # Create directory if it doesn't exist
#         os.makedirs(dir_store, exist_ok=True)

#         # Detect URL type
#         url_type = UniversalDownloader.detect_url_type(url)

#         print(f"🔄 Downloading {url_type.upper()} URL: {url[:100]}...")

#         # Route to appropriate download method
#         if url_type == "http":
#             print("⬇️⬇️⬇️ DOWNLOAD HTTP ⬇️⬇️⬇️")
#             file_path = await UniversalDownloader.download_http_url(url, dir_store)

#         elif url_type == "base64":
#             print("⬇️⬇️⬇️ DOWNLOAD BASE64 ⬇️⬇️⬇️")
#             file_path = await UniversalDownloader.download_base64_url(url, dir_store)

#         elif url_type == "blob":
#             print("⬇️⬇️⬇️ DOWNLOAD BLOG ⬇️⬇️⬇️")
#             if tab is None:
#                 raise Exception("Browser tab is required for blob URL downloads")
#             file_path = await UniversalDownloader.download_image_blog(
#                 tab, url, dir_store
#             )

#         elif url_type == "ftp":
#             print("⬇️⬇️⬇️ DOWNLOAD FTP ⬇️⬇️⬇️")
#             raise Exception("FTP downloads not yet implemented")

#         elif url_type == "file":
#             print("⬇️⬇️⬇️ DOWNLOAD FILE ⬇️⬇️⬇️")
#             raise Exception("File:// URLs not supported for security reasons")

#         else:
#             raise Exception(f"Unsupported URL type: {url_type}")

#     except Exception as e:
#         print(f"❌ Download failed: {e}")
#         raise e


async def download(
    tab: nd.Tab, url: str, dir_store: str, new_name_file: Optional[str] = None
) -> str:
    """
    Universal download function for all file types and URL types

    Args:
        tab: nodriver tab object (can be None for HTTP/Base64 downloads)
        url: URL to download (HTTP, HTTPS, blob, data URL)
        dir_store: Directory to store the downloaded file
        new_name_file: New name for the file (without extension). If None, keep original name.

    Returns:
        str: Path to the downloaded file

    Raises:
        Exception: If download fails
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(dir_store, exist_ok=True)

        # Detect URL type
        url_type = UniversalDownloader.detect_url_type(url)

        print(f"🔄 Downloading {url_type.upper()} URL: {url[:100]}...")

        # Route to appropriate download method
        if url_type == "http":
            print("⬇️⬇️⬇️ DOWNLOAD HTTP ⬇️⬇️⬇️")
            file_path = await UniversalDownloader.download_http_url(url, dir_store)

        elif url_type == "base64":
            print("⬇️⬇️⬇️ DOWNLOAD BASE64 ⬇️⬇️⬇️")
            file_path = await UniversalDownloader.download_base64_url(url, dir_store)

        elif url_type == "blob":
            print("⬇️⬇️⬇️ DOWNLOAD BLOG ⬇️⬇️⬇️")
            if tab is None:
                raise Exception("Browser tab is required for blob URL downloads")
            file_path = await UniversalDownloader.download_image_blog(
                tab, url, dir_store
            )

        elif url_type == "ftp":
            print("⬇️⬇️⬇️ DOWNLOAD FTP ⬇️⬇️⬇️")
            raise Exception("FTP downloads not yet implemented")

        elif url_type == "file":
            print("⬇️⬇️⬇️ DOWNLOAD FILE ⬇️⬇️⬇️")
            raise Exception("File:// URLs not supported for security reasons")

        else:
            raise Exception(f"Unsupported URL type: {url_type}")

        if new_name_file:
            # Get file extension from original path
            extension = os.path.splitext(file_path)[1]

            # Create new path with the new name and original extension
            new_file_path = os.path.join(dir_store, f"{new_name_file}{extension}")

            # Rename (move) the file
            shutil.move(file_path, new_file_path)
            file_path = new_file_path

        return file_path

    except Exception as e:
        print(f"❌ Download failed: {e}")
        raise e

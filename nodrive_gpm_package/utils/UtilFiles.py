import os, zipfile, time, shutil, json, datetime, traceback, re, requests

# os.getenv("USERPROFILE")	C:\Users\Admin
# os.getenv("HOMEPATH")	    \Users\Admin
# os.getenv("HOMEDRIVE")	C:
# os.getenv("APPDATA")	    C:\Users\Admin\AppData\Roaming
# os.getenv("LOCALAPPDATA")	C:\Users\Admin\AppData\Local


def getDownloadsDirectory():
    return os.path.join(os.environ["USERPROFILE"], "Downloads")


def getGPMProfilesDirectory():
    return os.path.join(
        os.environ["USERPROFILE"], "Downloads", "GPMLogin", "chrome_extensions"
    )


def getGPMDriverPath():
    return os.path.join(
        os.getenv("LOCALAPPDATA"),
        "Programs",
        "GPMLogin",
        "gpm_browser",
        "gpm_browser_chromium_core_132",
        "gpmdriver.exe",
    )  # => C:\Users\Admin\AppData\Local\Programs\GPMLogin\gpm_browser\gpm_browser_chromium_core_132\gpmdriver.exe


def renameDownloadedFileAndMoveToFolder(
    numberFileOrigin: int,
    newName: str,
    folderDownload: str,
    folderTarget: str = None,
    maxRetries=500,
    callback: any = None,
) -> str:

    # Get the initial number of files in the Downloads folder
    print("\n✂️✂️✂️RENAME AND MOVE FOLDER✂️✂️✂️")

    countRetries = 0
    while True:
        if callback:
            callback()
        print(f"Waiting for rename new file {countRetries}...")
        if countRetries == maxRetries:
            return None
        # List all files in the download directory
        files = os.listdir(folderDownload)
        print("<--------------------------🗄️🗄️🗄️🗄️🗄️-------------------------->")
        print("numberFileOrigin:::", numberFileOrigin)
        print("numberNewFiles:::", len(files))

        # Check if new files have been added (count has increased)
        if len(files) > numberFileOrigin:
            # Find the newest downloaded file
            newestFile = max(
                [os.path.join(folderDownload, f) for f in files], key=os.path.getmtime
            )

            # Check if the download process has finished
            if not newestFile.endswith(".crdownload") and not newestFile.endswith(
                ".tmp"
            ):  # Check if the file is still downloading
                # Get the file extension
                # fileExtension: .jpg, .png, .mp4, etc.
                _, fileExtension = os.path.splitext(newestFile)

                newFilePath = os.path.join(folderDownload, f"{newName}" + fileExtension)

                print("newestFile:::", newestFile)
                print("newFilePath:::", newFilePath)

                try:
                    if os.path.exists(newFilePath) and newestFile != newFilePath:
                        os.remove(newFilePath)
                        print(f"Deleted file: {newFilePath}")
                except Exception as e:
                    print("Error delete image:::", e)
                    pass

                # Rename the file
                if not os.path.exists(newFilePath):
                    time.sleep(1)
                    shutil.move(newestFile, newFilePath)
                    print(f"File renamed to: {newFilePath}")

                    # Move the renamed file to the target folder
                    if folderTarget:
                        targetFilePath = os.path.join(
                            folderTarget, f"{newName}" + fileExtension
                        )
                        shutil.move(newFilePath, targetFilePath)
                        print(f"File moved to: {targetFilePath}")
                    return newFilePath
                else:
                    return newFilePath
            time.sleep(1)
        else:
            time.sleep(1)
        countRetries += 1


def extractFolder(zipPath: str):
    print("\nEXTRACT FOLDER📁📁📁")

    # Extract the base name without the extension
    zipFilename = os.path.basename(zipPath)  # "square_1.zip"
    folderName = os.path.splitext(zipFilename)[0]  # "square_1"
    extensionName = os.path.splitext(zipFilename)[1]  # "square_1"

    print("extensionName:::", extensionName)
    if extensionName == ".zip" or extensionName == ".rar":
        # Define the extraction directory by joining the zip file's directory with the new folder name
        zipDir = os.path.dirname(zipPath)
        extractTo = os.path.join(zipDir, folderName)

        # Create the target directory if it doesn't exist
        os.makedirs(extractTo, exist_ok=True)

        # Open the ZIP file and extract its contents into the new folder
        with zipfile.ZipFile(zipPath, "r") as zip_ref:
            zip_ref.extractall(extractTo)

        os.remove(zipPath)


def writeErrToJson(errorMessage):
    errorFile = "error.json"
    if not os.path.exists(errorFile):
        with open(errorFile, "w", encoding="utf-8") as f:
            json.dump([], f)

    try:
        # Đọc dữ liệu hiện tại
        with open(errorFile, "r", encoding="utf-8") as f:
            errors = json.load(f)

        # Tạo thông tin lỗi
        error_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error_message": errorMessage,
            "traceback": traceback.format_exc(),
        }

        # Thêm vào danh sách lỗi
        errors.append(error_data)

        # Ghi lại file
        with open(errorFile, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"Error while logging error: {e}")


def deleteFolder(folderPath):
    """
    Xóa một folder và tất cả các file/folder bên trong nó.

    Args:
        folderPath (str): Đường dẫn đến folder cần xóa.
    """
    try:
        if os.path.exists(folderPath):
            shutil.rmtree(folderPath)
            print(f"Đã xóa folder: {folderPath}")
        else:
            print(f"Folder {folderPath} không tồn tại.")
    except Exception as e:
        print(f"Lỗi khi xóa folder {folderPath}: {e}")
        writeErrToJson(str(e))


def deleteFile(filePath: str):
    """
    Xóa một file.
    Args:
        filePath (str): Đường dẫn đến file cần xóa.
    """
    try:
        if os.path.exists(filePath):
            os.remove(filePath)
            print(f"Đã xóa file: {filePath}")
        else:
            print(f"File {filePath} không tồn tại.")
    except Exception as e:
        print(f"Lỗi khi xóa file {filePath}: {e}")
        writeErrToJson(str(e))


def downloadImageUrl(url: str, dirStore: str):
    try:
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(dirStore), exist_ok=True)

        # Tải xuống hình ảnh
        response = requests.get(url)

        response.raise_for_status()

        # Lưu hình ảnh vào tệp
        with open(dirStore, "wb") as file:
            file.write(response.content)

        print(f"Đã tải xuống và lưu hình với đường dẫn: {dirStore}")
    except Exception as e:
        print(f"Lỗi khi tải xuống hình ảnh: {e}")
        raise Exception(f"Lỗi khi tải xuống hình ảnh {url}")


def downloadFileWithBase64(base64: str, dirStore, filename=None):
    """
    Download file từ base64 data URI

    Args:
        base64: Base64 data URI string
        dirStore: Thư mục lưu file
        filename: Tên file (không bao gồm extension)

    Returns:
        Full path của file đã lưu hoặc None nếu lỗi
    """
    if not base64 or not base64.startswith("data:"):
        print("Invalid base64 data")
        return None

    # Tách header và data
    header, base64_data = base64.split(",", 1)

    # Xác định MIME type và extension (hỗ trợ mọi loại file)
    mime_patterns = {
        # Audio
        r"data:audio/([^;]+)": {
            "mp3": "mp3",
            "wav": "wav",
            "ogg": "ogg",
            "mpeg": "mp3",
            "mp4": "m4a",
        },
        # Images
        r"data:image/([^;]+)": {
            "jpeg": "jpg",
            "jpg": "jpg",
            "png": "png",
            "gif": "gif",
            "webp": "webp",
            "svg+xml": "svg",
        },
        # Video
        r"data:video/([^;]+)": {
            "mp4": "mp4",
            "webm": "webm",
            "avi": "avi",
            "mov": "mov",
        },
        # Documents
        r"data:application/([^;]+)": {
            "pdf": "pdf",
            "json": "json",
            "xml": "xml",
            "zip": "zip",
        },
        # Text
        r"data:text/([^;]+)": {
            "plain": "txt",
            "html": "html",
            "css": "css",
            "javascript": "js",
        },
    }

    extension = "bin"  # Default extension

    # Tìm MIME type và extension
    for pattern, ext_map in mime_patterns.items():
        mime_match = re.search(pattern, header)
        if mime_match:
            format_type = mime_match.group(1)
            extension = ext_map.get(format_type, format_type)
            break

    # Tạo thư mục nếu chưa có
    if not os.path.exists(dirStore):
        os.makedirs(dirStore)

    # Tạo filename nếu chưa có
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"file_{timestamp}"

    # Tạo full path
    full_filename = f"{filename}.{extension}"
    file_path = os.path.join(dirStore, full_filename)

    # Tránh trùng tên file
    counter = 1
    while os.path.exists(file_path):
        new_filename = f"{filename}_{counter}.{extension}"
        file_path = os.path.join(dirStore, new_filename)
        counter += 1

    # Decode và lưu
    try:
        file_bytes = base64.b64decode(base64_data)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        print(f"✅ File đã được lưu: {file_path}")
        print(f"📁 Kích thước: {len(file_bytes)} bytes ({len(file_bytes)/1024:.1f} KB)")
        return file_path

    except Exception as e:
        print(f"❌ Lỗi khi decode base64: {e}")
        return None

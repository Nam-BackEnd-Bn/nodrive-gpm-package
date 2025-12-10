import os
import winreg
import ctypes
from pathlib import Path
from pywinauto import Application
import threading

lock = threading.Lock()


def add_to_path(name):
    """
    Thêm một thư mục vào biến môi trường PATH của người dùng hiện tại

    Args:
        directory (str): Đường dẫn đầy đủ đến thư mục cần thêm

    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    # Chuẩn hóa đường dẫn
    directory = os.path.join(os.getcwd(), "libs", name)
    directory = str(Path(directory).resolve())

    try:
        # Mở registry key cho biến môi trường người dùng
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment",
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        )

        # Lấy giá trị PATH hiện tại
        try:
            path_value, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            path_value = ""

        # Kiểm tra xem thư mục đã có trong PATH chưa
        path_entries = [entry.lower() for entry in path_value.split(";") if entry]
        if directory.lower() in path_entries:
            print(f"Thư mục '{directory}' đã tồn tại trong PATH.")
            return True

        # Thêm thư mục vào PATH
        new_path = path_value + ";" + directory if path_value else directory

        # Ghi giá trị mới vào registry
        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)

        # Thông báo thay đổi biến môi trường cho các ứng dụng khác
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")

        print(f"Đã thêm thành công '{directory}' vào PATH.")
        print("Vui lòng khởi động lại các cửa sổ terminal đang mở để áp dụng thay đổi.")
        return True

    except Exception as e:
        print(f"Lỗi khi thêm vào PATH: {e}")
        return False


def focusWindowByTitle(title: str):
    app = Application().connect(title=title)
    dlg = app.window(title=title)
    dlg.set_focus()


def listWindowTitles():
    app = Application().connect()  # Connect to the running application
    windows = app.windows()  # Get all windows of the application
    titles = [window.window_text() for window in windows]  # List of titles

    # Print out each title in the list
    listTitleOpen = []
    for title in titles:
        if title == "Open":
            listTitleOpen.append(title)

    return listTitleOpen


def isPopupOpen() -> bool:
    try:
        Application().connect(title="Open")
        return True
    except Exception as e:
        return False



import sys
import ctypes
from ctypes import wintypes
import asyncio
import psutil
import logging

logger = logging.getLogger(__name__)

class WindowPositioner:
    """Helper class for calculating and applying browser window positions."""

    @staticmethod
    def calculate_grid_geometry(grid_row, grid_col, grid_rows, grid_cols):
        """
        Calculate window geometry (x, y, width, height) based on grid parameters
        and current screen resolution.
        """
        try:
            if sys.platform != 'win32':
                return None

            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)

            if grid_rows and grid_cols:
                w = screen_width // grid_cols
                h = screen_height // grid_rows
                x = grid_col * w
                y = grid_row * h
                return (x, y, w, h)
            
            return None
        except Exception as e:
            logger.error(f"Error calculating grid geometry: {e}")
            return None

    @staticmethod
    async def force_position_window(browser, x, y, width, height, profile_name="Unknown"):
        """
        Force the browser window to a specific position using Windows API
        and PID detection via debugging port.
        """
        if sys.platform != 'win32':
            return

        try:
            user32 = ctypes.windll.user32
            
            # 1. FIND PID
            target_pid = None
            
            # Method A: Direct Attribute
            try:
                if hasattr(browser, "process") and hasattr(browser.process, "pid"):
                    target_pid = browser.process.pid
                elif hasattr(browser, "pid"):
                     target_pid = browser.pid
            except:
                 pass

            # Method B: Via Connection/Port (Robust fallback)
            if not target_pid:
                try:
                    # browser.connection.target usually contains the websocket url like ws://127.0.0.1:9222/...
                    # Extract port
                    port = None
                    if hasattr(browser, "connection") and hasattr(browser.connection, "target"):
                         import re
                         match = re.search(r':(\d+)/', str(browser.connection.target))
                         if match:
                             port = int(match.group(1))
                    
                    # Or check config/args if available
                    if not port and hasattr(browser, "config") and hasattr(browser.config, "port"):
                        port = browser.config.port

                    if port:
                        logger.info(f"[{profile_name}] Identifying process via port {port}")
                        # Find process listening on this port
                        for proc in psutil.process_iter(['pid', 'name']):
                            try:
                                for conn in proc.connections():
                                    if conn.laddr.port == port:
                                        target_pid = proc.pid
                                        break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                            if target_pid:
                                break
                except Exception as e:
                    logger.debug(f"[{profile_name}] Error finding PID via port: {e}")

            logger.info(f"[{profile_name}] Browser PID: {target_pid}")

            # 2. FIND WINDOW HANLDE (HWND)
            target_hwnd = None
            max_retries = 20
            
            for i in range(max_retries):
                if target_hwnd:
                    break
                    
                def enum_cb(hwnd, _):
                    if not user32.IsWindowVisible(hwnd):
                        return True
                    
                    pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    
                    if target_pid and pid.value == target_pid:
                        # Found exact match
                        class_name = ctypes.create_unicode_buffer(256)
                        user32.GetClassNameW(hwnd, class_name, 256)
                        # Browsers usually have 'Chrome_WidgetWin_1'
                        if "Chrome_WidgetWin" in class_name.value:
                             nonlocal target_hwnd
                             target_hwnd = hwnd
                             return False # Stop enumeration
                    return True

                enum_func = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
                user32.EnumWindows(enum_func(enum_cb), 0)
                
                if not target_hwnd:
                    await asyncio.sleep(0.5)

            # 3. MOVE WINDOW
            if target_hwnd:
                try:
                    # Restore
                    SW_RESTORE = 9
                    user32.ShowWindow(target_hwnd, SW_RESTORE)
                    
                    # Set Pos
                    SWP_NOZORDER = 0x0004
                    SWP_SHOWWINDOW = 0x0040
                    
                    success = user32.SetWindowPos(
                        target_hwnd, 
                        0, 
                        int(x), int(y), int(width), int(height), 
                        SWP_NOZORDER | SWP_SHOWWINDOW
                    )
                    if success:
                        logger.info(f"✅ [{profile_name}] Window moved to {x},{y} {width}x{height}")
                    else:
                        logger.error(f"❌ [{profile_name}] SetWindowPos failed")
                except Exception as e:
                    logger.error(f"Error moving window: {e}")
            else:
                logger.warning(f"⚠️ [{profile_name}] Could not find window for PID {target_pid}")
        except Exception as e:
            logger.error(f"Error in force_position_window: {e}")

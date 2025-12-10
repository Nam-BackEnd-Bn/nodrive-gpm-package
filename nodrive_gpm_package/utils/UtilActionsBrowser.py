import os
import nodriver as nd, time, asyncio
import win32gui
import win32con
from nodriver import cdp


async def closeTabByIndex(browser: nd.Browser, tabIdx: int) -> bool:
    """
    Close tab by index (0-based) for NoDriver

    Args:
        browser: NoDriver Browser instance
        tabIdx: Index of tab to close (0-based)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get all tabs from browser.tabs property
        tabs = list(browser.tabs)
        print(
            f"tabs::: {[f'Tab {i}: {tab.target.target_id}' for i, tab in enumerate(tabs)]}"
        )

        if 0 <= tabIdx < len(tabs):
            target_tab = tabs[tabIdx]

            # Get current active tab by checking browser.main_tab or browser.current_tab
            current_tab = browser.main_tab  # Current active tab

            print(
                f"current_tab ID::: {current_tab.target.target_id if current_tab else 'None'}"
            )
            print(f"target_tab ID::: {target_tab.target.target_id}")

            # Get tab title before closing for logging
            try:
                target_title = await target_tab.send(
                    nd.cdp.runtime.evaluate(expression="document.title")
                )
                target_title = (
                    target_title.result.value if target_title.result else "Unknown"
                )
            except:
                target_title = "Unknown"

            # Close the target tab
            await target_tab.close()

            # If we closed the current active tab, switch to another tab
            if (
                current_tab
                and target_tab.target.target_id == current_tab.target.target_id
            ):
                remaining_tabs = [
                    tab
                    for tab in tabs
                    if tab.target.target_id != target_tab.target.target_id
                ]
                if remaining_tabs:
                    # Switch to the first remaining tab
                    await remaining_tabs[0].activate()
                    print(f"🔄 Switched to tab: {remaining_tabs[0].target.target_id}")

            print(f"✅ Closed tab at index {tabIdx}: '{target_title}'")
            return True
        else:
            print(f"❌ Invalid tab index: {tabIdx}. Valid range: 0-{len(tabs)-1}")
            return False

    except Exception as e:
        print(f"❌ Error closing tab by index: {e}")
        return False


async def switchToTab(browser: nd.Browser, tabIdx: int) -> bool:
    """
    Switch to tab by index (0-based) for NoDriver

    Args:
        browser: NoDriver Browser instance
        tabIdx: Index of tab to switch to (0-based)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get all tabs from browser.tabs property
        tabs = list(browser.tabs)
        print(
            f"tabs::: {[f'Tab {i}: {tab.target.target_id}' for i, tab in enumerate(tabs)]}"
        )

        if 0 <= tabIdx < len(tabs):
            target_tab = tabs[tabIdx]

            # Activate the target tab
            await target_tab.activate()

            # Get tab title for confirmation
            try:
                title_result = await target_tab.send(
                    nd.cdp.runtime.evaluate(expression="document.title")
                )
                title = title_result.result.value if title_result.result else "Unknown"
            except:
                title = "Unknown"

            print(f"✅ Switched to tab {tabIdx}: '{title}'")
            return True
        else:
            print(f"❌ Invalid tab index: {tabIdx}. Valid range: 0-{len(tabs)-1}")
            return False

    except Exception as e:
        print(f"❌ Error switching tab: {e}")
        return False


# ===== UTILITY FUNCTIONS =====


async def listAllTabs(browser: nd.Browser) -> list:
    """
    List all open tabs with their details

    Args:
        browser: NoDriver Browser instance

    Returns:
        List of tab details
    """
    try:
        tabs = list(browser.tabs)
        tab_details = []

        for i, tab in enumerate(tabs):
            try:
                # Get tab title and URL
                title_result = await tab.send(
                    nd.cdp.runtime.evaluate(expression="document.title")
                )
                title = title_result.result.value if title_result.result else "Unknown"

                url = tab.url if hasattr(tab, "url") else "Unknown"

                detail = {
                    "index": i,
                    "id": tab.target.target_id,
                    "title": title,
                    "url": url,
                    "is_active": tab == browser.main_tab,
                }
                tab_details.append(detail)

            except Exception as e:
                print(f"Error getting details for tab {i}: {e}")
                tab_details.append(
                    {
                        "index": i,
                        "id": (
                            tab.target.target_id
                            if hasattr(tab, "target")
                            else "Unknown"
                        ),
                        "title": "Error",
                        "url": "Error",
                        "is_active": False,
                    }
                )

        return tab_details

    except Exception as e:
        print(f"❌ Error listing tabs: {e}")
        return []


async def closeAllTabsExcept(browser: nd.Browser, keepTabIdx: int) -> bool:
    """
    Close all tabs except the specified one

    Args:
        browser: NoDriver Browser instance
        keepTabIdx: Index of tab to keep open (0-based)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        tabs = list(browser.tabs)

        if not (0 <= keepTabIdx < len(tabs)):
            print(f"❌ Invalid keep tab index: {keepTabIdx}")
            return False

        keep_tab = tabs[keepTabIdx]

        # Close all other tabs
        for i, tab in enumerate(tabs):
            if i != keepTabIdx:
                try:
                    await tab.close()
                    print(f"✅ Closed tab {i}")
                except Exception as e:
                    print(f"❌ Error closing tab {i}: {e}")

        # Activate the kept tab
        await keep_tab.activate()
        print(f"✅ Kept tab {keepTabIdx} active")

        return True

    except Exception as e:
        print(f"❌ Error closing tabs: {e}")
        return False


import win32gui
import win32con
import asyncio
import time
from typing import Tuple, List, Optional


async def bringBrowserToTop(tab: nd.Tab):
    """Bring browser window to top using NoDriver"""
    try:
        # Get original title
        original_title = await tab.evaluate("document.title")
        unique_id = str(int(time.time() * 1000))
        marked_title = f"{original_title}_{unique_id}"

        # Set temporary title to identify window
        await tab.evaluate(f"document.title = '{marked_title}';")
        await asyncio.sleep(0.3)

        # Find window by title
        def find_marked_window(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and marked_title in title:
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(find_marked_window, windows)

        if windows:
            hwnd = windows[0]

            # Bring window to top
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW,
            )

            # Remove topmost flag to allow normal window behavior
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_NOTOPMOST,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW,
            )

            win32gui.SetForegroundWindow(hwnd)

            # Restore original title
            await tab.evaluate(f"document.title = '{original_title}';")

            print("✅ Browser brought to top successfully!")
            return True
        else:
            print("❌ Window not found")
            return False

    except Exception as e:
        print(f"❌ Failed to bring browser to top: {e}")
        return False


class BrowserVisibilityChecker:

    # System windows that should NEVER be counted for coverage
    SYSTEM_WINDOWS_TO_IGNORE = {
        "Program Manager",  # Desktop wallpaper - ALWAYS ignore
        "Windows Input Experience",  # IME popups
        "Desktop Window Manager",
        "Microsoft Text Input Application",
        "Windows Shell Experience Host",
        "Task Switching",
        "WorkerW",  # Desktop worker process
        "Progman",  # Program Manager alternative name
    }

    # Windows that are usually minimized or not really covering
    LOW_PRIORITY_WINDOWS = {
        "Settings",
        "Control Panel",
        "Task Manager",
        "Windows Security",
        "Restore pages?",  # Browser restore dialog
    }

    @staticmethod
    def get_window_rect(hwnd) -> Tuple[int, int, int, int]:
        """Get window rectangle (left, top, right, bottom)"""
        return win32gui.GetWindowRect(hwnd)

    @staticmethod
    def get_window_class_name(hwnd) -> str:
        """Get window class name for better identification"""
        try:
            return win32gui.GetClassName(hwnd)
        except:
            return ""

    @staticmethod
    def is_window_minimized(hwnd) -> bool:
        """Check if window is minimized"""
        return win32gui.IsIconic(hwnd)

    @staticmethod
    def is_window_maximized(hwnd) -> bool:
        """Check if window is maximized"""
        try:
            placement = win32gui.GetWindowPlacement(hwnd)
            return placement[1] == 3
        except:
            return False

    @staticmethod
    def get_foreground_window_info() -> dict:
        """Get information about currently active window"""
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            class_name = BrowserVisibilityChecker.get_window_class_name(hwnd)
            return {
                "hwnd": hwnd,
                "title": title,
                "class_name": class_name,
                "rect": rect,
                "is_minimized": win32gui.IsIconic(hwnd),
                "is_maximized": BrowserVisibilityChecker.is_window_maximized(hwnd),
            }
        return None

    @staticmethod
    def find_browser_window(marked_title: str) -> Optional[int]:
        """Find browser window by marked title"""

        def find_window(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and marked_title in title:
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(find_window, windows)
        return windows[0] if windows else None

    @staticmethod
    def should_ignore_window_completely(title: str, class_name: str, hwnd: int) -> bool:
        """Check if window should be completely ignored"""
        # Ignore empty titles
        if not title or title.strip() == "":
            return True

        # Ignore known system windows
        if title in BrowserVisibilityChecker.SYSTEM_WINDOWS_TO_IGNORE:
            return True

        # Ignore by class name
        system_classes = {"Progman", "WorkerW", "Shell_TrayWnd", "DV2ControlHost"}
        if class_name in system_classes:
            return True

        # Ignore desktop and taskbar by checking if it covers entire screen
        try:
            rect = win32gui.GetWindowRect(hwnd)
            screen_width = win32gui.GetSystemMetrics(0)
            screen_height = win32gui.GetSystemMetrics(1)

            window_width = rect[2] - rect[0]
            window_height = rect[3] - rect[1]

            # If window covers entire screen and is at (0,0), likely desktop
            if (
                rect[0] == 0
                and rect[1] == 0
                and window_width >= screen_width
                and window_height >= screen_height
            ):
                return True

        except:
            pass

        return False

    @staticmethod
    def is_window_actually_visible(hwnd: int) -> bool:
        """Check if window is actually visible (not just IsWindowVisible)"""
        try:
            # Check if window is visible
            if not win32gui.IsWindowVisible(hwnd):
                return False

            # Check if window is minimized
            if win32gui.IsIconic(hwnd):
                return False

            # Check if window has actual size
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            if width <= 0 or height <= 0:
                return False

            # Check if window is cloaked (Windows 8+)
            try:
                import ctypes
                from ctypes import wintypes

                dwmapi = ctypes.windll.dwmapi
                cloaked = wintypes.DWORD()

                result = dwmapi.DwmGetWindowAttribute(
                    hwnd,
                    14,  # DWMWA_CLOAKED
                    ctypes.byref(cloaked),
                    ctypes.sizeof(cloaked),
                )

                if result == 0 and cloaked.value != 0:
                    return False

            except:
                pass  # If DWM check fails, assume visible

            return True

        except:
            return False

    @staticmethod
    def get_overlapping_windows_debug(target_hwnd) -> List[dict]:
        """Get overlapping windows with detailed debug info"""
        target_rect = win32gui.GetWindowRect(target_hwnd)
        overlapping = []
        all_windows = []  # For debugging

        def enum_windows(hwnd, param):
            title = win32gui.GetWindowText(hwnd)
            class_name = BrowserVisibilityChecker.get_window_class_name(hwnd)

            # Collect all windows for debugging
            all_windows.append(
                {
                    "hwnd": hwnd,
                    "title": title,
                    "class_name": class_name,
                    "is_visible": win32gui.IsWindowVisible(hwnd),
                    "is_minimized": win32gui.IsIconic(hwnd),
                    "rect": (
                        win32gui.GetWindowRect(hwnd)
                        if win32gui.IsWindowVisible(hwnd)
                        else None
                    ),
                }
            )

            # Skip target window
            if hwnd == target_hwnd:
                return True

            # Check if should ignore completely
            if BrowserVisibilityChecker.should_ignore_window_completely(
                title, class_name, hwnd
            ):
                return True

            # Check if actually visible
            if not BrowserVisibilityChecker.is_window_actually_visible(hwnd):
                return True

            window_rect = win32gui.GetWindowRect(hwnd)

            # Check if windows overlap
            if BrowserVisibilityChecker.rectangles_overlap(target_rect, window_rect):
                coverage = BrowserVisibilityChecker.calculate_overlap_percentage(
                    target_rect, window_rect
                )

                overlapping.append(
                    {
                        "hwnd": hwnd,
                        "title": title,
                        "class_name": class_name,
                        "rect": window_rect,
                        "coverage": coverage,
                        "is_low_priority": title
                        in BrowserVisibilityChecker.LOW_PRIORITY_WINDOWS,
                    }
                )
            return True

        win32gui.EnumWindows(enum_windows, None)

        return overlapping, all_windows

    @staticmethod
    def rectangles_overlap(
        rect1: Tuple[int, int, int, int], rect2: Tuple[int, int, int, int]
    ) -> bool:
        """Check if two rectangles overlap"""
        left1, top1, right1, bottom1 = rect1
        left2, top2, right2, bottom2 = rect2

        return not (
            right1 <= left2 or right2 <= left1 or bottom1 <= top2 or bottom2 <= top1
        )

    @staticmethod
    def calculate_overlap_percentage(
        rect1: Tuple[int, int, int, int], rect2: Tuple[int, int, int, int]
    ) -> float:
        """Calculate percentage of rect1 that is overlapped by rect2"""
        left1, top1, right1, bottom1 = rect1
        left2, top2, right2, bottom2 = rect2

        # Calculate intersection
        left = max(left1, left2)
        top = max(top1, top2)
        right = min(right1, right2)
        bottom = min(bottom1, bottom2)

        if left >= right or top >= bottom:
            return 0.0

        # Calculate areas
        intersection_area = (right - left) * (bottom - top)
        rect1_area = (right1 - left1) * (bottom1 - top1)

        return (intersection_area / rect1_area) * 100 if rect1_area > 0 else 0.0


async def checkBrowserVisibility(
    tab: nd.Tab, threshold_percentage: float = 50.0
) -> dict:
    """
    Debug version to understand why coverage is wrong
    """
    try:
        # Mark the browser window
        original_title = await tab.evaluate("document.title")
        unique_id = str(int(time.time() * 1000))
        marked_title = f"{original_title}_{unique_id}"

        await tab.evaluate(f"document.title = '{marked_title}';")
        await asyncio.sleep(0.3)

        checker = BrowserVisibilityChecker()

        # Find browser window
        browser_hwnd = checker.find_browser_window(marked_title)
        if not browser_hwnd:
            return {"error": "Browser window not found"}

        # Get browser window info
        browser_rect = checker.get_window_rect(browser_hwnd)
        browser_class = checker.get_window_class_name(browser_hwnd)
        is_minimized = checker.is_window_minimized(browser_hwnd)
        is_maximized = checker.is_window_maximized(browser_hwnd)

        # print(f"🔍 BROWSER DEBUG INFO:")
        # print(f"  📱 Title: {marked_title}")
        # print(f"  📊 Rect: {browser_rect}")
        # print(
        #     f"  📏 Size: {browser_rect[2] - browser_rect[0]}x{browser_rect[3] - browser_rect[1]}"
        # )
        # print(f"  🏷️ Class: {browser_class}")
        # print(f"  📱 Minimized: {is_minimized}")
        # print(f"  📺 Maximized: {is_maximized}")

        # Get foreground window info
        foreground_info = checker.get_foreground_window_info()
        is_active = (
            foreground_info["hwnd"] == browser_hwnd if foreground_info else False
        )

        # print(f"  ⭐ Active: {is_active}")
        # print(
        #     f"  🎯 Foreground: {foreground_info['title'] if foreground_info else 'None'}"
        # )

        # Get overlapping windows with debug info
        overlapping_windows, all_windows = checker.get_overlapping_windows_debug(
            browser_hwnd
        )

        # print(f"\n📋 ALL WINDOWS DEBUG (first 10):")
        # for i, window in enumerate(all_windows[:10]):
        #     print(
        #         f"  {i+1}. '{window['title']}' ({window['class_name']}) - Visible: {window['is_visible']}"
        #     )

        # print(f"\n🚫 OVERLAPPING WINDOWS:")
        total_meaningful_coverage = 0.0
        meaningful_windows = []

        for window in overlapping_windows:
            coverage = window["coverage"]
            is_ignored = checker.should_ignore_window_completely(
                window["title"], window["class_name"], window["hwnd"]
            )

            # print(f"  📐 '{window['title']}' ({window['class_name']})")
            # print(
            #     f"      Coverage: {coverage:.2f}%, Ignored: {is_ignored}, Low Priority: {window['is_low_priority']}"
            # )
            # print(f"      Rect: {window['rect']}")

            # Only count meaningful coverage
            if not is_ignored and not window["is_low_priority"] and coverage > 1.0:
                total_meaningful_coverage += coverage
                meaningful_windows.append(
                    {
                        "title": window["title"],
                        "coverage_percentage": round(coverage, 2),
                    }
                )

        # Determine if browser is actually obscured
        is_actually_obscured = total_meaningful_coverage >= threshold_percentage

        # Restore original title
        # await tab.evaluate(f"document.title = '{original_title}';")

        # threshold_percentage: Ngưỡng % để coi như "bị che"
        # is_minimized: Browser có bị minimize không
        # is_minimized: Browser có bị maximized không
        # is_active: Browser có đang active không(Fucus)
        # is_actually_obscured: Browser có thực sự bị che (meaningful) không; threshold = 30% -> meaningful_coverage = 45% → True (bị che) | threshold = 30%, meaningful_coverage = 15% → False (không bị che)
        # meaningful_coverage_percentage: % bị che bởi ứng dụng thật
        # meaningful_covering_windows: Danh sách các ứng dụng quan trọng đang che browser
        # browser_size: Kích thước browser dạng string dễ đọc
        # browser_rect: Tọa độ browser trên màn hình
        # foreground_window: App đang active(Fucus)

        result = {
            "is_minimized": bool(is_minimized),
            "is_maximized": is_maximized,
            "is_active": is_active,
            "is_actually_obscured": is_actually_obscured,
            "meaningful_coverage_percentage": round(
                min(total_meaningful_coverage, 100.0), 2
            ),
            "threshold_percentage": threshold_percentage,
            "meaningful_covering_windows": meaningful_windows,
            "browser_rect": browser_rect,
            "browser_size": f"{browser_rect[2] - browser_rect[0]}x{browser_rect[3] - browser_rect[1]}",
            "foreground_window": foreground_info["title"] if foreground_info else None,
            "all_overlapping_count": len(overlapping_windows),
            "meaningful_overlapping_count": len(meaningful_windows),
        }

        # print(f"\n✅ FINAL RESULT:")
        # print(f"  🚫 Actually obscured: {is_actually_obscured}")
        # print(f"  📊 Meaningful coverage: {total_meaningful_coverage:.2f}%")
        # print(f"  📈 Meaningful windows: {len(meaningful_windows)}")
        # print("result:::::", result)

        return result

    except Exception as e:
        return {"error": f"Failed to debug visibility: {e}"}


class DialogHandler:
    def __init__(self, tab: nd.Tab):
        self.tab = tab
        self.setup_handlers()

    def setup_handlers(self):
        """Setup automatic dialog handling"""
        self.tab.add_handler(nd.cdp.page.JavascriptDialogOpening, self.handle_dialog)

    async def handle_dialog(self, event):
        """Handle all types of browser dialogs"""
        dialog_type = event.type_
        message = event.message

        print(f"🔔 Dialog detected: {dialog_type} - {message}")

        if dialog_type == "beforeunload":
            # Always accept leave page dialogs
            await self.tab.send(nd.cdp.page.handle_javascript_dialog(accept=True))
            print("✅ Automatically accepted Leave dialog")
        elif dialog_type == "confirm":
            # Handle confirm dialogs
            await self.tab.send(nd.cdp.page.handle_javascript_dialog(accept=True))
            print("✅ Automatically accepted Confirm dialog")
        elif dialog_type == "alert":
            # Handle alert dialogs
            await self.tab.send(nd.cdp.page.handle_javascript_dialog(accept=True))
            print("✅ Automatically accepted Alert dialog")


async def setFolderDownload(tab: nd.Tab, downloadDir: str):
    # Tạo download directory
    os.makedirs(downloadDir, exist_ok=True)

    # Raw CDP command approach
    raw_result = await tab.send(
        cdp.browser.set_download_behavior(
            behavior="allow",
            download_path=downloadDir,
            events_enabled=True,  # Enable download events
        )
    )
    print(f"Raw CDP result: {raw_result}")

    # Check if file was downloaded
    files = os.listdir(downloadDir)
    print(f"Downloaded files: {files}")

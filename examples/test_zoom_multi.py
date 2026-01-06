import asyncio
import sys
import os
import random
import time

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import nodriver as nd
from nodrive_gpm_package.utils import UtilActions

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

# Global lock to prevent input conflict (mouse/keyboard are shared resources)
input_lock = asyncio.Lock()
# Barrier will be initialized in main
barrier = None

async def set_window_geometry(tab, x, y, width, height):
    if not win32gui:
        print("Win32GUI not found, skipping window positioning")
        return

    try:
        # Mark window
        original_title = await tab.evaluate("document.title")
        unique_id = str(int(time.time() * 1000)) + str(random.randint(0, 1000))
        marked_title = f"{original_title}_{unique_id}"
        await tab.evaluate(f"document.title = '{marked_title}';")
        await asyncio.sleep(0.5)
        
        found_hwnd = None
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if marked_title in title:
                    windows.append(hwnd)
        
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        
        if hwnds:
            hwnd = hwnds[0]
            # Restore title
            await tab.evaluate(f"document.title = '{original_title}';")
            
            # Move and Resize
            # SWP_NOZORDER (0x0004) | SWP_NOACTIVATE (0x0010)
            flags = win32con.SWP_NOZORDER | 0x0010
            win32gui.SetWindowPos(hwnd, 0, x, y, width, height, flags)
            print(f"Set window pos: {x}, {y}, {width}x{height}")
        else:
            print("Window not found for positioning")
            await tab.evaluate(f"document.title = '{original_title}';")

    except Exception as e:
        print(f"Error setting window geometry: {e}")

async def zoom_test(index):
    browser = None
    try:
        print(f"[{index}] Starting browser...")
        browser = await nd.start(headless=False)
        tab = await browser.get("https://aistudio.google.com")
        await asyncio.sleep(2)
        
        # Position the window
        # Width 350, Height 600, positioned by index
        await set_window_geometry(tab, index * 350, 0, 350, 600)
        
        # Wait for all browsers to be ready
        print(f"[{index}] Waiting for barrier...")
        await barrier.wait()
        
        async with input_lock:
            print(f"[{index}] Acquired lock. Starting zoom test...")
            
            # We need to make sure the window is foreground for win32api to send keys to it!
            # The UtilActions.zoomPage tries to find window and setForeground.
            # So just calling it should be enough.
            
            # Test Custom 50%
            print(f"[{index}] Custom Zoom 50%...")
            await UtilActions.zoomPage(tab, action="custom", customScale=0.5)
            await asyncio.sleep(1)
            
            final_ratio = await tab.evaluate("window.devicePixelRatio")
            print(f"[{index}] Final DPR: {final_ratio}")
            
            if abs(float(final_ratio) - 0.5) < 0.1:
                print(f"[{index}] [SUCCESS]")
            else:
                print(f"[{index}] [FAILED]")
                
        # Keep browser open for a moment to see result
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"[{index}] Error: {e}")
    finally:
        if browser:
            browser.stop()

async def main():
    print("Starting Multi-Browser Zoom Test (4 instances)...")
    
    global barrier
    barrier = asyncio.Barrier(4)
    
    # Create 4 tasks (fits 1920 width with 350px each)
    tasks = [zoom_test(i) for i in range(4)]
    
    # Run them concurrently
    await asyncio.gather(*tasks)
    
    print("All tests complete.")

if __name__ == "__main__":
    asyncio.run(main())

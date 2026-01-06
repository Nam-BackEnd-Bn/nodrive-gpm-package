import asyncio
import sys
import os
import random

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import nodriver as nd
from nodrive_gpm_package.utils import UtilActions

# Global lock to prevent input conflict (mouse/keyboard are shared resources)
input_lock = asyncio.Lock()

async def zoom_test(index):
    browser = None
    try:
        print(f"[{index}] Starting browser...")
        browser = await nd.start(headless=False)
        tab = await browser.get("https://aistudio.google.com")
        await asyncio.sleep(2)
        
        # initial_ratio = await tab.evaluate("window.devicePixelRatio")
        # print(f"[{index}] Initial DPR: {initial_ratio}")
        
        async with input_lock:
            print(f"[{index}] Acquired lock. Starting zoom test...")
            
            # Test Zoom In
            # print(f"[{index}] Zoom In...")
            # await UtilActions.zoomPage(tab, action="in", times=2)
            # await asyncio.sleep(1)
            
            # Test Custom 50%
            print(f"[{index}] Custom Zoom 50%...")
            await UtilActions.zoomPage(tab, action="custom", customScale=0.5)
            await asyncio.sleep(1)
            
            final_ratio = await tab.evaluate("window.devicePixelRatio")
            print(f"[{index}] Final DPR: {final_ratio}")
            
            if abs(float(final_ratio) - 0.5) < 0.1:
                print(f"[{index}] ✅ SUCCESS")
            else:
                print(f"[{index}] ❌ FAILED")
                
        # Keep browser open for a moment to see result
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"[{index}] Error: {e}")
    finally:
        if browser:
            browser.stop()

async def main():
    print("Starting Multi-Browser Zoom Test (5 instances)...")
    
    # Create 5 tasks
    tasks = [zoom_test(i) for i in range(5)]
    
    # Run them concurrently
    await asyncio.gather(*tasks)
    
    print("All tests complete.")

if __name__ == "__main__":
    asyncio.run(main())

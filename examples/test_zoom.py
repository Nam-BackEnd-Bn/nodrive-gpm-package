import asyncio
import sys
import os

# Add project root to sys.path to ensure we import the local package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import nodriver as nd
from nodrive_gpm_package.utils import UtilActions

async def main():
    try:
        print("Starting browser...")
        browser = await nd.start(headless=False)
        tab = await browser.get("https://aistudio.google.com")
        
        print("Waiting for page load...")
        await asyncio.sleep(2)
        
        initial_ratio = await tab.evaluate("window.devicePixelRatio")
        print(f"Initial devicePixelRatio: {initial_ratio}")
        
        # Test Zoom In
        print("Testing Zoom In (2 times)...")
        await UtilActions.zoomPage(tab, action="in", times=2)
        await asyncio.sleep(2)
        
        ratio_after_in = await tab.evaluate("window.devicePixelRatio")
        print(f"Ratio after Zoom In: {ratio_after_in}")
        
        # Test Custom Zoom (50%)
        print("Testing Custom Zoom to 50% (0.5)...")
        await UtilActions.zoomPage(tab, action="custom", customScale=0.5)
        await asyncio.sleep(10)
        
        ratio_custom = await tab.evaluate("window.devicePixelRatio")
        print(f"Ratio after Custom Zoom (50%): {ratio_custom}")
        
        # Test Reset
        print("Testing Reset Zoom...")
        await UtilActions.zoomPage(tab, action="reset")
        await asyncio.sleep(2)

        final_ratio = await tab.evaluate("window.devicePixelRatio")
        print(f"Final devicePixelRatio: {final_ratio}")
        
        print("Test complete")
        browser.stop()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

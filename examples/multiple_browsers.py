"""
Multiple Browsers Example
Demonstrates launching multiple browsers in parallel
"""

import asyncio
from nodrive_gpm_package import GPMClient


async def launch_and_use(client: GPMClient, profile_name: str, position: int):
    """Launch a browser and use it"""
    
    print(f"🚀 [{profile_name}] Launching at position {position}...")
    
    browser = await client.launch(
        profile_name=profile_name,
        position=position
    )
    
    if browser:
        print(f"✅ [{profile_name}] Browser launched successfully")
        
        # Navigate to different pages
        urls = [
            "https://www.google.com",
            "https://www.github.com",
            "https://www.stackoverflow.com",
            "https://www.reddit.com",
        ]
        
        url = urls[position % len(urls)]
        tab = await browser.get(url)
        await asyncio.sleep(2)  # Wait for page to load
        
        try:
            title = await tab.evaluate("document.title")
            print(f"📄 [{profile_name}] Loaded: {title}")
        except Exception as e:
            print(f"📄 [{profile_name}] Loaded: {url}")
        
        return True
    else:
        print(f"❌ [{profile_name}] Failed to launch")
        return False


async def main():
    """Launch multiple browsers in parallel"""
    
    client = GPMClient()
    
    # Number of browsers to launch
    num_browsers = 4
    
    print(f"🚀 Launching {num_browsers} browsers...\n")
    
    # Launch all browsers in parallel
    tasks = [
        launch_and_use(client, f"profile_{i}", i)
        for i in range(num_browsers)
    ]
    
    results = await asyncio.gather(*tasks)
    
    successful = sum(results)
    print(f"\n✅ Successfully launched {successful}/{num_browsers} browsers")
    
    # Keep browsers open for a while
    print("\n⏳ Browsers will stay open for 30 seconds...")
    await asyncio.sleep(30)
    
    # Close all browsers
    print("\n🔒 Closing all browsers...")
    for i in range(num_browsers):
        client.close(f"profile_{i}")
    
    print("✅ All done!")


if __name__ == "__main__":
    asyncio.run(main())

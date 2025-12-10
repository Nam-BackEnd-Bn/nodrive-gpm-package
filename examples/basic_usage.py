"""
Basic Usage Example
Demonstrates simple browser launching
"""

import asyncio
from nodrive_gpm_package import GPMClient


async def main():
    """Launch a simple browser"""
    
    # Create client with default configuration
    client = GPMClient()
    
    print("🚀 Launching browser with profile 'example_profile'...")
    
    # Launch browser
    browser = await client.launch("example_profile")
    
    if browser:
        print("✅ Browser launched successfully!")
        
        # Get the main tab and navigate
        tab = await browser.get("https://www.google.com")
        
        # Wait for the page to load
        await asyncio.sleep(2)
        
        # Get page title and URL using JavaScript evaluation
        title = await tab.evaluate("document.title")
        print(f"📄 Page title: {title}")
        print(f"📄 Page URL: {tab.url}")
        
        # Wait a bit more
        await asyncio.sleep(3)
        
        # Close the profile
        print("🔒 Closing browser...")
        client.close("example_profile")
        print("✅ Done!")
    else:
        print("❌ Failed to launch browser")


if __name__ == "__main__":
    asyncio.run(main())

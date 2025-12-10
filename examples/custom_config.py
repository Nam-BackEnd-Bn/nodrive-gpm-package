"""
Custom Configuration Example
Demonstrates using custom configuration
"""

import asyncio
from nodrive_gpm_package import GPMClient, GPMConfig


async def main():
    """Use custom configuration"""
    
    # Create custom configuration
    config = GPMConfig(
        gpm_api_base_url="http://127.0.0.1:12003/api/v3",
        browser_width=1920,
        browser_height=1080,
        browser_scale=1.0,
        max_browsers_per_line=3,
        max_retries=5,
        retry_delay=10,
        debug=True  # Enable debug output
    )
    
    print("⚙️ Using custom configuration:")
    print(f"  - Browser size: {config.browser_width}x{config.browser_height}")
    print(f"  - Scale: {config.browser_scale}")
    print(f"  - Max retries: {config.max_retries}")
    
    # Create client with custom config
    client = GPMClient(config=config)
    
    # Launch browser
    print("\n🚀 Launching browser...")
    browser = await client.launch(
        profile_name="custom_config_profile",
        position=0
    )
    
    if browser:
        print("✅ Browser launched with custom configuration!")
        
        # Use the browser
        tab = await browser.get("https://ipinfo.io")
        await asyncio.sleep(2)  # Wait for page to load
        
        try:
            title = await tab.evaluate("document.title")
            print(f"📄 Loaded: {title}")
        except Exception as e:
            print(f"📄 Loaded: https://ipinfo.io")
        
        await asyncio.sleep(5)
        
        # Close
        client.close("custom_config_profile")
        print("✅ Browser closed")
    else:
        print("❌ Failed to launch browser")


if __name__ == "__main__":
    asyncio.run(main())

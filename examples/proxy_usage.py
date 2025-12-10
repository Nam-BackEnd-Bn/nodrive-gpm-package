
"""
Proxy Usage Example
Demonstrates launching browser with proxy configuration
"""

import asyncio
from nodrive_gpm_package import GPMClient


async def main():
    """Launch browser with proxy"""
    
    client = GPMClient()
    
    # Example 1: HTTP Proxy
    print("🌐 Launching with HTTP proxy...")
    browser1 = await client.launch(
        profile_name="profile_http",
        proxy_type="http",
        # proxy="123.45.67.89:1080:username:password",  # Replace with your proxy
        position=0
    )
    
    if browser1:
        print("✅ HTTP proxy browser launched")
        # Navigate to IP check page
        tab1 = await browser1.get("https://ipinfo.io")
        await asyncio.sleep(3)
        
        # Get the IP information
        try:
            page_text = await tab1.evaluate("document.body.innerText")
            print(f"📍 HTTP Proxy IP Info:\n{page_text[:200]}...")
        except Exception as e:
            print(f"⚠️ Could not read page: {e}")
    else:
        print("❌ Failed to launch HTTP proxy browser")
    
    # Example 2: SOCKS5 Proxy
    print("\n🌐 Launching with SOCKS5 proxy...")
    browser2 = await client.launch(
        profile_name="profile_socks5",
        proxy_type="socks5",
        proxy="123.45.67.89:1080:username:password",  # Replace with your proxy
        position=1
    )
    
    if browser2:
        print("✅ SOCKS5 proxy browser launched")
        # Navigate to IP check page
        tab2 = await browser2.get("https://ipinfo.io")
        await asyncio.sleep(3)
        
        # Get the IP information
        try:
            page_text = await tab2.evaluate("document.body.innerText")
            print(f"📍 SOCKS5 Proxy IP Info:\n{page_text[:200]}...")
        except Exception as e:
            print(f"⚠️ Could not read page: {e}")
    else:
        print("❌ Failed to launch SOCKS5 proxy browser")
    
    # Wait before closing
    print("\n⏳ Waiting 10 seconds before closing...")
    await asyncio.sleep(10)
    
    # Close all browsers
    print("\n🔒 Closing browsers...")
    if browser1:
        client.close("profile_http")
    if browser2:
        client.close("profile_socks5")
    
    print("✅ All browsers closed")


if __name__ == "__main__":
    asyncio.run(main())

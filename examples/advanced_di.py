"""
Advanced Dependency Injection Example
Demonstrates using DI pattern for maximum control
"""

import asyncio
from nodrive_gpm_package import (
    GPMConfig,
    GPMApiClient,
    ProfileMonitor,
    GPMService,
    ProfileCreateRequest,
    ProxyType,
)


async def main():
    """Advanced usage with dependency injection"""
    
    # 1. Create custom configuration
    config = GPMConfig(
        gpm_api_base_url="http://127.0.0.1:12003/api/v3",
        browser_width=1600,
        browser_height=900,
        max_retries=5,
        debug=True
    )
    
    print("⚙️ Configuration created")
    
    # 2. Create API client
    api_client = GPMApiClient(config=config)
    
    print("🔌 API client initialized")
    
    # 3. Create profile monitor
    monitor = ProfileMonitor(config=config)
    
    print("👁️ Profile monitor initialized")
    
    # 4. Inject dependencies into service
    service = GPMService(
        config=config,
        api_client=api_client,
        monitor=monitor
    )
    
    print("🏗️ Service created with injected dependencies\n")
    
    # 5. Use low-level API directly
    print("📋 Creating profile with API client...")
    
    try:
        profile_request = ProfileCreateRequest(
            profile_name="di_example_profile",
            is_masked_font=True,
            is_noise_canvas=True,
            is_noise_webgl=True,
            is_noise_client_rect=True,
            is_noise_audio_context=True,
            raw_proxy=None  # No proxy for this example
        )
        
        profile = api_client.create_profile(profile_request)
        print(f"✅ Profile created: {profile.name} (ID: {profile.id})\n")
        
    except Exception as e:
        print(f"ℹ️ Profile might already exist: {e}\n")
    
    # 6. Use monitor to check status
    print("🔍 Checking profile status with monitor...")
    status_result = monitor.check_all_profiles_status()
    
    print(f"  Running profiles: {len(status_result.running)}")
    print(f"  Stopped profiles: {len(status_result.stopped)}")
    print(f"  Pending profiles: {len(status_result.pending)}\n")
    
    # 7. Launch browser using service
    print("🚀 Launching browser with service...")
    
    browser = await service.launch_browser(
        profile_name="di_example_profile",
        proxy_type=None,
        proxy_string=None,
        persistent_position=0
    )
    
    if browser:
        print("✅ Browser launched via service\n")
        
        # Use browser
        tab = await browser.get("https://ipinfo.io")
        await asyncio.sleep(2)  # Wait for page to load
        
        try:
            title = await tab.evaluate("document.title")
            print(f"📄 Page loaded: {title}\n")
        except Exception as e:
            print(f"📄 Page loaded: https://ipinfo.io\n")
        
        await asyncio.sleep(5)
        
        # Close using service
        print("🔒 Closing profile via service...")
        service.close_profile("di_example_profile")
        print("✅ Profile closed\n")
    
    # 8. Cleanup
    print("🧹 Cleaning up...")
    api_client.__exit__(None, None, None)
    print("✅ Resources cleaned up")
    
    print("\n✅ Advanced DI example complete!")


if __name__ == "__main__":
    asyncio.run(main())

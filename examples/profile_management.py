"""
Profile Management Example
Demonstrates profile management operations
"""

import asyncio
from nodrive_gpm_package import GPMClient, ProfileStatus


async def main():
    """Demonstrate profile management"""
    
    client = GPMClient()
    
    # 1. List all profiles
    print("📋 Listing all profiles:")
    profiles = client.get_profiles()
    
    for profile in profiles[:5]:  # Show first 5
        print(f"  - {profile.name} (ID: {profile.id}, Status: {profile.status})")
    
    print(f"\nTotal profiles: {len(profiles)}\n")
    
    # 2. Launch a profile
    profile_name = "management_test"
    print(f"🚀 Launching profile '{profile_name}'...")
    
    browser = await client.launch(profile_name)
    
    if browser:
        print(f"✅ Profile launched successfully\n")
        
        # 3. Check profile status
        print(f"🔍 Checking profile status...")
        status = client.get_status(profile_name)
        print(f"  Status: {status}\n")
        
        if status == ProfileStatus.RUNNING:
            print("✅ Profile is confirmed running")
        
        # Use the browser
        tab = await browser.get("https://www.google.com")
        await asyncio.sleep(2)  # Wait for page to load
        
        try:
            title = await tab.evaluate("document.title")
            print(f"📄 Loaded: {title}\n")
        except Exception as e:
            print(f"📄 Loaded: https://www.google.com\n")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # 4. Close profile
        print(f"🔒 Closing profile '{profile_name}'...")
        success = client.close(profile_name)
        
        if success:
            print("✅ Profile closed successfully\n")
            
            # Verify status changed
            status = client.get_status(profile_name)
            print(f"  New status: {status}\n")
    
    # 5. Optional: Delete profile (commented out for safety)
    # print(f"🗑️ Deleting profile '{profile_name}'...")
    # client.delete_profile(profile_name)
    # print("✅ Profile deleted\n")
    
    print("✅ Profile management demo complete!")


if __name__ == "__main__":
    asyncio.run(main())

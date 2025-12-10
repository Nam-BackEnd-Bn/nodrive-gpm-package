"""
Captcha Service Usage Examples
Demonstrates how to use the CaptchaService for solving reCAPTCHA challenges
"""

import asyncio
from nodrive_gpm_package import CaptchaService, CaptchaServiceException

# Your API keys
ACHICAPTCHA_CLIENT_KEY = "your_achicaptcha_api_key_here"
GOOGLE_SECRET_KEY = "your_google_recaptcha_secret_here"  # Optional, for verification


def example_solve_recaptcha_v2():
    """Example: Solve reCAPTCHA v2"""
    print("=" * 60)
    print("Example 1: Solve reCAPTCHA v2")
    print("=" * 60)
    
    # Initialize service
    service = CaptchaService(
        client_key=ACHICAPTCHA_CLIENT_KEY,
        google_secret_key=GOOGLE_SECRET_KEY,
        debug=True
    )
    
    try:
        # Solve captcha
        solution = service.solve_recaptcha_v2(
            website_url="https://www.google.com/recaptcha/api2/demo",
            website_key="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
        )
        
        print(f"\n✅ Captcha solved successfully!")
        print(f"Task ID: {solution.task_id}")
        print(f"Token: {solution.token[:50]}...")
        print(f"Status: {solution.status}")
        if solution.cost:
            print(f"Cost: ${solution.cost}")
        
        return solution.token
        
    except CaptchaServiceException as e:
        print(f"❌ Error: {e}")
        return None


def example_solve_with_proxy():
    """Example: Solve reCAPTCHA v2 with proxy"""
    print("\n" + "=" * 60)
    print("Example 2: Solve reCAPTCHA v2 with Proxy")
    print("=" * 60)
    
    service = CaptchaService(client_key=ACHICAPTCHA_CLIENT_KEY)
    
    try:
        solution = service.solve_recaptcha_v2(
            website_url="https://www.google.com/recaptcha/api2/demo",
            website_key="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
            proxy="123.45.67.89:8080:username:password",  # Your proxy
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        )
        
        print(f"✅ Captcha solved with proxy!")
        print(f"Token: {solution.token[:50]}...")
        
    except CaptchaServiceException as e:
        print(f"❌ Error: {e}")


def example_solve_recaptcha_v3():
    """Example: Solve reCAPTCHA v3"""
    print("\n" + "=" * 60)
    print("Example 3: Solve reCAPTCHA v3")
    print("=" * 60)
    
    service = CaptchaService(client_key=ACHICAPTCHA_CLIENT_KEY)
    
    try:
        solution = service.solve_recaptcha_v3(
            website_url="https://example.com",
            website_key="6LcR_okUAAAAAPYrPe-HK_0RULO1aZM15ENyM-Mf",
            action="homepage",
            min_score=0.7
        )
        
        print(f"✅ reCAPTCHA v3 solved!")
        print(f"Token: {solution.token[:50]}...")
        
    except CaptchaServiceException as e:
        print(f"❌ Error: {e}")


def example_verify_token():
    """Example: Verify reCAPTCHA token"""
    print("\n" + "=" * 60)
    print("Example 4: Verify reCAPTCHA Token")
    print("=" * 60)
    
    service = CaptchaService(
        client_key=ACHICAPTCHA_CLIENT_KEY,
        google_secret_key=GOOGLE_SECRET_KEY
    )
    
    try:
        # First solve captcha
        print("Solving captcha...")
        solution = service.solve_recaptcha_v2(
            website_url="https://www.google.com/recaptcha/api2/demo",
            website_key="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
        )
        
        # Then verify
        print("\nVerifying token with Google...")
        verification = service.verify_recaptcha(solution.token)
        
        if verification.success:
            print("✅ Token is valid!")
            print(f"Hostname: {verification.hostname}")
            print(f"Challenge timestamp: {verification.challenge_ts}")
            if verification.score:
                print(f"Score: {verification.score}")
        else:
            print("❌ Token verification failed")
            print(f"Error codes: {verification.error_codes}")
            
    except CaptchaServiceException as e:
        print(f"❌ Error: {e}")


def example_get_balance():
    """Example: Check account balance"""
    print("\n" + "=" * 60)
    print("Example 5: Check Account Balance")
    print("=" * 60)
    
    service = CaptchaService(client_key=ACHICAPTCHA_CLIENT_KEY)
    
    try:
        balance = service.get_balance()
        print(f"💰 Account Balance: ${balance['balance']}")
        
    except CaptchaServiceException as e:
        print(f"❌ Error: {e}")


async def example_integrate_with_browser():
    """Example: Integrate captcha solving with browser automation"""
    print("\n" + "=" * 60)
    print("Example 6: Integrate with Browser Automation")
    print("=" * 60)
    
    from nodrive_gpm_package import GPMClient
    
    # Initialize services
    captcha_service = CaptchaService(client_key=ACHICAPTCHA_CLIENT_KEY)
    gpm_client = GPMClient()
    
    try:
        # Launch browser
        print("Launching browser...")
        browser = await gpm_client.launch("captcha_profile")
        
        if not browser:
            print("Failed to launch browser")
            return
        
        # Navigate to page with captcha
        print("Navigating to page...")
        page = await browser.get("https://www.google.com/recaptcha/api2/demo")
        
        # Get captcha site key from page (in real scenario)
        website_key = "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
        website_url = page.url
        
        # Solve captcha
        print("Solving captcha...")
        solution = captcha_service.solve_recaptcha_v2(
            website_url=website_url,
            website_key=website_key
        )
        
        print(f"✅ Got captcha token: {solution.token[:50]}...")
        
        # Inject token into page (example)
        script = f"""
        document.getElementById('g-recaptcha-response').innerHTML = '{solution.token}';
        """
        
        try:
            await page.evaluate(script)
            print("✅ Token injected into page")
        except:
            print("Note: Token injection depends on page structure")
        
        # Submit form or continue automation...
        
        # Close browser
        gpm_client.close("captcha_profile")
        print("✅ Browser closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_custom_timeout():
    """Example: Custom timeout and poll interval"""
    print("\n" + "=" * 60)
    print("Example 7: Custom Timeout Settings")
    print("=" * 60)
    
    # Initialize with custom settings
    service = CaptchaService(
        client_key=ACHICAPTCHA_CLIENT_KEY,
        default_timeout=180,  # 3 minutes
        poll_interval=5,      # Check every 5 seconds
        debug=True
    )
    
    try:
        solution = service.solve_recaptcha_v2(
            website_url="https://www.google.com/recaptcha/api2/demo",
            website_key="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
            timeout=60  # Override default for this request
        )
        
        print(f"✅ Solved with custom timeout: {solution.token[:50]}...")
        
    except CaptchaServiceException as e:
        print(f"❌ Error: {e}")


def example_batch_solving():
    """Example: Solve multiple captchas"""
    print("\n" + "=" * 60)
    print("Example 8: Batch Captcha Solving")
    print("=" * 60)
    
    service = CaptchaService(client_key=ACHICAPTCHA_CLIENT_KEY)
    
    # List of captchas to solve
    captchas = [
        {
            "url": "https://www.google.com/recaptcha/api2/demo",
            "key": "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
        },
        # Add more captchas here
    ]
    
    results = []
    
    for i, captcha in enumerate(captchas, 1):
        print(f"\nSolving captcha {i}/{len(captchas)}...")
        try:
            solution = service.solve_recaptcha_v2(
                website_url=captcha["url"],
                website_key=captcha["key"]
            )
            results.append({
                "success": True,
                "token": solution.token,
                "cost": solution.cost
            })
            print(f"✅ Captcha {i} solved")
        except CaptchaServiceException as e:
            results.append({
                "success": False,
                "error": str(e)
            })
            print(f"❌ Captcha {i} failed: {e}")
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    total_cost = sum(r.get("cost", 0) for r in results if r["success"])
    
    print(f"\n📊 Summary:")
    print(f"   Total: {len(results)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {len(results) - successful}")
    print(f"   Total cost: ${total_cost:.4f}")


def example_error_handling():
    """Example: Comprehensive error handling"""
    print("\n" + "=" * 60)
    print("Example 9: Error Handling")
    print("=" * 60)
    
    service = CaptchaService(client_key=ACHICAPTCHA_CLIENT_KEY)
    
    # Test various error scenarios
    test_cases = [
        {
            "name": "Invalid site key",
            "url": "https://example.com",
            "key": "invalid_key"
        },
        {
            "name": "Invalid URL",
            "url": "not-a-url",
            "key": "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
        },
    ]
    
    for test in test_cases:
        print(f"\n🧪 Testing: {test['name']}")
        try:
            solution = service.solve_recaptcha_v2(
                website_url=test["url"],
                website_key=test["key"],
                timeout=30
            )
            print(f"✅ Unexpectedly succeeded")
        except CaptchaServiceException as e:
            print(f"❌ Caught expected error: {e}")
        except Exception as e:
            print(f"⚠️ Unexpected error type: {type(e).__name__}: {e}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("🤖 Captcha Service Examples")
    print("=" * 60)
    print("\nIMPORTANT: Update ACHICAPTCHA_CLIENT_KEY with your API key")
    print("=" * 60)
    
    # Uncomment the examples you want to run
    
    # Basic examples
    # example_solve_recaptcha_v2()
    # example_solve_with_proxy()
    # example_solve_recaptcha_v3()
    # example_verify_token()
    # example_get_balance()
    
    # Advanced examples
    # asyncio.run(example_integrate_with_browser())
    # example_custom_timeout()
    # example_batch_solving()
    # example_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ Examples completed")
    print("=" * 60)


if __name__ == "__main__":
    main()


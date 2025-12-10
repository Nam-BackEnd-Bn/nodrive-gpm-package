import random


class DynamicUserAgentGenerator:
    """Dynamic User Agent Generator that matches real browser version"""

    def __init__(self):
        # Common device specs
        self.mobile_devices = [
            ("Pixel 8", "Linux; Android 14"),
            ("Pixel 7 Pro", "Linux; Android 14"),
            ("SM-G998B", "Linux; Android 14"),  # Galaxy S21 Ultra
            ("SM-S918B", "Linux; Android 14"),  # Galaxy S23 Ultra
            ("OnePlus 12", "Linux; Android 14"),
            ("2201116SG", "Linux; Android 13"),  # Xiaomi 12
            ("CPH2451", "Linux; Android 13"),  # OnePlus 11
            ("SM-A546B", "Linux; Android 14"),  # Galaxy A54
        ]

        self.tablet_devices = [
            ("SM-X900", "Linux; Android 13"),  # Galaxy Tab S8 Ultra
            ("SM-T970", "Linux; Android 13"),  # Galaxy Tab S7+
            ("Lenovo TB-X306X", "Linux; Android 12"),
            ("Xiaomi Pad 6", "Linux; Android 13"),
        ]

        self.desktop_platforms = [
            "Windows NT 10.0; Win64; x64",
            "Windows NT 11.0; Win64; x64",
            "Macintosh; Intel Mac OS X 10_15_7",
            "Macintosh; Intel Mac OS X 14_2",
            "X11; Linux x86_64",
        ]

    def generate_mobile_ua(self, chrome_version: str, webkit_version: str) -> str:
        """Generate realistic mobile user agent"""
        device, platform = random.choice(self.mobile_devices)

        # Generate realistic WebKit version (usually close to Chrome)
        return f"Mozilla/5.0 ({platform}; {device}) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/{webkit_version}"

    def generate_tablet_ua(self, chrome_version: str, webkit_version: str) -> str:
        """Generate realistic tablet user agent"""
        device, platform = random.choice(self.tablet_devices)

        return f"Mozilla/5.0 ({platform}; {device}) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}"

    def generate_desktop_ua(self, chrome_version: str, webkit_version: str) -> str:
        """Generate realistic desktop user agent"""
        platform = random.choice(self.desktop_platforms)

        return f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}"

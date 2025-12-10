import time
import statistics
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
import socks  # Thư viện PySocks


@dataclass
class ProxyInfo:
    """Thông tin proxy với hỗ trợ SOCKS5"""

    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "socks5"  # Mặc định là SOCKS5

    def get_proxy_url(self) -> str:
        """Tạo proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    def get_proxy_dict(self) -> dict:
        """Tạo proxy dict cho requests với hỗ trợ SOCKS"""
        proxy_url = self.get_proxy_url()

        if self.protocol in ["socks4", "socks5"]:
            return {
                "http": proxy_url,
                "https": proxy_url,
                "socks4": proxy_url if self.protocol == "socks4" else None,
                "socks5": proxy_url if self.protocol == "socks5" else None,
            }
        return {"http": proxy_url, "https": proxy_url}


@dataclass
class SpeedTestResult:
    """Kết quả test tốc độ"""

    proxy: ProxyInfo
    is_working: bool
    response_time: float  # seconds
    download_speed: float  # MB/s
    upload_speed: float  # MB/s
    latency: float  # ms
    error: Optional[str] = None

    def __str__(self):
        if not self.is_working:
            return f"❌ {self.proxy.host}:{self.proxy.port} - Error: {self.error}"
        return f"✅ {self.proxy.host}:{self.proxy.port} - Speed: {self.download_speed:.2f} MB/s, Latency: {self.latency:.0f}ms"


class ProxySpeedTester:
    """Class chính để test tốc độ proxy với hỗ trợ SOCKS5"""

    def __init__(self):
        # URLs để test (dùng HTTP thay vì HTTPS để tránh vấn đề chứng chỉ)
        self.test_urls = {
            "ping": "http://httpbin.org/status/200",
            "small_file": "http://httpbin.org/bytes/1024",  # 1KB
            "medium_file": "http://httpbin.org/bytes/102400",  # 100KB
            "large_file": "http://httpbin.org/bytes/1048576",  # 1MB
            "ip_check": "http://httpbin.org/ip",
            "location_check": "http://ipapi.co/json",
        }

        # Timeout settings
        self.timeout = 30  # seconds
        self.connection_timeout = 15  # seconds

    def _set_socks_proxy(self, proxy: ProxyInfo):
        """Thiết lập SOCKS proxy ở mức socket (cho các thư viện không hỗ trợ proxy)"""
        if proxy.protocol == "socks5":
            socks.set_default_proxy(
                socks.SOCKS5,
                proxy.host,
                proxy.port,
                username=proxy.username,
                password=proxy.password,
            )
            socket.socket = socks.socksocket
        elif proxy.protocol == "socks4":
            socks.set_default_proxy(
                socks.SOCKS4, proxy.host, proxy.port, username=proxy.username
            )
            socket.socket = socks.socksocket

    def test_proxy_connectivity(self, proxy: ProxyInfo) -> bool:
        """Test kết nối cơ bản của proxy"""
        try:
            # Thiết lập SOCKS proxy nếu cần
            if proxy.protocol in ["socks4", "socks5"]:
                self._set_socks_proxy(proxy)

            response = requests.get(
                self.test_urls["ping"],
                proxies=proxy.get_proxy_dict(),
                timeout=self.connection_timeout,
            )
            return response.status_code == 200
        except Exception as e:
            return False
        finally:
            # Reset proxy settings
            if proxy.protocol in ["socks4", "socks5"]:
                socks.set_default_proxy()
                socket.socket = socket._socketobject

    def measure_latency(self, proxy: ProxyInfo, num_tests: int = 3) -> float:
        """Đo độ trễ (latency) của proxy"""
        latencies = []

        for _ in range(num_tests):
            try:
                if proxy.protocol in ["socks4", "socks5"]:
                    self._set_socks_proxy(proxy)

                start_time = time.time()
                response = requests.get(
                    self.test_urls["ping"],
                    proxies=proxy.get_proxy_dict(),
                    timeout=self.connection_timeout,
                )
                end_time = time.time()

                if response.status_code == 200:
                    latency = (end_time - start_time) * 1000  # Convert to ms
                    latencies.append(latency)

            except Exception as e:
                continue
            finally:
                if proxy.protocol in ["socks4", "socks5"]:
                    socks.set_default_proxy()
                    socket.socket = socket._socketobject

        return statistics.mean(latencies) if latencies else float("inf")

    def measure_download_speed(self, proxy: ProxyInfo) -> float:
        """Đo tốc độ download"""
        try:
            if proxy.protocol in ["socks4", "socks5"]:
                self._set_socks_proxy(proxy)

            start_time = time.time()
            response = requests.get(
                self.test_urls["medium_file"],
                proxies=proxy.get_proxy_dict(),
                timeout=self.timeout,
                stream=True,
            )

            if response.status_code != 200:
                return 0.0

            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                total_size += len(chunk)

            end_time = time.time()
            duration = max(end_time - start_time, 0.001)  # Đảm bảo không chia cho 0

            # Convert to MB/s
            speed_mbps = (total_size / (1024 * 1024)) / duration
            return speed_mbps

        except Exception as e:
            return 0.0
        finally:
            if proxy.protocol in ["socks4", "socks5"]:
                socks.set_default_proxy()
                socket.socket = socket._socketobject

    def test_single_proxy(self, proxy: ProxyInfo) -> SpeedTestResult:
        """Test một proxy đơn lẻ"""

        # Test kết nối cơ bản
        if not self.test_proxy_connectivity(proxy):
            return SpeedTestResult(
                proxy=proxy,
                is_working=False,
                response_time=0.0,
                download_speed=0.0,
                upload_speed=0.0,
                latency=0.0,
                error="Connection failed",
            )

        try:
            # Đo các thông số
            latency = self.measure_latency(proxy)
            download_speed = self.measure_download_speed(proxy)

            # Đo response time tổng thể
            start_time = time.time()
            requests.get(
                self.test_urls["ping"],
                proxies=proxy.get_proxy_dict(),
                timeout=self.connection_timeout,
            )
            response_time = time.time() - start_time

            result = SpeedTestResult(
                proxy=proxy,
                is_working=True,
                response_time=response_time,
                download_speed=download_speed,
                upload_speed=0.0,  # Tạm bỏ qua upload test cho SOCKS
                latency=latency,
            )

            return result

        except Exception as e:
            return SpeedTestResult(
                proxy=proxy,
                is_working=False,
                response_time=0.0,
                download_speed=0.0,
                upload_speed=0.0,
                latency=0.0,
                error=str(e),
            )

    def test_multiple_proxies(
        self, proxies: List[ProxyInfo], max_workers: int = 5
    ) -> List[SpeedTestResult]:
        """Test nhiều proxy đồng thời"""
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.test_single_proxy, proxy): proxy
                for proxy in proxies
            }

            for future in as_completed(future_to_proxy):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print("ok")

        return results

    def get_fastest_proxy(self, proxies: List[ProxyInfo]) -> Optional[ProxyInfo]:
        """Tìm proxy nhanh nhất"""

        results = self.test_multiple_proxies(proxies)
        working_results = [r for r in results if r.is_working]

        if not working_results:
            return None

        # Sắp xếp theo tốc độ download (ưu tiên) và latency
        working_results.sort(key=lambda x: (-x.download_speed, x.latency))

        for i, result in enumerate(working_results, 1):
            status = "🏆 FASTEST" if i == 1 else f"#{i}"

        fastest = working_results[0]

        return fastest.proxy


# Example usage với SOCKS5 proxy
def example_usage():
    """Ví dụ sử dụng với SOCKS5 proxy"""

    # Định nghĩa các proxy SOCKS5
    proxies = [
        ProxyInfo(
            host="206.125.175.178",
            port=18489,
            username="cPCLZN",
            password="YGdaJt",
            protocol="socks5",
        ),
        ProxyInfo(
            host="184.164.87.105",
            port=28155,
            username="proxy",
            password="1b65d88a",
            protocol="socks5",
        ),
    ]

    # Test và chọn proxy nhanh nhất
    tester = ProxySpeedTester()
    fastest_proxy = tester.get_fastest_proxy(proxies)

    if fastest_proxy:
        return fastest_proxy

    return None


if __name__ == "__main__":
    example_usage()

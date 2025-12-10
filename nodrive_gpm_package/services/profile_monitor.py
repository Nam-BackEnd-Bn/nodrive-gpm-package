"""
Profile monitoring service
Handles profile status detection and process management
"""

import os
import psutil
import win32gui
from typing import Dict, List, Set, Optional
from win32process import GetWindowThreadProcessId
from concurrent.futures import ThreadPoolExecutor

from ..config import GPMConfig, get_config
from ..enums import ProfileStatus


class ProfileStatusResult:
    """Result of profile status check"""
    
    def __init__(
        self,
        stopped: List[str] = None,
        running: List[str] = None,
        pending: List[str] = None,
    ):
        self.stopped = stopped or []
        self.running = running or []
        self.pending = pending or []
    
    def get_status(self, profile_name: str) -> ProfileStatus:
        """Get status for a specific profile"""
        if profile_name in self.running:
            return ProfileStatus.RUNNING
        elif profile_name in self.pending:
            return ProfileStatus.PENDING
        elif profile_name in self.stopped:
            return ProfileStatus.STOPPED
        return ProfileStatus.UNKNOWN
    
    def is_running(self, profile_name: str) -> bool:
        """Check if profile is actively running"""
        return profile_name in self.running
    
    def is_pending(self, profile_name: str) -> bool:
        """Check if profile is pending (process exists but not active)"""
        return profile_name in self.pending


class ProfileMonitor:
    """
    Monitor Chrome profile status
    
    Detects whether profiles are:
    - STOPPED: No Chrome process
    - RUNNING: Chrome process with active window or CPU usage
    - PENDING: Chrome process exists but appears idle
    """
    
    def __init__(self, config: Optional[GPMConfig] = None):
        """
        Initialize profile monitor
        
        Args:
            config: Optional GPMConfig instance
        """
        self.config = config or get_config()
        self.profiles_dir = self.config.profiles_directory
    
    def check_profiles_running(self, profile_names: List[str]) -> Dict[str, bool]:
        """
        Quick check if specific profiles are running
        
        Args:
            profile_names: List of profile names to check
            
        Returns:
            Dict mapping profile name to running status
        """
        results = {profile: False for profile in profile_names}
        
        # Get all Chrome processes once
        chrome_processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] == "chrome.exe" and proc.info["cmdline"]:
                    cmdline = " ".join(proc.info["cmdline"])
                    if self.profiles_dir in cmdline:
                        chrome_processes.append(cmdline)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check each profile
        for profile in profile_names:
            profile_path = os.path.join(self.profiles_dir, profile)
            for cmdline in chrome_processes:
                if profile_path in cmdline:
                    results[profile] = True
                    break
        
        return results
    
    def check_all_profiles_status(self) -> ProfileStatusResult:
        """
        Comprehensive status check for all profiles
        
        Returns:
            ProfileStatusResult with stopped, running, and pending profiles
        """
        if not os.path.exists(self.profiles_dir):
            print(f"⚠️ Profiles directory does not exist: {self.profiles_dir}")
            return ProfileStatusResult()
        
        # Get all profile directories
        profiles = [
            d
            for d in os.listdir(self.profiles_dir)
            if os.path.isdir(os.path.join(self.profiles_dir, d))
        ]
        
        if not profiles:
            return ProfileStatusResult(stopped=profiles)
        
        # Normalize profile paths
        profile_paths = {
            profile: os.path.join(self.profiles_dir, profile).lower().replace("\\", "/")
            for profile in profiles
        }
        
        # Scan all Chrome processes once
        chrome_processes = self._get_chrome_processes()
        
        if not chrome_processes:
            return ProfileStatusResult(stopped=profiles)
        
        # Get active window PIDs
        active_pids = self._get_active_window_pids()
        
        # Map profiles to their processes
        profile_to_processes = {profile: [] for profile in profiles}
        for proc in chrome_processes:
            cmdline = proc["cmdline"]
            for profile, normalized_path in profile_paths.items():
                if normalized_path in cmdline or profile.lower() in cmdline:
                    profile_to_processes[profile].append(proc)
        
        # Check status for each profile in parallel
        result = {}
        with ThreadPoolExecutor(max_workers=min(len(profiles), 10)) as executor:
            futures = [
                executor.submit(
                    self._check_profile_status,
                    profile,
                    profile_to_processes[profile],
                    active_pids,
                )
                for profile in profiles
            ]
            
            for future in futures:
                profile, status_info = future.result()
                result[profile] = status_info
        
        # Transform results
        stopped, running, pending = [], [], []
        
        for profile, status_info in result.items():
            if not status_info["is_running"] or status_info["status"] == "stopped":
                stopped.append(profile)
            elif status_info["status"] == "running":
                running.append(profile)
            elif status_info["status"] == "pending":
                pending.append(profile)
        
        return ProfileStatusResult(stopped=stopped, running=running, pending=pending)
    
    def _get_chrome_processes(self) -> List[Dict]:
        """Get all Chrome processes with their info"""
        chrome_processes = []
        
        for proc in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent"]):
            try:
                if proc.info["name"] and "chrome" in proc.info["name"].lower():
                    cmdline = proc.info.get("cmdline") or []
                    cmdline_str = (
                        " ".join([str(cmd) for cmd in cmdline]).lower().replace("\\", "/")
                    )
                    chrome_processes.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cpu_initial": proc.info["cpu_percent"],
                            "cmdline": cmdline_str,
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return chrome_processes
    
    def _get_active_window_pids(self) -> Set[int]:
        """Get PIDs of processes with active windows"""
        active_pids = set()
        
        def enum_callback(hwnd, active_pids):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                try:
                    _, pid = GetWindowThreadProcessId(hwnd)
                    if win32gui.GetForegroundWindow() == hwnd:
                        active_pids.add(pid)
                except:
                    pass
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, active_pids)
        except:
            pass
        
        return active_pids
    
    def _check_profile_status(
        self,
        profile: str,
        processes: List[Dict],
        active_pids: Set[int],
    ) -> tuple:
        """
        Check status of a single profile
        
        Returns:
            Tuple of (profile_name, status_dict)
        """
        if not processes:
            return (profile, {"is_running": False, "status": "stopped"})
        
        # Check if profile has active window
        is_active_window = any(proc["pid"] in active_pids for proc in processes)
        
        # Check CPU usage
        cpu_changed = False
        for proc in processes:
            try:
                p = psutil.Process(proc["pid"])
                cpu_initial = proc["cpu_initial"]
                cpu_current = p.cpu_percent(interval=self.config.cpu_check_interval)
                
                if (
                    abs(cpu_current - cpu_initial) > self.config.cpu_threshold
                    or cpu_initial > self.config.cpu_threshold
                    or cpu_current > self.config.cpu_threshold
                ):
                    cpu_changed = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        is_running = cpu_changed or is_active_window
        status = "running" if is_running else "pending"
        
        return (profile, {"is_running": True, "status": status})

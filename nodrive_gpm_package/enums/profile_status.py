"""Profile status enumeration"""

from enum import Enum


class ProfileStatus(str, Enum):
    """Profile running status"""
    
    STOPPED = "stopped"
    RUNNING = "running"
    PENDING = "pending"  # Process exists but not actively running
    UNKNOWN = "unknown"


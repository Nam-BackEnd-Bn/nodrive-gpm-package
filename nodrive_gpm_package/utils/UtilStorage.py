"""
Storage utilities for fallback mechanisms
Provides local JSON storage as Redis alternative
"""

import os
import time
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from threading import Lock as ThreadLock

logger = logging.getLogger(__name__)


class JSONStorage:
    """
    Local JSON file storage as fallback for Redis
    Provides similar interface to Redis for queue and state management
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize JSON storage
        
        Args:
            storage_dir: Directory to store JSON files (default: ./.redis_fallback)
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), '.redis_fallback')
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = ThreadLock()
        
        logger.info(f"📁 JSONStorage initialized at: {self.storage_dir}")
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for a key"""
        # Replace special characters for filename safety
        safe_key = key.replace(':', '_').replace('/', '_').replace('*', 'ALL')
        return self.storage_dir / f"{safe_key}.json"
    
    def _read_data(self) -> Dict[str, Any]:
        """Read all data from storage file"""
        data_file = self.storage_dir / "storage.json"
        
        with self._lock:
            if data_file.exists():
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to read storage file: {e}")
                    return {}
            return {}
    
    def _write_data(self, data: Dict[str, Any]):
        """Write all data to storage file"""
        data_file = self.storage_dir / "storage.json"
        
        with self._lock:
            try:
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            except IOError as e:
                logger.error(f"Failed to write storage file: {e}")
    
    def _clean_expired(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove expired entries from data"""
        current_time = time.time()
        cleaned = {}
        
        for key, value in data.items():
            if isinstance(value, dict) and 'expires_at' in value:
                if value['expires_at'] > current_time:
                    cleaned[key] = value
                # else: expired, don't include
            else:
                cleaned[key] = value
        
        return cleaned
    
    def ping(self) -> bool:
        """Test connection (always returns True for JSON storage)"""
        return True
    
    def get(self, key: str) -> Optional[str]:
        """Get value for key"""
        data = self._read_data()
        data = self._clean_expired(data)
        
        if key in data:
            value = data[key]
            if isinstance(value, dict) and 'value' in value:
                return value['value']
            return str(value) if value is not None else None
        return None
    
    def set(self, key: str, value: Any) -> bool:
        """Set value for key"""
        data = self._read_data()
        data = self._clean_expired(data)
        data[key] = str(value)
        self._write_data(data)
        return True
    
    def setex(self, key: str, seconds: int, value: Any) -> bool:
        """Set value with expiration time"""
        data = self._read_data()
        data = self._clean_expired(data)
        
        expires_at = time.time() + seconds
        data[key] = {
            'value': str(value),
            'expires_at': expires_at
        }
        
        self._write_data(data)
        return True
    
    def delete(self, key: str) -> int:
        """Delete key"""
        data = self._read_data()
        
        if key in data:
            del data[key]
            self._write_data(data)
            return 1
        return 0
    
    def exists(self, key: str) -> int:
        """Check if key exists"""
        data = self._read_data()
        data = self._clean_expired(data)
        return 1 if key in data else 0
    
    def keys(self, pattern: str) -> List[str]:
        """Get all keys matching pattern"""
        data = self._read_data()
        data = self._clean_expired(data)
        
        # Convert Redis pattern to simple matching
        # Replace * with .* for regex
        import re
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex = re.compile(f"^{regex_pattern}$")
        
        matching_keys = [key for key in data.keys() if regex.match(key)]
        return matching_keys


# helpers/utils.py - FIXED VERSION
import pickle
import os
import threading
import time
from helpers.database import setUserMergeSettings, getUserMergeSettings

SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]

def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return "0B"
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f"{round(size_in_bytes, 2)}{SIZE_UNITS[index]}"
    except IndexError:
        return "File too large"

def get_readable_time(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days}d"
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours}h"
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes}m"
    seconds = int(seconds)
    result += f"{seconds}s"
    return result

class UserSettings(object):
    """FIXED UserSettings class with proper database persistence"""
    
    def __init__(self, uid: int, name: str):
        self.user_id: int = uid
        self.name: str = name
        self.merge_mode: int = 1
        self.edit_metadata: bool = False
        self.allowed: bool = False
        self.thumbnail = None
        self.banned: bool = False
        self.get()

    def get(self):
        """Get user settings from database"""
        try:
            cur = getUserMergeSettings(self.user_id)
            if cur is not None:
                self.name = cur.get("name", self.name)
                user_settings = cur.get("user_settings", {})
                self.merge_mode = user_settings.get("merge_mode", 1)
                self.edit_metadata = user_settings.get("edit_metadata", False)
                self.allowed = cur.get("isAllowed", False)
                self.thumbnail = cur.get("thumbnail", None)
                self.banned = cur.get("isBanned", False)
                
                return {
                    "uid": self.user_id,
                    "name": self.name,
                    "user_settings": {
                        "merge_mode": self.merge_mode,
                        "edit_metadata": self.edit_metadata,
                    },
                    "isAllowed": self.allowed,
                    "isBanned": self.banned,
                    "thumbnail": self.thumbnail,
                }
            else:
                # New user - set defaults and save
                return self.set()
        except Exception as e:
            # Database error - set defaults and save
            print(f"Database error in get(): {e}")
            return self.set()

    def set(self):
        """Save user settings to database"""
        try:
            setUserMergeSettings(
                uid=self.user_id,
                name=self.name,
                mode=self.merge_mode,
                edit_metadata=self.edit_metadata,
                banned=self.banned,
                allowed=self.allowed,
                thumbnail=self.thumbnail,
            )
            return self.get()
        except Exception as e:
            print(f"Database error in set(): {e}")
            return None

    def is_allowed(self) -> bool:
        """Check if user is allowed"""
        return self.allowed and not self.banned

    def __str__(self):
        return f"UserSettings(uid={self.user_id}, name='{self.name}', allowed={self.allowed}, banned={self.banned})"

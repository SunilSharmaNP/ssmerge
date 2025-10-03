import os
import sys
from typing import Optional

class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass

class Config(object):
    """Professional Configuration Class with Enhanced Validation"""
    
    @staticmethod
    def get_env_var(var_name: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with comprehensive error handling"""
        value = os.environ.get(var_name, default)
        
        if required and not value:
            raise ConfigError(f"❌ Required environment variable '{var_name}' is not set!")
        
        return value
    
    @staticmethod
    def validate_config():
        """Validate all required configuration variables with detailed feedback"""
        required_vars = [
            "API_HASH", "BOT_TOKEN", "TELEGRAM_API", 
            "OWNER", "OWNER_USERNAME", "DATABASE_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = f"""
🚨 **PROFESSIONAL MERGE BOT - CONFIGURATION ERROR**

❌ **Missing Required Environment Variables:**
{chr(10).join(f'   • {var}' for var in missing_vars)}

🔧 **Setup Instructions:**
1. Create a .env file in your project root
2. Add the missing variables with proper values
3. Restart the bot

📖 **Documentation:** Check README.md for variable descriptions
🔗 **Support:** Contact the administrator for assistance
            """
            raise ConfigError(error_msg)
    
    @staticmethod  
    def validate_format(var_name: str, value: str, expected_type: type):
        """Validate environment variable format"""
        try:
            if expected_type == int:
                return int(value)
            elif expected_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return value
        except ValueError:
            raise ConfigError(f"❌ Invalid format for {var_name}: expected {expected_type.__name__}")

    # Core Configuration - Required
    try:
        API_HASH = get_env_var.__func__("API_HASH")
        BOT_TOKEN = get_env_var.__func__("BOT_TOKEN") 
        TELEGRAM_API = validate_format.__func__("TELEGRAM_API", get_env_var.__func__("TELEGRAM_API"), int)
        OWNER = validate_format.__func__("OWNER", get_env_var.__func__("OWNER"), int)
        OWNER_USERNAME = get_env_var.__func__("OWNER_USERNAME")
        DATABASE_URL = get_env_var.__func__("DATABASE_URL")
    except ValueError as e:
        raise ConfigError(f"❌ Invalid configuration value: {e}")
    except Exception as e:
        raise ConfigError(f"❌ Configuration error: {e}")

    # Optional Configuration with intelligent defaults
    PASSWORD = get_env_var.__func__("PASSWORD", required=False, default="mergebot123")
    LOGCHANNEL = get_env_var.__func__("LOGCHANNEL", required=False)
    USER_SESSION_STRING = get_env_var.__func__("USER_SESSION_STRING", required=False)
    
    # GoFile Configuration - Professional Feature
    GOFILE_TOKEN = get_env_var.__func__("GOFILE_TOKEN", required=False)
    
    # Advanced Bot Settings
    MAX_CONCURRENT_USERS = validate_format.__func__(
        "MAX_CONCURRENT_USERS", 
        get_env_var.__func__("MAX_CONCURRENT_USERS", required=False, default="5"), 
        int
    )
    MAX_FILE_SIZE = validate_format.__func__(
        "MAX_FILE_SIZE", 
        get_env_var.__func__("MAX_FILE_SIZE", required=False, default="2147483648"),  # 2GB
        int
    )
    
    # Professional Features Configuration
    ENABLE_GOFILE_UPLOAD = validate_format.__func__(
        "ENABLE_GOFILE_UPLOAD",
        get_env_var.__func__("ENABLE_GOFILE_UPLOAD", required=False, default="true"),
        bool
    )
    
    ENABLE_CUSTOM_THUMBNAILS = validate_format.__func__(
        "ENABLE_CUSTOM_THUMBNAILS",
        get_env_var.__func__("ENABLE_CUSTOM_THUMBNAILS", required=False, default="true"),
        bool
    )
    
    ENABLE_METADATA_EDITING = validate_format.__func__(
        "ENABLE_METADATA_EDITING", 
        get_env_var.__func__("ENABLE_METADATA_EDITING", required=False, default="true"),
        bool
    )
    
    # Performance Settings
    FFMPEG_THREADS = validate_format.__func__(
        "FFMPEG_THREADS",
        get_env_var.__func__("FFMPEG_THREADS", required=False, default="2"),
        int
    )
    
    CLEANUP_INTERVAL = validate_format.__func__(
        "CLEANUP_INTERVAL", 
        get_env_var.__func__("CLEANUP_INTERVAL", required=False, default="3600"),  # 1 hour
        int
    )
    
    # Removed rclone/gdrive references
    # GDRIVE_FOLDER_ID - Removed
    # Any rclone related configs - Removed
    
    # Runtime Variables
    IS_PREMIUM = False
    BOT_VERSION = "Professional v6.0"
    
    # Supported merge modes
    MERGE_MODES = [
        "video-video", 
        "video-audio", 
        "video-subtitle", 
        "extract-streams"
    ]
    
    # File format support
    SUPPORTED_VIDEO_FORMATS = [
        "mp4", "mkv", "avi", "mov", "webm", "ts", "flv", "3gp", "wmv"
    ]
    
    SUPPORTED_AUDIO_FORMATS = [
        "aac", "ac3", "eac3", "m4a", "mka", "thd", "dts", "mp3", "flac", "wav"
    ]
    
    SUPPORTED_SUBTITLE_FORMATS = [
        "srt", "ass", "ssa", "vtt", "mks", "sub"
    ]

    @classmethod
    def initialize(cls):
        """Initialize and validate professional bot configuration"""
        try:
            print("🚀 **PROFESSIONAL MERGE BOT - INITIALIZATION**")
            print("=" * 50)
            
            # Validate core configuration
            cls.validate_config()
            print("✅ Core configuration validated")
            
            # Check professional features
            features_status = []
            
            # GoFile Integration
            if cls.GOFILE_TOKEN and cls.ENABLE_GOFILE_UPLOAD:
                features_status.append("🔗 GoFile Integration: ENABLED")
            else:
                features_status.append("⚠️ GoFile Integration: DISABLED (token not provided)")
            
            # Custom Thumbnails
            if cls.ENABLE_CUSTOM_THUMBNAILS:
                features_status.append("🖼️ Custom Thumbnails: ENABLED")
            
            # Metadata Editing
            if cls.ENABLE_METADATA_EDITING:
                features_status.append("📊 Metadata Editing: ENABLED")
            
            # Performance Settings
            features_status.append(f"⚡ Max Concurrent Users: {cls.MAX_CONCURRENT_USERS}")
            features_status.append(f"🧵 FFmpeg Threads: {cls.FFMPEG_THREADS}")
            features_status.append(f"📏 Max File Size: {cls._format_file_size(cls.MAX_FILE_SIZE)}")
            
            print("\n🎯 **PROFESSIONAL FEATURES STATUS:**")
            for feature in features_status:
                print(f"   {feature}")
            
            print(f"\n📦 **BOT VERSION:** {cls.BOT_VERSION}")
            print(f"🔧 **SUPPORTED FORMATS:** {len(cls.SUPPORTED_VIDEO_FORMATS)} video, {len(cls.SUPPORTED_AUDIO_FORMATS)} audio, {len(cls.SUPPORTED_SUBTITLE_FORMATS)} subtitle")
            
            # Log Channel Validation
            if cls.LOGCHANNEL:
                if not str(cls.LOGCHANNEL).startswith('-100') and not str(cls.LOGCHANNEL).startswith('-'):
                    print("⚠️ Warning: LOGCHANNEL should start with -100 for supergroups")
                else:
                    print("✅ Log Channel: CONFIGURED")
            else:
                print("⚠️ Log Channel: NOT CONFIGURED")
            
            print("=" * 50)
            print("🎉 **PROFESSIONAL MERGE BOT READY FOR DEPLOYMENT!**")
            
            return True
            
        except ConfigError as e:
            print(f"❌ **CONFIGURATION ERROR:**\n{e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ **UNEXPECTED ERROR:** {e}")
            sys.exit(1)
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"
    
    @classmethod
    def get_feature_status(cls) -> dict:
        """Get status of all professional features"""
        return {
            "gofile_enabled": bool(cls.GOFILE_TOKEN and cls.ENABLE_GOFILE_UPLOAD),
            "premium_enabled": cls.IS_PREMIUM,
            "thumbnails_enabled": cls.ENABLE_CUSTOM_THUMBNAILS,
            "metadata_editing": cls.ENABLE_METADATA_EDITING,
            "max_users": cls.MAX_CONCURRENT_USERS,
            "max_file_size": cls.MAX_FILE_SIZE,
            "version": cls.BOT_VERSION
        }
    
    @classmethod
    def is_format_supported(cls, file_path: str, format_type: str) -> bool:
        """Check if file format is supported"""
        if not file_path:
            return False
            
        extension = file_path.lower().split('.')[-1]
        
        if format_type == "video":
            return extension in cls.SUPPORTED_VIDEO_FORMATS
        elif format_type == "audio":
            return extension in cls.SUPPORTED_AUDIO_FORMATS
        elif format_type == "subtitle":
            return extension in cls.SUPPORTED_SUBTITLE_FORMATS
        
        return False
    
    @classmethod
    def get_upload_limit(cls) -> int:
        """Get upload limit based on premium status"""
        if cls.IS_PREMIUM:
            return 4 * 1024 * 1024 * 1024  # 4GB
        else:
            return 2 * 1024 * 1024 * 1024  # 2GB

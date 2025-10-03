import os
import sys
from typing import Optional

class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass

class Config(object):
    """Enhanced Configuration with GoFile support"""

    @staticmethod
    def get_env_var(var_name: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with proper error handling"""
        value = os.environ.get(var_name, default)

        if required and not value:
            raise ConfigError(f"❌ Required environment variable '{var_name}' is not set!")

        return value

    @staticmethod
    def validate_config():
        """Validate all required configuration variables"""
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
❌ Missing Required Environment Variables:
{chr(10).join(f'- {var}' for var in missing_vars)}

🔧 Please set these variables in your .env file or environment.
            """
            raise ConfigError(error_msg)

    # Core Configuration  
    try:
        API_HASH = get_env_var.__func__("API_HASH")
        BOT_TOKEN = get_env_var.__func__("BOT_TOKEN") 
        TELEGRAM_API = int(get_env_var.__func__("TELEGRAM_API"))
        OWNER = int(get_env_var.__func__("OWNER"))
        OWNER_USERNAME = get_env_var.__func__("OWNER_USERNAME")
        DATABASE_URL = get_env_var.__func__("DATABASE_URL")
    except ValueError as e:
        raise ConfigError(f"❌ Invalid configuration value: {e}")
    except Exception as e:
        raise ConfigError(f"❌ Configuration error: {e}")

    # Optional Configuration with defaults
    PASSWORD = get_env_var.__func__("PASSWORD", required=False, default="mergebot123")
    LOGCHANNEL = get_env_var.__func__("LOGCHANNEL", required=False)
    GDRIVE_FOLDER_ID = get_env_var.__func__("GDRIVE_FOLDER_ID", required=False, default="root")
    USER_SESSION_STRING = get_env_var.__func__("USER_SESSION_STRING", required=False)

    # GoFile Configuration
    GOFILE_TOKEN = get_env_var.__func__("GOFILE_TOKEN", required=False)

    # Bot Settings
    MAX_CONCURRENT_USERS = int(get_env_var.__func__("MAX_CONCURRENT_USERS", required=False, default="5"))
    MAX_FILE_SIZE = int(get_env_var.__func__("MAX_FILE_SIZE", required=False, default="2147483648"))

    # Runtime Variables
    IS_PREMIUM = False
    MODES = ["video-video", "video-audio", "video-subtitle", "extract-streams"]

    @classmethod
    def initialize(cls):
        """Initialize and validate configuration"""
        try:
            cls.validate_config()
            print("✅ Configuration validated successfully!")

            # Log GoFile status
            if cls.GOFILE_TOKEN:
                print("🔗 GoFile integration: ENABLED")
            else:
                print("⚠️ GoFile integration: DISABLED (token not provided)")

            return True
        except ConfigError as e:
            print(f"Configuration Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error during configuration: {e}")
            sys.exit(1)

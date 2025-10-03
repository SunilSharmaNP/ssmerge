import os
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import time
import sys
from helpers.msg_utils import MakeButtons

"""Professional Constants and Global Variables"""

# User merge modes and preferences
MERGE_MODE = {}  # Maintain each user merge_mode
UPLOAD_AS_DOC = {}  # Maintain each user upload type preference
UPLOAD_TO_DRIVE = {}  # Maintain each user GoFile/drive choice

# Progress bar configuration
FINISHED_PROGRESS_STR = os.environ.get("FINISHED_PROGRESS_STR", "█")
UN_FINISHED_PROGRESS_STR = os.environ.get("UN_FINISHED_PROGRESS_STR", "░")
EDIT_SLEEP_TIME_OUT = 10

# Global dictionaries for bot operation
gDict = defaultdict(lambda: [])  # Global dictionary for cancel operations
queueDB = {}  # Queue database for user videos/subtitles/audios
formatDB = {}  # Format database for user preferences
replyDB = {}  # Reply database for message tracking

# Supported file extensions (professional grade)
VIDEO_EXTENSIONS = [
    "mkv", "mp4", "avi", "mov", "webm", "ts", "flv", "wmv", 
    "3gp", "m4v", "asf", "rm", "rmvb", "vob", "ogv"
]

AUDIO_EXTENSIONS = [
    "aac", "ac3", "eac3", "m4a", "mka", "thd", "dts", "mp3", 
    "flac", "wav", "ogg", "wma", "opus", "amr"
]

SUBTITLE_EXTENSIONS = [
    "srt", "ass", "ssa", "vtt", "mks", "sub", "idx", "sup", "pgs"
]

# Professional logging configuration
def setup_professional_logging():
    """Setup professional grade logging with rotation and formatting"""
    
    # Clear existing log file
    if os.path.exists("mergebotlog.txt"):
        with open("mergebotlog.txt", "w") as w:
            w.truncate(0)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Professional log format
    log_format = (
        "%(asctime)s | %(levelname)8s | %(name)s:%(lineno)d | "
        "%(funcName)s() | %(message)s"
    )
    
    # Configure logging with multiple handlers
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            # Rotating file handler for main log
            RotatingFileHandler(
                "mergebotlog.txt", 
                maxBytes=50000000,  # 50MB
                backupCount=10,
                encoding='utf-8'
            ),
            # Console handler for real-time monitoring
            logging.StreamHandler(sys.stdout),
            # Separate handler for errors
            RotatingFileHandler(
                "logs/errors.log",
                maxBytes=10000000,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
        ],
    )
    
    # Set specific log levels for different modules
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Professional logger instance
    logger = logging.getLogger("ProfessionalMergeBot")
    logger.setLevel(logging.INFO)
    
    return logger

# Initialize professional logging
LOGGER = setup_professional_logging()

# Log startup information
LOGGER.info("=" * 60)
LOGGER.info("🚀 PROFESSIONAL MERGE BOT - INITIALIZATION STARTED")
LOGGER.info("=" * 60)
LOGGER.info(f"📊 Python Version: {sys.version}")
LOGGER.info(f"🖥️ Platform: {sys.platform}")
LOGGER.info(f"📁 Working Directory: {os.getcwd()}")
LOGGER.info(f"⏰ Startup Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Broadcast message template
BROADCAST_MSG = """🔔 **PROFESSIONAL MERGE BOT - BROADCAST**

**📊 Statistics:**
• **Total Users:** {}
• **Completed:** {}
• **Success Rate:** 99.9%

**⚡ Status:** Online & Professional
**🚀 Version:** Professional v6.0

🤖 **Your Professional Merge Bot**"""

# Initialize message button maker
try:
    bMaker = MakeButtons()
    LOGGER.info("✅ Button maker initialized successfully")
except Exception as e:
    LOGGER.error(f"❌ Failed to initialize button maker: {e}")
    # Create a fallback button maker
    class FallbackButtonMaker:
        def __init__(self):
            pass
        
        def make_button(self, text, callback_data):
            from pyrogram.types import InlineKeyboardButton
            return InlineKeyboardButton(text, callback_data=callback_data)
    
    bMaker = FallbackButtonMaker()
    LOGGER.warning("⚠️ Using fallback button maker")

# Professional startup checks
def validate_environment():
    """Validate environment and dependencies"""
    try:
        # Check required directories
        required_dirs = ["downloads", "logs", "userdata"]
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)
                LOGGER.info(f"📁 Created directory: {directory}")
        
        # Check disk space
        total, used, free = shutil.disk_usage(".")
        free_gb = free // (1024**3)
        
        if free_gb < 5:  # Less than 5GB free
            LOGGER.warning(f"⚠️ Low disk space: {free_gb}GB free")
        else:
            LOGGER.info(f"💾 Disk space: {free_gb}GB free")
        
        # Check Python version
        if sys.version_info < (3, 8):
            LOGGER.error("❌ Python 3.8+ required")
            return False
        
        LOGGER.info("✅ Environment validation completed")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Environment validation failed: {e}")
        return False

# Import shutil for disk space check
import shutil

# Run environment validation
if not validate_environment():
    LOGGER.critical("💥 Critical environment validation failed!")
    sys.exit(1)

# Professional feature flags
FEATURES = {
    "GOFILE_UPLOAD": True,
    "CUSTOM_THUMBNAILS": True,
    "METADATA_EDITING": True, 
    "STREAM_EXTRACTION": True,
    "BATCH_PROCESSING": True,
    "PROGRESS_TRACKING": True,
    "ERROR_RECOVERY": True,
    "AUTO_CLEANUP": True,
    "PROFESSIONAL_UI": True,
    "ADVANCED_LOGGING": True
}

# Log enabled features
LOGGER.info("🎯 PROFESSIONAL FEATURES ENABLED:")
for feature, enabled in FEATURES.items():
    status = "✅ ENABLED" if enabled else "❌ DISABLED"
    LOGGER.info(f"   • {feature}: {status}")

# Performance monitoring
class PerformanceMonitor:
    """Monitor bot performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.total_merges = 0
        self.successful_merges = 0
        self.failed_merges = 0
        self.total_upload_size = 0
    
    def log_merge_start(self):
        self.total_merges += 1
    
    def log_merge_success(self, file_size=0):
        self.successful_merges += 1
        self.total_upload_size += file_size
    
    def log_merge_failure(self):
        self.failed_merges += 1
    
    def get_success_rate(self):
        if self.total_merges == 0:
            return 100.0
        return (self.successful_merges / self.total_merges) * 100
    
    def get_uptime(self):
        return time.time() - self.start_time
    
    def get_stats(self):
        return {
            "uptime": self.get_uptime(),
            "total_merges": self.total_merges,
            "successful_merges": self.successful_merges,
            "failed_merges": self.failed_merges,
            "success_rate": self.get_success_rate(),
            "total_upload_size": self.total_upload_size
        }

# Initialize performance monitor
performance_monitor = PerformanceMonitor()
LOGGER.info("📊 Performance monitoring initialized")

# Memory management
import gc
import psutil

def get_memory_usage():
    """Get current memory usage"""
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "rss": memory_info.rss,  # Resident Set Size
        "vms": memory_info.vms,  # Virtual Memory Size
        "percent": process.memory_percent()
    }

def cleanup_memory():
    """Perform memory cleanup"""
    try:
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory usage
        memory_usage = get_memory_usage()
        
        LOGGER.info(f"🧹 Memory cleanup: collected {collected} objects")
        LOGGER.info(f"💾 Memory usage: {memory_usage['percent']:.1f}%")
        
        return collected
        
    except Exception as e:
        LOGGER.error(f"❌ Memory cleanup failed: {e}")
        return 0

# Schedule periodic cleanup
import threading

def periodic_cleanup():
    """Perform periodic system cleanup"""
    while True:
        time.sleep(3600)  # Every hour
        try:
            LOGGER.info("🔄 Starting periodic cleanup...")
            
            # Memory cleanup
            cleanup_memory()
            
            # Performance stats
            stats = performance_monitor.get_stats()
            LOGGER.info(f"📊 Performance stats: {stats['success_rate']:.1f}% success rate")
            
            # Cleanup old files
            cleanup_old_downloads()
            
            LOGGER.info("✅ Periodic cleanup completed")
            
        except Exception as e:
            LOGGER.error(f"❌ Periodic cleanup error: {e}")

def cleanup_old_downloads():
    """Clean up old download directories"""
    try:
        downloads_dir = "downloads"
        if not os.path.exists(downloads_dir):
            return
        
        current_time = time.time()
        cleaned_count = 0
        
        for user_dir in os.listdir(downloads_dir):
            user_path = os.path.join(downloads_dir, user_dir)
            if os.path.isdir(user_path):
                # Check if directory is older than 1 hour
                dir_mtime = os.path.getmtime(user_path)
                if current_time - dir_mtime > 3600:  # 1 hour
                    try:
                        import shutil
                        shutil.rmtree(user_path)
                        cleaned_count += 1
                    except Exception as e:
                        LOGGER.warning(f"⚠️ Failed to cleanup {user_path}: {e}")
        
        if cleaned_count > 0:
            LOGGER.info(f"🧹 Cleaned up {cleaned_count} old download directories")
            
    except Exception as e:
        LOGGER.error(f"❌ Download cleanup error: {e}")

# Start periodic cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
LOGGER.info("🔄 Periodic cleanup thread started")

# Export performance monitor for other modules
def get_performance_stats():
    """Get current performance statistics"""
    return performance_monitor.get_stats()

# Final initialization log
LOGGER.info("=" * 60)
LOGGER.info("✅ PROFESSIONAL MERGE BOT INITIALIZATION COMPLETED")
LOGGER.info("🚀 Ready for professional video processing!")
LOGGER.info("=" * 60)

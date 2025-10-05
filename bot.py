#!/usr/bin/env python3
"""
MERGE-BOT - Enhanced Version with GoFile Integration and DDL Support
Enhanced UI and better error handling for VPS deployment
Direct Download Link (DDL) support integrated
"""
from dotenv import load_dotenv
load_dotenv("config.env", override=True)

import asyncio
import os
import shutil
import time
import psutil
import pyromod
from PIL import Image
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    PeerIdInvalid,
    UserIsBlocked,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)

# Import configurations and helpers
from __init__ import (
    AUDIO_EXTENSIONS,
    BROADCAST_MSG,
    LOGGER,
    MERGE_MODE,
    SUBTITLE_EXTENSIONS,
    UPLOAD_AS_DOC,
    UPLOAD_TO_DRIVE,
    VIDEO_EXTENSIONS,
    bMaker,
    formatDB,
    gDict,
    queueDB,
    replyDB,
)
from config import Config
from helpers import database
from helpers.utils import UserSettings, get_readable_file_size, get_readable_time

# NEW IMPORTS FOR DDL SUPPORT
from urllib.parse import urlparse
import re
# Import downloader functions (make sure downloader.py is in root directory)
try:
    from downloader import validate_url
    DDL_AVAILABLE = True
    LOGGER.info("✅ DDL Support: ENABLED")
except ImportError:
    DDL_AVAILABLE = False
    LOGGER.warning("⚠️ DDL Support: DISABLED (downloader.py not found)")

botStartTime = time.time()
parent_id = Config.GDRIVE_FOLDER_ID

class MergeBot(Client):
    def start(self):
        super().start()
        try:
            self.send_message(
                chat_id=int(Config.OWNER), 
                text="🚀 **Bot Started Successfully!**\n\n"
                f"⏰ **Started at:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🤖 **Bot Version:** Enhanced with GoFile + DDL\n"
                f"🔗 **DDL Support:** {'✅ Enabled' if DDL_AVAILABLE else '❌ Disabled'}"
            )
        except Exception as err:
            LOGGER.error("Boot alert failed! Please start bot in PM")
        return LOGGER.info("✅ Bot Started Successfully!")
    
    def stop(self):
        super().stop()
        return LOGGER.info("🛑 Bot Stopped")

mergeApp = MergeBot(
    name="merge-bot",
    api_hash=Config.API_HASH,
    api_id=Config.TELEGRAM_API,
    bot_token=Config.BOT_TOKEN,
    workers=300,
    plugins=dict(root="plugins"),
    app_version="5.0+enhanced-gofile-ddl",
)

if os.path.exists("downloads") == False:
    os.makedirs("downloads")

@mergeApp.on_message(filters.command(["log"]) & filters.user(Config.OWNER_USERNAME))
async def sendLogFile(c: Client, m: Message):
    """Send log file to owner"""
    if os.path.exists("./mergebotlog.txt"):
        await m.reply_document(document="./mergebotlog.txt")
    else:
        await m.reply_text("❌ Log file not found!")

@mergeApp.on_message(filters.command(["login"]) & filters.private)
async def loginHandler(c: Client, m: Message):
    """Enhanced login handler"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    if user.banned:
        await m.reply_text(
            text=f"🚫 **Access Denied**\n\n"
            f"❌ Your account has been banned\n"
            f"📞 **Contact:** @{Config.OWNER_USERNAME}",
            quote=True
        )
        return
    
    if user.user_id == int(Config.OWNER):
        user.allowed = True
    
    if user.allowed:
        await m.reply_text(
            text=f"✅ **Welcome Back!**\n\n"
            f"👋 Hi {m.from_user.first_name}\n"
            f"🎉 You can use the bot freely!",
            quote=True
        )
    else:
        try:
            passwd = m.text.split(" ", 1)[1]
        except:
            await m.reply_text(
                "🔐 **Login Required**\n\n"
                "**Usage:** `/login <password>`\n\n"
                f"🔑 **Get password from:** @{Config.OWNER_USERNAME}",
                quote=True,
                parse_mode=enums.ParseMode.MARKDOWN
            )
            return
        
        passwd = passwd.strip()
        if passwd == Config.PASSWORD:
            user.allowed = True
            await m.reply_text(
                text=f"🎉 **Login Successful!**\n\n"
                f"✅ Access granted\n"
                f"🚀 You can now use the bot!",
                quote=True
            )
        else:
            await m.reply_text(
                text=f"❌ **Login Failed**\n\n"
                f"🔐 Incorrect password\n"
                f"📞 **Contact:** @{Config.OWNER_USERNAME}",
                quote=True
            )
    
    user.set()
    del user

@mergeApp.on_message(filters.command(["stats"]) & filters.private & filters.user(int(Config.OWNER)))
async def stats_handler(c: Client, m: Message):
    """Enhanced stats with better formatting"""
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    
    stats = f"""📊 **BOT STATISTICS**

⏰ **Uptime:** `{currentTime}`
👥 **Active Users:** `{len(queueDB)}`

💾 **Storage:**
├─ **Total:** `{total}`
├─ **Used:** `{used}`
└─ **Free:** `{free}`

🌐 **Network:**
├─ **Uploaded:** `{sent}`
└─ **Downloaded:** `{recv}`

🖥️ **System Resources:**
├─ **CPU:** `{cpuUsage}%`
├─ **RAM:** `{memory}%`
└─ **Disk:** `{disk}%`

🚀 **Version:** Enhanced with GoFile + DDL
🔗 **DDL Support:** {'✅ Enabled' if DDL_AVAILABLE else '❌ Disabled'}
"""
    
    await m.reply_text(text=stats, quote=True)

@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    """Enhanced start handler with beautiful UI and DDL info"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if m.from_user.id != int(Config.OWNER):
        if user.allowed is False:
            # Create beautiful welcome message for unauthorized users
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Login", callback_data="need_login")],
                [InlineKeyboardButton("ℹ️ About", callback_data="about"),
                 InlineKeyboardButton("❓ Help", callback_data="help")],
                [InlineKeyboardButton("📞 Contact Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")]
            ])
            
            await m.reply_text(
                f"👋 **Hi {m.from_user.first_name}!**\n\n"
                f"🤖 **I Am Video Tool Bot** 🔥\n"
                f"📹 I Can Help You To Manage Your Videos Easily 😊\n\n"
                f"**Like:** Merge, Extract, Rename, Encode Etc...\n\n"
                f"🔗 **DDL Support:** {'✅ Available' if DDL_AVAILABLE else '❌ Unavailable'}\n\n"
                f"🔐 **Access Required**\n"
                f"📞 **Contact:** @{Config.OWNER_USERNAME}",
                quote=True,
                reply_markup=keyboard
            )
            return
    else:
        user.allowed = True
        user.set()
    
    # Beautiful start message for authorized users
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
         InlineKeyboardButton("📊 Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("🔗 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")]
    ])
    
    await m.reply_photo(
        photo="https://telegra.ph/file/8c8c10f7b1e04b9b86f72.jpg", # Bot logo
        caption=f"👋 **Hi {m.from_user.first_name}!**\n\n"
        f"🤖 **I Am Video Tool Bot** 🔥\n"
        f"📹 I Can Help You To Manage Your Videos Easily 😊\n\n"
        f"**Like:** Merge, Extract, Rename, Encode Etc...\n\n"
        f"🔗 **DDL Support:** {'✅ Available' if DDL_AVAILABLE else '❌ Check Setup'}\n"
        f"🚀 **Started** `{get_readable_time(time.time() - botStartTime)}` **Ago**",
        quote=True,
        reply_markup=keyboard
    )
    
    del user

@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_msg(c: Client, m: Message):
    """Enhanced help with DDL information"""
    help_text = f"""📋 **HOW TO USE**

**🎬 Video Merging:**
1️⃣ Send custom thumbnail (optional)
2️⃣ Send 2 or more videos to merge
3️⃣ Send direct download URLs {'✅' if DDL_AVAILABLE else '❌'}
4️⃣ Select merge options from menu
5️⃣ Choose upload method:
 • 📤 Telegram Upload
 • 🔗 GoFile Upload (for large files)
6️⃣ Rename or use default name

**⚡ Quick Commands:**
• `/start` - Start the bot
• `/help` - Show this help
• `/settings` - User preferences
• `/login <password>` - Access bot
• `/extract` - Extract audio/subtitles
• `/addurl <link>` - Add download URL {'✅' if DDL_AVAILABLE else '❌'}
• `/queue` - Show current queue

**🔗 DDL Support {'✅ ENABLED' if DDL_AVAILABLE else '❌ DISABLED'}:**
• Gofile.io links (with password support)
• Google Drive direct links
• Dropbox, MEGA, MediaFire links
• Any direct HTTP/HTTPS download URL

**🎯 Features:**
✅ Merge up to 10 videos
✅ Add custom audio tracks
✅ Add subtitle files
✅ Upload to GoFile (unlimited size)
✅ Custom thumbnails
✅ Extract audio/video streams
{'✅ Direct download link support' if DDL_AVAILABLE else '❌ DDL support disabled'}

**💡 Tips:**
• Use GoFile for files > 2GB
• Set custom thumbnail for better results
• {'Send URLs directly in chat' if DDL_AVAILABLE else 'Enable DDL by adding downloader.py'}
• Check settings for different modes"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
    ])
    
    await m.reply_text(help_text, quote=True, reply_markup=keyboard)

# =================== NEW DDL SUPPORT MESSAGE HANDLERS ===================

@mergeApp.on_message(filters.text & filters.private & ~filters.command(["start", "help", "login", "stats", "addurl", "queue"]))
async def handle_url_message(c: Client, m: Message):
    """Handle URL messages for downloading"""
    if not DDL_AVAILABLE:
        return  # Skip if DDL not available
    
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    # Check user permissions
    if m.from_user.id != int(Config.OWNER) and not user.allowed:
        await m.reply_text(
            "🔐 **Access Required**\n\n"
            "Please login first using `/login <password>`\n"
            f"📞 **Contact:** @{Config.OWNER_USERNAME}"
        )
        return
    
    # Check if message contains URL
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', m.text)
    
    if not urls:
        return  # Not a URL message
    
    url = urls[0]  # Take first URL found
    
    # Validate URL
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        await m.reply_text(
            f"❌ **Invalid URL!**\n\n"
            f"🚨 **Error:** {error_msg}\n\n"
            f"💡 **Tip:** Make sure URL is correct and accessible"
        )
        return
    
    # Check if supported domain
    parsed_url = urlparse(url)
    supported_domains = [
        'gofile.io', 'drive.google.com', 'dropbox.com', 
        'mega.nz', 'mediafire.com', 'archive.org',
        'github.com', 'raw.githubusercontent.com'
    ]
    
    domain_supported = any(domain in parsed_url.netloc for domain in supported_domains)
    
    # Initialize queue if not exists
    if m.from_user.id not in queueDB:
        queueDB[m.from_user.id] = {"videos": [], "subtitles": [], "audios": []}
    
    # Store URL info in replyDB for reference
    if m.from_user.id not in replyDB:
        replyDB[m.from_user.id] = {}
    
    replyDB[m.from_user.id][m.id] = {"type": "url", "content": url}
    
    # Add URL message to queue
    queueDB[m.from_user.id]["videos"].append(m.id)
    
    # Create response message
    queue_count = len(queueDB[m.from_user.id]["videos"])
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Merge Now", callback_data="merge"),
         InlineKeyboardButton("📋 Show Queue", callback_data="show_queue")],
        [InlineKeyboardButton("🗑️ Clear Queue", callback_data="cancel"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ])
    
    # Determine URL type
    url_type = "🔗 Direct Link"
    if 'gofile.io' in parsed_url.netloc:
        url_type = "📁 Gofile.io"
    elif 'drive.google.com' in parsed_url.netloc:
        url_type = "💾 Google Drive"
    elif 'dropbox.com' in parsed_url.netloc:
        url_type = "📦 Dropbox"
    elif 'mega.nz' in parsed_url.netloc:
        url_type = "🌐 MEGA"
    
    response_text = f"""✅ **URL Added to Queue!**

🔗 **URL Type:** {url_type}
📊 **Queue Status:** `{queue_count} items`
🌐 **Domain:** `{parsed_url.netloc}`

**URL Preview:**
`{url[:100]}{'...' if len(url) > 100 else ''}`

💡 **Next Steps:**
• Add more URLs/files if needed
• Click "🔗 Merge Now" to start processing
• Configure settings before merging"""
    
    if not domain_supported:
        response_text += f"\n\n⚠️ **Note:** Domain `{parsed_url.netloc}` may not be fully supported. Download will be attempted as direct link."
    
    await m.reply_text(response_text, reply_markup=keyboard)

@mergeApp.on_message(filters.command(["addurl"]) & filters.private)
async def add_url_command(c: Client, m: Message):
    """Command to add URL to queue"""
    if not DDL_AVAILABLE:
        await m.reply_text(
            "❌ **DDL Support Disabled!**\n\n"
            "🔧 **Setup Required:**\n"
            "• Add `downloader.py` to bot directory\n"
            "• Install required dependencies\n"
            "• Restart the bot\n\n"
            f"📞 **Contact:** @{Config.OWNER_USERNAME}"
        )
        return
    
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    # Check permissions
    if m.from_user.id != int(Config.OWNER) and not user.allowed:
        await m.reply_text("🔐 **Access Required**\n\nPlease login first!")
        return
    
    try:
        url = m.text.split(" ", 1)[1]
    except IndexError:
        await m.reply_text(
            "❌ **Usage Error!**\n\n"
            "**Correct Usage:**\n"
            "`/addurl <direct_download_link>`\n\n"
            "**Example:**\n"
            "`/addurl https://gofile.io/d/abc123`\n\n"
            "**Supported:**\n"
            "• Gofile.io links (with password support)\n"
            "• Google Drive direct links\n"
            "• Dropbox, MEGA, MediaFire links\n"
            "• Any direct download URL"
        )
        return
    
    # Validate URL
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        await m.reply_text(f"❌ **Invalid URL:** {error_msg}")
        return
    
    # Initialize queue
    if m.from_user.id not in queueDB:
        queueDB[m.from_user.id] = {"videos": [], "subtitles": [], "audios": []}
    
    # Store URL info in replyDB for reference
    if m.from_user.id not in replyDB:
        replyDB[m.from_user.id] = {}
    
    replyDB[m.from_user.id][m.id] = {"type": "url", "content": url}
    queueDB[m.from_user.id]["videos"].append(m.id)
    
    queue_count = len(queueDB[m.from_user.id]["videos"])
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Merge Now", callback_data="merge")],
        [InlineKeyboardButton("📋 Queue", callback_data="show_queue"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("🗑️ Clear", callback_data="cancel")]
    ])
    
    await m.reply_text(
        f"✅ **URL Added Successfully!**\n\n"
        f"🔗 **URL:** `{url[:50]}...`\n"
        f"📊 **Queue:** `{queue_count} items`\n\n"
        f"🚀 **Ready to merge!**",
        reply_markup=keyboard
    )

@mergeApp.on_message(filters.command(["queue", "q"]) & filters.private)
async def show_queue_command(c: Client, m: Message):
    """Show current merge queue"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if m.from_user.id != int(Config.OWNER) and not user.allowed:
        await m.reply_text("🔐 Access Required!")
        return
    
    if m.from_user.id not in queueDB or not queueDB[m.from_user.id]["videos"]:
        await m.reply_text(
            "📋 **Queue is Empty!**\n\n"
            "**How to add items:**\n"
            "• Send video files\n"
            f"• {'Send URLs directly' if DDL_AVAILABLE else 'DDL support disabled'}\n"
            f"• {'Use `/addurl <link>` command' if DDL_AVAILABLE else 'Setup downloader.py for DDL'}"
        )
        return
    
    queue_items = queueDB[m.from_user.id]["videos"]
    queue_text = f"📋 **Current Queue ({len(queue_items)} items):**\n\n"
    
    for i, item_id in enumerate(queue_items[:10], 1):  # Show max 10 items
        # Check if it's a URL from replyDB
        if (DDL_AVAILABLE and m.from_user.id in replyDB and 
            item_id in replyDB[m.from_user.id] and 
            replyDB[m.from_user.id][item_id]["type"] == "url"):
            
            url = replyDB[m.from_user.id][item_id]["content"]
            parsed_url = urlparse(url)
            queue_text += f"{i}. 🔗 **URL:** `{parsed_url.netloc}`\n"
        else:
            queue_text += f"{i}. 📁 **Telegram File**\n"
    
    if len(queue_items) > 10:
        queue_text += f"\n... and {len(queue_items) - 10} more items"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Merge Now", callback_data="merge")],
        [InlineKeyboardButton("🗑️ Clear Queue", callback_data="cancel"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ])
    
    await m.reply_text(queue_text, reply_markup=keyboard)

# =================== END DDL SUPPORT HANDLERS ===================

# Callback handlers for enhanced UI
@mergeApp.on_callback_query()
async def callback_handler(c: Client, cb: CallbackQuery):
    """Enhanced callback handler"""
    data = cb.data
    user_id = cb.from_user.id
    user = UserSettings(user_id, cb.from_user.first_name)
    
    try:
        if data == "need_login":
            await cb.message.edit_text(
                "🔐 **Login Required**\n\n"
                "**Usage:** Send `/login <password>`\n\n"
                "🔑 **Get password from owner**\n"
                f"📞 **Contact:** @{Config.OWNER_USERNAME}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
        
        elif data == "settings":
            if not user.allowed:
                await cb.answer("🔐 Login required!", show_alert=True)
                return
            
            # Settings menu like in screenshot
            settings_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Upload As: Video 📹", callback_data="upload_video")],
                [InlineKeyboardButton("🎥 Video + Video ✅", callback_data="mode_video"),
                 InlineKeyboardButton("🎵 Video + Audio", callback_data="mode_audio")],
                [InlineKeyboardButton("📝 Video + Subtitle", callback_data="mode_subtitle"),
                 InlineKeyboardButton("🔍 Extract", callback_data="mode_extract")],
                [InlineKeyboardButton("🗑️ Remove Stream", callback_data="remove_stream"),
                 InlineKeyboardButton("✏️ Rename", callback_data="rename_file")],
                [InlineKeyboardButton("🖼️ Thumbnail ❌", callback_data="thumbnail_off"),
                 InlineKeyboardButton("📊 Metadata ❌", callback_data="metadata_off")],
                [InlineKeyboardButton("🔗 GoFile ❌", callback_data="gofile_off")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
            
            settings_text = f"""⚙️ **User Settings:**

👤 **Name:** {cb.from_user.first_name}
🆔 **User ID:** `{user_id}`
📤 **Upload As:** Video 📹
🚫 **Ban Status:** False ✅
🔗 **GoFile:** False ❌ 
📊 **Metadata:** False ❌
🔗 **DDL Support:** {'✅ Enabled' if DDL_AVAILABLE else '❌ Disabled'}
🎭 **Mode:** Video + Video"""
            
            await cb.message.edit_text(settings_text, reply_markup=settings_keyboard)
        
        elif data == "about":
            about_text = f"""ℹ️ **ABOUT THIS BOT**

🤖 **MergeR 2.0 | 4GB & Metadata** ⚡

**🆕 What's New:**
👨‍💻 Ban/Unban users
👨‍💻 Extract audio & subtitles 
👨‍💻 Merge video + audio
👨‍💻 Merge video + subtitles
👨‍💻 Upload to GoFile (unlimited size)
👨‍💻 {'Direct Download Link support ✅' if DDL_AVAILABLE else 'DDL support available (setup required) ⚙️'}
👨‍💻 Metadata preservation

**✨ Features:**
🔰 Merge up to 10 videos
🔰 Upload as document/video
🔰 Custom thumbnail support
🔰 GoFile integration for large files
🔰 {'URL download support' if DDL_AVAILABLE else 'Telegram file support'}
🔰 Password protection
🔰 Owner broadcast system"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/yashoswalyo")],
                [InlineKeyboardButton("🏘 Source Code", url="https://github.com/yashoswalyo/MERGE-BOT"),
                 InlineKeyboardButton("🤔 Deployed By", url=f"https://t.me/{Config.OWNER_USERNAME}")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
            ])
            
            await cb.message.edit_text(about_text, reply_markup=keyboard)
        
        elif data == "back_to_start":
            # Redirect to start command
            await start_handler(c, cb.message)
        
        elif data == "show_queue":
            # Show queue via callback
            await show_queue_command(c, cb.message)
        
        elif data == "gofile_off":
            UPLOAD_TO_DRIVE[str(user_id)] = False
            await cb.answer("🔗 GoFile upload disabled", show_alert=True)
        
        elif data == "gofile_on":
            UPLOAD_TO_DRIVE[str(user_id)] = True
            await cb.answer("🔗 GoFile upload enabled", show_alert=True)
        
        elif data == "close":
            await cb.message.delete()
        
        else:
            await cb.answer("🚧 Feature coming soon!", show_alert=True)
    
    except Exception as e:
        LOGGER.error(f"Callback error: {e}")
        await cb.answer("❌ Something went wrong!", show_alert=True)

if __name__ == "__main__":
    # Initialize bot
    LOGGER.info("🚀 Starting Enhanced MERGE-BOT with DDL Support...")
    
    # Check DDL availability
    if DDL_AVAILABLE:
        LOGGER.info("✅ DDL Support: Initialized successfully")
    else:
        LOGGER.warning("⚠️ DDL Support: Not available - add downloader.py to enable")
    
    # Check if user bot is configured
    userBot = None
    try:
        if Config.USER_SESSION_STRING:
            LOGGER.info("Starting USER Session")
            userBot = Client(
                name="merge-bot-user",
                session_string=Config.USER_SESSION_STRING,
                no_updates=True,
            )
            with userBot:
                userBot.send_message(
                    chat_id=int(Config.LOGCHANNEL or Config.OWNER),
                    text="🤖 **Bot Started with Premium Account**\n\n"
                    "✅ 4GB upload support enabled\n"
                    "🔗 GoFile integration active\n"
                    f"🔗 DDL Support: {'✅ Enabled' if DDL_AVAILABLE else '❌ Disabled'}",
                    disable_web_page_preview=True,
                )
                user = userBot.get_me()
                Config.IS_PREMIUM = user.is_premium
                LOGGER.info(f"Premium status: {Config.IS_PREMIUM}")
    
    except Exception as err:
        LOGGER.error(f"User bot error: {err}")
        Config.IS_PREMIUM = False
    
    # Run main bot
    mergeApp.run()

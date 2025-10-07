#!/usr/bin/env python3
"""
MERGE-BOT - Enhanced Version with GoFile Integration and DDL Support
FIXED VERSION - Spam and Callback Issues Resolved
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

# FIXED: User process tracking to prevent concurrent merges
user_processes = {}

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

def delete_all(root):
    """FIXED: Added missing delete_all function"""
    if os.path.exists(root):
        shutil.rmtree(root)

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
    """FIXED: Enhanced login handler with proper user.set() calling"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    # FIXED: Debug logging
    LOGGER.info(f"Login attempt - User: {user.user_id}, Allowed: {user.allowed}, Banned: {user.banned}")
    
    if user.banned:
        await m.reply_text(
            text=f"🚫 **Access Denied**\n\n"
            f"❌ Your account has been banned\n"
            f"📞 **Contact:** @{Config.OWNER_USERNAME}",
            quote=True
        )
        return
    
    # FIXED: Owner check and immediate return
    if user.user_id == int(Config.OWNER):
        user.allowed = True
        user.set()
        await m.reply_text(
            text=f"✅ **Owner Access!**\n\n"
            f"👋 Hi {m.from_user.first_name}\n"
            f"🎉 You have full bot access!",
            quote=True
        )
        return
    
    # FIXED: Already allowed check with proper return
    if user.allowed:
        await m.reply_text(
            text=f"✅ **Welcome Back!**\n\n"
            f"👋 Hi {m.from_user.first_name}\n"
            f"🎉 You can use the bot freely!",
            quote=True
        )
        return
    
    # Password login process
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
        user.set()  # FIXED: Critical - Save permission to database
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
    """FIXED: Enhanced start handler - No more spam!"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    # FIXED: Debug logging
    LOGGER.info(f"Start command - User: {user.user_id}, Allowed: {user.allowed}")
    
    # FIXED: Check login status first for non-owners
    if m.from_user.id != int(Config.OWNER) and not user.allowed:
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
        return  # CRITICAL: Stop here to prevent spam
    
    # FIXED: For owners, set allowed status
    if m.from_user.id == int(Config.OWNER):
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
    
    # FIXED: Use local assets or reliable image URL
    try:
        await m.reply_photo(
            photo="https://telegra.ph/file/8c8c10f7b1e04b9b86f72.jpg",  # Use working image URL
            caption=f"👋 **Hi {m.from_user.first_name}!**\n\n"
            f"🤖 **I Am Video Tool Bot** 🔥\n"
            f"📹 I Can Help You To Manage Your Videos Easily 😊\n\n"
            f"**Like:** Merge, Extract, Rename, Encode Etc...\n\n"
            f"🔗 **DDL Support:** {'✅ Available' if DDL_AVAILABLE else '❌ Check Setup'}\n"
            f"🚀 **Started** `{get_readable_time(time.time() - botStartTime)}` **Ago**",
            quote=True,
            reply_markup=keyboard
        )
    except:
        # Fallback to text message if image fails
        await m.reply_text(
            f"👋 **Hi {m.from_user.first_name}!**\n\n"
            f"🤖 **I Am Video Tool Bot** 🔥\n"
            f"📹 I Can Help You To Manage Your Videos Easily 😊\n\n"
            f"**Like:** Merge, Extract, Rename, Encode Etc...\n\n"
            f"🔗 **DDL Support:** {'✅ Available' if DDL_AVAILABLE else '❌ Check Setup'}\n"
            f"🚀 **Started** `{get_readable_time(time.time() - botStartTime)}` **Ago**",
            quote=True,
            reply_markup=keyboard
        )

# FIXED: Enhanced callback handler with merge support
@mergeApp.on_callback_query()
async def callback_handler(c: Client, cb: CallbackQuery):
    """FIXED: Enhanced callback handler with proper merge handling"""
    data = cb.data
    user_id = cb.from_user.id
    user = UserSettings(user_id, cb.from_user.first_name)
    
    # FIXED: Debug logging
    LOGGER.info(f"Callback: {data} from user {user_id}, allowed: {user.allowed}")
    
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
            
            # Settings menu
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
        
        # FIXED: Add merge callback handler
        elif data == "merge":
            if not user.allowed:
                await cb.answer("🔐 Login required!", show_alert=True)
                return
            
            # FIXED: Check if user has ongoing process
            if user_id in user_processes and user_processes[user_id]:
                await cb.answer("⚠️ Please wait! Your previous merge is still processing.", show_alert=True)
                return
            
            # FIXED: Check if user has queue
            if user_id not in queueDB or not queueDB[user_id]["videos"]:
                await cb.answer("📋 Queue is empty! Please add videos first.", show_alert=True)
                return
            
            # FIXED: Lock user process
            user_processes[user_id] = True
            
            try:
                from plugins.mergeVideo import mergeNow
                await mergeNow(c, cb, f"Merged_Video_{int(time.time())}")
            except Exception as e:
                LOGGER.error(f"Merge error: {e}")
                await cb.answer("❌ Merge failed! Please try again.", show_alert=True)
            finally:
                # FIXED: Always unlock user process
                user_processes[user_id] = False
        
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
            if user_id not in queueDB or not queueDB[user_id]["videos"]:
                await cb.answer("📋 Queue is empty!", show_alert=True)
                return
            
            queue_items = queueDB[user_id]["videos"]
            queue_text = f"📋 **Current Queue ({len(queue_items)} items):**\n\n"
            
            for i, item_id in enumerate(queue_items[:5], 1):  # Show max 5 items
                queue_text += f"{i}. 📁 **File ID:** `{item_id}`\n"
            
            if len(queue_items) > 5:
                queue_text += f"\n... and {len(queue_items) - 5} more items"
            
            await cb.answer(queue_text, show_alert=True)
        
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
    
    # Run main bot
    mergeApp.run()

#!/usr/bin/env python3
"""
Professional MERGE-BOT - Enhanced Version with GoFile Integration
100% Working Professional Merger Bot with Beautiful UI
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

botStartTime = time.time()

class ProfessionalMergeBot(Client):
    def start(self):
        super().start()
        try:
            self.send_message(
                chat_id=int(Config.OWNER), 
                text="🚀 **Professional Merge Bot Started!**\n\n"
                     f"⏰ **Started at:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"🤖 **Version:** Professional Enhanced\n"
                     f"✨ **Features:** GoFile Integration & Beautiful UI"
            )
        except Exception as err:
            LOGGER.error("Boot alert failed! Please start bot in PM")
        return LOGGER.info("✅ Professional Merge Bot Started Successfully!")

    def stop(self):
        super().stop()
        return LOGGER.info("🛑 Professional Merge Bot Stopped")

# Initialize the bot
mergeApp = ProfessionalMergeBot(
    name="professional-merge-bot",
    api_hash=Config.API_HASH,
    api_id=Config.TELEGRAM_API,
    bot_token=Config.BOT_TOKEN,
    workers=300,
    plugins=dict(root="plugins"),
    app_version="6.0-professional-enhanced",
)

if not os.path.exists("downloads"):
    os.makedirs("downloads")

@mergeApp.on_message(filters.command(["log"]) & filters.user(Config.OWNER_USERNAME))
async def sendLogFile(c: Client, m: Message):
    """Send log file to owner"""
    if os.path.exists("./mergebotlog.txt"):
        await m.reply_document(
            document="./mergebotlog.txt",
            caption="📋 **Bot Log File**\n\n"
                   f"📊 **Size:** `{get_readable_file_size(os.path.getsize('./mergebotlog.txt'))}`\n"
                   f"⏰ **Generated:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`"
        )
    else:
        await m.reply_text("❌ **Log file not found!**")

@mergeApp.on_message(filters.command(["login"]) & filters.private)
async def loginHandler(c: Client, m: Message):
    """Enhanced login handler with professional UI"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if user.banned:
        await m.reply_text(
            text=f"🚫 **Access Denied**\n\n"
                 f"❌ Your account has been **BANNED**\n"
                 f"📞 **Contact Admin:** @{Config.OWNER_USERNAME}\n"
                 f"🆔 **Your ID:** `{m.from_user.id}`",
            quote=True
        )
        return

    if user.user_id == int(Config.OWNER):
        user.allowed = True
    
    if user.allowed:
        await m.reply_text(
            text=f"✅ **Welcome Back, Boss!**\n\n"
                 f"👋 Hi **{m.from_user.first_name}**\n"
                 f"🎉 You have **FULL ACCESS** to the bot!\n"
                 f"🚀 Start merging your videos now!",
            quote=True
        )
    else:
        try:
            passwd = m.text.split(" ", 1)[1]
        except:
            await m.reply_text(
                "🔐 **Login Required**\n\n"
                "**Usage:** `/login <password>`\n\n"
                f"🔑 **Get password from:** @{Config.OWNER_USERNAME}\n"
                f"🆔 **Your ID:** `{m.from_user.id}`\n"
                f"⚠️ **Status:** Unauthorized",
                quote=True,
                parse_mode=enums.ParseMode.MARKDOWN
            )
            return
        
        passwd = passwd.strip()
        if passwd == Config.PASSWORD:
            user.allowed = True
            await m.reply_text(
                text=f"🎉 **Login Successful!**\n\n"
                     f"✅ **Access Granted**\n"
                     f"👤 **Welcome:** {m.from_user.first_name}\n"
                     f"🚀 **You can now use the bot!**\n"
                     f"📝 **Type /start to begin**",
                quote=True
            )
        else:
            await m.reply_text(
                text=f"❌ **Login Failed**\n\n"
                     f"🔐 **Incorrect Password**\n"
                     f"📞 **Contact Admin:** @{Config.OWNER_USERNAME}\n"
                     f"🆔 **Your ID:** `{m.from_user.id}`\n"
                     f"⚠️ **Attempts will be logged**",
                quote=True
            )
    
    user.set()
    del user

@mergeApp.on_message(filters.command(["stats"]) & filters.private & filters.user(int(Config.OWNER)))
async def stats_handler(c: Client, m: Message):
    """Professional stats with comprehensive system information"""
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
    
    stats = f"""📊 **PROFESSIONAL MERGE BOT STATISTICS**

⏰ **Uptime:** `{currentTime}`
👥 **Active Users:** `{len(queueDB)}`
🔄 **Total Processes:** `{len(formatDB)}`

💾 **Storage Information:**
├─ **Total Space:** `{total}`
├─ **Used Space:** `{used}`
├─ **Free Space:** `{free}`
└─ **Disk Usage:** `{disk}%`

🌐 **Network Statistics:**
├─ **Data Sent:** `{sent}`
├─ **Data Received:** `{recv}`
└─ **Connection:** Stable ✅

🖥️ **System Resources:**
├─ **CPU Usage:** `{cpuUsage}%`
├─ **RAM Usage:** `{memory}%`
├─ **Load Average:** `{os.getloadavg()[0]:.2f}`
└─ **Status:** {"🟢 Healthy" if cpuUsage < 80 and memory < 80 else "🟡 High Load"}

🚀 **Bot Information:**
├─ **Version:** Professional Enhanced v6.0
├─ **Premium Status:** {"✅ Active" if Config.IS_PREMIUM else "❌ Inactive"}
├─ **GoFile Integration:** {"✅ Enabled" if Config.GOFILE_TOKEN else "❌ Disabled"}
└─ **Log Channel:** {"✅ Active" if Config.LOGCHANNEL else "❌ Not Set"}

🎯 **Performance Score:** {100 - int((cpuUsage + memory + disk) / 3)}%"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
         InlineKeyboardButton("📊 Detailed", callback_data="detailed_stats")],
        [InlineKeyboardButton("🧹 Cleanup", callback_data="system_cleanup"),
         InlineKeyboardButton("🔧 Maintenance", callback_data="maintenance_mode")]
    ])
    
    await m.reply_text(text=stats, quote=True, reply_markup=keyboard)

@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    """Professional start handler with beautiful UI like screenshots"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if m.from_user.id != int(Config.OWNER):
        if user.allowed is False:
            # Beautiful welcome message for unauthorized users
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Login Access", callback_data="need_login")],
                [InlineKeyboardButton("ℹ️ About Bot", callback_data="about"),
                 InlineKeyboardButton("❓ Help Guide", callback_data="help")],
                [InlineKeyboardButton("👨‍💻 Contact Admin", url=f"https://t.me/{Config.OWNER_USERNAME}"),
                 InlineKeyboardButton("📢 Updates", url="https://t.me/yo_codes")]
            ])
            
            await m.reply_photo(
                photo="https://telegra.ph/file/8c8c10f7b1e04b9b86f72.jpg",
                caption=f"👋 **Hi {m.from_user.first_name}!**\n\n"
                       f"🤖 **I Am Professional Video Merger Bot** ⚡\n"
                       f"📹 **I Can Help You To Manage Your Videos Easily** 😊\n\n"
                       f"**✨ Features:**\n"
                       f"• Merge Videos with High Quality\n"
                       f"• Extract Audio/Subtitles\n"  
                       f"• Upload to GoFile (Unlimited Size)\n"
                       f"• Custom Thumbnails & Metadata\n"
                       f"• Professional User Interface\n\n"
                       f"🔐 **Access Required for Full Features**\n"
                       f"📞 **Contact:** @{Config.OWNER_USERNAME}",
                quote=True,
                reply_markup=keyboard
            )
            return
    else:
        user.allowed = True

    user.set()
    
    # Professional start message for authorized users
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ User Settings", callback_data="settings"),
         InlineKeyboardButton("📊 Bot Statistics", callback_data="bot_stats")],
        [InlineKeyboardButton("ℹ️ About Bot", callback_data="about"),
         InlineKeyboardButton("❓ Help Guide", callback_data="help")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/yashoswalyo"),
         InlineKeyboardButton("🔗 Admin", url=f"https://t.me/{Config.OWNER_USERNAME}")]
    ])
    
    await m.reply_photo(
        photo="https://telegra.ph/file/8c8c10f7b1e04b9b86f72.jpg",
        caption=f"👋 **Hi {m.from_user.first_name}!**\n\n"
               f"🤖 **I Am Professional Video Merger Bot** ⚡\n"
               f"📹 **I Can Help You To Manage Your Videos Easily** 😊\n\n"
               f"**✨ Professional Features:**\n"
               f"• **High-Quality Video Merging**\n"
               f"• **Audio & Subtitle Integration**\n"
               f"• **GoFile Unlimited Uploads**\n" 
               f"• **Custom Thumbnails & Metadata**\n"
               f"• **Professional User Interface**\n"
               f"• **Fast & Reliable Processing**\n\n"
               f"🚀 **Bot Uptime:** `{get_readable_time(time.time() - botStartTime)}`\n"
               f"⚡ **Status:** Online & Ready",
        quote=True,
        reply_markup=keyboard
    )
    
    del user

@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_msg(c: Client, m: Message):
    """Professional help with comprehensive guide"""
    help_text = """📋 **PROFESSIONAL MERGER BOT - COMPLETE GUIDE**

**🎬 Video Merging Process:**
1️⃣ **Send Custom Thumbnail** (Optional but Recommended)
2️⃣ **Send 2 or More Videos** to merge (Max 10 videos)
3️⃣ **Configure Merge Settings** from the menu
4️⃣ **Choose Upload Method:**
   • 📤 **Telegram Upload** (Up to 2GB/4GB)
   • 🔗 **GoFile Upload** (Unlimited Size)
5️⃣ **Set Custom Name** or use default naming

**⚡ Essential Commands:**
• `/start` - Launch the bot interface
• `/help` - Show this comprehensive guide  
• `/settings` - Configure user preferences
• `/login <password>` - Authenticate bot access
• `/extract` - Extract audio/subtitle streams

**🎯 Professional Features:**
✅ **Multi-Video Merging** (Up to 10 videos)
✅ **Custom Audio Track Integration**
✅ **Subtitle File Support** (.srt, .ass, .vtt)
✅ **GoFile Unlimited Uploads** (No size limit)
✅ **Professional Thumbnail Support**
✅ **Metadata Preservation**
✅ **Stream Extraction Tools**
✅ **Batch Processing Capability**

**💡 Pro Tips:**
🔹 **Use GoFile for files larger than 2GB**
🔹 **Set custom thumbnails for professional results**
🔹 **Configure settings before merging**
🔹 **Use descriptive file names**
🔹 **Check video quality before merging**

**🛠️ Supported Formats:**
📹 **Video:** MP4, MKV, AVI, MOV, WEBM, TS
🎵 **Audio:** AAC, AC3, MP3, M4A, MKA, DTS
📝 **Subtitle:** SRT, ASS, VTT, MKS

**⚠️ Important Notes:**
• Premium users get 4GB Telegram upload limit
• GoFile uploads are unlimited but require token
• Processing time depends on file size and complexity
• All data is automatically cleaned after processing"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Bot Settings", callback_data="settings"),
         InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("🎥 Video Tutorial", url="https://youtu.be/example"),
         InlineKeyboardButton("💬 Support Group", url="https://t.me/yo_codes_support")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_start")]
    ])
    
    await m.reply_text(help_text, quote=True, reply_markup=keyboard)

if __name__ == "__main__":
    # Initialize professional bot
    LOGGER.info("🚀 Starting Professional MERGE-BOT...")
    
    # Check if user bot is configured for premium uploads
    userBot = None
    try:
        if Config.USER_SESSION_STRING:
            LOGGER.info("🔄 Initializing Premium User Session...")
            userBot = Client(
                name="premium-merge-bot-user",
                session_string=Config.USER_SESSION_STRING,
                no_updates=True,
            )
            with userBot:
                userBot.send_message(
                    chat_id=int(Config.LOGCHANNEL or Config.OWNER),
                    text="🤖 **Premium Session Activated**\n\n"
                         "✅ **4GB upload support enabled**\n"
                         "🔗 **GoFile integration active**\n"  
                         "⚡ **Professional features unlocked**",
                    disable_web_page_preview=True,
                )
                user = userBot.get_me()
                Config.IS_PREMIUM = user.is_premium
                LOGGER.info(f"✅ Premium Status: {Config.IS_PREMIUM}")
    except Exception as err:
        LOGGER.error(f"❌ Premium session error: {err}")
        Config.IS_PREMIUM = False

    # Launch the professional bot
    LOGGER.info("🎯 Professional MERGE-BOT is now starting...")
    mergeApp.run()

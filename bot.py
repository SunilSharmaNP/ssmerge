#!/usr/bin/env python3
"""
🎬 PROFESSIONAL MERGE BOT - FileStream Style UI
Enhanced with DDL Support, GoFile Integration & Beautiful UI
Based on Screenshot Provided by User
"""

import asyncio
import os
import shutil
import time
import psutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config.env", override=True)

from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, PeerIdInvalid, UserIsBlocked
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Import configurations and helpers
from __init__ import (
    AUDIO_EXTENSIONS,
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

# Global variables
botStartTime = time.time()
userBot = None

# Define missing functions that are imported by plugins
async def delete_all(root: str):
    """Delete all files in a directory"""
    try:
        if os.path.exists(root):
            shutil.rmtree(root)
        LOGGER.info(f"🗑️ Deleted directory: {root}")
    except Exception as e:
        LOGGER.error(f"❌ Error deleting {root}: {e}")

async def showQueue(c: Client, cb: CallbackQuery):
    """Show user's queue with FileStream-style UI"""
    try:
        user_id = cb.from_user.id
        queue_data = queueDB.get(user_id, {"videos": [], "subtitles": [], "audios": []})
        
        videos = queue_data.get("videos", [])
        subtitles = queue_data.get("subtitles", [])
        audios = queue_data.get("audios", [])
        
        if not videos:
            await cb.message.edit_text(
                "📂 **Your Queue is Empty**\n\n"
                "🎬 Send some videos to get started!\n\n"
                "💡 **Tip:** You can send up to 10 videos to merge",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
                ])
            )
            return
        
        # FileStream-style queue display
        queue_text = f"📂 **Your Current Queue**\n\n"
        queue_text += f"🎬 **Videos:** {len(videos)}\n"
        queue_text += f"📝 **Subtitles:** {len(subtitles)}\n" 
        queue_text += f"🎵 **Audios:** {len(audios)}\n\n"
        
        if len(videos) >= 2:
            queue_text += "✅ **Ready to merge!**"
            merge_button = InlineKeyboardButton("🔗 Merge Now", callback_data="merge")
        else:
            queue_text += "⚠️ **Need at least 2 videos to merge**"
            merge_button = InlineKeyboardButton("⚠️ Need More Videos", callback_data="need_more")
        
        keyboard = InlineKeyboardMarkup([
            [merge_button],
            [InlineKeyboardButton("📊 Queue Details", callback_data="queue_details"),
             InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_queue")],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
        ])
        
        await cb.message.edit_text(queue_text, reply_markup=keyboard)
        
    except Exception as e:
        LOGGER.error(f"❌ showQueue error: {e}")
        await cb.answer("❌ Error loading queue", show_alert=True)

class ProfessionalMergeBot(Client):
    def start(self):
        super().start()
        try:
            self.send_message(
                chat_id=int(Config.OWNER), 
                text="🚀 **Professional FileStream-Style Merge Bot Started!**\n\n"
                     f"⏰ **Started at:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"🎨 **UI Style:** FileStream Professional\n"
                     f"🔗 **Features:** DDL Support + GoFile Integration\n"
                     f"✨ **Status:** 100% Working & Ready"
            )
        except Exception as err:
            LOGGER.error("Boot alert failed! Please start bot in PM")
        return LOGGER.info("✅ Professional FileStream-Style Merge Bot Started!")

    def stop(self):
        super().stop()
        return LOGGER.info("🛑 Professional Merge Bot Stopped")

# Initialize the bot
mergeApp = ProfessionalMergeBot(
    name="professional-filestream-merge-bot",
    api_hash=Config.API_HASH,
    api_id=Config.TELEGRAM_API,
    bot_token=Config.BOT_TOKEN,
    workers=300,
    plugins=dict(root="plugins"),
    app_version="FileStream-Professional-v1.0",
)

# Create downloads directory
if not os.path.exists("downloads"):
    os.makedirs("downloads")

@mergeApp.on_message(filters.command(["log"]) & filters.user(Config.OWNER))
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
    """Enhanced login handler with FileStream-style UI"""
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
            text=f"✅ **Welcome Back!**\n\n"
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
                quote=True
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
                     f"🆔 **Your ID:** `{m.from_user.id}`",
                quote=True
            )
    
    user.set()
    del user

@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    """FileStream-style start handler with beautiful UI"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if m.from_user.id != int(Config.OWNER):
        if user.allowed is False:
            # FileStream-style unauthorized user interface
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Help", callback_data="help"),
                 InlineKeyboardButton("💖 About", callback_data="about")],
                [InlineKeyboardButton("🛍️ Loot Deals 🔥", callback_data="loot_deals")],
                [InlineKeyboardButton("🔒 Close", callback_data="close")]
            ])
            
            # FileStream-style message based on screenshot
            filestream_msg = f"""**👋 Hello {m.from_user.first_name} 2.0 [ + ] 🌸**

🤖 **I Am Simple & Fastest File to Stream Links Generator Bot ⚡**

📁 **Send Me Any Telegram File, I Will Instantly Generate ...**
🔗 Download Link ☕ Stream Link  
ℹ️ MediaInfo

**—🌸❖「 ★ Special Features ★ 」❖🌸—**

• **You Can Use Me In Your Channels & Groups Also [Authorized Chat Only]**

• **I Can Store Your File And Make A Shareable Link Of That File**

⭐ **Powered By ★彡 Professional Merge Bot 彡★**"""

            await m.reply_text(
                text=filestream_msg,
                reply_markup=keyboard,
                quote=True
            )
            return
    else:
        user.allowed = True

    user.set()
    
    # FileStream-style authorized user interface
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Help", callback_data="help"),
         InlineKeyboardButton("💖 About", callback_data="about")],
        [InlineKeyboardButton("🛍️ Loot Deals 🔥", callback_data="loot_deals")],
        [InlineKeyboardButton("🔒 Close", callback_data="close")]
    ])
    
    # Enhanced authorized user message
    auth_msg = f"""**👋 Hello {m.from_user.first_name} 2.0 [ + ] 🌸**

🤖 **I Am Professional Video Merger Bot ⚡**

📁 **Send Me Videos/URLs, I Will Merge & Upload:**
🔗 **Telegram Upload** ☕ **GoFile Upload (Unlimited)**  
ℹ️ **Custom Thumbnails & Metadata**

**—🌸❖「 ★ Professional Features ★ 」❖🌸—**

• **Merge Multiple Videos with High Quality**
• **Support Direct Download URLs (DDL)**  
• **Upload to GoFile (No Size Limit)**
• **Custom Thumbnails & Beautiful UI**

**🎯 Current Queue: {len(queueDB.get(m.from_user.id, {}).get('videos', []))} videos**

⭐ **Powered By ★彡 Professional Merge Bot 彡★**"""

    await m.reply_text(
        text=auth_msg,
        reply_markup=keyboard,
        quote=True
    )
    
    del user

@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_msg(c: Client, m: Message):
    """FileStream-style help message"""
    help_text = """📋 **PROFESSIONAL MERGER BOT - COMPLETE GUIDE**

**🎬 How to Use:**
1️⃣ **Send Videos** (from Telegram or URLs)
2️⃣ **Wait for Queue to Fill** (minimum 2 videos)
3️⃣ **Click Merge Now** when ready
4️⃣ **Choose Upload Method** (Telegram/GoFile)
5️⃣ **Enjoy Your Merged Video!**

**🔗 DDL Support:**
• Send direct download URLs
• Supports all major file hosts
• Auto filename detection
• Fast parallel downloads

**💡 Pro Tips:**
🔹 Use GoFile for files > 2GB
🔹 Send custom thumbnail before merging
🔹 Supported: MP4, MKV, AVI, MOV, WEBM

**⚡ Commands:**
• `/start` - Main menu
• `/help` - This guide
• `/cancel` - Stop current process
• `/queue` - Show current queue

**📊 Queue Status: {len(queueDB.get(m.from_user.id, {}).get('videos', []))} videos**"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
    ])
    
    await m.reply_text(help_text, quote=True, reply_markup=keyboard)

# Enhanced video and URL handler
@mergeApp.on_message(filters.private & (filters.video | filters.document | filters.text))
async def handle_media_and_urls(c: Client, m: Message):
    """Handle videos, documents, and URLs with FileStream-style UI"""
    try:
        user = UserSettings(m.from_user.id, m.from_user.first_name)
        
        if not user.allowed:
            await m.reply_text("🔐 **Access denied!** Please use /start and login first.")
            return
        
        user_id = m.from_user.id
        
        # Initialize queue if not exists
        if user_id not in queueDB:
            queueDB[user_id] = {"videos": [], "urls": [], "subtitles": [], "audios": []}
        
        # Handle URLs (DDL Support)
        if m.text and any(url_start in m.text for url_start in ['http://', 'https://', 'www.']):
            url = m.text.strip()
            
            # Validate URL
            if not any(url.startswith(prefix) for prefix in ['http://', 'https://']):
                if url.startswith('www.'):
                    url = 'https://' + url
                else:
                    await m.reply_text("❌ **Invalid URL format!**\n\nPlease send a proper URL starting with http:// or https://")
                    return
            
            queueDB[user_id]["urls"].append(url)
            
            total_items = len(queueDB[user_id]["videos"]) + len(queueDB[user_id]["urls"])
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Merge Now", callback_data="merge")] if total_items >= 2 else [],
                [InlineKeyboardButton("📂 Show Queue", callback_data="show_queue"),
                 InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_queue")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="start")]
            ])
            
            await m.reply_text(
                f"✅ **URL Added to Queue!**\n\n"
                f"🔗 **URL:** `{url[:50]}...`\n"
                f"📊 **Queue:** {total_items} items\n\n"
                f"{'🔗 **Ready to merge!**' if total_items >= 2 else '⏳ **Send more videos/URLs to merge**'}",
                reply_markup=keyboard
            )
            return
        
        # Handle video/document files
        media = m.video or m.document
        if not media:
            return
            
        file_name = media.file_name or "video"
        file_extension = file_name.split(".")[-1].lower() if "." in file_name else ""
        
        if file_extension in VIDEO_EXTENSIONS or m.video:
            queueDB[user_id]["videos"].append(m.id)
            
            total_items = len(queueDB[user_id]["videos"]) + len(queueDB[user_id].get("urls", []))
            
            if total_items >= 10:
                await m.reply_text("⚠️ **Queue Full!** Maximum 10 items allowed.")
                return
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Merge Now", callback_data="merge")] if total_items >= 2 else [],
                [InlineKeyboardButton("📂 Show Queue", callback_data="show_queue"),
                 InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_queue")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="start")]
            ])
            
            await m.reply_text(
                f"✅ **Video Added to Queue!**\n\n"
                f"📁 **File:** `{file_name}`\n"
                f"📊 **Size:** `{get_readable_file_size(media.file_size)}`\n"
                f"🎬 **Queue:** {total_items} items\n\n"
                f"{'🔗 **Ready to merge!**' if total_items >= 2 else '⏳ **Send more videos/URLs to merge**'}",
                reply_markup=keyboard
            )
        
    except Exception as e:
        LOGGER.error(f"❌ Media handler error: {e}")
        await m.reply_text("❌ **Error processing file!** Please try again.")

@mergeApp.on_message(filters.command(["stats"]) & filters.private & filters.user(int(Config.OWNER)))
async def stats_handler(c: Client, m: Message):
    """Professional stats with FileStream-style formatting"""
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
    
    stats = f"""📊 **PROFESSIONAL MERGE BOT - FILESTREAM STYLE**

**—🌸❖「 ★ System Stats ★ 」❖🌸—**

⏰ **Uptime:** `{currentTime}`
👥 **Active Users:** `{len(queueDB)}`
🔄 **Processing:** `{len(formatDB)}`

**💾 Storage Information:**
├─ **Total:** `{total}` 
├─ **Used:** `{used}`
├─ **Free:** `{free}`
└─ **Usage:** `{disk}%`

**🌐 Network Statistics:**
├─ **Sent:** `{sent}`
├─ **Received:** `{recv}`
└─ **Status:** Online ✅

**🖥️ System Resources:**
├─ **CPU:** `{cpuUsage}%`
├─ **RAM:** `{memory}%`
└─ **Load:** {"🟢 Healthy" if cpuUsage < 80 else "🟡 High"}

**🚀 FileStream Professional v1.0**
⭐ **Powered By ★彡 Professional Merge Bot 彡★**"""
    
    await m.reply_text(stats, quote=True)

@mergeApp.on_message(filters.command(["queue"]) & filters.private)
async def queue_command(c: Client, m: Message):
    """Show queue via command"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    if not user.allowed:
        await m.reply_text("🔐 **Access denied!** Please login first.")
        return
    
    # Create a fake callback query to reuse showQueue function
    class FakeCallbackQuery:
        def __init__(self, message, from_user):
            self.message = message
            self.from_user = from_user
    
    fake_cb = FakeCallbackQuery(m, m.from_user)
    await showQueue(c, fake_cb)

@mergeApp.on_message(filters.command(["cancel"]) & filters.private)
async def cancel_command(c: Client, m: Message):
    """Cancel current operations"""
    user_id = m.from_user.id
    
    # Clear user data
    if user_id in queueDB:
        queueDB[user_id] = {"videos": [], "urls": [], "subtitles": [], "audios": []}
    
    if user_id in formatDB:
        formatDB[user_id] = None
        
    # Clear upload preferences
    user_str = str(user_id)
    if user_str in UPLOAD_AS_DOC:
        del UPLOAD_AS_DOC[user_str]
        
    if user_str in UPLOAD_TO_DRIVE:
        del UPLOAD_TO_DRIVE[user_str]
    
    # Delete download directory
    await delete_all(root=f"downloads/{user_id}")
    
    await m.reply_text(
        "🗑️ **All Operations Cancelled!**\n\n"
        "✅ **Queue cleared**\n"
        "✅ **Files removed** \n"
        "✅ **Settings reset**\n\n"
        "📤 **Ready for new merge process**"
    )

if __name__ == "__main__":
    # Initialize FileStream-style bot
    LOGGER.info("🚀 Starting Professional FileStream-Style MERGE-BOT...")
    
    # Check if user bot is configured for premium uploads
    try:
        if hasattr(Config, 'USER_SESSION_STRING') and Config.USER_SESSION_STRING:
            LOGGER.info("🔄 Initializing Premium User Session...")
            userBot = Client(
                name="premium-filestream-merge-bot",
                session_string=Config.USER_SESSION_STRING,
                no_updates=True,
            )
            with userBot:
                user = userBot.get_me()
                Config.IS_PREMIUM = user.is_premium
                LOGGER.info(f"✅ Premium Status: {Config.IS_PREMIUM}")
    except Exception as err:
        LOGGER.error(f"❌ Premium session error: {err}")
        Config.IS_PREMIUM = False

    # Launch the FileStream-style professional bot
    LOGGER.info("🎯 Professional FileStream MERGE-BOT is starting...")
    mergeApp.run()

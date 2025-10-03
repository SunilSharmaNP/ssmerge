#!/usr/bin/env python3
"""
MERGE-BOT - Enhanced Version with GoFile Integration
Enhanced UI and better error handling for VPS deployment
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
parent_id = Config.GDRIVE_FOLDER_ID

class MergeBot(Client):
    def start(self):
        super().start()
        try:
            self.send_message(
                chat_id=int(Config.OWNER), 
                text="🚀 **Bot Started Successfully!**\n\n"
                     f"⏰ **Started at:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"🤖 **Bot Version:** Enhanced with GoFile"
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
    app_version="5.0+enhanced-gofile",
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
                "🔑 **Get password from:** @{Config.OWNER_USERNAME}",
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

🚀 **Version:** Enhanced with GoFile
"""

    await m.reply_text(text=stats, quote=True)

@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    """Enhanced start handler with beautiful UI like screenshots"""
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
                f"🔐 **Access Required**\n"
                f"📞 **Contact:** @{Config.OWNER_USERNAME}",
                quote=True,
                reply_markup=keyboard
            )
            return
    else:
        user.allowed = True

    user.set()

    # Beautiful start message for authorized users (like in screenshot)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
         InlineKeyboardButton("📊 Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("🔗 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")]
    ])

    await m.reply_photo(
        photo="https://telegra.ph/file/8c8c10f7b1e04b9b86f72.jpg",  # Bot logo
        caption=f"👋 **Hi {m.from_user.first_name}!**\n\n"
                f"🤖 **I Am Video Tool Bot** 🔥\n"
                f"📹 I Can Help You To Manage Your Videos Easily 😊\n\n"
                f"**Like:** Merge, Extract, Rename, Encode Etc...\n\n"
                f"🚀 **Started** `{get_readable_time(time.time() - botStartTime)}` **Ago**",
        quote=True,
        reply_markup=keyboard
    )

    del user

@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_msg(c: Client, m: Message):
    """Enhanced help with better formatting"""
    help_text = """📋 **HOW TO USE**

**🎬 Video Merging:**
1️⃣ Send custom thumbnail (optional)
2️⃣ Send 2 or more videos to merge
3️⃣ Select merge options from menu
4️⃣ Choose upload method:
   • 📤 Telegram Upload
   • 🔗 GoFile Upload (for large files)
5️⃣ Rename or use default name

**⚡ Quick Commands:**
• `/start` - Start the bot
• `/help` - Show this help
• `/settings` - User preferences
• `/login <password>` - Access bot
• `/extract` - Extract audio/subtitles

**🎯 Features:**
✅ Merge up to 10 videos
✅ Add custom audio tracks
✅ Add subtitle files  
✅ Upload to GoFile (unlimited size)
✅ Custom thumbnails
✅ Extract audio/video streams

**💡 Tips:**
• Use GoFile for files > 2GB
• Set custom thumbnail for better results
• Check settings for different modes"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
    ])

    await m.reply_text(help_text, quote=True, reply_markup=keyboard)

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
                "📞 **Contact:** @{Config.OWNER_USERNAME}",
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
🔗 **Go File:** False ❌  
📊 **Metadata:** False ❌
🎭 **Mode:** Video + Video"""

            await cb.message.edit_text(settings_text, reply_markup=settings_keyboard)

        elif data == "about":
            about_text = """ℹ️ **ABOUT THIS BOT**

🤖 **MergeR 2.0 | 4GB & Metadata** ⚡

**🆕 What's New:**
👨‍💻 Ban/Unban users
👨‍💻 Extract audio & subtitles  
👨‍💻 Merge video + audio
👨‍💻 Merge video + subtitles
👨‍💻 Upload to GoFile (unlimited size)
👨‍💻 Metadata preservation

**✨ Features:**
🔰 Merge up to 10 videos
🔰 Upload as document/video
🔰 Custom thumbnail support
🔰 GoFile integration for large files
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
    LOGGER.info("🚀 Starting Enhanced MERGE-BOT...")

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
                         "🔗 GoFile integration active",
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

#!/usr/bin/env python3
"""
MERGE-BOT - Complete Fixed Version
All spam, callback, and merge issues resolved
"""
from dotenv import load_dotenv
load_dotenv("config.env", override=True)

import os
import shutil
import time
import psutil
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Import configurations
from __init__ import (
    AUDIO_EXTENSIONS, LOGGER, MERGE_MODE, SUBTITLE_EXTENSIONS, 
    UPLOAD_AS_DOC, UPLOAD_TO_DRIVE, VIDEO_EXTENSIONS,
    formatDB, gDict, queueDB, replyDB
)
from config import Config
from helpers.utils import UserSettings, get_readable_file_size, get_readable_time

botStartTime = time.time()

class MergeBot(Client):
    def start(self):
        super().start()
        try:
            self.send_message(
                chat_id=int(Config.OWNER), 
                text="🚀 **Bot Started Successfully!**\n\n"
                     f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                     "🤖 Version: SSMERGE Bot v2.0"
            )
        except Exception:
            pass
        LOGGER.info("✅ Bot Started Successfully!")

    def stop(self):
        super().stop()
        LOGGER.info("🛑 Bot Stopped")

def delete_all(root):
    """Delete directory and all contents"""
    if os.path.exists(root):
        shutil.rmtree(root)

mergeApp = MergeBot(
    name="merge-bot",
    api_hash=Config.API_HASH,
    api_id=Config.TELEGRAM_API,
    bot_token=Config.BOT_TOKEN,
    workers=300,
    app_version="2.0+fixed",
)

# Create downloads directory
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# ================== LOGIN HANDLER ==================

@mergeApp.on_message(filters.command(["login"]) & filters.private)
async def loginHandler(c: Client, m: Message):
    """Fixed login handler with proper persistence"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    LOGGER.info(f"Login attempt - User: {user.user_id}, Allowed: {user.allowed}")
    
    if user.banned:
        await m.reply_text(
            "🚫 **Access Denied**\n\n❌ Your account has been banned\n"
            f"📞 Contact: @{Config.OWNER_USERNAME}",
            quote=True
        )
        return

    # Owner gets immediate access
    if user.user_id == int(Config.OWNER):
        user.allowed = True
        user.set()
        await m.reply_text(
            "✅ **Owner Access Granted!**\n\n"
            f"👋 Hi {m.from_user.first_name}\n🎉 You have full bot access!",
            quote=True
        )
        return

    # Check if already allowed
    if user.allowed:
        await m.reply_text(
            "✅ **Welcome Back!**\n\n"
            f"👋 Hi {m.from_user.first_name}\n🎉 You can use the bot freely!",
            quote=True
        )
        return

    # Password login
    try:
        passwd = m.text.split(" ", 1)[1].strip()
    except IndexError:
        await m.reply_text(
            "🔐 **Login Required**\n\n"
            "**Usage:** `/login <password>`\n\n"
            f"🔑 Get password from: @{Config.OWNER_USERNAME}",
            quote=True
        )
        return

    if passwd == Config.PASSWORD:
        user.allowed = True
        user.set()  # CRITICAL: Save to database
        await m.reply_text(
            "🎉 **Login Successful!**\n\n"
            "✅ Access granted\n🚀 You can now use the bot!",
            quote=True
        )
    else:
        await m.reply_text(
            "❌ **Login Failed**\n\n"
            "🔐 Incorrect password\n"
            f"📞 Contact: @{Config.OWNER_USERNAME}",
            quote=True
        )

# ================== START HANDLER ==================

@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    """Fixed start handler - no more spam"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    LOGGER.info(f"Start command - User: {user.user_id}, Allowed: {user.allowed}")
    
    # Check access for non-owners
    if m.from_user.id != int(Config.OWNER) and not user.allowed:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔐 Login", callback_data="need_login")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")],
            [InlineKeyboardButton("📞 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")]
        ])
        
        await m.reply_text(
            f"👋 **Hi {m.from_user.first_name}!**\n\n"
            "🤖 **I Am Video Merge Bot** 🔥\n"
            "📹 I Can Help You Merge Videos Easily 😊\n\n"
            "🔐 **Access Required**\n"
            f"📞 Contact: @{Config.OWNER_USERNAME}",
            quote=True,
            reply_markup=keyboard
        )
        return  # STOP HERE - NO SPAM

    # Owner access
    if m.from_user.id == int(Config.OWNER):
        user.allowed = True
        user.set()

    # Authorized user menu
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🔗 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")]
    ])
    
    await m.reply_text(
        f"👋 **Hi {m.from_user.first_name}!**\n\n"
        "🤖 **I Am Video Merge Bot** 🔥\n"
        "📹 I Can Help You Merge Videos Easily 😊\n\n"
        "✅ **You are authorized to use this bot**\n"
        f"🚀 Uptime: `{get_readable_time(time.time() - botStartTime)}`",
        quote=True,
        reply_markup=keyboard
    )

# ================== VIDEO UPLOAD HANDLER ==================

@mergeApp.on_message((filters.video | filters.document) & filters.private)
async def video_upload_handler(c: Client, m: Message):
    """Handle video uploads and add to queue"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if not user.allowed and m.from_user.id != int(Config.OWNER):
        await m.reply_text("🔐 **Access Required!** Please login first using `/login <password>`")
        return
    
    # Initialize user queue if not exists
    if m.from_user.id not in queueDB:
        queueDB[m.from_user.id] = {"videos": [], "subtitles": [], "audios": []}

    # Check file type and add to appropriate queue
    file_added = False
    file_name = "Unknown"
    file_size = 0
    
    if m.video:
        queueDB[m.from_user.id]["videos"].append(m.id)
        file_name = m.video.file_name or f"video_{m.id}.mp4"
        file_size = m.video.file_size
        file_added = True
        
    elif m.document:
        file_ext = m.document.file_name.split('.')[-1].lower() if m.document.file_name else ""
        
        if file_ext in VIDEO_EXTENSIONS:
            queueDB[m.from_user.id]["videos"].append(m.id)
            file_added = True
        elif file_ext in AUDIO_EXTENSIONS:
            queueDB[m.from_user.id]["audios"].append(m.id)
            file_added = True  
        elif file_ext in SUBTITLE_EXTENSIONS:
            queueDB[m.from_user.id]["subtitles"].append(m.id)
            file_added = True
            
        file_name = m.document.file_name or f"document_{m.id}"
        file_size = m.document.file_size

    if file_added:
        # Show queue status with merge button
        video_count = len(queueDB[m.from_user.id]["videos"])
        audio_count = len(queueDB[m.from_user.id]["audios"]) 
        subtitle_count = len(queueDB[m.from_user.id]["subtitles"])
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Merge Now", callback_data="merge")],
            [InlineKeyboardButton("📋 Show Queue", callback_data="show_queue"),
             InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_queue")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ])
        
        await m.reply_text(
            f"✅ **File Added to Queue!**\n\n"
            f"📁 **File:** `{file_name}`\n"
            f"📊 **Size:** `{get_readable_file_size(file_size)}`\n\n"
            f"📋 **Queue Status:**\n"
            f"🎬 Videos: **{video_count}**\n"
            f"🎵 Audios: **{audio_count}**\n"
            f"📝 Subtitles: **{subtitle_count}**\n\n"
            f"{'🚀 Ready to merge!' if video_count >= 2 else '📥 Add more videos to merge'}",
            reply_markup=keyboard
        )
    else:
        await m.reply_text(
            "❌ **Unsupported File Type!**\n\n"
            "📌 **Supported formats:**\n"
            f"🎬 Videos: `{', '.join(VIDEO_EXTENSIONS)}`\n"
            f"🎵 Audios: `{', '.join(AUDIO_EXTENSIONS)}`\n"
            f"📝 Subtitles: `{', '.join(SUBTITLE_EXTENSIONS)}`"
        )

# ================== CALLBACK HANDLER ==================

@mergeApp.on_callback_query()
async def callback_handler(c: Client, cb):
    """Fixed callback handler with all functions"""
    data = cb.data
    user_id = cb.from_user.id
    user = UserSettings(user_id, cb.from_user.first_name)
    
    LOGGER.info(f"Callback: {data} from user {user_id}, allowed: {user.allowed}")
    
    try:
        if data == "need_login":
            await cb.message.edit_text(
                "🔐 **Login Required**\n\n"
                "**Usage:** Send `/login <password>`\n\n"
                f"🔑 Get password from: @{Config.OWNER_USERNAME}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
                ])
            )
            
        elif data == "back_to_start":
            await start_handler(c, cb.message)
            
        elif data == "settings":
            if not user.allowed:
                await cb.answer("🔐 Login required!", show_alert=True)
                return
                
            settings_text = f"""⚙️ **User Settings**

👤 **Name:** {cb.from_user.first_name}
🆔 **User ID:** `{user_id}`
🎭 **Mode:** Video + Video
📤 **Upload:** As Video
🚫 **Banned:** No ✅
✅ **Allowed:** Yes"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎥 Mode: Video+Video", callback_data="mode_1")],
                [InlineKeyboardButton("🎵 Mode: Video+Audio", callback_data="mode_2")],
                [InlineKeyboardButton("📝 Mode: Video+Subtitle", callback_data="mode_3")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
            ])
            
            await cb.message.edit_text(settings_text, reply_markup=keyboard)
            
        elif data.startswith("mode_"):
            mode_id = int(data.split("_")[1])
            user.merge_mode = mode_id
            user.set()
            
            mode_names = {1: "Video+Video", 2: "Video+Audio", 3: "Video+Subtitle"}
            await cb.answer(f"✅ Mode changed to: {mode_names.get(mode_id, 'Unknown')}")
            
        elif data == "merge":
            if not user.allowed:
                await cb.answer("🔐 Login required!", show_alert=True)
                return
                
            if user_id not in queueDB or not queueDB[user_id]["videos"]:
                await cb.answer("📋 Queue is empty! Please add videos first.", show_alert=True)
                return
                
            video_count = len(queueDB[user_id]["videos"])
            if video_count < 2:
                await cb.answer("📥 Need at least 2 videos to merge!", show_alert=True)
                return
            
            # Start merge process
            await cb.message.edit_text(
                "🔄 **Starting Merge Process...**\n\n"
                f"📁 Processing {video_count} videos\n"
                "⏳ Please wait, this may take a while..."
            )
            
            try:
                # Import and call merge function
                from helpers.merge_helper import start_merge_process
                await start_merge_process(c, cb, user_id)
                
            except ImportError:
                await cb.message.edit_text(
                    "❌ **Merge Module Not Found!**\n\n"
                    "🚨 The merge functionality is not available.\n"
                    "📞 Contact the developer for assistance."
                )
            except Exception as e:
                LOGGER.error(f"Merge error: {e}")
                await cb.message.edit_text(
                    "❌ **Merge Failed!**\n\n"
                    f"🚨 Error: `{str(e)}`\n"
                    "💡 Please try again or contact support."
                )
                
        elif data == "show_queue":
            if user_id not in queueDB:
                await cb.answer("📋 Queue is empty!", show_alert=True)
                return
                
            video_count = len(queueDB[user_id]["videos"])
            audio_count = len(queueDB[user_id]["audios"])
            subtitle_count = len(queueDB[user_id]["subtitles"])
            
            queue_text = f"""📋 **Current Queue:**

🎬 Videos: {video_count}
🎵 Audios: {audio_count}  
📝 Subtitles: {subtitle_count}

Total Items: {video_count + audio_count + subtitle_count}"""
            
            await cb.answer(queue_text, show_alert=True)
            
        elif data == "clear_queue":
            if user_id in queueDB:
                queueDB[user_id] = {"videos": [], "subtitles": [], "audios": []}
                await cb.answer("🗑️ Queue cleared successfully!", show_alert=True)
            else:
                await cb.answer("📋 Queue is already empty!", show_alert=True)
                
        elif data == "about":
            about_text = """ℹ️ **About This Bot**

🤖 **SSMERGE Bot v2.0**

**Features:**
✅ Merge multiple videos
✅ Add audio tracks  
✅ Add subtitle files
✅ Custom thumbnails
✅ Password protection
✅ User management

**Developer:** @SunilSharmaNP
**Support:** Contact owner for issues"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
            ])
            
            await cb.message.edit_text(about_text, reply_markup=keyboard)
            
        elif data == "stats":
            if user_id != int(Config.OWNER):
                await cb.answer("❌ Owner only!", show_alert=True)
                return
                
            uptime = get_readable_time(time.time() - botStartTime)
            total_users = len(queueDB)
            
            stats_text = f"""📊 **Bot Statistics**

⏰ **Uptime:** `{uptime}`
👥 **Active Users:** `{total_users}`
🤖 **Version:** SSMERGE v2.0
📅 **Started:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(botStartTime))}"""
            
            await cb.answer(stats_text, show_alert=True)
            
        else:
            await cb.answer("🚧 Feature coming soon!", show_alert=True)
            
    except Exception as e:
        LOGGER.error(f"Callback error: {e}")
        await cb.answer("❌ Something went wrong!", show_alert=True)

# ================== ADDITIONAL COMMANDS ==================

@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_handler(c: Client, m: Message):
    """Help command"""
    help_text = """❓ **How to Use**

1️⃣ **Login:** `/login <password>`
2️⃣ **Send Videos:** Upload 2 or more video files
3️⃣ **Click Merge:** Press the "🔥 Merge Now" button
4️⃣ **Wait:** Bot will process and send merged video

**Commands:**
• `/start` - Start the bot
• `/login <password>` - Login to use bot
• `/help` - Show this help
• `/settings` - User preferences

**Support:** Contact @{Config.OWNER_USERNAME}"""
    
    await m.reply_text(help_text, quote=True)

@mergeApp.on_message(filters.command(["settings"]) & filters.private)
async def settings_command(c: Client, m: Message):
    """Settings command"""
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if not user.allowed and m.from_user.id != int(Config.OWNER):
        await m.reply_text("🔐 **Access Required!** Please login first.")
        return
    
    # Trigger settings callback
    await callback_handler(c, type('obj', (object,), {
        'data': 'settings',
        'from_user': m.from_user,
        'message': m,
        'answer': lambda x, show_alert=False: None
    })())

if __name__ == "__main__":
    LOGGER.info("🚀 Starting SSMERGE Bot...")
    mergeApp.run()

import asyncio
import os
import time
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import MessageNotModified

from bot import UPLOAD_AS_DOC, UPLOAD_TO_DRIVE, delete_all, formatDB, gDict, queueDB, replyDB, LOGGER
from config import Config
from helpers.utils import UserSettings
from plugins.mergeVideo import mergeNow

# Import GoFile uploader
try:
    from helpers.uploader import GofileUploader
    GOFILE_AVAILABLE = True
except ImportError:
    GOFILE_AVAILABLE = False
    LOGGER.warning("GoFile uploader not available")

@Client.on_callback_query()
async def callback_handler(c: Client, cb: CallbackQuery):
    """Enhanced callback handler with GoFile support and better error handling"""
    try:
        user_id = cb.from_user.id
        data = cb.data
        user = UserSettings(user_id, cb.from_user.first_name)

        # Check user permissions
        if user_id != int(Config.OWNER) and not user.allowed:
            await cb.answer("🔐 Access denied! Please login first.", show_alert=True)
            return

        LOGGER.info(f"Callback from user {user_id}: {data}")

        if data == "cancel":
            await handle_cancel(cb, user_id)

        elif data == "merge":
            await handle_merge_request(c, cb, user_id)

        elif data.startswith("rename"):
            await handle_rename(cb, user_id)

        elif data.startswith("upload"):
            await handle_upload_mode(cb, data, user_id)

        elif data.startswith("gofile"):
            await handle_gofile_toggle(cb, data, user_id)

        elif data == "settings":
            await show_settings_menu(cb, user)

        elif data == "help":
            await show_help_menu(cb)

        elif data == "about":
            await show_about_menu(cb)

        elif data == "back_to_start":
            await show_start_menu(c, cb)

        elif data == "close":
            await cb.message.delete()

        else:
            # Handle other callbacks
            await cb.answer("🚧 Feature under development!", show_alert=True)

    except Exception as e:
        LOGGER.error(f"Callback handler error: {e}")
        try:
            await cb.answer("❌ Something went wrong! Please try again.", show_alert=True)
        except:
            pass

async def handle_cancel(cb: CallbackQuery, user_id: int):
    """Handle cancel operation with proper cleanup"""
    try:
        # Clear user data
        if user_id in queueDB:
            queueDB[user_id] = {"videos": [], "subtitles": [], "audios": []}

        if user_id in formatDB:
            formatDB[user_id] = None

        if user_id in replyDB:
            del replyDB[user_id]

        # Clear upload preferences
        if str(user_id) in UPLOAD_AS_DOC:
            del UPLOAD_AS_DOC[str(user_id)]

        if str(user_id) in UPLOAD_TO_DRIVE:
            del UPLOAD_TO_DRIVE[str(user_id)]

        # Delete download directory
        await delete_all(root=f"downloads/{str(user_id)}")

        await cb.message.edit_text(
            "🗑️ **Operation Cancelled**\n\n"
            "✅ All files and settings cleared\n"
            "📤 Ready for new merge request"
        )

        LOGGER.info(f"Cancelled operation for user {user_id}")

    except Exception as e:
        LOGGER.error(f"Cancel handler error: {e}")
        await cb.answer("❌ Error during cancellation", show_alert=True)

async def handle_merge_request(c: Client, cb: CallbackQuery, user_id: int):
    """Handle merge request with better UI"""
    try:
        # Check if user has videos to merge
        if user_id not in queueDB or not queueDB[user_id]["videos"]:
            await cb.answer("❌ No videos found to merge!", show_alert=True)
            return

        videos_count = len(queueDB[user_id]["videos"])

        # Show merge options with GoFile integration
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Upload to Telegram", callback_data="upload_telegram")],
            [InlineKeyboardButton("🔗 Upload to GoFile", callback_data="upload_gofile")],
            [InlineKeyboardButton("📁 Upload as Document", callback_data="upload_document"),
             InlineKeyboardButton("🎬 Upload as Video", callback_data="upload_video")],
            [InlineKeyboardButton("✏️ Custom Name", callback_data="rename_custom"),
             InlineKeyboardButton("📝 Default Name", callback_data="rename_default")],
            [InlineKeyboardButton("🔙 Back", callback_data="show_queue")]
        ])

        await cb.message.edit_text(
            f"🔀 **Ready to Merge!**\n\n"
            f"📹 **Videos:** `{videos_count}`\n"
            f"📊 **Mode:** Video Merge\n\n"
            f"**Choose upload method:**",
            reply_markup=keyboard
        )

    except Exception as e:
        LOGGER.error(f"Merge request error: {e}")
        await cb.answer("❌ Error preparing merge", show_alert=True)

async def handle_upload_mode(cb: CallbackQuery, data: str, user_id: int):
    """Handle upload mode selection"""
    try:
        if data == "upload_telegram":
            UPLOAD_TO_DRIVE[str(user_id)] = False
            await cb.answer("📤 Telegram upload selected", show_alert=False)

        elif data == "upload_gofile":
            if GOFILE_AVAILABLE:
                UPLOAD_TO_DRIVE[str(user_id)] = True
                await cb.answer("🔗 GoFile upload selected", show_alert=False)
            else:
                await cb.answer("❌ GoFile not available", show_alert=True)
                return

        elif data == "upload_document":
            UPLOAD_AS_DOC[str(user_id)] = True
            await cb.answer("📁 Document mode selected", show_alert=False)

        elif data == "upload_video":
            UPLOAD_AS_DOC[str(user_id)] = False
            await cb.answer("🎬 Video mode selected", show_alert=False)

        # Start merging process
        await start_merge_process(cb, user_id)

    except Exception as e:
        LOGGER.error(f"Upload mode error: {e}")
        await cb.answer("❌ Error setting upload mode", show_alert=True)

async def handle_gofile_toggle(cb: CallbackQuery, data: str, user_id: int):
    """Handle GoFile toggle"""
    try:
        if not GOFILE_AVAILABLE:
            await cb.answer("❌ GoFile integration not available", show_alert=True)
            return

        if data == "gofile_on":
            UPLOAD_TO_DRIVE[str(user_id)] = True
            await cb.answer("🔗 GoFile upload enabled", show_alert=False)
        else:
            UPLOAD_TO_DRIVE[str(user_id)] = False
            await cb.answer("📤 Telegram upload enabled", show_alert=False)

        # Refresh settings menu
        await show_settings_menu(cb, UserSettings(user_id, cb.from_user.first_name))

    except Exception as e:
        LOGGER.error(f"GoFile toggle error: {e}")
        await cb.answer("❌ Error toggling GoFile", show_alert=True)

async def handle_rename(cb: CallbackQuery, user_id: int):
    """Handle file renaming"""
    try:
        if cb.data == "rename_default":
            # Use default name
            file_name = f"downloads/{user_id}/[@{Config.OWNER_USERNAME}]_merged.mkv"
            await start_merge_with_name(cb, user_id, file_name)

        elif cb.data == "rename_custom":
            await cb.message.edit_text(
                "✏️ **Custom File Name**\n\n"
                "📝 Reply with your desired filename\n"
                "⚠️ Don't include file extension\n\n"
                "**Example:** `My Merged Video`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="merge")]
                ])
            )
            # Note: This would need to be handled in a separate message handler

    except Exception as e:
        LOGGER.error(f"Rename error: {e}")
        await cb.answer("❌ Error handling rename", show_alert=True)

async def start_merge_process(cb: CallbackQuery, user_id: int):
    """Start the actual merge process"""
    try:
        # Generate default filename
        timestamp = int(time.time())
        file_name = f"downloads/{user_id}/[@{Config.OWNER_USERNAME}]_{timestamp}.mkv"

        await start_merge_with_name(cb, user_id, file_name)

    except Exception as e:
        LOGGER.error(f"Start merge error: {e}")
        await cb.answer("❌ Error starting merge process", show_alert=True)

async def start_merge_with_name(cb: CallbackQuery, user_id: int, file_name: str):
    """Start merge with specified filename"""
    try:
        await cb.message.edit_text("🔄 **Starting merge process...**\n\nPlease wait...")

        # Import and call merge function
        from plugins.mergeVideo import mergeNow
        await mergeNow(cb.client, cb, file_name)

    except Exception as e:
        LOGGER.error(f"Merge with name error: {e}")
        await cb.message.edit_text(
            f"❌ **Merge Failed!**\n\n"
            f"🚨 **Error:** `{str(e)}`\n\n"
            f"💡 Please try again or contact support."
        )

async def show_settings_menu(cb: CallbackQuery, user: UserSettings):
    """Show enhanced settings menu like in screenshots"""
    try:
        # Get current settings
        upload_mode = "Video 📹" if not UPLOAD_AS_DOC.get(str(user.user_id), False) else "Document 📁"
        gofile_status = "✅" if UPLOAD_TO_DRIVE.get(str(user.user_id), False) else "❌"

        settings_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📤 Upload As: {upload_mode}", callback_data="toggle_upload_mode")],
            [InlineKeyboardButton("🎥 Video + Video ✅", callback_data="mode_video"),
             InlineKeyboardButton("🎵 Video + Audio", callback_data="mode_audio")],
            [InlineKeyboardButton("📝 Video + Subtitle", callback_data="mode_subtitle"),
             InlineKeyboardButton("🔍 Extract", callback_data="mode_extract")],
            [InlineKeyboardButton("🗑️ Remove Stream", callback_data="remove_stream"),
             InlineKeyboardButton("✏️ Rename", callback_data="rename_file")],
            [InlineKeyboardButton("🖼️ Thumbnail ❌", callback_data="thumbnail_toggle")],
            [InlineKeyboardButton(f"🔗 GoFile {gofile_status}", callback_data="gofile_toggle")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])

        settings_text = f"""⚙️ **User Settings:**

👤 **Name:** {user.name}
🆔 **User ID:** `{user.user_id}`
📤 **Upload As:** {upload_mode}
🚫 **Ban Status:** {"True" if user.banned else "False"} {"❌" if user.banned else "✅"}
🔗 **GoFile:** {gofile_status}
📊 **Metadata:** False ❌
🎭 **Mode:** Video + Video"""

        await cb.message.edit_text(settings_text, reply_markup=settings_keyboard)

    except Exception as e:
        LOGGER.error(f"Settings menu error: {e}")
        await cb.answer("❌ Error loading settings", show_alert=True)

async def show_help_menu(cb: CallbackQuery):
    """Show help menu"""
    help_text = """❓ **HELP & USAGE**

**🎬 How to Merge Videos:**
1️⃣ Send videos (2-10 files)
2️⃣ Click "🔗 Merge Now"
3️⃣ Choose upload method
4️⃣ Wait for processing

**📤 Upload Options:**
• **Telegram:** Direct upload (2GB limit)
• **GoFile:** External upload (unlimited)

**⚙️ Settings:**
• Change upload mode
• Toggle GoFile upload
• Set custom thumbnails

**💡 Tips:**
• Use GoFile for large files
• Set thumbnails before merging
• Check logs if issues occur"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
    ])

    await cb.message.edit_text(help_text, reply_markup=keyboard)

async def show_about_menu(cb: CallbackQuery):
    """Show about menu"""
    about_text = """ℹ️ **ABOUT MERGE-BOT**

🤖 **Version:** 2.0 Enhanced
⚡ **Features:** 4GB Support & GoFile

**🆕 What's New:**
✅ GoFile integration (unlimited size)
✅ Enhanced UI/UX
✅ Better error handling
✅ Process management fixes
✅ Improved stability

**🔥 Core Features:**
🎬 Merge up to 10 videos
🎵 Add audio tracks
📝 Add subtitles
🖼️ Custom thumbnails
📤 Multiple upload options
🔗 GoFile support

**👨‍💻 Enhanced by AI Assistant**
**🏠 Original by @yashoswalyo**"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/yashoswalyo")],
        [InlineKeyboardButton("🏘 Source", url="https://github.com/yashoswalyo/MERGE-BOT"),
         InlineKeyboardButton("🤔 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
    ])

    await cb.message.edit_text(about_text, reply_markup=keyboard)

async def show_start_menu(c: Client, cb: CallbackQuery):
    """Show start menu"""
    user = UserSettings(cb.from_user.id, cb.from_user.first_name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
         InlineKeyboardButton("📊 Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("🔗 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}")]
    ])

    await cb.message.edit_text(
        f"👋 **Hi {cb.from_user.first_name}!**\n\n"
        f"🤖 **I Am Video Tool Bot** 🔥\n"
        f"📹 I Can Help You To Manage Your Videos Easily 😊\n\n"
        f"**Like:** Merge, Extract, Rename, Encode Etc...\n\n"
        f"🚀 **Enhanced with GoFile Integration**",
        reply_markup=keyboard
    )

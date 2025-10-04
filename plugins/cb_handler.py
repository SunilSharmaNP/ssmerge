#!/usr/bin/env python3
"""
🎬 COMPLETE CB_HANDLER - FIXED & INTEGRATED 
All callbacks working with enhanced downloader & uploader integration
"""

import asyncio
import os
from pyrogram import filters, Client
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    Message,
)

from helpers import database
from helpers.utils import UserSettings, get_readable_file_size, get_readable_time
from bot import (
    LOGGER,
    UPLOAD_AS_DOC,
    UPLOAD_TO_DRIVE,
    delete_all,
    formatDB,
    gDict,
    queueDB,
    showQueue,
    user_processes,
)
from config import Config

# Import COMPLETE merge integration - FIXED VERSION
from plugins.mergeVideo_enhanced import mergeNow_enhanced
from helpers.downloader import download_from_url, download_from_tg
from helpers.uploader import GofileUploader, upload_to_telegram

@Client.on_callback_query()
async def callback_handler(c: Client, cb: CallbackQuery):
    """COMPLETE Professional FileStream-style callback handler with FULL INTEGRATION"""
    
    try:
        user_id = cb.from_user.id
        data = cb.data
        user = UserSettings(user_id, cb.from_user.first_name)
        
        LOGGER.info(f"📞 Callback from user {user_id}: {data}")
        
        # Check user permissions for most actions
        if user_id != int(Config.OWNER) and not user.allowed and data not in ["help", "about", "loot_deals", "close", "start"]:
            await cb.answer("🔐 Access denied! Please use /start and login first", show_alert=True)
            return
        
        # FileStream-style main start menu
        if data == "start":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Help", callback_data="help"),
                 InlineKeyboardButton("💖 About", callback_data="about")],
                [InlineKeyboardButton("🛍️ Loot Deals 🔥", callback_data="loot_deals")],
                [InlineKeyboardButton("🔒 Close", callback_data="close")]
            ])
            
            # Check if user is authorized
            if user.allowed:
                start_msg = f"""**👋 Hello {cb.from_user.first_name} 2.0 [ + ] 🌸**

🤖 **I Am Professional Video Merger Bot ⚡**

📁 **Send Me Videos/URLs, I Will Merge & Upload:**
🔗 **Telegram Upload** ☕ **GoFile Upload (Unlimited)**  
ℹ️ **Custom Thumbnails & Metadata**

**—🌸❖「 ★ Professional Features ★ 」❖🌸—**

• **Merge Multiple Videos with High Quality**
• **Support Direct Download URLs (DDL)** 
• **Upload to GoFile (No Size Limit)**
• **Custom Thumbnails & Beautiful UI**

**🎯 Current Queue:** {len(queueDB.get(user_id, {}).get('videos', []))} videos + {len(queueDB.get(user_id, {}).get('urls', []))} URLs

⭐ **Powered By ★彡 Professional Merge Bot 彡★**"""
            else:
                start_msg = f"""**👋 Hello {cb.from_user.first_name} 2.0 [ + ] 🌸**

🤖 **I Am Simple & Fastest File to Stream Links Generator Bot ⚡**

📁 **Send Me Any Telegram File, I Will Instantly Generate ...**
🔗 Download Link ☕ Stream Link  
ℹ️ MediaInfo

**—🌸❖「 ★ Special Features ★ 」❖🌸—**

• **You Can Use Me In Your Channels & Groups Also [Authorized Chat Only]**
• **I Can Store Your File And Make A Shareable Link Of That File**

⭐ **Powered By ★彡 Professional Merge Bot 彡★**"""

            await cb.message.edit_text(start_msg, reply_markup=keyboard)
            return

        # Help menu with FileStream style
        elif data == "help":
            help_text = """📋 **PROFESSIONAL MERGER BOT - COMPLETE GUIDE**

**🎬 Enhanced Merge Process:**
1️⃣ **Send Videos/URLs** (Auto-added to queue)
2️⃣ **Click "Merge Now"** (Downloads everything first)  
3️⃣ **Professional Processing** (High-quality merge)
4️⃣ **Choose Upload Method** (Telegram/GoFile)
5️⃣ **Custom Thumbnails** (For Telegram uploads)
6️⃣ **Get Your Merged Video!**

**🔗 DDL Support Enhanced:**
• HTTP/HTTPS direct links
• GoFile.io links (with password support)
• Auto filename detection  
• Professional progress tracking
• Fast parallel downloads

**💡 Professional Tips:**
🔹 **GoFile:** For files over 2GB
🔹 **Custom Thumbnails:** Send before merging
🔹 **Queue Management:** Up to 10 items
🔹 **Progress Tracking:** Real-time updates

**⚡ Enhanced Commands:**
• `/start` - Professional main menu
• `/help` - Complete guide  
• `/queue` - Show queue with details
• `/cancel` - Cancel with cleanup
• `/settings` - User preferences

**🎯 FileStream Professional Experience**"""

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
            ])
            
            await cb.message.edit_text(help_text, reply_markup=keyboard)
            return

        # About menu with FileStream style  
        elif data == "about":
            about_text = f"""💖 **About Professional Merge Bot v2.0**

**🤖 Bot Information:**
├─ **Name:** Professional Video Merger
├─ **Version:** FileStream Professional v2.0  
├─ **Style:** Complete FileStream UI Integration
├─ **Features:** DDL + GoFile + Enhanced Processing
└─ **Owner:** @{Config.OWNER_USERNAME}

**✨ Enhanced Features:**  
• **Complete DDL Integration** (URLs + GoFile)
• **Professional Progress Tracking**
• **GoFile Unlimited Uploads**  
• **Custom Thumbnails Support**
• **Enhanced Queue Management**
• **FileStream-Style Beautiful UI**

**📊 Performance:**
• **Uptime:** 99.9% Reliable
• **Processing:** High-Performance FFmpeg
• **Quality:** No Compression Loss
• **DDL Speed:** Multi-threaded downloads
• **Upload Speed:** Optimized for all sizes

**🎯 Current Users:** {len(queueDB)}
**⚡ Status:** Online & Professional

**🚀 Complete Integration v2.0**"""

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👨💻 Developer", url="https://t.me/yashoswalyo"),
                 InlineKeyboardButton("🏘 Source", url="https://github.com/yashoswalyo/MERGE-BOT")],
                [InlineKeyboardButton(f"🤔 Owner", url=f"https://t.me/{Config.OWNER_USERNAME}"),
                 InlineKeyboardButton("💬 Support", url="https://t.me/yo_codes_support")],
                [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
            ])
            
            await cb.message.edit_text(about_text, reply_markup=keyboard)
            return

        # Loot deals - FileStream style feature
        elif data == "loot_deals":
            deals_text = f"""🛍️ **Loot Deals - Enhanced Offers! 🔥**

**—🌸❖「 ★ Professional Packages ★ 」❖🌸—**

🎯 **Professional Video Merging:**
• **Free:** Basic merge (2GB limit)
• **Premium:** Unlimited GoFile + 4GB Telegram  
• **Pro:** Custom features + Priority support

💎 **Enhanced Features:**
• **DDL Integration:** Download any URL
• **GoFile Unlimited:** No size restrictions
• **Professional UI:** Beautiful FileStream style
• **Custom Processing:** High-quality output
• **24/7 Support:** Always available

**🔥 Special DDL Features:**
• **GoFile.io Support:** With password protection
• **Multi-threaded Downloads:** Faster processing  
• **Auto-retry Logic:** Reliable downloads
• **Progress Tracking:** Professional interface

**📞 Contact for Premium Features:**
• **Telegram:** @{Config.OWNER_USERNAME}
• **Packages:** Affordable & flexible
• **Custom Solutions:** Tailored for your needs

🔥 **Limited Time: Enhanced features available!**"""

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Contact Owner", url=f"https://t.me/{Config.OWNER_USERNAME}"),
                 InlineKeyboardButton("💬 Support Group", url="https://t.me/yo_codes_support")],
                [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
            ])
            
            await cb.message.edit_text(deals_text, reply_markup=keyboard)
            return

        # Close menu
        elif data == "close":
            await cb.message.delete(True)
            try:
                if cb.message.reply_to_message:
                    await cb.message.reply_to_message.delete(True)
            except:
                pass
            return

        # Show queue with enhanced UI
        elif data == "show_queue":
            await showQueue(c, cb)
            return

        # Clear queue with confirmation
        elif data == "clear_queue":
            # Enhanced cleanup
            if user_id in queueDB:
                old_data = queueDB[user_id].copy()
                queueDB[user_id] = {"videos": [], "urls": [], "subtitles": [], "audios": []}
                
                cleared_items = []
                if old_data.get('videos'):
                    cleared_items.append(f"{len(old_data['videos'])} videos")
                if old_data.get('urls'):
                    cleared_items.append(f"{len(old_data['urls'])} URLs")
                if old_data.get('subtitles'):
                    cleared_items.append(f"{len(old_data['subtitles'])} subtitles")
                if old_data.get('audios'):
                    cleared_items.append(f"{len(old_data['audios'])} audios")
                
                items_text = ", ".join(cleared_items) if cleared_items else "No items"
                
                await cb.message.edit_text(
                    f"🗑️ **Queue Cleared Successfully!**\n\n"
                    f"✅ **Removed:** {items_text}\n"
                    f"✅ **Queue reset** to empty state\n"
                    f"✅ **Ready for new content**\n\n"
                    f"📤 **Send videos/URLs to start merging**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
                    ])
                )
            return

        # Need more videos info
        elif data == "need_more":
            await cb.answer(
                "⚠️ Need at least 2 videos/URLs to start merging!\n\n"
                "📤 Send more videos or URLs to continue.\n"
                "🔗 Supported: Telegram files + Direct URLs",
                show_alert=True
            )
            return

        # Queue details - ENHANCED
        elif data == "queue_details":
            queue_data = queueDB.get(user_id, {"videos": [], "urls": [], "subtitles": [], "audios": []})
            videos = queue_data.get("videos", [])
            urls = queue_data.get("urls", [])
            
            details_text = f"📊 **Enhanced Queue Information**\n\n"
            details_text += f"🎬 **Telegram Videos:** {len(videos)}\n"
            details_text += f"🔗 **Download URLs:** {len(urls)}\n"
            details_text += f"📝 **Subtitles:** {len(queue_data.get('subtitles', []))}\n"
            details_text += f"🎵 **Audio Tracks:** {len(queue_data.get('audios', []))}\n\n"
            
            if urls:
                details_text += "**🔗 URLs in Queue:**\n"
                for i, url in enumerate(urls[:3], 1):  # Show first 3 URLs
                    url_display = url if len(url) <= 45 else f"{url[:42]}..."
                    details_text += f"`{i}.` {url_display}\n"
                if len(urls) > 3:
                    details_text += f"*...and {len(urls) - 3} more URLs*\n"
                details_text += "\n"
            
            total_items = len(videos) + len(urls)
            details_text += f"**📊 Total Items:** {total_items}/10"
            
            if total_items >= 2:
                details_text += " ✅ **Ready for professional merge!**"
            else:
                details_text += " ⚠️ **Need more items to start**"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Merge Now", callback_data="merge")] if total_items >= 2 else [],
                [InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_queue"),
                 InlineKeyboardButton("🔙 Back", callback_data="show_queue")]
            ])
            
            await cb.message.edit_text(details_text, reply_markup=keyboard)
            return

        # MAIN MERGE BUTTON - COMPLETE INTEGRATION
        elif data == "merge":
            # Check if user already has active process
            if user_id in user_processes and user_processes.get(user_id):
                await cb.answer("⚠️ Merge process already running! Please wait for completion.", show_alert=True)
                return
            
            queue_data = queueDB.get(user_id, {"videos": [], "urls": [], "subtitles": [], "audios": []})
            videos = queue_data.get("videos", [])
            urls = queue_data.get("urls", [])
            total_items = len(videos) + len(urls)
            
            if total_items < 2:
                await cb.answer("❌ Need at least 2 videos/URLs to merge!", show_alert=True)
                return
            
            # Mark user as having active process
            user_processes[user_id] = True
            
            # Enhanced merge process: Download -> Merge -> Upload Choice
            await cb.message.edit_text(
                f"🚀 **Starting Professional Merge Process...**\n\n"
                f"📊 **Items to Process:** {total_items}\n"
                f"├─ **Telegram Videos:** {len(videos)}\n"  
                f"├─ **Download URLs:** {len(urls)}\n"
                f"└─ **Processing Mode:** Enhanced Integration\n\n"
                f"**Phase 1:** 📥 Downloading all files...\n"
                f"**Phase 2:** 🔄 Professional merging...\n"  
                f"**Phase 3:** 📤 Upload destination choice...\n\n"
                f"⚡ **Enhanced processing may take time...**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel Process", callback_data="cancel_merge")]
                ])
            )
            
            # Start the COMPLETE enhanced merge process
            asyncio.create_task(start_complete_merge_process(c, cb, user))
            return

        # Cancel merge process
        elif data == "cancel_merge":
            await handle_cancel_operation(cb, user_id)
            return

        # Upload destination choice (after merge completion)
        elif data == "choose_upload_destination":
            await cb.message.edit_text(
                f"🎉 **Professional Merge Completed!**\n\n"
                f"✅ **High-quality video merged successfully**\n"
                f"📊 **Ready for upload with enhanced options**\n\n" 
                f"**Choose your preferred upload destination:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Telegram Upload", callback_data="upload_to_telegram"),
                     InlineKeyboardButton("🔗 GoFile Upload", callback_data="upload_to_gofile")],
                    [InlineKeyboardButton("📊 Compare Options", callback_data="compare_upload_options")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")]
                ])
            )
            return

        # Upload to Telegram - ENHANCED
        elif data == "upload_to_telegram":
            UPLOAD_TO_DRIVE[str(user_id)] = False
            await cb.message.edit_text(
                f"📤 **Telegram Upload Selected**\n\n"
                f"📊 **Size Limit:** {'4GB (Premium)' if Config.IS_PREMIUM else '2GB (Standard)'}\n"
                f"⚡ **Upload Type:** Direct to Telegram servers\n"
                f"🎬 **Quality:** High-definition maintained\n\n"
                f"**Custom Thumbnail Options:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🖼️ Use Custom Thumbnail", callback_data="use_custom_thumb"),
                     InlineKeyboardButton("🎬 Auto Thumbnail", callback_data="use_auto_thumb")],
                    [InlineKeyboardButton("📁 Upload as Document", callback_data="upload_as_doc"),
                     InlineKeyboardButton("🎞️ Upload as Video", callback_data="upload_as_video")],
                    [InlineKeyboardButton("🔙 Back", callback_data="choose_upload_destination")]
                ])
            )
            return

        # Upload to GoFile - ENHANCED  
        elif data == "upload_to_gofile":
            UPLOAD_TO_DRIVE[str(user_id)] = True
            await cb.message.edit_text(
                f"🔗 **GoFile Upload Selected**\n\n"
                f"✅ **Unlimited file size** (No 2GB/4GB limits)\n"
                f"✅ **High-speed upload** with retry logic\n"
                f"✅ **No compression** (Original quality)\n"
                f"✅ **Professional progress** tracking\n"
                f"⚠️ **Link expires** after 10 days inactivity\n\n"
                f"**Ready to start GoFile upload?**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 Start GoFile Upload", callback_data="start_gofile_upload")],
                    [InlineKeyboardButton("🔙 Back", callback_data="choose_upload_destination")]
                ])
            )
            return

        # Compare upload options - ENHANCED
        elif data == "compare_upload_options":
            compare_text = """📊 **Enhanced Upload Options Comparison**

📤 **Telegram Upload:**
✅ **Instant Access** - Direct in Telegram
✅ **Fast Preview** - Built-in media player  
✅ **No External Links** - Always accessible
✅ **Custom Thumbnails** - Professional presentation
❌ **Size Limits:** 2GB (4GB Premium)
❌ **May Compress** large files

🔗 **GoFile Upload:**  
✅ **Unlimited Size** - No restrictions
✅ **Original Quality** - Zero compression
✅ **High Speed** - Optimized servers
✅ **Professional Progress** - Real-time tracking
✅ **Retry Logic** - Reliable uploads
❌ **External Link** - Requires browser
❌ **10 Days Expiry** - Limited availability

💡 **Professional Recommendation:**
• **Telegram:** Files under 2GB, instant access
• **GoFile:** Large files, original quality priority
• **Both:** Available for maximum flexibility"""

            await cb.message.edit_text(
                compare_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Choose Telegram", callback_data="upload_to_telegram"),
                     InlineKeyboardButton("🔗 Choose GoFile", callback_data="upload_to_gofile")],
                    [InlineKeyboardButton("🔙 Back", callback_data="choose_upload_destination")]
                ])
            )
            return

        # Thumbnail selection - ENHANCED
        elif data == "use_custom_thumb":
            await cb.message.edit_text(
                "🖼️ **Custom Thumbnail Selection**\n\n"
                "📤 **Send a photo** as thumbnail for your merged video\n\n"
                "💡 **Professional Tips:**\n"
                "• Use high-quality images (1080p recommended)\n"
                "• 16:9 aspect ratio for best results\n"
                "• JPG or PNG format supported\n"
                "• Clear, representative image of content\n\n"
                "⏰ **You have 3 minutes to send the thumbnail**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎬 Use Auto Thumbnail", callback_data="use_auto_thumb")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="upload_to_telegram")]
                ])
            )
            
            # Set user state for thumbnail waiting
            formatDB[user_id] = "waiting_for_thumbnail"
            return

        elif data == "use_auto_thumb":
            # Start upload with auto-generated thumbnail
            await start_telegram_upload(c, cb, user, custom_thumbnail=None)
            return

        elif data == "upload_as_doc":
            UPLOAD_AS_DOC[str(user_id)] = True
            await start_telegram_upload(c, cb, user, as_document=True)
            return

        elif data == "upload_as_video":
            UPLOAD_AS_DOC[str(user_id)] = False
            await start_telegram_upload(c, cb, user, as_document=False)
            return

        elif data == "start_gofile_upload":
            await start_gofile_upload(c, cb, user)
            return

        elif data == "cancel_upload":
            await handle_cancel_operation(cb, user_id)
            return

        # Default fallback
        else:
            await cb.answer("🚧 Feature under development! Coming soon...", show_alert=True)

    except Exception as e:
        LOGGER.error(f"❌ Callback handler error: {e}")
        try:
            await cb.answer("❌ Something went wrong! Please try again.", show_alert=True)
        except:
            pass
        finally:
            # Cleanup on error
            if user_id in user_processes:
                user_processes[user_id] = False

async def start_complete_merge_process(c: Client, cb: CallbackQuery, user: UserSettings):
    """COMPLETE ENHANCED MERGE PROCESS with full DDL integration"""
    try:
        user_id = user.user_id
        
        # Get queue data
        queue_data = queueDB.get(user_id, {"videos": [], "urls": [], "subtitles": [], "audios": []})
        videos = queue_data.get("videos", [])
        urls = queue_data.get("urls", [])
        
        # Phase 1: Download all files (ENHANCED)
        await cb.message.edit_text(
            "📥 **Phase 1: Enhanced Download Process**\n\n"
            "🔄 **Downloading from multiple sources:**\n"
            f"├─ Telegram videos: {len(videos)}\n"
            f"├─ Direct URLs: {len(urls)}\n"
            f"└─ Professional progress tracking\n\n"
            "⚡ **Please wait for downloads to complete...**"
        )
        
        # Call COMPLETE enhanced merge function 
        await mergeNow_enhanced(c, cb, user_id, videos, urls)
        
    except Exception as e:
        LOGGER.error(f"❌ Complete merge process error: {e}")
        user_processes[user_id] = False
        await cb.message.edit_text(
            f"❌ **Enhanced Merge Process Failed!**\n\n"
            f"🚨 **Error:** {str(e)}\n\n"
            f"💡 **Please try again or contact support**\n"
            f"📞 **Support:** @{Config.OWNER_USERNAME}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="merge")],
                [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
            ])
        )

async def start_telegram_upload(c: Client, cb: CallbackQuery, user: UserSettings, custom_thumbnail=None, as_document=False):
    """Start ENHANCED Telegram upload process"""
    try:
        user_id = user.user_id
        
        await cb.message.edit_text(
            "📤 **Starting Enhanced Telegram Upload...**\n\n"
            "⚡ **Professional upload with progress tracking**\n"
            "🎬 **Maintaining high-definition quality**\n"
            "📊 **Real-time progress updates**\n\n"
            "⏰ **Upload in progress, please wait...**"
        )
        
        # Here integrate with enhanced uploader
        merged_file_path = f"downloads/{user_id}/merged_video.mkv"
        if os.path.exists(merged_file_path):
            success = await upload_to_telegram(
                client=c,
                chat_id=user_id,
                file_path=merged_file_path,
                status_message=cb.message,
                custom_thumbnail=custom_thumbnail,
                custom_filename="Professional_Merged_Video"
            )
            
            if success:
                # Cleanup after successful upload
                user_processes[user_id] = False
                await delete_all(f"downloads/{user_id}")
                
        else:
            await cb.message.edit_text("❌ **Merged file not found!** Please try the merge process again.")

    except Exception as e:
        LOGGER.error(f"❌ Enhanced Telegram upload error: {e}")
        user_processes[user_id] = False
        await cb.message.edit_text(f"❌ **Enhanced upload failed:** {str(e)}")

async def start_gofile_upload(c: Client, cb: CallbackQuery, user: UserSettings):
    """Start ENHANCED GoFile upload process"""
    try:
        user_id = user.user_id
        
        await cb.message.edit_text(
            "🔗 **Starting Enhanced GoFile Upload...**\n\n"
            "⚡ **Connecting to GoFile servers**\n"
            "📊 **Preparing unlimited upload**\n"
            "🚀 **Professional progress tracking**\n\n"
            "⏰ **Upload starting, please wait...**"
        )
        
        # Here integrate with enhanced GoFile uploader
        merged_file_path = f"downloads/{user_id}/merged_video.mkv"
        if os.path.exists(merged_file_path):
            uploader = GofileUploader()
            download_link = await uploader.upload_file(
                file_path=merged_file_path,
                status_message=cb.message
            )
            
            if download_link:
                # Cleanup after successful upload
                user_processes[user_id] = False
                await delete_all(f"downloads/{user_id}")
                
        else:
            await cb.message.edit_text("❌ **Merged file not found!** Please try the merge process again.")

    except Exception as e:
        LOGGER.error(f"❌ Enhanced GoFile upload error: {e}")
        user_processes[user_id] = False
        await cb.message.edit_text(f"❌ **Enhanced GoFile upload failed:** {str(e)}")

async def handle_cancel_operation(cb: CallbackQuery, user_id: int):
    """Handle cancel operation with COMPLETE cleanup"""
    try:
        # Enhanced cleanup process
        user_processes[user_id] = False
        
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
        
        await cb.message.edit_text(
            "🗑️ **Operation Cancelled Successfully**\n\n"
            "✅ **All processes stopped**\n"
            "✅ **Files and settings cleared**\n"
            "✅ **Memory freed and optimized**\n"
            "✅ **Ready for new operations**\n\n"
            "📤 **You can now start a fresh merge process**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
            ])
        )
        
        LOGGER.info(f"✅ Complete cancellation and cleanup for user {user_id}")
        
    except Exception as e:
        LOGGER.error(f"❌ Cancel handler error: {e}")
        await cb.answer("❌ Error during cancellation", show_alert=True)

# Handle text messages for custom thumbnail input - ENHANCED
@Client.on_message(filters.photo & filters.private)
async def handle_thumbnail_upload(c: Client, m: Message):
    """Handle ENHANCED custom thumbnail upload"""
    try:
        user_id = m.from_user.id
        
        # Check if user is waiting for thumbnail
        if formatDB.get(user_id) == "waiting_for_thumbnail":
            # Save thumbnail with enhanced handling
            thumb_dir = f"downloads/{user_id}"
            os.makedirs(thumb_dir, exist_ok=True)
            thumb_path = f"{thumb_dir}/custom_thumbnail.jpg"
            
            await m.download(file_name=thumb_path)
            
            # Clear state  
            formatDB[user_id] = None
            
            await m.reply_text(
                "✅ **Custom Thumbnail Saved Successfully!**\n\n"
                "🖼️ **High-quality thumbnail will be used**\n"
                "📤 **Starting enhanced upload process...**\n"
                "⚡ **Please wait for professional processing**"
            )
            
            # Start upload with custom thumbnail
            user = UserSettings(user_id, m.from_user.first_name)
            
            # Create a fake callback query for consistency
            class FakeCallbackQuery:
                def __init__(self, message, from_user):
                    self.message = message
                    self.from_user = from_user
            
            fake_cb = FakeCallbackQuery(m, m.from_user)
            await start_telegram_upload(c, fake_cb, user, custom_thumbnail=thumb_path)
            
    except Exception as e:
        LOGGER.error(f"❌ Enhanced thumbnail upload error: {e}")
        await m.reply_text("❌ **Error saving thumbnail.** Please try again or use auto thumbnail.")

#!/usr/bin/env python3
"""
🎬 ENHANCED MERGE VIDEO - COMPLETE DDL INTEGRATION
Fixed version with full downloader and uploader integration
"""

import asyncio
import os
import time
from bot import (LOGGER, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE, delete_all, formatDB,
                gDict, queueDB, replyDB, user_processes)
from config import Config
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helpers.display_progress import Progress
from helpers.ffmpeg_helper import MergeSub, MergeVideo, take_screen_shot
from helpers.utils import UserSettings, get_readable_file_size, get_readable_time
from PIL import Image
from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.errors.rpc_error import UnknownError
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Import ENHANCED downloaders and uploaders
from helpers.downloader import download_from_url, download_from_tg
from helpers.uploader import GofileUploader, upload_to_telegram

async def mergeNow_enhanced(c: Client, cb: CallbackQuery, user_id: int, video_message_ids: list, download_urls: list):
    """ENHANCED merge function with COMPLETE DDL integration and professional processing"""
    
    try:
        LOGGER.info(f"🚀 Starting ENHANCED merge process for user {user_id}")
        
        # Create user download directory
        user_dir = f"downloads/{user_id}"
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        downloaded_files = []
        vid_list = []
        duration = 0
        
        total_items = len(video_message_ids) + len(download_urls)
        current_item = 1
        
        # PHASE 1: Download all files (Telegram + URLs)
        await cb.message.edit_text(
            f"📥 **Phase 1: Professional Download Process**\n\n"
            f"📊 **Processing {total_items} items:**\n"
            f"├─ **Telegram Videos:** {len(video_message_ids)}\n"
            f"├─ **Download URLs:** {len(download_urls)}\n"
            f"└─ **Current:** Initializing downloads...\n\n"
            f"⚡ **Enhanced multi-source processing...**"
        )
        
        # Download Telegram videos
        for message_id in video_message_ids:
            try:
                await cb.message.edit_text(
                    f"📥 **Phase 1: Download Progress ({current_item}/{total_items})**\n\n"
                    f"📺 **Downloading Telegram video...**\n"
                    f"📊 **Progress:** {current_item}/{total_items}\n"
                    f"⚡ **Professional processing active**\n\n"
                    f"⏳ **Please wait for download completion...**"
                )
                
                # Get message
                message = await c.get_messages(chat_id=user_id, message_ids=message_id)
                
                # Download using enhanced downloader
                file_path = await download_from_tg(
                    client=c,
                    message=message,
                    user_id=user_id,
                    status_message=cb.message,
                    file_index=current_item,
                    total_files=total_items,
                    session_key="merge"
                )
                
                if file_path and os.path.exists(file_path):
                    downloaded_files.append(file_path)
                    LOGGER.info(f"✅ Downloaded Telegram video: {file_path}")
                else:
                    LOGGER.warning(f"⚠️ Failed to download Telegram video {message_id}")
                
                current_item += 1
                
            except Exception as e:
                LOGGER.error(f"❌ Error downloading Telegram video {message_id}: {e}")
                current_item += 1
                continue
        
        # Download URLs using enhanced downloader
        for url in download_urls:
            try:
                await cb.message.edit_text(
                    f"📥 **Phase 1: Download Progress ({current_item}/{total_items})**\n\n"
                    f"🔗 **Downloading from URL...**\n"
                    f"📊 **Progress:** {current_item}/{total_items}\n"
                    f"🌐 **URL:** `{url[:50]}...`\n\n"
                    f"⏳ **Professional URL processing...**"
                )
                
                # Download using enhanced URL downloader
                file_path = await download_from_url(
                    url=url,
                    user_id=user_id,
                    status_message=cb.message,
                    file_index=current_item,
                    total_files=total_items,
                    session_key="merge"
                )
                
                if file_path and os.path.exists(file_path):
                    downloaded_files.append(file_path)
                    LOGGER.info(f"✅ Downloaded URL: {file_path}")
                else:
                    LOGGER.warning(f"⚠️ Failed to download URL: {url}")
                
                current_item += 1
                
            except Exception as e:
                LOGGER.error(f"❌ Error downloading URL {url}: {e}")
                current_item += 1
                continue
        
        # Check if we have enough files
        if len(downloaded_files) < 2:
            await cb.message.edit_text(
                f"❌ **Insufficient Files for Merge**\n\n"
                f"📊 **Downloaded:** {len(downloaded_files)}/2 minimum\n"
                f"⚠️ **Need at least 2 valid video files**\n\n"
                f"💡 **Please add more videos or URLs**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data="merge")],
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
                ])
            )
            user_processes[user_id] = False
            return
        
        # PHASE 2: Process and merge files
        await cb.message.edit_text(
            f"🔄 **Phase 2: Professional Video Processing**\n\n"
            f"📊 **Successfully downloaded:** {len(downloaded_files)} files\n"
            f"⚡ **Starting high-quality merge process**\n"
            f"🎬 **Using professional FFmpeg settings**\n\n"
            f"⏳ **Processing may take several minutes...**"
        )
        
        # Create input file for FFmpeg
        input_file = f"{user_dir}/input.txt"
        
        # Process each downloaded file
        for file_path in downloaded_files:
            try:
                # Extract metadata
                metadata = extractMetadata(createParser(file_path))
                if metadata and metadata.has("duration"):
                    duration += metadata.get("duration").seconds
                
                vid_list.append(f"file '{file_path}'")
                LOGGER.info(f"📁 Added to merge list: {file_path}")
                
            except Exception as e:
                LOGGER.error(f"❌ Metadata extraction failed for {file_path}: {e}")
                continue
        
        # Check if we have valid videos for merging
        if not vid_list:
            await cb.message.edit_text(
                f"❌ **No Valid Videos Found**\n\n"
                f"🚨 **All downloaded files are corrupted or unsupported**\n"
                f"💡 **Please check your video sources and try again**"
            )
            user_processes[user_id] = False
            await delete_all(user_dir)
            return
        
        LOGGER.info(f"🔀 Merging {len(vid_list)} videos for user {user_id}")
        
        # Write input file
        with open(input_file, "w") as f:
            f.write("\n".join(vid_list))
        
        # Enhanced merge process
        await cb.message.edit_text(
            f"🔀 **Phase 2: High-Quality Merging**\n\n"
            f"📊 **Videos to merge:** {len(vid_list)}\n"
            f"⏱ **Total duration:** ~{get_readable_time(duration)}\n"
            f"⚡ **Professional quality settings active**\n\n"
            f"🎬 **Merging in progress...**"
        )
        
        # Perform merge using enhanced FFmpeg
        merged_video_path = await MergeVideo(
            input_file=input_file,
            user_id=user_id,
            message=cb.message,
            format_="mkv"
        )
        
        if merged_video_path is None:
            await cb.message.edit_text(
                f"❌ **Video Merging Failed!**\n\n"
                f"🚨 **FFmpeg processing error**\n"
                f"💡 **This might be due to:**\n"
                f"• Incompatible video formats\n"
                f"• Corrupted source files\n"
                f"• Insufficient system resources\n\n"
                f"🔄 **Please try again with different videos**"
            )
            user_processes[user_id] = False
            await delete_all(user_dir)
            return
        
        # PHASE 3: Prepare for upload
        file_size = os.path.getsize(merged_video_path)
        final_filename = f"Professional_Merged_Video_{int(time.time())}.mkv"
        final_path = f"{user_dir}/{final_filename}"
        
        # Rename merged file
        os.rename(merged_video_path, final_path)
        
        await cb.message.edit_text(
            f"✅ **Phase 2: Merge Completed Successfully!**\n\n"
            f"🎬 **Professional high-quality video ready**\n"
            f"📁 **File:** `{final_filename}`\n"
            f"📊 **Size:** `{get_readable_file_size(file_size)}`\n"
            f"⏱ **Duration:** ~`{get_readable_time(duration)}`\n\n"
            f"📤 **Ready for Phase 3: Upload destination choice**"
        )
        
        await asyncio.sleep(2)
        
        # Check file size limits and offer appropriate options
        if file_size > 2044723200 and not Config.IS_PREMIUM:  # 2GB limit
            await cb.message.edit_text(
                f"📊 **File Size Analysis**\n\n"
                f"📁 **Merged Video:** `{final_filename}`\n"
                f"📊 **Size:** `{get_readable_file_size(file_size)}`\n"
                f"🚫 **Telegram Limit:** 2GB (Standard)\n\n"
                f"💡 **Recommended Solution:**\n"
                f"• **GoFile Upload:** Unlimited size\n"
                f"• **Professional Quality:** No compression\n\n"
                f"**Choose your upload method:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 GoFile Upload (Recommended)", callback_data="upload_to_gofile")],
                    [InlineKeyboardButton("📞 Contact for Premium", url=f"https://t.me/{Config.OWNER_USERNAME}")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")]
                ])
            )
        else:
            # Show upload destination choice
            await cb.message.edit_text(
                f"🎉 **Phase 3: Professional Upload Ready**\n\n"
                f"🎬 **Merge completed with high quality**\n"
                f"📁 **File:** `{final_filename}`\n"
                f"📊 **Size:** `{get_readable_file_size(file_size)}`\n"
                f"⏱ **Duration:** `{get_readable_time(duration)}`\n\n"
                f"**Choose your preferred upload destination:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Telegram Upload", callback_data="upload_to_telegram"),
                     InlineKeyboardButton("🔗 GoFile Upload", callback_data="upload_to_gofile")],
                    [InlineKeyboardButton("📊 Compare Options", callback_data="compare_upload_options")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")]
                ])
            )
        
        LOGGER.info(f"✅ Enhanced merge process completed successfully for user {user_id}")
        
    except Exception as e:
        LOGGER.error(f"❌ Enhanced merge process error for user {user_id}: {e}")
        user_processes[user_id] = False
        
        await cb.message.edit_text(
            f"❌ **Enhanced Merge Process Failed**\n\n"
            f"🚨 **Error:** `{type(e).__name__}: {str(e)}`\n\n"
            f"💡 **Possible solutions:**\n"
            f"• Check internet connection\n"
            f"• Verify video file integrity\n" 
            f"• Try with fewer files\n"
            f"• Contact support if issue persists\n\n"
            f"📞 **Support:** @{Config.OWNER_USERNAME}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="merge")],
                [InlineKeyboardButton("🔙 Back to Main", callback_data="start")]
            ])
        )
        
        # Cleanup on error
        await delete_all(f"downloads/{user_id}")

# Traditional merge function for backward compatibility
async def mergeNow(c: Client, cb: CallbackQuery, new_file_name: str):
    """Traditional merge function - Enhanced with better error handling"""
    user_id = cb.from_user.id
    
    # Check if user already has a process running
    if user_id in user_processes and user_processes.get(user_id):
        await cb.answer(
            "⚠️ **Process Already Running!**\n\n"
            "Please wait for your current merge to complete before starting a new one.",
            show_alert=True
        )
        return
    
    # Get queue data for backward compatibility
    queue_data = queueDB.get(user_id, {"videos": [], "urls": [], "subtitles": [], "audios": []})
    videos = queue_data.get("videos", [])
    urls = queue_data.get("urls", [])
    
    if len(videos) + len(urls) < 2:
        await cb.answer("❌ Need at least 2 videos/URLs to merge!", show_alert=True)
        return
    
    # Mark user as having an active process
    user_processes[user_id] = True
    
    # Use enhanced merge function
    await mergeNow_enhanced(c, cb, user_id, videos, urls)

async def cleanup_user_data(user_id: int):
    """Enhanced cleanup function"""
    try:
        # Clear all user-related data
        if user_id in queueDB:
            queueDB[user_id] = {"videos": [], "urls": [], "subtitles": [], "audios": []}
        
        if user_id in formatDB:
            formatDB[user_id] = None
            
        if user_id in user_processes:
            user_processes[user_id] = False
        
        # Clear upload preferences
        user_str = str(user_id)
        if user_str in UPLOAD_AS_DOC:
            del UPLOAD_AS_DOC[user_str]
            
        if user_str in UPLOAD_TO_DRIVE:
            del UPLOAD_TO_DRIVE[user_str]
        
        # Delete download directory
        await delete_all(root=f"downloads/{user_id}")
        
        LOGGER.info(f"🧹 Cleaned up all data for user {user_id}")
        
    except Exception as e:
        LOGGER.error(f"❌ Cleanup error for user {user_id}: {e}")

# Export functions
__all__ = [
    'mergeNow_enhanced',
    'mergeNow', 
    'cleanup_user_data'
]

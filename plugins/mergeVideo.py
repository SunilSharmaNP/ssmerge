import asyncio
import os
import time
from bot import (LOGGER, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE, delete_all, formatDB,
                 gDict, queueDB, replyDB)
from config import Config
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helpers.display_progress import Progress
from helpers.ffmpeg_helper import MergeSub, MergeVideo, take_screen_shot
from helpers.uploader import uploadVideo
from helpers.utils import UserSettings, get_readable_file_size, get_readable_time
from PIL import Image
from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.errors.rpc_error import UnknownError
from pyrogram.types import CallbackQuery

# Global process management to prevent conflicts
user_processes = {}

async def mergeNow(c: Client, cb: CallbackQuery, new_file_name: str):
    """Professional merge function with enhanced process management"""
    user_id = cb.from_user.id
    
    # Check if user already has a process running
    if user_id in user_processes and user_processes[user_id]:
        await cb.answer(
            "⚠️ **Process Already Running!**\n\n"
            "Please wait for your current merge to complete before starting a new one.",
            show_alert=True
        )
        return
    
    # Mark user as having an active process
    user_processes[user_id] = True
    
    try:
        LOGGER.info(f"🔄 Starting merge process for user {user_id}")
        
        omess = cb.message.reply_to_message
        vid_list = []
        sub_list = []
        sIndex = 0
        await cb.message.edit("⭕ **Initializing Professional Merge Process...**")
        duration = 0
        
        list_message_ids = queueDB.get(cb.from_user.id, {}).get("videos", [])
        list_message_ids.sort()
        list_subtitle_ids = queueDB.get(cb.from_user.id, {}).get("subtitles", [])
        
        LOGGER.info(f"📊 Premium Status: {Config.IS_PREMIUM}")
        LOGGER.info(f"📹 Videos: {list_message_ids}")
        LOGGER.info(f"📝 Subtitles: {list_subtitle_ids}")
        
        if not list_message_ids:
            await cb.answer("❌ **No videos found in queue!**", show_alert=True)
            await cb.message.delete(True)
            return
        
        # Create user download directory
        user_dir = f"downloads/{user_id}"
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        input_file = f"{user_dir}/input.txt"
        total_videos = len(list_message_ids)
        current_video = 1
        
        # Process each video
        for message_id in list_message_ids:
            try:
                # Get message
                message = await c.get_messages(chat_id=cb.from_user.id, message_ids=message_id)
                media = message.video or message.document
                
                if not media:
                    continue
                
                # Update progress
                await cb.message.edit(
                    f"📥 **Downloading Video {current_video}/{total_videos}**\n\n"
                    f"📁 **File:** `{media.file_name}`\n"
                    f"📊 **Size:** `{get_readable_file_size(media.file_size)}`\n"
                    f"⏳ **Please wait...**"
                )
                
                LOGGER.info(f"📥 Downloading: {media.file_name}")
                await asyncio.sleep(2)
                
                # Download video
                file_dl_path = None
                sub_dl_path = None
                
                try:
                    c_time = time.time()
                    prog = Progress(cb.from_user.id, c, cb.message)
                    
                    download_path = f"{user_dir}/{message.id}/vid.mkv"
                    os.makedirs(os.path.dirname(download_path), exist_ok=True)
                    
                    file_dl_path = await c.download_media(
                        message=media,
                        file_name=download_path,
                        progress=prog.progress_for_pyrogram,
                        progress_args=(
                            f"🚀 **Downloading:** `{media.file_name}`",
                            c_time,
                            f"\n**Progress: {current_video}/{total_videos}**"
                        ),
                    )
                    
                    # Check if process was cancelled
                    if gDict[cb.message.chat.id] and cb.message.id in gDict[cb.message.chat.id]:
                        return
                    
                    await cb.message.edit(
                        f"✅ **Downloaded Successfully!**\n\n"
                        f"📁 **File:** `{media.file_name}`\n"
                        f"📊 **Size:** `{get_readable_file_size(media.file_size)}`"
                    )
                    
                    LOGGER.info(f"✅ Downloaded: {media.file_name}")
                    await asyncio.sleep(2)
                    
                except UnknownError as e:
                    LOGGER.warning(f"⚠️ Unknown error during download: {e}")
                    continue
                except Exception as downloadErr:
                    LOGGER.error(f"❌ Download failed: {downloadErr}")
                    # Remove failed video from queue
                    try:
                        queueDB.get(cb.from_user.id)["videos"].remove(message_id)
                    except:
                        pass
                    await cb.message.edit("❗ **File skipped due to download error**")
                    await asyncio.sleep(3)
                    continue
                
                # Handle subtitles if available
                if sIndex < len(list_subtitle_ids) and list_subtitle_ids[sIndex] is not None:
                    try:
                        sub_message = await c.get_messages(
                            chat_id=cb.from_user.id, 
                            message_ids=list_subtitle_ids[sIndex]
                        )
                        
                        sub_dl_path = await c.download_media(
                            message=sub_message,
                            file_name=f"{user_dir}/{sub_message.id}/",
                        )
                        
                        LOGGER.info(f"📝 Got subtitle: {sub_message.document.file_name}")
                        
                        # Merge subtitle with video
                        file_dl_path = await MergeSub(file_dl_path, sub_dl_path, cb.from_user.id)
                        LOGGER.info("✅ Subtitle merged successfully")
                        
                    except Exception as e:
                        LOGGER.warning(f"⚠️ Subtitle processing failed: {e}")
                
                sIndex += 1
                
                # Extract metadata and add to video list
                try:
                    metadata = extractMetadata(createParser(file_dl_path))
                    if metadata and metadata.has("duration"):
                        duration += metadata.get("duration").seconds
                    vid_list.append(f"file '{file_dl_path}'")
                except Exception as e:
                    LOGGER.error(f"❌ Metadata extraction failed: {e}")
                    await cleanup_user_data(cb.from_user.id)
                    await cb.message.edit("⚠️ **Video file is corrupted or unsupported**")
                    return
                
                current_video += 1
                
            except Exception as e:
                LOGGER.error(f"❌ Error processing video {current_video}: {e}")
                current_video += 1
                continue
        
        # Remove duplicates from video list
        vid_list = list(dict.fromkeys(vid_list))
        
        if not vid_list:
            await cleanup_user_data(cb.from_user.id)
            await cb.message.edit("❌ **No valid videos found for merging**")
            return
        
        LOGGER.info(f"🔀 Merging {len(vid_list)} videos for user {cb.from_user.id}")
        await cb.message.edit(
            f"🔀 **Merging {len(vid_list)} Videos...**\n\n"
            f"⚡ **Using Professional Quality Settings**\n"
            f"⏳ **Please wait, this may take a while...**"
        )
        
        # Create input file for FFmpeg
        with open(input_file, "w") as f:
            f.write("\n".join(vid_list))
        
        # Merge videos
        merged_video_path = await MergeVideo(
            input_file=input_file, 
            user_id=cb.from_user.id, 
            message=cb.message, 
            format_="mkv"
        )
        
        if merged_video_path is None:
            await cb.message.edit("❌ **Video merging failed!**")
            await cleanup_user_data(cb.from_user.id)
            return
        
        try:
            await cb.message.edit("✅ **Videos Merged Successfully!**")
        except MessageNotModified:
            await cb.message.edit("Videos Merged Successfully! ✅")
        
        LOGGER.info(f"✅ Video merged successfully for: {cb.from_user.first_name}")
        await asyncio.sleep(3)
        
        # Rename merged file
        file_size = os.path.getsize(merged_video_path)
        os.rename(merged_video_path, new_file_name)
        
        await cb.message.edit(
            f"🔄 **File Renamed Successfully**\n\n"
            f"📁 **New Name:** `{os.path.basename(new_file_name)}`\n"
            f"📊 **Size:** `{get_readable_file_size(file_size)}`"
        )
        await asyncio.sleep(3)
        
        merged_video_path = new_file_name
        
        # Check file size limits
        if file_size > 2044723200 and not Config.IS_PREMIUM:  # 2GB limit
            await cb.message.edit(
                f"📁 **File Size Alert**\n\n"
                f"📊 **Current Size:** `{get_readable_file_size(file_size)}`\n"
                f"🚫 **Telegram Limit:** `2GB`\n\n"
                f"💡 **Solutions:**\n"
                f"• Use GoFile upload option (unlimited)\n"
                f"• Contact @{Config.OWNER_USERNAME} for premium access\n"
                f"• Try compressing the video"
            )
            
            # Offer GoFile upload option
            if Config.GOFILE_TOKEN:
                UPLOAD_TO_DRIVE[str(user_id)] = True
            else:
                await cleanup_user_data(cb.from_user.id)
                return
        
        if Config.IS_PREMIUM and file_size > 4241280205:  # 4GB limit
            await cb.message.edit(
                f"📁 **File Too Large Even for Premium**\n\n"
                f"📊 **Current Size:** `{get_readable_file_size(file_size)}`\n"
                f"🚫 **Premium Limit:** `4GB`\n\n"
                f"💡 **Solution:** Use GoFile upload (unlimited size)"
            )
            
            if Config.GOFILE_TOKEN:
                UPLOAD_TO_DRIVE[str(user_id)] = True
            else:
                await cleanup_user_data(cb.from_user.id)
                return
        
        # Extract video metadata for upload
        await cb.message.edit("🎥 **Extracting Video Information...**")
        duration = 1
        width = 1280
        height = 720
        
        try:
            metadata = extractMetadata(createParser(merged_video_path))
            if metadata:
                if metadata.has("duration"):
                    duration = metadata.get("duration").seconds
                if metadata.has("width"):
                    width = metadata.get("width")
                if metadata.has("height"):
                    height = metadata.get("height")
        except Exception as e:
            LOGGER.warning(f"⚠️ Metadata extraction warning: {e}")
        
        # Generate or download thumbnail
        video_thumbnail = None
        try:
            user = UserSettings(cb.from_user.id, cb.from_user.first_name)
            thumb_id = user.thumbnail
            
            if thumb_id:
                video_thumbnail = f"{user_dir}_thumb.jpg"
                await c.download_media(message=str(thumb_id), file_name=video_thumbnail)
                LOGGER.info("✅ Custom thumbnail downloaded")
            else:
                raise Exception("No custom thumbnail")
                
        except Exception:
            LOGGER.info("🖼️ Generating automatic thumbnail")
            video_thumbnail = await take_screen_shot(
                merged_video_path, user_dir, (duration / 2)
            )
        
        # Process thumbnail
        try:
            if video_thumbnail and os.path.exists(video_thumbnail):
                thumb = extractMetadata(createParser(video_thumbnail))
                if thumb:
                    thumb_height = thumb.get("height", height)
                    thumb_width = thumb.get("width", width)
                else:
                    thumb_height, thumb_width = height, width
                
                # Resize thumbnail
                img = Image.open(video_thumbnail)
                if thumb_width > thumb_height:
                    img = img.resize((320, int(320 * thumb_height / thumb_width)))
                elif thumb_height > thumb_width:
                    img = img.resize((int(320 * thumb_width / thumb_height), 320))
                else:
                    img = img.resize((320, 320))
                
                img.save(video_thumbnail)
                img = Image.open(video_thumbnail).convert("RGB")
                img.save(video_thumbnail, "JPEG")
                
        except Exception as e:
            LOGGER.warning(f"⚠️ Thumbnail processing failed: {e}")
            video_thumbnail = None
        
        # Upload the merged video
        upload_success = await uploadVideo(
            c=c,
            cb=cb,
            merged_video_path=merged_video_path,
            width=width,
            height=height,
            duration=duration,
            video_thumbnail=video_thumbnail,
            file_size=file_size,
            upload_mode=UPLOAD_AS_DOC.get(str(cb.from_user.id), False),
        )
        
        if upload_success:
            await cb.message.delete(True)
            LOGGER.info(f"✅ Upload completed successfully for user {user_id}")
        
        # Cleanup
        await cleanup_user_data(cb.from_user.id)
        
    except Exception as e:
        LOGGER.error(f"❌ Merge process failed for user {user_id}: {e}")
        await cb.message.edit(
            f"❌ **Merge Process Failed!**\n\n"
            f"🚨 **Error:** `{str(e)}`\n\n"
            f"💡 **Try Again or Contact:** @{Config.OWNER_USERNAME}"
        )
        await cleanup_user_data(cb.from_user.id)
    finally:
        # Always clear the user process flag
        if user_id in user_processes:
            user_processes[user_id] = False

async def cleanup_user_data(user_id):
    """Enhanced cleanup function with comprehensive data removal"""
    try:
        LOGGER.info(f"🧹 Cleaning up data for user {user_id}")
        
        # Remove download directory
        user_dir = f"downloads/{user_id}"
        if os.path.exists(user_dir):
            await delete_all(root=user_dir)
        
        # Clear database entries
        if user_id in queueDB:
            queueDB[user_id] = {"videos": [], "subtitles": [], "audios": []}
        
        if user_id in formatDB:
            formatDB[user_id] = None
            
        if user_id in replyDB:
            del replyDB[user_id]
        
        # Clear upload preferences
        user_str = str(user_id)
        if user_str in UPLOAD_AS_DOC:
            del UPLOAD_AS_DOC[user_str]
            
        if user_str in UPLOAD_TO_DRIVE:
            del UPLOAD_TO_DRIVE[user_str]
        
        # Clear process flag
        if user_id in user_processes:
            user_processes[user_id] = False
            
        LOGGER.info(f"✅ Cleanup completed for user {user_id}")
        
    except Exception as e:
        LOGGER.error(f"❌ Cleanup error for user {user_id}: {e}")

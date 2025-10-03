import asyncio
import os
import time
import aiohttp
from aiohttp import ClientSession, ClientTimeout, FormData
from random import choice
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

from config import Config
from __init__ import LOGGER
from helpers.utils import get_readable_file_size, get_readable_time

# GoFile Configuration
GOFILE_CHUNK_SIZE = 8192 * 1024  # 8MB chunks
GOFILE_UPLOAD_TIMEOUT = 3600  # 1 hour timeout
GOFILE_RETRY_ATTEMPTS = 3
GOFILE_RETRY_WAIT_MIN = 2
GOFILE_RETRY_WAIT_MAX = 10

def get_human_readable_size(size_bytes):
    """Convert bytes to human readable format"""
    return get_readable_file_size(size_bytes)

def get_speed(start_time, uploaded_bytes):
    """Calculate upload speed"""
    elapsed = time.time() - start_time
    if elapsed > 0:
        speed_bps = uploaded_bytes / elapsed
        return get_readable_file_size(speed_bps) + "/s"
    return "0 B/s"

def get_time_left(start_time, uploaded_bytes, total_size):
    """Calculate ETA"""
    if uploaded_bytes == 0:
        return "∞"
    elapsed = time.time() - start_time
    speed = uploaded_bytes / elapsed if elapsed > 0 else 0
    if speed > 0:
        remaining = (total_size - uploaded_bytes) / speed
        return get_readable_time(remaining)
    return "∞"

def get_progress_bar(percentage, length=20):
    """Generate progress bar"""
    filled = int(length * percentage)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"

async def smart_progress_editor(message, text):
    """Smart message editor with error handling"""
    try:
        await message.edit_text(text, disable_web_page_preview=True)
    except Exception as e:
        LOGGER.warning(f"Progress update failed: {e}")

class GofileUploader:
    """Professional GoFile uploader with advanced features"""
    
    def __init__(self, token=None):
        self.api_url = "https://api.gofile.io/"
        self.token = token or getattr(Config, 'GOFILE_TOKEN', None)
        if not self.token:
            LOGGER.warning("⚠️ GOFILE_TOKEN not found. Uploads will be anonymous.")
        self.chunk_size = GOFILE_CHUNK_SIZE
        self.session = None

    async def _get_session(self):
        """Get or create an aiohttp ClientSession"""
        if self.session is None or self.session.closed:
            self.session = ClientSession(
                timeout=ClientTimeout(total=GOFILE_UPLOAD_TIMEOUT),
                headers={
                    'User-Agent': 'ProfessionalMergeBot/6.0',
                    'Accept': 'application/json'
                }
            )
        return self.session
    
    async def close(self):
        """Close the aiohttp ClientSession"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    @retry(
        stop=stop_after_attempt(GOFILE_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=GOFILE_RETRY_WAIT_MIN, max=GOFILE_RETRY_WAIT_MAX),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def __get_server(self):
        """Get the best GoFile server for uploading"""
        LOGGER.info("🔍 Getting optimal GoFile server...")
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.api_url}getServer") as resp:
                resp.raise_for_status()
                result = await resp.json()
                
                if result.get("status") == "ok":
                    server = result["data"]["server"]
                    LOGGER.info(f"✅ Selected GoFile server: {server}")
                    return server
                else:
                    raise Exception(f"GoFile API error: {result.get('message', 'Unknown error')}")
        except Exception as e:
            LOGGER.error(f"❌ Failed to get GoFile server: {e}")
            # Fallback to default server
            return "store1"
    
    async def upload_file(self, file_path: str, status_message=None):
        """Upload file to GoFile with professional progress tracking"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"❌ File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # Check file size (GoFile has 5GB limit for free users)
        if file_size > (5 * 1024 * 1024 * 1024):
            LOGGER.warning(f"⚠️ Large file detected: {get_human_readable_size(file_size)}")

        try:
            # Update status
            if status_message:
                await smart_progress_editor(
                    status_message, 
                    "🔗 **Connecting to GoFile servers...**\n\n"
                    f"📁 **File:** `{filename}`\n"
                    f"📊 **Size:** `{get_human_readable_size(file_size)}`"
                )
            
            # Get upload server
            server = await self.__get_server()
            upload_url = f"https://{server}.gofile.io/uploadFile"
            
        except Exception as e:
            error_msg = f"Failed to connect to GoFile: {e}"
            LOGGER.error(f"❌ {error_msg}")
            if status_message:
                await status_message.edit_text(
                    f"❌ **GoFile Upload Failed!**\n\n"
                    f"🚨 **Error:** `{error_msg}`\n\n"
                    f"💡 **Tip:** GoFile servers might be busy. Try again later."
                )
            raise
        
        # Start upload process
        if status_message:
            await smart_progress_editor(
                status_message,
                f"🚀 **Starting GoFile Upload...**\n\n"
                f"📁 **File:** `{filename}`\n"
                f"📊 **Size:** `{get_human_readable_size(file_size)}`\n"
                f"🌐 **Server:** `{server}`"
            )
        
        start_time = time.time()
        
        try:
            session = await self._get_session()
            
            # Prepare form data
            form = FormData()
            if self.token:
                form.add_field("token", self.token)
            
            # Upload with progress tracking
            with open(file_path, 'rb') as f:
                form.add_field("file", f, filename=filename, content_type="application/octet-stream")
                
                # Progress tracking callback
                upload_progress_callback = None
                if status_message:
                    async def progress_callback():
                        while True:
                            try:
                                current_pos = f.tell()
                                progress_percent = current_pos / file_size
                                speed = get_speed(start_time, current_pos)
                                eta = get_time_left(start_time, current_pos, file_size)
                                
                                progress_text = f"""🔗 **Uploading to GoFile.io...**

📁 **File:** `{filename}`
📊 **Total Size:** `{get_human_readable_size(file_size)}`
{get_progress_bar(progress_percent)} `{progress_percent:.1%}`
📈 **Uploaded:** `{get_human_readable_size(current_pos)}`
🚀 **Speed:** `{speed}`
⏱️ **ETA:** `{eta}`
🌐 **Server:** `{server}`"""
                                
                                await smart_progress_editor(status_message, progress_text.strip())
                                await asyncio.sleep(2)  # Update every 2 seconds
                            except:
                                break
                    
                    # Start progress tracking
                    upload_progress_callback = asyncio.create_task(progress_callback())
                
                # Perform upload
                async with session.post(upload_url, data=form) as resp:
                    if upload_progress_callback:
                        upload_progress_callback.cancel()
                    
                    resp.raise_for_status()
                    resp_json = await resp.json()
            
            # Process response
            if resp_json.get("status") == "ok":
                download_page = resp_json["data"]["downloadPage"]
                file_code = resp_json["data"]["code"]
                
                if status_message:
                    elapsed_time = time.time() - start_time
                    await status_message.edit_text(
                        f"✅ **GoFile Upload Complete!**\n\n"
                        f"📁 **File:** `{filename}`\n"
                        f"📊 **Size:** `{get_human_readable_size(file_size)}`\n"
                        f"⏱️ **Time:** `{elapsed_time:.1f}s`\n"
                        f"🌐 **Server:** `{server}`\n"
                        f"🔗 **Download Link:** {download_page}\n"
                        f"🆔 **File Code:** `{file_code}`\n\n"
                        f"💡 **Note:** Link expires after 10 days of inactivity."
                    )
                
                LOGGER.info(f"✅ GoFile upload successful: {download_page}")
                return {
                    "download_page": download_page,
                    "file_code": file_code,
                    "server": server,
                    "size": file_size,
                    "filename": filename
                }
            else:
                error_msg = resp_json.get("message", "Unknown error")
                raise Exception(f"GoFile upload failed: {error_msg}")
        
        except Exception as e:
            error_msg = f"GoFile upload error: {e}"
            LOGGER.error(f"❌ {error_msg}")
            if status_message:
                await status_message.edit_text(
                    f"❌ **GoFile Upload Failed!**\n\n"
                    f"📁 **File:** `{filename}`\n"
                    f"🚨 **Error:** `{str(e)}`\n\n"
                    f"💡 **Tip:** Try again or contact support if issue persists."
                )
            raise
        finally:
            await self.close()

# Enhanced upload video function with GoFile integration
async def uploadVideo(c, cb, merged_video_path, width, height, duration, video_thumbnail, file_size, upload_mode):
    """Professional video upload with GoFile integration and better error handling"""
    try:
        LOGGER.info(f"📤 Starting upload process for: {merged_video_path}")
        
        user_id = cb.from_user.id
        from __init__ import UPLOAD_TO_DRIVE, UPLOAD_AS_DOC
        
        # Check if GoFile upload is requested
        if UPLOAD_TO_DRIVE.get(str(user_id), False):
            try:
                await cb.message.edit("🔗 **Preparing GoFile Upload...**")
                
                gofile = GofileUploader()
                upload_result = await gofile.upload_file(merged_video_path, cb.message)
                
                # Send result to user
                caption = f"""🎉 **Video Successfully Uploaded to GoFile!**

📁 **File:** `{upload_result['filename']}`
📊 **Size:** `{get_readable_file_size(upload_result['size'])}`
🌐 **Server:** `{upload_result['server']}`
🔗 **Download:** {upload_result['download_page']}
🆔 **Code:** `{upload_result['file_code']}`

💡 **Note:** Link expires after 10 days of inactivity.
🚀 **Uploaded with Professional Merge Bot**"""

                await cb.message.edit(caption)
                
                # Send to log channel if configured
                if Config.LOGCHANNEL:
                    try:
                        # Validate log channel ID format
                        log_channel_id = str(Config.LOGCHANNEL)
                        if not log_channel_id.startswith('-100') and not log_channel_id.startswith('-'):
                            log_channel_id = f"-100{log_channel_id}"
                        
                        await c.send_message(
                            chat_id=int(log_channel_id),
                            text=f"📤 **GoFile Upload Complete**\n\n"
                                 f"👤 **User:** {cb.from_user.first_name} (`{user_id}`)\n"
                                 f"📁 **File:** `{upload_result['filename']}`\n"
                                 f"📊 **Size:** `{get_readable_file_size(upload_result['size'])}`\n"
                                 f"🔗 **Link:** {upload_result['download_page']}\n"
                                 f"⏰ **Time:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`"
                        )
                    except Exception as e:
                        LOGGER.warning(f"⚠️ Failed to send to log channel: {e}")
                
                return True
                
            except Exception as e:
                LOGGER.error(f"❌ GoFile upload failed: {e}")
                await cb.message.edit(
                    f"❌ **GoFile Upload Failed!**\n\n"
                    f"🚨 **Error:** `{str(e)}`\n\n"
                    f"🔄 **Falling back to Telegram upload...**"
                )
                # Continue to Telegram upload
                await asyncio.sleep(3)
        
        # Regular Telegram upload
        caption = f"""📹 **Professional Merge Complete**

📁 **File:** `{os.path.basename(merged_video_path)}`
📊 **Size:** `{get_readable_file_size(file_size)}`
⏱️ **Duration:** `{get_readable_time(duration)}`
🎥 **Resolution:** `{width}x{height}`

🤖 **Merged with Professional Bot**
👨‍💻 **By:** @{Config.OWNER_USERNAME}
⚡ **Quality:** High Definition"""
        
        if upload_mode:  # Upload as document
            await cb.message.edit("📤 **Uploading as Document...**")
            from helpers.display_progress import Progress
            prog = Progress(cb.from_user.id, c, cb.message)
            c_time = time.time()
            
            sent_message = await c.send_document(
                chat_id=cb.from_user.id,
                document=merged_video_path,
                thumb=video_thumbnail,
                caption=caption,
                progress=prog.progress_for_pyrogram,
                progress_args=(f"📤 **Uploading Document...**", c_time)
            )
        else:  # Upload as video
            await cb.message.edit("📤 **Uploading as Video...**")
            from helpers.display_progress import Progress
            prog = Progress(cb.from_user.id, c, cb.message)
            c_time = time.time()
            
            sent_message = await c.send_video(
                chat_id=cb.from_user.id,
                video=merged_video_path,
                duration=duration,
                width=width,
                height=height,
                thumb=video_thumbnail,
                caption=caption,
                supports_streaming=True,
                progress=prog.progress_for_pyrogram,
                progress_args=(f"📤 **Uploading Video...**", c_time)
            )
        
        # Send to log channel with better error handling
        if Config.LOGCHANNEL and sent_message:
            try:
                # Validate and format log channel ID
                log_channel_id = str(Config.LOGCHANNEL)
                if not log_channel_id.startswith('-100') and not log_channel_id.startswith('-'):
                    log_channel_id = f"-100{log_channel_id}"
                
                log_caption = f"""📤 **Video Merged & Uploaded**

👤 **User:** {cb.from_user.first_name} (`{cb.from_user.id}`)
📁 **File:** `{os.path.basename(merged_video_path)}`
📊 **Size:** `{get_readable_file_size(file_size)}`
⏱️ **Duration:** `{get_readable_time(duration)}`
🎥 **Resolution:** `{width}x{height}`
📱 **Upload Mode:** {"Document" if upload_mode else "Video"}
⚡ **Status:** Professional Quality"""

                await sent_message.copy(
                    chat_id=int(log_channel_id),
                    caption=log_caption
                )
                LOGGER.info(f"✅ Sent to log channel: {log_channel_id}")
                
            except ValueError as e:
                LOGGER.error(f"❌ Invalid log channel ID format: {Config.LOGCHANNEL} - {e}")
            except Exception as e:
                LOGGER.error(f"❌ Failed to send to log channel: {e}")
        
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Upload failed: {e}")
        try:
            await cb.message.edit(
                f"❌ **Upload Failed!**\n\n"
                f"🚨 **Error:** `{str(e)}`\n\n"
                f"💡 **Tip:** Try again or contact support @{Config.OWNER_USERNAME}"
            )
        except:
            pass
        return False

# Enhanced file uploader for extracted files
async def uploadFiles(c, cb, up_path, n, all):
    """Upload extracted files with professional handling"""
    try:
        from helpers.display_progress import Progress
        prog = Progress(cb.from_user.id, c, cb.message)
        c_time = time.time()
        
        file_size = os.path.getsize(up_path)
        filename = os.path.basename(up_path)
        
        caption = f"""📦 **Extracted File**

📁 **File:** `{filename}`
📊 **Size:** `{get_readable_file_size(file_size)}`
🔢 **Progress:** `{n}/{all}`

🤖 **Extracted with Professional Bot**
👨‍💻 **By:** @{Config.OWNER_USERNAME}"""

        sent_message = await c.send_document(
            chat_id=cb.message.chat.id,
            document=up_path,
            caption=caption,
            progress=prog.progress_for_pyrogram,
            progress_args=(
                f"📤 **Uploading:** `{filename}`",
                c_time,
                f"\n**Progress: {n}/{all}**"
            ),
        )

        # Send to log channel
        if Config.LOGCHANNEL and sent_message:
            try:
                log_channel_id = str(Config.LOGCHANNEL)
                if not log_channel_id.startswith('-100') and not log_channel_id.startswith('-'):
                    log_channel_id = f"-100{log_channel_id}"
                
                log_caption = f"""📦 **File Extracted & Uploaded**

👤 **User:** {cb.from_user.first_name} (`{cb.from_user.id}`)
📁 **File:** `{filename}`
📊 **Size:** `{get_readable_file_size(file_size)}`
🔢 **Batch:** `{n}/{all}`
⏰ **Time:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`"""

                await sent_message.copy(
                    chat_id=int(log_channel_id),
                    caption=log_caption
                )
            except Exception as e:
                LOGGER.warning(f"⚠️ Failed to send to log channel: {e}")
                
    except Exception as e:
        LOGGER.error(f"❌ File upload failed: {e}")
        await cb.message.edit(f"❌ **Upload failed for:** `{os.path.basename(up_path)}`")

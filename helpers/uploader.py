#!/usr/bin/env python3
"""
Enhanced Professional GoFile Uploader
Integrated with FileStream-style Merge Bot
Based on provided uploader-8.py with improvements
"""

import os
import time
import asyncio
from aiohttp import ClientSession, FormData, ClientTimeout
from random import choice
from config import Config
from helpers.utils import get_readable_file_size, get_readable_time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

# Global variables for progress throttling
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 3.0

# GoFile Configuration
GOFILE_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB chunks
GOFILE_UPLOAD_TIMEOUT = 3600  # 1 hour timeout
GOFILE_RETRY_ATTEMPTS = 5
GOFILE_RETRY_WAIT_MIN = 1
GOFILE_RETRY_WAIT_MAX = 60

async def smart_progress_editor(status_message, text: str):
    """Smart progress editor with throttling to avoid flood limits."""
    if not status_message or not hasattr(status_message, 'chat'):
        return

    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()
    last_time = last_edit_time.get(message_key, 0)

    if (now - last_time) > EDIT_THROTTLE_SECONDS:
        try:
            await status_message.edit_text(text)
            last_edit_time[message_key] = now
        except Exception as e:
            # Silently handle rate limits and other common Telegram API errors
            pass

def get_time_left(start_time: float, current: int, total: int) -> str:
    """Calculate estimated time remaining."""
    if current <= 0 or (time.time() - start_time) <= 0:
        return "Calculating..."

    elapsed = time.time() - start_time
    if elapsed < 0.1:
        return "Calculating..."

    rate = current / elapsed
    if rate == 0:
        return "Calculating..."

    remaining_bytes = total - current
    if remaining_bytes <= 0:
        return "0s"

    remaining = remaining_bytes / rate
    if remaining < 60:
        return f"{int(remaining)}s"
    elif remaining < 3600:
        return f"{int(remaining // 60)}m {int(remaining % 60)}s"
    else:
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return f"{hours}h {minutes}m"

def get_speed(start_time: float, current: int) -> str:
    """Calculate upload/download speed."""
    elapsed = time.time() - start_time
    if elapsed <= 0:
        return "0 B/s"

    speed = current / elapsed
    if speed < 1024:
        return f"{speed:.1f} B/s"
    elif speed < 1024 * 1024:
        return f"{speed / 1024:.1f} KB/s"
    else:
        return f"{speed / (1024 * 1024):.1f} MB/s"

def get_progress_bar(progress: float, length: int = 20) -> str:
    """Get a styled progress bar."""
    filled_len = int(length * progress)
    return "█" * filled_len + "░" * (length - filled_len)

async def create_default_thumbnail(video_path: str) -> str | None:
    """Create a default thumbnail from video."""
    thumbnail_path = f"{os.path.splitext(video_path)[0]}.jpg"
    try:
        # Generate thumbnail from middle of video using FFmpeg
        command = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-i', video_path,
            '-ss', '10',  # 10 seconds from start
            '-vframes', '1',
            '-c:v', 'mjpeg', '-f', 'image2',
            '-y', thumbnail_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await process.communicate()
        if process.returncode != 0:
            print(f"Error creating default thumbnail: {stderr.decode().strip()}")
            return None

        return thumbnail_path if os.path.exists(thumbnail_path) else None

    except Exception as e:
        print(f"Exception creating thumbnail: {e}")
        return None

class GofileUploader:
    """Enhanced GoFile uploader with real-time progress tracking."""
    
    def __init__(self, token=None):
        self.api_url = "https://api.gofile.io/"
        self.token = token or getattr(Config, 'GOFILE_TOKEN', None)
        if not self.token:
            print("Warning: GOFILE_TOKEN not found in config. GoFile uploads might be anonymous.")
        self.chunk_size = GOFILE_CHUNK_SIZE
        self.session = None

    async def _get_session(self):
        """Get or create an aiohttp ClientSession."""
        if self.session is None or self.session.closed:
            self.session = ClientSession(
                timeout=ClientTimeout(total=GOFILE_UPLOAD_TIMEOUT)
            )
        return self.session

    async def close(self):
        """Close the aiohttp ClientSession."""
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
        """Get the best GoFile server for uploading with retries."""
        print("🔍 Getting GoFile server...")
        session = await self._get_session()
        async with session.get(f"{self.api_url}servers") as resp:
            resp.raise_for_status()
            result = await resp.json()
            if result.get("status") == "ok":
                servers = result["data"]["servers"]
                selected_server = choice(servers)["name"]
                print(f"✅ Selected GoFile server: {selected_server}")
                return selected_server
            else:
                raise Exception(f"GoFile API error: {result.get('message', 'Unknown error')}")

    async def upload_file(self, file_path: str, status_message=None):
        """Upload file to GoFile with enhanced progress tracking."""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)

        if file_size > (10 * 1024 * 1024 * 1024):  # 10GB limit
            raise ValueError(f"File size {get_readable_file_size(file_size)} exceeds GoFile limit (10GB).")

        # Get upload server
        try:
            if status_message:
                await smart_progress_editor(status_message, "🔗 **Connecting to GoFile servers...**")
            
            server = await self.__get_server()
            upload_url = f"https://{server}.gofile.io/uploadFile"

        except RetryError as e:
            error_msg = f"Failed to get GoFile server: {e.last_attempt.exception()}"
            print(error_msg)
            if status_message:
                await status_message.edit_text(
                    f"❌ **GoFile Upload Failed!**\n\n"
                    f"🚨 **Error:** `{error_msg}`\n\n"
                    f"💡 **Tip:** GoFile servers might be busy. Try again later."
                )
            raise Exception(error_msg) from e

        if status_message:
            await smart_progress_editor(
                status_message,
                f"🚀 **Starting GoFile Upload...**\n\n"
                f"📁 **File:** `{filename}`\n"
                f"📊 **Size:** `{get_readable_file_size(file_size)}`"
            )

        start_time = time.time()
        uploaded_bytes = 0

        try:
            session = await self._get_session()

            @retry(
                stop=stop_after_attempt(GOFILE_RETRY_ATTEMPTS),
                wait=wait_exponential(multiplier=1, min=GOFILE_RETRY_WAIT_MIN, max=GOFILE_RETRY_WAIT_MAX),
                retry=retry_if_exception_type(Exception),
                reraise=True
            )
            async def _perform_upload():
                nonlocal uploaded_bytes
                uploaded_bytes = 0

                # Create FormData
                form = FormData()
                if self.token:
                    form.add_field("token", self.token)

                # File sender with progress tracking
                async def file_sender():
                    nonlocal uploaded_bytes
                    with open(file_path, 'rb') as f_stream:
                        while True:
                            chunk_data = f_stream.read(self.chunk_size)
                            if not chunk_data:
                                break

                            uploaded_bytes += len(chunk_data)

                            # Update progress
                            if status_message:
                                progress_percent = uploaded_bytes / file_size
                                speed = get_speed(start_time, uploaded_bytes)
                                eta = get_time_left(start_time, uploaded_bytes, file_size)

                                progress_text = f"""🔗 **Uploading to GoFile.io...**

📁 **File:** `{filename}`
📊 **Total Size:** `{get_readable_file_size(file_size)}`

{get_progress_bar(progress_percent)} `{progress_percent:.1%}`

📈 **Uploaded:** `{get_readable_file_size(uploaded_bytes)}`
🚀 **Speed:** `{speed}`
⏱ **ETA:** `{eta}`"""

                                await smart_progress_editor(status_message, progress_text.strip())

                            yield chunk_data
                            await asyncio.sleep(0.001)

                # Add file field
                form.add_field("file", file_sender(), filename=filename, content_type="application/octet-stream")

                async with session.post(upload_url, data=form) as resp:
                    resp.raise_for_status()
                    return await resp.json()

            resp_json = await _perform_upload()

            if resp_json.get("status") == "ok":
                download_page = resp_json["data"]["downloadPage"]
                
                if status_message:
                    elapsed_time = time.time() - start_time
                    await status_message.edit_text(
                        f"✅ **GoFile Upload Complete!**\n\n"
                        f"📁 **File:** `{filename}`\n"
                        f"📊 **Size:** `{get_readable_file_size(file_size)}`\n"
                        f"⏱ **Time:** `{elapsed_time:.1f}s`\n"
                        f"🔗 **Link:** {download_page}\n\n"
                        f"💡 **Note:** Links expire after 10 days of inactivity."
                    )

                return download_page
            else:
                error_msg = resp_json.get("message", "Unknown error")
                raise Exception(f"GoFile upload failed: {error_msg}")

        except RetryError as e:
            error_msg = f"GoFile upload failed after retries: {e.last_attempt.exception()}"
            print(error_msg)
            if status_message:
                await status_message.edit_text(
                    f"❌ **GoFile Upload Failed!**\n\n"
                    f"📁 **File:** `{filename}`\n"
                    f"🚨 **Error:** `{error_msg}`\n\n"
                    f"💡 **Tip:** Check GoFile status or try again."
                )
            raise Exception(error_msg) from e

        except Exception as e:
            print(f"❌ GoFile upload error: {e}")
            if status_message:
                await status_message.edit_text(
                    f"❌ **GoFile Upload Failed!**\n\n"
                    f"📁 **File:** `{filename}`\n"
                    f"🚨 **Error:** `{str(e)}`\n\n"
                    f"💡 **Tip:** Try again or contact support."
                )
            raise e

        finally:
            await self.close()

async def upload_to_telegram(client, chat_id: int, file_path: str, status_message, custom_thumbnail: str = None, custom_filename: str = None):
    """Enhanced Telegram upload with professional progress tracking."""
    is_default_thumb_created = False
    thumb_to_upload = custom_thumbnail

    try:
        # Handle thumbnail
        if not thumb_to_upload:
            await smart_progress_editor(status_message, "🖼 **Creating thumbnail...**")
            thumb_to_upload = await create_default_thumbnail(file_path)
            if thumb_to_upload:
                is_default_thumb_created = True
                await smart_progress_editor(status_message, "✅ **Thumbnail created!**")

        # Get file info
        file_size = os.path.getsize(file_path)
        final_filename = custom_filename or os.path.basename(file_path)

        if not final_filename.endswith('.mkv'):
            final_filename += '.mkv'

        caption = f"""🎬 **Professional Video Upload Complete!**

📁 **File:** `{final_filename}`
📊 **Size:** `{get_readable_file_size(file_size)}`
🎯 **Quality:** `High Definition`

⭐ **Powered By FileStream-Style Merge Bot**"""

        # Progress tracking
        start_time = time.time()
        last_progress_time = start_time

        async def progress(current, total):
            nonlocal last_progress_time
            now = time.time()
            
            if (now - last_progress_time) < EDIT_THROTTLE_SECONDS and current < total:
                return
            
            last_progress_time = now
            progress_percent = current / total
            speed = get_speed(start_time, current)
            eta = get_time_left(start_time, current, total)

            progress_text = f"""📤 **Uploading to Telegram...**

📁 **File:** `{final_filename}`
📊 **Total Size:** `{get_readable_file_size(total)}`

{get_progress_bar(progress_percent)} `{progress_percent:.1%}`

📈 **Uploaded:** `{get_readable_file_size(current)}`
🚀 **Speed:** `{speed}`
⏱ **ETA:** `{eta}`

📡 **Status:** {'Complete!' if current >= total else 'Uploading...'}"""

            await smart_progress_editor(status_message, progress_text.strip())

        # Upload the video
        await smart_progress_editor(status_message, f"🚀 **Starting Telegram upload...**\n\n📁 **File:** `{final_filename}`")

        await client.send_video(
            chat_id=chat_id,
            video=file_path,
            caption=caption.strip(),
            file_name=final_filename,
            thumb=thumb_to_upload,
            progress=progress
        )

        # Success - delete status message
        try:
            await status_message.delete()
        except:
            pass

        return True

    except Exception as e:
        error_text = f"""❌ **Telegram Upload Failed!**

📁 **File:** `{custom_filename or 'merged_video'}.mkv`
🚨 **Error:** `{type(e).__name__}: {str(e)}`

💡 **Possible Solutions:**
• Check file size (max 2GB for bots)
• Ensure stable internet connection  
• Try again after a few minutes
• Contact support if problem persists"""

        print(f"Telegram upload failed: {e}")
        await status_message.edit_text(error_text.strip())
        return False

    finally:
        # Cleanup default thumbnail
        if is_default_thumb_created and thumb_to_upload and os.path.exists(thumb_to_upload):
            try:
                os.remove(thumb_to_upload)
                print(f"Cleaned up thumbnail: {thumb_to_upload}")
            except Exception as e:
                print(f"Error cleaning up thumbnail: {e}")

# Export main functions
__all__ = [
    'GofileUploader',
    'upload_to_telegram', 
    'create_default_thumbnail',
    'smart_progress_editor'
]

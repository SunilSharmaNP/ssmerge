#!/usr/bin/env python3
"""
Enhanced Professional Downloader with DDL Support
Integrated with FileStream-style Merge Bot
Based on provided downloader-10.py with improvements
"""

import aiohttp
import asyncio
import os
import time
import logging
from datetime import datetime
from config import Config
from helpers.utils import get_readable_file_size, get_readable_time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError
from urllib.parse import urlparse, unquote
import re
import requests
from hashlib import sha256
import json
from pyrogram.errors import FloodWait

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
last_edit_time = {}
EDIT_THROTTLE_SECONDS = 2.0
DOWNLOAD_CANCELLED = {}

# Enhanced Configuration
DOWNLOAD_CHUNK_SIZE = 512 * 1024  # 512 KB chunks
TG_CHUNK_SIZE = 256 * 1024  # 256 KB for Telegram
DOWNLOAD_CONNECT_TIMEOUT = 15
DOWNLOAD_READ_TIMEOUT = 120
DOWNLOAD_RETRY_ATTEMPTS = 3
DOWNLOAD_RETRY_WAIT_MIN = 1
DOWNLOAD_RETRY_WAIT_MAX = 10
MAX_URL_LENGTH = 8048
MAX_CONCURRENT_CONNECTIONS = 2

# GoFile configuration
GOFILE_API_URL = "https://api.gofile.io"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PASSWORD_ERROR_MESSAGE = "ERROR: Password is required for this link\\n\\nUse: /cmd {link} password"

class DirectDownloadLinkException(Exception):
    pass

class DownloadCancelledException(Exception):
    pass

def start_download_session(user_id: int, session_key: str = "default"):
    """Start a new download session"""
    key = f"{user_id}_{session_key}"
    DOWNLOAD_CANCELLED[key] = False
    logger.info(f"🟢 Started download session: {key}")

def cancel_download(user_id: int, session_key: str = "default"):
    """Cancel ongoing download"""
    key = f"{user_id}_{session_key}"
    DOWNLOAD_CANCELLED[key] = True
    logger.info(f"🔴 Cancelled download session: {key}")

def is_download_cancelled(user_id: int, session_key: str = "default") -> bool:
    """Check if download is cancelled"""
    key = f"{user_id}_{session_key}"
    return DOWNLOAD_CANCELLED.get(key, False)

def cleanup_download_session(user_id: int, session_key: str = "default"):
    """Clean up download session"""
    key = f"{user_id}_{session_key}"
    if key in DOWNLOAD_CANCELLED:
        del DOWNLOAD_CANCELLED[key]
    logger.info(f"🧹 Cleaned up download session: {key}")

async def smart_progress_editor(status_message, text: str):
    """Enhanced progress editor with FloodWait handling"""
    if not status_message or not hasattr(status_message, 'chat'):
        return

    message_key = f"{status_message.chat.id}_{status_message.id}"
    now = time.time()
    last_time = last_edit_time.get(message_key, 0)

    # Enhanced throttling
    priority_keywords = ["Complete!", "Failed", "Error", "Cancelled", "Starting", "100%"]
    is_priority = any(keyword in text for keyword in priority_keywords)

    if (now - last_time) > EDIT_THROTTLE_SECONDS or is_priority:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await status_message.edit_text(text)
                last_edit_time[message_key] = now
                break
            except FloodWait as e:
                if attempt < max_retries - 1:
                    logger.warning(f"FloodWait {e.value}s, retrying...")
                    await asyncio.sleep(e.value)
                else:
                    logger.warning(f"FloodWait exceeded max retries")
            except Exception as e:
                logger.debug(f"Progress update failed: {e}")
                break

def get_time_left(start_time: float, current: int, total: int) -> str:
    """Enhanced time calculation"""
    if current <= 0 or total <= 0:
        return "Calculating..."

    elapsed = time.time() - start_time
    if elapsed <= 0.2:
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
    """Enhanced speed calculation"""
    elapsed = time.time() - start_time
    if elapsed <= 0:
        return "0 B/s"

    speed = current / elapsed
    if speed < 1024:
        return f"{speed:.0f} B/s"
    elif speed < 1024 * 1024:
        return f"{speed / 1024:.1f} KB/s"
    else:
        return f"{speed / (1024 * 1024):.2f} MB/s"

def get_progress_bar(progress: float, length: int = 20) -> str:
    """Get a styled progress bar"""
    filled_len = int(length * progress)
    return "█" * filled_len + "░" * (length - filled_len)

def validate_url(url: str) -> tuple[bool, str]:
    """Enhanced URL validation"""
    if not url or not isinstance(url, str):
        return False, "Invalid URL format"

    if len(url) > MAX_URL_LENGTH:
        return False, f"URL length exceeds maximum allowed ({MAX_URL_LENGTH} characters)"

    parsed_url = urlparse(url)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        return False, "URL must have a scheme (http/https) and network location"

    if parsed_url.scheme not in ('http', 'https'):
        return False, "URL scheme must be http or https"

    # Check for suspicious extensions
    path = parsed_url.path.lower()
    dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.sh']
    if any(path.endswith(ext) for ext in dangerous_extensions):
        return False, "Potentially dangerous file type in URL path"

    return True, "Valid"

def get_filename_from_url(url: str, fallback_name: str = None) -> str:
    """Enhanced filename extraction"""
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        filename = unquote(filename)

        if '?' in filename:
            filename = filename.split('?')[0]

        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip(' .').strip()
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

        if not filename or len(filename) < 3 or filename.lower() in ('download', 'file', 'index'):
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = fallback_name or f"download_{timestamp_str}.bin"

        if '.' not in filename:
            filename += '.bin'

        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:(200 - len(ext))] + ext

        return filename

    except Exception as e:
        logger.error(f"Error extracting filename from URL '{url}': {e}")
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        return fallback_name or f"download_error_{timestamp_str}.bin"

def handle_gofile_url(url: str, password: str = None) -> tuple:
    """Handle gofile.io URLs and return direct download link"""
    try:
        _password = sha256(password.encode("utf-8")).hexdigest() if password else ""
        _id = url.split("/")[-1]
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")

    def __get_token(session):
        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }
        
        __url = f"{GOFILE_API_URL}/accounts"
        try:
            __res = session.post(__url, headers=headers).json()
            if __res["status"] != "ok":
                raise DirectDownloadLinkException("ERROR: Failed to get token.")
            return __res["data"]["token"]
        except Exception as e:
            raise e

    def __fetch_links(session, _id, folderPath=""):
        _url = f"{GOFILE_API_URL}/contents/{_id}?wt=4fd6sg89d7s6&cache=true"
        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate, br", 
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Authorization": "Bearer" + " " + token,
        }

        if _password:
            _url += f"&password={_password}"

        try:
            _json = session.get(_url, headers=headers).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")

        if _json["status"] in "error-passwordRequired":
            raise DirectDownloadLinkException(
                f"ERROR:\\n{PASSWORD_ERROR_MESSAGE.format(url=url)}"
            )

        if _json["status"] in "error-passwordWrong":
            raise DirectDownloadLinkException("ERROR: This password is wrong!")

        if _json["status"] in "error-notFound":
            raise DirectDownloadLinkException("ERROR: File not found on gofile's server")

        if _json["status"] in "error-notPublic":
            raise DirectDownloadLinkException("ERROR: This folder is not public")

        data = _json["data"]
        if not details["title"]:
            details["title"] = data["name"] if data["type"] == "folder" else _id

        contents = data["children"]
        for content in contents.values():
            if content["type"] == "folder":
                if not content["public"]:
                    continue
                if not folderPath:
                    newFolderPath = os.path.join(details["title"], content["name"])
                else:
                    newFolderPath = os.path.join(folderPath, content["name"])
                __fetch_links(session, content["id"], newFolderPath)
            else:
                if not folderPath:
                    folderPath = details["title"]

                item = {
                    "path": os.path.join(folderPath),
                    "filename": content["name"],
                    "url": content["link"],
                }

                if "size" in content:
                    size = content["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    details["total_size"] += size

                details["contents"].append(item)

    details = {"contents": [], "title": "", "total_size": 0}
    
    with requests.Session() as session:
        try:
            token = __get_token(session)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")

        details["header"] = f"Cookie: accountToken={token}"

        try:
            __fetch_links(session, _id)
        except Exception as e:
            raise DirectDownloadLinkException(e)

        if len(details["contents"]) == 1:
            return (details["contents"][0]["url"], details["header"])
        elif len(details["contents"]) > 1:
            logger.warning(f"Gofile link has multiple files. Downloading the first one: {details['contents'][0]['filename']}")
            return (details["contents"][0]["url"], details["header"])
        else:
            raise DirectDownloadLinkException("No downloadable content found in gofile link")

@retry(
    stop=stop_after_attempt(DOWNLOAD_RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=DOWNLOAD_RETRY_WAIT_MIN, max=DOWNLOAD_RETRY_WAIT_MAX),
    retry=retry_if_exception_type(aiohttp.ClientError) | retry_if_exception_type(asyncio.TimeoutError),
    reraise=True,
    before_sleep=lambda retry_state: logger.warning(f"Retrying download (attempt {retry_state.attempt_number})...")
)
async def _perform_download_request(session: aiohttp.ClientSession, url: str, dest_path: str, status_message, total_size: int, user_id: int, session_key: str = "default"):
    """Enhanced download request with professional progress tracking"""
    start_time = time.time()
    last_progress_time = start_time
    downloaded = 0

    try:
        # Check for cancellation
        if is_download_cancelled(user_id, session_key):
            raise DownloadCancelledException("Download cancelled by user")

        async with session.get(url) as response:
            response.raise_for_status()

            if total_size == 0 and 'content-length' in response.headers:
                total_size = int(response.headers['content-length'])
                logger.info(f"Content-Length: {total_size} bytes for {os.path.basename(dest_path)}")

            with open(dest_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(DOWNLOAD_CHUNK_SIZE):
                    # Check for cancellation
                    if is_download_cancelled(user_id, session_key):
                        raise DownloadCancelledException("Download cancelled by user")

                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if (now - last_progress_time) >= EDIT_THROTTLE_SECONDS or downloaded >= total_size:
                        last_progress_time = now

                        if total_size > 0:
                            progress_percent = downloaded / total_size
                            speed = get_speed(start_time, downloaded)
                            eta = get_time_left(start_time, downloaded, total_size)

                            progress_text = (
                                f"📥 **Professional URL Downloader**\\n\\n"
                                f"📁 **File:** `{os.path.basename(dest_path)}`\\n"
                                f"📊 **Size:** `{get_readable_file_size(total_size)}`\\n\\n"
                                f"➤ {get_progress_bar(progress_percent)} `{progress_percent:.1%}`\\n\\n"
                                f"📈 **Downloaded:** `{get_readable_file_size(downloaded)}`\\n"
                                f"🚀 **Speed:** `{speed}`\\n"
                                f"⏱ **ETA:** `{eta}`\\n"
                                f"📡 **Status:** {'Complete!' if downloaded >= total_size else 'Downloading...'}\\n\\n"
                                f"💡 **FileStream-Style Professional Downloader**"
                            )

                            await smart_progress_editor(status_message, progress_text)

                    await asyncio.sleep(0.001)

        return downloaded

    except DownloadCancelledException:
        logger.info(f"Download cancelled for {os.path.basename(dest_path)}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise

    except Exception as e:
        logger.error(f"Download error: {e}")
        raise e

async def download_from_url(url: str, user_id: int, status_message, file_index: int = 1, total_files: int = 1, password: str = None, session_key: str = "default") -> str | None:
    """Enhanced URL download with FileStream-style progress"""
    start_time = time.time()
    
    # Initialize download session
    start_download_session(user_id, session_key)

    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            await smart_progress_editor(status_message, f"❌ **Invalid URL!**\\n\\n🚨 **Error:** {error_msg}")
            return None

        # Check for cancellation
        if is_download_cancelled(user_id, session_key):
            await smart_progress_editor(status_message, "🚫 **Download Cancelled!**\\n\\n⚠️ Operation stopped by user.")
            return None

        # Handle gofile.io URLs
        parsed_url = urlparse(url)
        headers_dict = {}

        if 'gofile.io' in parsed_url.netloc:
            try:
                await smart_progress_editor(status_message, "🔍 **Processing gofile.io link...**")
                direct_url, headers_str = await asyncio.to_thread(handle_gofile_url, url, password)
                
                if headers_str:
                    for header_line in headers_str.split('\\n'):
                        if ':' in header_line:
                            key, value = header_line.split(':', 1)
                            headers_dict[key.strip()] = value.strip()
                
                url = direct_url
                await smart_progress_editor(status_message, f"✅ **Gofile.io processed!**\\n\\n📁 **Direct URL:** `{url[:70]}...`")

            except DirectDownloadLinkException as e:
                await smart_progress_editor(status_message, f"❌ **Gofile.io Error!**\\n\\n🚨 **Error:** {str(e)}")
                return None

        # Setup paths
        file_name = get_filename_from_url(url)
        user_download_dir = os.path.join("downloads", str(user_id))
        os.makedirs(user_download_dir, exist_ok=True)
        dest_path = os.path.join(user_download_dir, file_name)

        # Prevent overwriting
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("_%H%M%S")
            dest_path = os.path.join(user_download_dir, f"{base}{timestamp}{ext}")
            file_name = os.path.basename(dest_path)

        # Enhanced headers
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }

        if headers_dict:
            headers.update(headers_dict)

        # Timeout configuration
        timeout_config = aiohttp.ClientTimeout(
            total=None,
            connect=DOWNLOAD_CONNECT_TIMEOUT,
            sock_read=DOWNLOAD_READ_TIMEOUT
        )

        # Connection configuration
        connector = aiohttp.TCPConnector(
            limit=MAX_CONCURRENT_CONNECTIONS,
            limit_per_host=1,
            keepalive_timeout=15,
            enable_cleanup_closed=True,
            ttl_dns_cache=300
        )

        async with aiohttp.ClientSession(headers=headers, timeout=timeout_config, connector=connector) as session:
            # HEAD request for file info
            total_size = 0
            try:
                async with session.head(url, allow_redirects=True) as head_response:
                    head_response.raise_for_status()
                    total_size = int(head_response.headers.get('content-length', 0))
                    content_type = head_response.headers.get('content-type', 'application/octet-stream')
                    
                    await smart_progress_editor(
                        status_message,
                        f"📥 **FileStream-Style Downloader** ({file_index}/{total_files})\\n\\n"
                        f"📡 **Download Starting...**\\n\\n"
                        f"📁 **File:** `{file_name}`\\n"
                        f"📊 **Size:** `{get_readable_file_size(total_size) if total_size > 0 else 'Unknown'}`\\n"
                        f"📋 **Type:** `{content_type.split(';')[0].strip()}`"
                    )

            except aiohttp.ClientError as e:
                logger.warning(f"HEAD request failed: {e}. Proceeding with GET.")
                await smart_progress_editor(
                    status_message,
                    f"📥 **FileStream-Style Downloader** ({file_index}/{total_files})\\n\\n"
                    f"📡 **Download Starting...**\\n\\n"
                    f"📁 **File:** `{file_name}`\\n"
                    f"📊 **Size:** `Unknown`"
                )

            # Check for cancellation
            if is_download_cancelled(user_id, session_key):
                await smart_progress_editor(status_message, "🚫 **Download Cancelled!**\\n\\n⚠️ Operation stopped by user.")
                return None

            # Perform download
            actual_downloaded_size = await _perform_download_request(session, url, dest_path, status_message, total_size, user_id, session_key)

            # Verify download
            actual_file_size = os.path.getsize(dest_path)
            if total_size > 0 and abs(actual_file_size - total_size) > 1024:
                logger.error(f"File size mismatch: expected {total_size}, got {actual_file_size}")
                os.remove(dest_path)
                await smart_progress_editor(status_message,
                    f"❌ **Download Failed!**\\n\\n"
                    f"📁 **File:** `{file_name}`\\n"
                    f"🚨 **Error:** File size mismatch\\n"
                    f"💡 **Tip:** Try downloading again."
                )
                return None

            # Success
            elapsed_time = time.time() - start_time
            await smart_progress_editor(status_message,
                f"✅ **URL Download Complete!** ({file_index}/{total_files})\\n\\n"
                f"📁 **File:** `{file_name}`\\n"
                f"📊 **Size:** `{get_readable_file_size(actual_file_size)}`\\n"
                f"⏱ **Time:** `{elapsed_time:.1f}s`\\n"
                f"🚀 **Speed:** `{get_speed(start_time, actual_file_size)}`\\n\\n"
                f"⭐ **FileStream-Style Professional Downloader**"
            )

            return dest_path

    except DownloadCancelledException:
        await smart_progress_editor(status_message, "🚫 **Download Cancelled!**\\n\\n⚠️ Operation stopped by user.")
        return None

    except Exception as e:
        logger.error(f"Download error: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        
        await smart_progress_editor(status_message,
            f"❌ **Download Failed!**\\n\\n"
            f"📁 **File:** `{file_name}`\\n"
            f"🚨 **Error:** `{type(e).__name__}: {str(e)}`\\n\\n"
            f"💡 **Tip:** Try again or contact support."
        )
        return None

    finally:
        cleanup_download_session(user_id, session_key)

async def download_from_tg(client, message, user_id: int, status_message, file_index: int = 1, total_files: int = 1, session_key: str = "default") -> str | None:
    """Enhanced Telegram download with FileStream-style UI"""
    # Initialize download session
    start_download_session(user_id, session_key)
    
    file_name = "Unknown File"
    dest_path = None

    try:
        # Setup paths
        user_download_dir = os.path.join("downloads", str(user_id))
        os.makedirs(user_download_dir, exist_ok=True)

        # Get file info
        file_obj = None
        file_size = 0
        file_type = "Unknown"

        if message.video:
            file_obj = message.video
            file_name = file_obj.file_name or f"video_{message.id}.mp4"
            file_size = file_obj.file_size
            file_type = "Video"
        elif message.document:
            file_obj = message.document
            file_name = file_obj.file_name or f"document_{message.id}"
            file_size = file_obj.file_size
            file_type = "Document"
        else:
            await smart_progress_editor(status_message, "❌ **No downloadable file found**")
            return None

        # File size validation
        if file_size > 2 * 1024 * 1024 * 1024:  # 2GB
            await smart_progress_editor(status_message,
                f"❌ **File Too Large!**\\n\\n"
                f"📁 **File:** `{file_name}`\\n"
                f"📊 **Size:** `{get_readable_file_size(file_size)}`\\n"
                f"🚨 **Limit:** `2GB (Telegram API)`"
            )
            return None

        # Setup destination path
        dest_path = os.path.join(user_download_dir, file_name)
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("_%H%M%S")
            file_name = f"{base}{timestamp}{ext}"
            dest_path = os.path.join(user_download_dir, file_name)

        # Enhanced initial status
        initial_text = (
            f"📥 **FileStream-Style Telegram Downloader** ({file_index}/{total_files})\\n\\n"
            f"📡 **Initializing Download...**\\n\\n"
            f"📁 **File:** `{file_name}`\\n"
            f"📊 **Size:** `{get_readable_file_size(file_size)}`\\n"
            f"🎯 **Type:** `{file_type}`\\n\\n"
            f"🚀 **Starting professional download...**"
        )

        await smart_progress_editor(status_message, initial_text)

        # Progress tracking
        start_time = time.time()

        async def enhanced_progress_callback(current, total):
            nonlocal last_edit_time
            
            # Check for cancellation
            if is_download_cancelled(user_id, session_key):
                raise DownloadCancelledException("Download cancelled by user")

            now = time.time()
            message_key = f"{status_message.chat.id}_{status_message.id}"
            last_time = last_edit_time.get(message_key, 0)

            is_complete = current >= total
            should_update = (now - last_time) >= EDIT_THROTTLE_SECONDS or is_complete

            if not should_update:
                return

            last_edit_time[message_key] = now

            progress = current / total if total > 0 else 0
            speed = get_speed(start_time, current)
            eta = get_time_left(start_time, current, total)
            elapsed = now - start_time

            progress_text = (
                f"📥 **FileStream Telegram Downloader** ({file_index}/{total_files})\\n\\n"
                f"📁 **File:** `{file_name}`\\n"
                f"📊 **Size:** `{get_readable_file_size(total)}`\\n\\n"
                f"➤ {get_progress_bar(progress)} `{progress:.1%}`\\n\\n"
                f"📈 **Downloaded:** `{get_readable_file_size(current)}`\\n"
                f"🚀 **Speed:** `{speed}`\\n"
                f"⏱ **ETA:** `{eta}`\\n"
                f"📡 **Status:** {'Complete!' if is_complete else 'Downloading...'}\\n\\n"
                f"⭐ **FileStream-Style Professional**"
            )

            await smart_progress_editor(status_message, progress_text)

        # Check for cancellation
        if is_download_cancelled(user_id, session_key):
            await smart_progress_editor(status_message, "🚫 **Download Cancelled!**\\n\\n⚠️ Operation stopped.")
            return None

        # Download with enhanced error handling
        try:
            file_path = await client.download_media(
                message=message,
                file_name=dest_path,
                progress=enhanced_progress_callback
            )

        except DownloadCancelledException:
            if dest_path and os.path.exists(dest_path):
                os.remove(dest_path)
            await smart_progress_editor(status_message, "🚫 **Download Cancelled!**\\n\\n⚠️ Operation stopped.")
            return None

        # Verification
        if not os.path.exists(file_path):
            await smart_progress_editor(status_message,
                f"❌ **Download Failed:** File not found\\n\\n"
                f"📁 **Expected:** `{file_path}`\\n"
                f"💡 **Tip:** Try again or check storage space."
            )
            return None

        actual_size = os.path.getsize(file_path)
        elapsed_time = time.time() - start_time

        # Success message
        success_text = (
            f"✅ **Telegram Download Complete!** ({file_index}/{total_files})\\n\\n"
            f"📁 **File:** `{file_name}`\\n"
            f"📊 **Size:** `{get_readable_file_size(actual_size)}`\\n"
            f"⏱ **Time:** `{elapsed_time:.1f}s`\\n"
            f"🚀 **Speed:** `{get_speed(start_time, actual_size)}`\\n\\n"
            f"⭐ **FileStream-Style Professional**"
        )

        await smart_progress_editor(status_message, success_text)
        return file_path

    except DownloadCancelledException:
        await smart_progress_editor(status_message, "🚫 **Download Cancelled!**\\n\\n⚠️ Operation stopped.")
        return None

    except Exception as e:
        error_text = (
            f"❌ **Telegram Download Failed!**\\n\\n"
            f"📁 **File:** `{file_name}`\\n"
            f"🚨 **Error:** `{type(e).__name__}: {str(e)}`\\n\\n"
            f"💡 **Solutions:**\\n"
            f"• Check file availability\\n"
            f"• Ensure stable connection\\n"
            f"• Try again or contact support"
        )

        logger.error(f"Telegram download error: {e}")

        try:
            if dest_path and os.path.exists(dest_path):
                os.remove(dest_path)
        except:
            pass

        await smart_progress_editor(status_message, error_text)
        return None

    finally:
        cleanup_download_session(user_id, session_key)

# Export main functions
__all__ = [
    'download_from_url',
    'download_from_tg',
    'smart_progress_editor',
    'cancel_download',
    'start_download_session',
    'cleanup_download_session'
]

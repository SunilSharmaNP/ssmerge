# Professional Video Tools Telegram Bot

## Project Overview
A comprehensive Telegram bot for video manipulation with professional features including merging, encoding, extracting streams, screenshots, trimming, and more. Built with Pyrogram and MongoDB for persistent user settings.

## Current Status
**Implementation Phase 1**: Critical bug fixes and foundation setup
- ✅ Fixed config.py method call errors (get_env_var.__func__ → get_env_var)
- ✅ Completed database functions (enableMetadataToggle, disableMetadataToggle)
- ✅ Fixed type errors in utils.py and config.py
- ✅ Installed all dependencies (Python 3.11, FFmpeg, MongoDB drivers)
- ✅ Environment variables configured
- 🔄 In Progress: Setting up workflows and completing feature implementation

## Recent Changes (October 24, 2025)
1. **Config System**: Fixed all `get_env_var.__func__()` calls to proper `get_env_var()` static method calls
2. **Database Functions**: Implemented complete `enableMetadataToggle` and `disableMetadataToggle` functions
3. **Type Safety**: Fixed type conversion issues for TELEGRAM_API, OWNER, MAX_CONCURRENT_USERS, MAX_FILE_SIZE
4. **Time Formatting**: Updated `get_readable_time()` to accept float instead of int
5. **Dependencies**: Installed Python 3.11, FFmpeg, and all required Python packages

## Architecture

### Core Files
- `bot.py`: Main bot entry point with command handlers
- `config.py`: Configuration management with environment variables
- `__init__.py`: Global constants and logging setup

### Helpers
- `helpers/database.py`: MongoDB integration for user settings
- `helpers/utils.py`: UserSettings class and utility functions
- `helpers/uploader.py`: GoFile and Telegram upload functionality
- `helpers/merge_helper.py`: Video merging logic
- `helpers/ffmpeg_helper.py`: FFmpeg operations
- `helpers/display_progress.py`: Progress tracking

### Plugins
- `plugins/cb_handler.py`: Callback query handling
- `plugins/mergeVideo.py`: Video+Video merging
- `plugins/mergeVideoAudio.py`: Video+Audio merging
- `plugins/mergeVideoSub.py`: Video+Subtitle merging
- `plugins/streams_extractor.py`: Stream extraction
- `plugins/metadataEditor.py`: Metadata editing

## Features (Planned)
- [x] Video merging (multiple videos)
- [x] Video + Audio merging
- [x] Video + Subtitle merging
- [x] Stream extraction
- [ ] Video encoding with presets (high/medium/low)
- [ ] Professional mediainfo display
- [ ] Screenshot generation
- [ ] Video trimming
- [ ] Sample video creation
- [ ] Image-based menus with captions
- [ ] All English language (removing Hindi)

## User Preferences
- Language: English only (converting all Hindi text)
- UI: Professional image menus with captions for every section
- Database: MongoDB with proper persistence for all user settings
- Features: All video tools features working professionally

## Database Schema
```
Collection: mergeSettings
{
  _id: user_id,
  name: "User Name",
  user_settings: {
    merge_mode: 1-4,
    edit_metadata: boolean
  },
  isAllowed: boolean,
  isBanned: boolean,
  thumbnail: file_id or null
}
```

## Environment Variables
- `API_HASH`: Telegram API hash
- `BOT_TOKEN`: Bot token from BotFather
- `TELEGRAM_API`: Telegram API ID
- `OWNER`: Owner user ID
- `OWNER_USERNAME`: Owner username
- `DATABASE_URL`: MongoDB connection string
- `PASSWORD`: Bot access password (optional)
- `GOFILE_TOKEN`: GoFile API token (optional)
- `LOGCHANNEL`: Log channel ID (optional)

## Source Repositories
1. **ssmerge** (beta branch): Base repository for video merging
2. **ve**: Video encoding with compression presets
3. **Anime-Leech**: Professional mediainfo and helper utilities
4. **animated-lamp**: Screenshot, trimming, sample video features

## Known Issues to Fix
- [ ] Complete all incomplete plugin files
- [ ] Add missing helper functions
- [ ] Convert all Hindi text to English
- [ ] Add image menus with captions
- [ ] Implement professional downloading/uploading
- [ ] Add video encoding feature
- [ ] Add screenshot generation
- [ ] Add video trimming
- [ ] Add sample video generation

## Development Notes
- Using Replit PostgreSQL database (configured but not used yet - will use MongoDB)
- Bot configured for MongoDB via DATABASE_URL
- FFmpeg installed for video processing
- All dependencies managed via pip/requirements.txt
- No Docker needed on Replit (removed Docker-related files if not needed)

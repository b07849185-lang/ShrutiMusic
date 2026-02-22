# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# System Upgraded (2026): PyTgCalls Modern Native Architecture
# Features: Zero Latency FFmpeg, StreamEnded Handler, Direct API Integration, Full Legacy Bridge

import asyncio
import os
from datetime import datetime, timedelta
from typing import Union, Optional

from pyrogram.types import InlineKeyboardMarkup
from pyrogram.errors import ChatAdminRequired

# Modern PyTgCalls Imports
from pytgcalls import PyTgCalls, filters
from pytgcalls.types import (
    MediaStream,
    AudioQuality,
    VideoQuality,
    Update,
    ChatUpdate
)
from pytgcalls.exceptions import NoActiveGroupCall

import config
from strings import get_string
from ShrutiMusic import LOGGER, YouTube, app, userbot
from ShrutiMusic.misc import db
from ShrutiMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from ShrutiMusic.utils.exceptions import AssistantErr
from ShrutiMusic.utils.thumbnails import gen_thumb

autoend = {}
counter = {}

# ===============================
# Helper Functions (Zero Latency FFmpeg)
# ===============================

def _build_stream(path: str, video: bool = False, ffmpeg_opts: str = "") -> MediaStream:
    """
    Constructs a MediaStream object compatible with PyTgCalls.
    Handles Audio/Video flags and ULTRA-FAST FFmpeg parameters.
    """
    path = str(path)
    is_url = path.startswith("http")
    
    # سرعة التشغيل اللحظية: إلغاء الـ Buffering وتقليل الـ Probesize
    base_flags = (
        "-threads 2 "
        "-probesize 1024 -analyzeduration 0 " 
        "-fflags +genpts+igndts+nobuffer+fastseek -sync ext "
    )
    
    if is_url:
        base_flags += "-reconnect 1 -reconnect_streamed 1 -reconnect_on_network_error 1 -reconnect_delay_max 5 "
    else:
        base_flags += "-re "

    final_ffmpeg = base_flags + ffmpeg_opts

    # 🚀 الحل الذكي: بناء القاموس وتجنب إرسال None للفيديو
    stream_params = {
        "media_path": path,
        "audio_parameters": AudioQuality.HIGH,
        "ffmpeg_parameters": final_ffmpeg
    }
    
    # إضافة بارامترات الفيديو فقط إذا كان التشغيل فيديو (لتجنب TypeError: NoneType)
    if video:
        stream_params["video_parameters"] = VideoQuality.HD_720p

    return MediaStream(**stream_params)

async def _clear_(chat_id: int) -> None:
    try:
        popped = db.pop(chat_id, None)
        if popped:
            try:
                file = popped[0].get("file")
                if file and "vid_" not in file and not file.startswith("http"):
                    os.remove(file)
            except:
                pass
        db[chat_id] = []
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except:
        pass

# ===============================
# The Main Call Controller Class
# ===============================

class Call:
    def __init__(self):
        self.userbot1 = getattr(userbot, "one", None)
        self.userbot2 = getattr(userbot, "two", None)
        self.userbot3 = getattr(userbot, "three", None)
        self.userbot4 = getattr(userbot, "four", None)
        self.userbot5 = getattr(userbot, "five", None)

        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls: set[int] = set()

    async def ping(self) -> str:
        return "PONG"

    # كباري التحكم الأساسية
    async def pause_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    async def resume_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    async def mute_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.mute(chat_id)

    async def unmute_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute(chat_id)

    # دوال الخروج
    async def stop_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await _clear_(chat_id)
        try:
            await assistant.leave_call(chat_id)
        except:
            pass
        finally:
            self.active_calls.discard(chat_id)

    async def force_stop_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            if check: check.pop(0)
        except:
            pass
        await _clear_(chat_id)
        try:
            await assistant.leave_call(chat_id)
        except:
            pass
        finally:
            self.active_calls.discard(chat_id)

    # اسم الدالة البديل لحل مشكلة watcher.py و reload.py
    async def stop_stream_force(self, chat_id: int) -> None:
        await self.force_stop_stream(chat_id)

    async def change_volume_call(self, chat_id: int, volume: int) -> None:
        assistant = await group_assistant(self, chat_id)
        try:
            await assistant.change_volume(chat_id, volume)
        except Exception as e:
            LOGGER(__name__).error(f"Failed to change volume for {chat_id}: {e}")

    # دوال التشغيل مع **kwargs لامتصاص البارامترات القديمة
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: int, duration: int, mode: str, **kwargs) -> None:
        assistant = await group_assistant(self, chat_id)
        ffmpeg_opts = f"-ss {to_seek} "
        is_video = (mode == "video")
        stream = _build_stream(file_path, video=is_video, ffmpeg_opts=ffmpeg_opts)
        await assistant.play(chat_id, stream)

    async def skip_stream(self, chat_id: int, link: str, video: bool = False, **kwargs) -> None:
        assistant = await group_assistant(self, chat_id)
        stream = _build_stream(link, video=video)
        await assistant.play(chat_id, stream)

    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: bool = False, **kwargs) -> None:
        assistant = await group_assistant(self, chat_id)
        stream = _build_stream(link, video=video)

        try:
            await assistant.play(chat_id, stream)
            self.active_calls.add(chat_id)
            await add_active_chat(chat_id)
            await music_on(chat_id)
            if video:
                await add_active_video_chat(chat_id)
            
            if await is_autoend():
                counter[chat_id] = {}
                try:
                    users = len(await assistant.get_participants(chat_id))
                    if users == 1:
                        autoend[chat_id] = datetime.now() + timedelta(minutes=1)
                except:
                    pass
                    
        except NoActiveGroupCall:
             raise AssistantErr("يرجى فتح المحادثة الصوتية أولاً.")
        except ChatAdminRequired:
            raise AssistantErr("البوت يحتاج إلى صلاحيات لفتح المكالمة.")
        except Exception as e:
            raise AssistantErr(f"Error: {e}")

    async def start(self) -> None:
        LOGGER(__name__).info("Starting PyTgCalls Clients (Modern Engine)...")
        if self.one and config.STRING1: await self.one.start()
        if self.two and config.STRING2: await self.two.start()
        if self.three and config.STRING3: await self.three.start()
        if self.four and config.STRING4: await self.four.start()
        if self.five and config.STRING5: await self.five.start()

    async def decorators(self) -> None:
        assistants = list(filter(None, [self.one, self.two, self.three, self.four, self.five]))
        for assistant in assistants:
            @assistant.on_update(filters.stream_end())
            async def stream_end_handler(client, update: Update):
                chat_id = update.chat_id
                await self.play(client, chat_id)

            @assistant.on_update(filters.chat_update(ChatUpdate.Status.LEFT_CALL))
            async def left_call_handler(client, update: Update):
                chat_id = update.chat_id
                await self.stop_stream(chat_id)
            
            @assistant.on_update(filters.chat_update(ChatUpdate.Status.KICKED))
            async def kicked_handler(client, update: Update):
                chat_id = update.chat_id
                await self.stop_stream(chat_id)

    async def play(self, client, chat_id: int) -> None:
        check = db.get(chat_id)
        if not check:
            await _clear_(chat_id)
            return

        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            
            if not check:
                await _clear_(chat_id)
                try: 
                    await client.leave_call(chat_id)
                except: 
                    pass
                finally: 
                    self.active_calls.discard(chat_id)
                return
        except:
            try: 
                await _clear_(chat_id)
                return await client.leave_call(chat_id)
            except: 
                return

        queued = check[0].get("file")
        title = (check[0].get("title") or "").title()
        user = check[0].get("by")
        original_chat_id = check[0].get("chat_id")
        streamtype = check[0].get("streamtype")
        videoid = check[0].get("vidid")
        duration = check[0].get("dur")
        
        is_video = str(streamtype) == "video"
        final_link = queued
        
        # الاتصال بمحرك يوتيوب الصاروخي لجلب رابط البث فوراً
        if "youtube" in str(queued) or "googleusercontent" in str(queued):
             try:
                direct = await YouTube.get_direct_link(f"https://youtube.com/watch?v={videoid}", prefer_audio=not is_video)
                if direct: 
                    final_link = direct
             except Exception as e: 
                LOGGER(__name__).error(f"Queue Play API Fetch Error: {e}")

        # بناء الاستريم بالطريقة المصلحة
        stream = _build_stream(final_link, video=is_video)

        try:
            await client.play(chat_id, stream)
            
            if is_video:
                await add_active_video_chat(chat_id)
            else:
                await remove_active_video_chat(chat_id)

            img = await gen_thumb(videoid)
            
            # محاولة جلب لغة الجروب وأزرار التشغيل بأمان
            try:
                from ShrutiMusic.utils.inline import stream_markup
                lang = await get_lang(chat_id)
                _ = get_string(lang)
                button = stream_markup(_, chat_id)
            except:
                button = None
                _ = get_string("ar") # افتراضي
            
            try:
                if db[chat_id][0].get("mystic"):
                    await db[chat_id][0].get("mystic").delete()
            except: 
                pass
            
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}", 
                    title[:23], 
                    duration, 
                    user
                ),
                reply_markup=InlineKeyboardMarkup(button) if button else None,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            
        except Exception as e:
            LOGGER(__name__).error(f"Queue Play Error: {e}")
            await _clear_(chat_id)
            await app.send_message(original_chat_id, "فشل في تشغيل المقطع التالي.")

# Instantiating the Call Class for ShrutiMusic
Nand = Call()

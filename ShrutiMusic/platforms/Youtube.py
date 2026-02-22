# System Upgraded (2026): Ultra-Fast YouTube Search & Download API
# Features: Async Native, Direct Indexing, Safe Getters, No-Loop Optimization

import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from ShrutiMusic.utils.formatters import time_to_seconds
import aiohttp
from ShrutiMusic import LOGGER

try:
    from py_yt import VideosSearch
except ImportError:
    from youtubesearchpython.__future__ import VideosSearch

API_URL = "https://shrutibots.site"

async def download_song(link: str) -> str:
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "audio"}
            
            async with session.get(
                f"{API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=7)
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                download_token = data.get("download_token")
                
                if not download_token:
                    return None
                
                stream_url = f"{API_URL}/stream/{video_id}?type=audio&token={download_token}"
                
                async with session.get(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as file_response:
                    if file_response.status == 302:
                        redirect_url = file_response.headers.get('Location')
                        if redirect_url:
                            async with session.get(redirect_url) as final_response:
                                if final_response.status != 200:
                                    return None
                                with open(file_path, "wb") as f:
                                    async for chunk in final_response.content.iter_chunked(16384):
                                        f.write(chunk)
                                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                    return file_path
                                return None
                    elif file_response.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(16384):
                                f.write(chunk)
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            return file_path
                        return None
                    else:
                        return None

    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return None

async def download_video(link: str) -> str:
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "video"}
            
            async with session.get(
                f"{API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=7)
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                download_token = data.get("download_token")
                
                if not download_token:
                    return None
                
                stream_url = f"{API_URL}/stream/{video_id}?type=video&token={download_token}"
                
                async with session.get(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as file_response:
                    if file_response.status == 302:
                        redirect_url = file_response.headers.get('Location')
                        if redirect_url:
                            async with session.get(redirect_url) as final_response:
                                if final_response.status != 200:
                                    return None
                                with open(file_path, "wb") as f:
                                    async for chunk in final_response.content.iter_chunked(16384):
                                        f.write(chunk)
                                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                    return file_path
                                return None
                    elif file_response.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(16384):
                                f.write(chunk)
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            return file_path
                        return None
                    else:
                        return None

    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return None

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    # 🚀 Optimization 1: Direct Indexing (No Loop) & Safe Getters
    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        res_data = await results.next()
        
        if not res_data or not res_data.get("result"):
            return "Unknown", "00:00", 0, "https://telegra.ph/file/0c976cc1508dbca64ad46.jpg", "Unknown"
            
        result = res_data["result"][0]
        title = result.get("title", "Unknown")
        duration_min = result.get("duration", "00:00")
        thumbnail = result.get("thumbnails", [{}])[0].get("url", "https://telegra.ph/file/0c976cc1508dbca64ad46.jpg").split("?")[0]
        vidid = result.get("id", "Unknown")
        duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        
        return title, duration_min, duration_sec, thumbnail, vidid

    # 🚀 Optimization 2
    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        res_data = await results.next()
        if res_data and res_data.get("result"):
            return res_data["result"][0].get("title", "Unknown Title")
        return "Unknown Title"

    # 🚀 Optimization 3
    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        res_data = await results.next()
        if res_data and res_data.get("result"):
            return res_data["result"][0].get("duration", "00:00")
        return "00:00"

    # 🚀 Optimization 4
    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        res_data = await results.next()
        if res_data and res_data.get("result"):
            return res_data["result"][0].get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        return "https://telegra.ph/file/0c976cc1508dbca64ad46.jpg"

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    # 🚀 Optimization 5
    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        results = VideosSearch(link, limit=1)
        res_data = await results.next()
        
        if not res_data or not res_data.get("result"):
            return {"title": "Unknown", "link": link, "vidid": "0", "duration_min": "00:00", "thumb": ""}, "0"
            
        result = res_data["result"][0]
        
        track_details = {
            "title": result.get("title", "Unknown"),
            "link": result.get("link", link),
            "vidid": result.get("id", "0"),
            "duration_min": result.get("duration", "00:00"),
            "thumb": result.get("thumbnails", [{}])[0].get("url", "").split("?")[0],
        }
        return track_details, result.get("id", "0")

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        a = VideosSearch(link, limit=10)
        res_data = await a.next()
        
        try:
            result = res_data.get("result")[query_type]
            title = result.get("title", "Unknown")
            duration_min = result.get("duration", "00:00")
            vidid = result.get("id", "0")
            thumbnail = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
            return title, duration_min, thumbnail, vidid
        except (IndexError, TypeError):
            return "Unknown", "00:00", "", "0"

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link

        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            
            if downloaded_file:
                return downloaded_file, True
            else:
                return None, False
        except Exception:
            return None, False

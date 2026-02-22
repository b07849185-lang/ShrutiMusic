import os
import asyncio
import aiofiles
import aiohttp
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# استخدام مكتبة البحث الخاصة بـ ShrutiMusic
from py_yt import VideosSearch

from config import YOUTUBE_IMG_URL
from ShrutiMusic import app

# Arabic Support
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    arabic_reshaper = None
    get_display = None

# ================= CONSTANTS =================
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

PANEL_W, PANEL_H = 763, 545
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 88
TRANSPARENCY = 7 
INNER_OFFSET = 36
THUMB_W, THUMB_H = 542, 273
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + INNER_OFFSET
TITLE_X = 377
META_X = 377
TITLE_Y = THUMB_Y + THUMB_H + 10
META_Y = TITLE_Y + 45
BAR_X, BAR_Y = 388, META_Y + 45
BAR_RED_LEN = 280
BAR_TOTAL_LEN = 480
MAX_TITLE_WIDTH = 580

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"
# =============================================

def fix_ar(text):
    if not text: return ""
    if arabic_reshaper and get_display:
        try:
            return get_display(arabic_reshaper.reshape(text))
        except: return text
    return text

def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    """Uses getlength which is compatible with Pillow 10+ & Python 3.13"""
    ellipsis = "…"
    try:
        if font.getlength(text) <= max_w:
            return text
        for i in range(len(text) - 1, 0, -1):
            if font.getlength(text[:i] + ellipsis) <= max_w:
                return text[:i] + ellipsis
    except AttributeError:
        # Fallback for older Pillow versions
        if font.getsize(text)[0] <= max_w:
            return text
        for i in range(len(text) - 1, 0, -1):
            if font.getsize(text[:i] + ellipsis)[0] <= max_w:
                return text[:i] + ellipsis
    return ellipsis

# رسم الأزرار برمجياً باستخدام Pillow (لعدم وجود صور خارجية)
def draw_player_icons(draw: ImageDraw.ImageDraw, center_x: int, center_y: int):
    icon_color = "black"
    
    # 1. زر التشغيل (Play) في المنتصف - مثلث
    play_size = 40
    play_polygon = [
        (center_x - 10, center_y - play_size//2),
        (center_x - 10, center_y + play_size//2),
        (center_x + 22, center_y)
    ]
    draw.polygon(play_polygon, fill=icon_color)

    # 2. زر المقطع التالي (Next) - على اليمين (مثلث + مستطيل)
    next_x = center_x + 90
    next_size = 28
    draw.polygon([
        (next_x, center_y - next_size//2),
        (next_x, center_y + next_size//2),
        (next_x + 20, center_y)
    ], fill=icon_color)
    draw.rectangle([next_x + 20, center_y - next_size//2, next_x + 25, center_y + next_size//2], fill=icon_color)

    # 3. زر المقطع السابق (Prev) - على اليسار (مثلث + مستطيل)
    prev_x = center_x - 90
    draw.polygon([
        (prev_x, center_y - next_size//2),
        (prev_x, center_y + next_size//2),
        (prev_x - 20, center_y)
    ], fill=icon_color)
    draw.rectangle([prev_x - 25, center_y - next_size//2, prev_x - 20, center_y + next_size//2], fill=icon_color)


async def gen_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_glass_v1.png")
    if os.path.exists(cache_path):
        return cache_path

    # جلب البيانات من يوتيوب باستخدام py_yt الخاصة بـ Shruti
    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        search = VideosSearch(url, limit=1)
        results_data = await search.next()
        data = results_data.get("result", [])[0]

        title = data.get("title", "Unknown Track")
        thumbnail = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL).split("?")[0]
        duration = data.get("duration", "00:00")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
        channel = data.get("channel", {}).get("name", "Unknown Channel")

    except Exception:
        title, thumbnail, duration, views, channel = "Unknown Track", YOUTUBE_IMG_URL, "00:00", "N/A", "ShrutiMusic"

    is_live = not duration or str(duration).strip().lower() in {"", "live", "live now"}
    duration_text = "Live" if is_live else duration or "00:00"

    # تحميل الصورة الأساسية
    thumb_path = os.path.join(CACHE_DIR, f"temp_{videoid}.png")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    thumb_path = DEFAULT_THUMB
    except:
        thumb_path = DEFAULT_THUMB

    if not os.path.exists(thumb_path):
        thumb_path = DEFAULT_THUMB

    try:
        # Base Image 1280x720
        base = Image.open(thumb_path).convert("RGBA")
        base = base.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # 1. Background Blur & Darken
        bg = base.filter(ImageFilter.BoxBlur(8))
        bg = ImageEnhance.Brightness(bg).enhance(0.5)

        # 2. Glass Panel
        crop = bg.crop((PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H))
        crop = crop.filter(ImageFilter.GaussianBlur(30))
        crop = ImageEnhance.Color(crop).enhance(1.3)
        crop = ImageEnhance.Brightness(crop).enhance(1.1)
        
        tint = Image.new("RGBA", crop.size, (255, 255, 255, TRANSPARENCY))
        glass_panel = Image.alpha_composite(crop, tint)
        
        mask = Image.new("L", (PANEL_W, PANEL_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, PANEL_W, PANEL_H), radius=40, fill=255)
        
        bg.paste(glass_panel, (PANEL_X, PANEL_Y), mask)

        # 3. Glass Border
        draw = ImageDraw.Draw(bg)
        draw.rounded_rectangle(
            (PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H),
            radius=40,
            outline=(255, 255, 255, 90),
            width=2
        )

        # 4. Load Fonts
        try:
            title_font = ImageFont.truetype(FONT_BOLD_PATH, 34)
            regular_font = ImageFont.truetype(FONT_REGULAR_PATH, 20)
        except:
            title_font = regular_font = ImageFont.load_default()

        # 5. Inner Thumbnail
        thumb_inner = base.resize((THUMB_W, THUMB_H), Image.Resampling.LANCZOS)
        tmask = Image.new("L", thumb_inner.size, 0)
        ImageDraw.Draw(tmask).rounded_rectangle((0, 0, THUMB_W, THUMB_H), radius=20, fill=255)
        bg.paste(thumb_inner, (THUMB_X, THUMB_Y), tmask)

        # 6. Clean Text Rendering (Arabic Compatible)
        final_title = fix_ar(trim_to_width(title, title_font, MAX_TITLE_WIDTH))
        final_views = fix_ar(f"Channel: {channel}  |  Views: {views}")

        draw.text((TITLE_X, TITLE_Y), final_title, fill="black", font=title_font)
        draw.text((META_X, META_Y), final_views, fill=(40, 40, 40), font=regular_font)

        # 7. Progress Bar
        draw.line([(BAR_X, BAR_Y), (BAR_X + BAR_RED_LEN, BAR_Y)], fill="#FF0000", width=6)
        draw.line([(BAR_X + BAR_RED_LEN, BAR_Y), (BAR_X + BAR_TOTAL_LEN, BAR_Y)], fill="#555555", width=5)
        draw.ellipse([(BAR_X + BAR_RED_LEN - 8, BAR_Y - 8), (BAR_X + BAR_RED_LEN + 8, BAR_Y + 8)], fill="#FF0000")

        # Time Labels
        draw.text((BAR_X, BAR_Y + 15), "00:00", fill="black", font=regular_font)
        end_color = "#FF0000" if is_live else "black"
        draw.text((BAR_X + BAR_TOTAL_LEN - (80 if is_live else 60), BAR_Y + 15), duration_text, fill=end_color, font=regular_font)

        # 8. Draw Player Icons using Pillow (No external images needed)
        draw_player_icons(draw, center_x=1280//2, center_y=BAR_Y + 65)

        # 9. Save final image
        bg.save(cache_path, quality=95, optimize=True)
        return cache_path

    except Exception as e:
        print(f"Thumb Gen Error: {e}")
        return DEFAULT_THUMB
    finally:
        # تنظيف مساحة السيرفر بمسح الصورة المؤقتة
        if thumb_path != DEFAULT_THUMB and os.path.exists(thumb_path):
            try: os.remove(thumb_path)
            except: pass

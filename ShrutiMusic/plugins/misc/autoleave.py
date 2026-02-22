# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
# All rights reserved. Contact: badboy809075@gmail.com
# System Upgraded (2026): Modern Auto-Leave Logic, PyTgCalls v3.x Compatible, Arabic Control

import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

import config
from ShrutiMusic import app
from ShrutiMusic.core.call import Nand, autoend
from ShrutiMusic.utils.database import get_client, is_active_chat, is_autoend

# متغير للتحكم في حالة المغادرة (الافتراضي: متوقف)
AUTO_LEAVE_STATE = False

# تحويل OWNER_ID لقائمة لتجنب أخطاء الفلاتر
SUDO_USERS = config.OWNER_ID if isinstance(config.OWNER_ID, list) else [config.OWNER_ID]

async def auto_leave():
    # نستخدم المتغير global للوصول لحالة التشغيل
    global AUTO_LEAVE_STATE
    
    # الاعتماد على وقت المغادرة من ملف الكونفيج أو وضع افتراضي (15 دقيقة = 900 ثانية)
    leave_time = getattr(config, "AUTO_LEAVE_ASSISTANT_TIME", 900)
    
    while not await asyncio.sleep(leave_time):
        # إذا كانت المغادرة متوقفة، تخطي الدورة الحالية
        if not AUTO_LEAVE_STATE:
            continue

        from ShrutiMusic.core.userbot import assistants

        for num in assistants:
            client = await get_client(num)
            left = 0
            try:
                async for i in client.get_dialogs():
                    if i.chat.type in [
                        ChatType.SUPERGROUP,
                        ChatType.GROUP,
                        ChatType.CHANNEL,
                    ]:
                        # الحفاظ على الجروبات المحمية الخاصة بك
                        if (
                            i.chat.id != config.LOG_GROUP_ID
                            and i.chat.id != -1002169072536
                            and i.chat.id != -1002499911479
                            and i.chat.id != -1002252855734
                        ):
                            if left == 20:
                                continue
                            if not await is_active_chat(i.chat.id):
                                try:
                                    await client.leave_chat(i.chat.id)
                                    left += 1
                                except:
                                    continue
            except:
                pass


asyncio.create_task(auto_leave())


async def auto_end():
    # الفحص كل 5 ثواني بدل 60 ثانية لسرعة الاستجابة
    while not await asyncio.sleep(5):
        ender = await is_autoend()
        if not ender:
            continue
            
        # استخدام list() لتجنب خطأ (dictionary changed size during iteration)
        for chat_id in list(autoend.keys()):
            timer = autoend.get(chat_id)
            if not timer:
                continue
                
            # النظام الحديث: نعتمد على المؤقت اللي اتعمل في call.py بدل عد المستمعين المباشر
            if datetime.now() > timer:
                if not await is_active_chat(chat_id):
                    autoend.pop(chat_id, None)
                    continue
                    
                autoend.pop(chat_id, None)
                try:
                    await Nand.stop_stream(chat_id)
                except:
                    continue
                try:
                    # رسالة عربية أنيقة
                    await app.send_message(
                        chat_id,
                        "قام البوت بمغادرة المحادثة الصوتية تلقائيا لعدم وجود مستمعين"
                    )
                except:
                    continue


asyncio.create_task(auto_end())


# ==========================================
# أوامر التحكم في المغادرة التلقائية (عربي - بدون سلاش)
# ==========================================

# أمر التفعيل
@app.on_message(filters.command(["تفعيل المغادرة", "شغل المغادرة"], prefixes=["", "/", "!"]) & filters.user(SUDO_USERS))
async def enable_auto_leave(client, message: Message):
    global AUTO_LEAVE_STATE
    if AUTO_LEAVE_STATE:
        await message.reply_text("المغادرة التلقائية مفعلة بالفعل ✅")
    else:
        AUTO_LEAVE_STATE = True
        await message.reply_text("تم تفعيل المغادرة التلقائية للمساعد بنجاح 🚀")

# أمر الإيقاف
@app.on_message(filters.command(["ايقاف المغادرة", "وقف المغادرة", "تعطيل المغادرة"], prefixes=["", "/", "!"]) & filters.user(SUDO_USERS))
async def disable_auto_leave(client, message: Message):
    global AUTO_LEAVE_STATE
    if not AUTO_LEAVE_STATE:
        await message.reply_text("المغادرة التلقائية متوقفة بالفعل ⚠️")
    else:
        AUTO_LEAVE_STATE = False
        await message.reply_text("تم إيقاف المغادرة التلقائية للمساعد بنجاح 🛑")

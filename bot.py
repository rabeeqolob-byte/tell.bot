import os
import json
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from docx import Document

import zipfile

if not os.path.exists("data"):
    with zipfile.ZipFile("data.zip", 'r') as zip_ref:
        zip_ref.extractall("data")
        
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ TOKEN NOT FOUND")
    exit()

# 👑 ايديك
ADMIN_ID = 6307427506

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = "users.json"

print("✅ Bot started...")
print("📂 DATA PATH:", DATA_PATH)

# ------------------ المستخدمين ------------------

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# ------------------ تنظيف النص ------------------

def clean_text(text):
    text = re.sub(r'[A-Za-z]', '', text)
    text = re.sub(r'[^؀-ۿ0-9\s\n.,!?؟،]', '', text)
    return text

# ------------------ قراءة docx ------------------

def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

# ------------------ تقسيم النص ------------------

def split_text(text, size=4000):
    return [text[i:i+size] for i in range(0, len(text), size)]

# ------------------ إنشاء الأزرار ------------------

def build_keyboard(path):
    keyboard = InlineKeyboardMarkup(row_width=2)

    try:
        items = sorted(os.listdir(path))
    except Exception as e:
        print("❌ ERROR reading folder:", e)
        return keyboard

    for item in items:
        full_path = os.path.join(path, item)

        if os.path.isdir(full_path):
            keyboard.insert(
                InlineKeyboardButton(
                    f"📂 {item}",
                    callback_data=f"dir|{full_path}"
                )
            )

        elif item.endswith(".docx") or item.endswith(".txt"):
            keyboard.insert(
                InlineKeyboardButton(
                    f"📄 {item}",
                    callback_data=f"file|{full_path}"
                )
            )

    # زر رجوع
    if path != DATA_PATH:
        parent = os.path.dirname(path)
        keyboard.add(
            InlineKeyboardButton("🔙 رجوع", callback_data=f"dir|{parent}")
        )

    return keyboard

# ------------------ start ------------------

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    print("📩 /start received")

    save_user(message.from_user.id)

    if message.from_user.id == ADMIN_ID:
        count = len(load_users())
        text = f"<b>👑 أهلاً بك</b>\n<b>👥 عدد المستخدمين: {count}</b>"
    else:
        text = "<b>📿 أهلاً بك في بوت الأدعية</b>"

    await message.answer(
        text,
        reply_markup=build_keyboard(DATA_PATH),
        parse_mode="HTML"
    )

# ------------------ اختبار (مهم) ------------------

@dp.message_handler()
async def test(message: types.Message):
    print("📩 message:", message.text)
    await message.answer("✅ البوت شغال")

# ------------------ الأزرار ------------------

@dp.callback_query_handler()
async def handle(callback: types.CallbackQuery):
    await callback.answer()

    try:
        action, path = callback.data.split("|", 1)
    except:
        await callback.message.answer("❌ خطأ")
        return

    if not os.path.exists(path):
        await callback.message.answer("❌ المسار غير موجود")
        return

    if action == "dir":
        await callback.message.edit_text(
            f"<b>📂 {os.path.basename(path) or 'الرئيسية'}</b>",
            reply_markup=build_keyboard(path),
            parse_mode="HTML"
        )

    elif action == "file":
        try:
            if path.endswith(".docx"):
                text = read_docx(path)

            elif path.endswith(".txt"):
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()

            else:
                await callback.message.answer("❌ ملف غير مدعوم")
                return

            text = clean_text(text)

            await bot.send_message(
                callback.from_user.id,
                f"<b>📄 {os.path.basename(path)}</b>",
                parse_mode="HTML"
            )

            for part in split_text(text):
                await bot.send_message(
                    callback.from_user.id,
                    f"<b>{part}</b>",
                    parse_mode="HTML"
                )

        except Exception as e:
            await callback.message.answer(f"❌ خطأ: {e}")

# ------------------ تشغيل ------------------

# ------------------ تشغيل ------------------

if __name__ == "__main__":
    import asyncio

    print("🚀 Starting bot...")

    # حذف أي جلسة قديمة
    asyncio.get_event_loop().run_until_complete(bot.delete_webhook())
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot) 
    
    # تشغيل البوت
    executor.start_polling(dp, skip_updates=True)
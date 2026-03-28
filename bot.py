import os
import json
import re
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from docx import Document
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ TOKEN NOT FOUND")
    exit()

# 👑 ايديك (من userinfobot)
ADMIN_ID = 6307427506

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_PATH = "data"
USERS_FILE = "users.json"

paths_map = {}

# ------------------ المستخدمين ------------------

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

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

# ------------------ إنشاء الأزرار ------------------

def build_keyboard(path):
    keyboard = InlineKeyboardMarkup(row_width=2)

    items = sorted(os.listdir(path))

    for item in items:
        full_path = os.path.join(path, item)

        key = str(uuid.uuid4())
        paths_map[key] = full_path

        if os.path.isdir(full_path):
            keyboard.insert(
                InlineKeyboardButton(f"📂 {item}", callback_data=f"dir|{key}")
            )

        elif item.endswith(".docx") or item.endswith(".txt"):
            keyboard.insert(
                InlineKeyboardButton(f"📄 {item}", callback_data=f"file|{key}")
            )

    # زر رجوع
    if path != DATA_PATH:
        parent = os.path.dirname(path)
        back_key = str(uuid.uuid4())
        paths_map[back_key] = parent

        keyboard.add(
            InlineKeyboardButton("🔙 رجوع", callback_data=f"dir|{back_key}")
        )

    return keyboard

# ------------------ start ------------------

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
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

# ------------------ الأزرار ------------------

@dp.callback_query_handler()
async def handle(callback: types.CallbackQuery):
    await callback.answer()

    try:
        action, key = callback.data.split("|")
    except:
        await callback.message.answer("❌ خطأ")
        return

    path = paths_map.get(key)

    if not path:
        await callback.message.answer("❌ المسار غير موجود")
        return

    # دخول مجلد
    if action == "dir":
        await callback.message.edit_text(
            f"<b>📂 {os.path.basename(path) or 'الرئيسية'}</b>",
            reply_markup=build_keyboard(path),
            parse_mode="HTML"
        )

    # فتح ملف
    elif action == "file":
        if os.path.exists(path):
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

                for i in range(0, len(text), 4000):
                    await bot.send_message(
                        callback.from_user.id,
                        f"<b>{text[i:i+4000]}</b>",
                        parse_mode="HTML"
                    )

            except Exception as e:
                await callback.message.answer(f"❌ خطأ: {e}")
        else:
            await callback.message.answer("❌ الملف غير موجود")

# ------------------ تشغيل ------------------
if __name__ == "__main__":
    import asyncio

    print("🚀 Starting bot...")

    asyncio.get_event_loop().run_until_complete(bot.delete_webhook())

    executor.start_polling(dp, skip_updates=True)

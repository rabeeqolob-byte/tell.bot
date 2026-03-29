import os
import json
import re
import asyncio
import zipfile
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from docx import Document

# ------------------ إعدادات ------------------

DATA_PATH = "data"
USERS_FILE = "users.json"
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 6307427506

if not TOKEN:
    print("❌ TOKEN NOT FOUND")
    exit()

# ------------------ فك الضغط ------------------

if not os.path.exists(DATA_PATH):
    if os.path.exists("data.zip"):
        print("📦 Extracting data.zip...")
        with zipfile.ZipFile("data.zip", 'r') as zip_ref:
            zip_ref.extractall(DATA_PATH)

        # إصلاح data/data
        inner = os.listdir(DATA_PATH)
        if len(inner) == 1:
            inner_path = os.path.join(DATA_PATH, inner[0])
            if os.path.isdir(inner_path):
                for f in os.listdir(inner_path):
                    os.rename(
                        os.path.join(inner_path, f),
                        os.path.join(DATA_PATH, f)
                    )
                os.rmdir(inner_path)

print("📂 DATA PATH:", DATA_PATH)
print("📄 Files:", os.listdir(DATA_PATH) if os.path.exists(DATA_PATH) else "❌ NOT FOUND")

# ------------------ البوت ------------------

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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

# ------------------ الكيبورد ------------------

def build_keyboard(path):
    keyboard = InlineKeyboardMarkup(row_width=2)

    try:
        items = sorted(os.listdir(path))
    except:
        return keyboard

    for item in items:
        full_path = os.path.join(path, item)

        if os.path.isdir(full_path):
            keyboard.insert(
                InlineKeyboardButton(
                    f"📂 {item}",
                    callback_data=f"dir|{item}"
                )
            )

        elif item.endswith(".txt") or item.endswith(".docx"):
            keyboard.insert(
                InlineKeyboardButton(
                    f"📄 {item}",
                    callback_data=f"file|{item}"
                )
            )

    if path != DATA_PATH:
        keyboard.add(
            InlineKeyboardButton("🔙 رجوع", callback_data="back")
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

# ------------------ مسارات المستخدمين ------------------

user_paths = {}

# ------------------ الأزرار ------------------

@dp.callback_query_handler()
async def handle(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    data = callback.data

    if user_id not in user_paths:
        user_paths[user_id] = DATA_PATH

    current_path = user_paths[user_id]

    # رجوع
    if data == "back":
        current_path = os.path.dirname(current_path)
        if current_path == "" or current_path == ".":
            current_path = DATA_PATH

    else:
        try:
            action, name = data.split("|")
        except:
            await callback.message.answer("❌ خطأ")
            return

        new_path = os.path.join(current_path, name)

        if action == "dir":
            if os.path.isdir(new_path):
                current_path = new_path
            else:
                await callback.message.answer("❌ المجلد غير موجود")
                return

        elif action == "file":
            try:
                if new_path.endswith(".docx"):
                    text = read_docx(new_path)
                else:
                    with open(new_path, "r", encoding="utf-8") as f:
                        text = f.read()

                text = clean_text(text)

                await bot.send_message(
                    user_id,
                    f"<b>📄 {name}</b>",
                    parse_mode="HTML"
                )

                for part in split_text(text):
                    await bot.send_message(
                        user_id,
                        f"<b>{part}</b>",
                        parse_mode="HTML"
                    )

                return

            except Exception as e:
                await callback.message.answer(f"❌ خطأ: {e}")
                return

    user_paths[user_id] = current_path

    await callback.message.edit_text(
        f"<b>📂 {os.path.basename(current_path) or 'الرئيسية'}</b>",
        reply_markup=build_keyboard(current_path),
        parse_mode="HTML"
    )

# ------------------ تشغيل ------------------

async def main():
    print("🚀 Starting bot...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Bot started")

        await dp.start_polling()

    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

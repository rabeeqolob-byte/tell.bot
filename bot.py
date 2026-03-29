import os
import json
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from docx import Document

# ------------------ إعدادات ------------------

BASE_FOLDERS = ["data", "data1"]  # 🔥 مجلدين
USERS_FILE = "users.json"
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 6307427506

if not TOKEN:
    print("❌ TOKEN NOT FOUND")
    exit()

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

        # 🔥 تقصير الاسم داخل callback
        short_name = item[:40]

        if os.path.isdir(full_path):
            keyboard.insert(
                InlineKeyboardButton(
                    f"📂 {item}",
                    callback_data=f"dir|{short_name}"
                )
            )

        elif item.endswith(".txt") or item.endswith(".docx"):
            keyboard.insert(
                InlineKeyboardButton(
                    f"📄 {item}",
                    callback_data=f"file|{short_name}"
                )
            )

    keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="back"))

    return keyboard

# ------------------ start ------------------

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    save_user(message.from_user.id)

    keyboard = InlineKeyboardMarkup(row_width=2)

    # 🔥 عرض المجلدين الأساسيين
    for folder in BASE_FOLDERS:
        if os.path.exists(folder):
            keyboard.add(
                InlineKeyboardButton(
                    f"📂 {folder}",
                    callback_data=f"root|{folder}"
                )
            )

    await message.answer(
        "<b>📿 اختر القسم</b>",
        reply_markup=keyboard,
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
        user_paths[user_id] = ""

    current_path = user_paths[user_id]

    # دخول مجلد رئيسي
    if data.startswith("root|"):
        folder = data.split("|")[1]
        current_path = folder

    # رجوع
    elif data == "back":
        current_path = os.path.dirname(current_path)

        if current_path == "":
            # رجوع للرئيسية
            keyboard = InlineKeyboardMarkup()
            for folder in BASE_FOLDERS:
                keyboard.add(
                    InlineKeyboardButton(
                        f"📂 {folder}",
                        callback_data=f"root|{folder}"
                    )
                )

            await callback.message.edit_text(
                "<b>📿 اختر القسم</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return

    else:
        try:
            action, name = data.split("|")
        except:
            await callback.message.answer("❌ خطأ")
            return

        # 🔥 نجيب الاسم الحقيقي من الملفات (حل مشكلة العربية)
        real_name = None
        for item in os.listdir(current_path):
            if item.startswith(name):
                real_name = item
                break

        if not real_name:
            await callback.message.answer("❌ الملف غير موجود")
            return

        new_path = os.path.join(current_path, real_name)

        # مجلد
        if action == "dir":
            current_path = new_path

        # ملف
        elif action == "file":
            try:
                if new_path.endswith(".docx"):
                    text = read_docx(new_path)
                else:
                    with open(new_path, "r", encoding="utf-8") as f:
                        text = f.read()

                text = clean_text(text)

                await bot.send_message(user_id, f"<b>📄 {real_name}</b>", parse_mode="HTML")

                for part in split_text(text):
                    await bot.send_message(user_id, f"<b>{part}</b>", parse_mode="HTML")

                return

            except Exception as e:
                await callback.message.answer(f"❌ خطأ: {e}")
                return

    user_paths[user_id] = current_path

    await callback.message.edit_text(
        f"<b>📂 {os.path.basename(current_path)}</b>",
        reply_markup=build_keyboard(current_path),
        parse_mode="HTML"
    )

# ------------------ تشغيل ------------------

async def main():
    print("🚀 Starting bot...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling()

    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

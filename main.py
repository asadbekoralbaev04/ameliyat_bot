# =========================================
# File: main.py
# =========================================

import asyncio
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ContentType,
)
from aiogram.filters import Command
from aiogram import F
import os

# =========================
# BOT SOZLAMALARI
BOT_TOKEN = "8382037003:AAEj6c23EtMLYOeeftwRnWvQY_RaxmF9vPw"
USTOZ_IDS = {
    1122869478,
    675336132,
    8316249416
}
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# JSON fayl
# File: telegram_bot/students.json
@dp.message(Command("students"))
async def show_groups_to_teacher(message: types.Message):
    if message.from_user.id not in USTOZ_IDS : 
        return

    load_students()  # <<< SHU QATORNI QO‘SH

    await message.answer(
        "Kursni tanlang:", 
        reply_markup=courses_keyboard_for_teacher())

DATA_FILE = "students.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        students_data = json.load(f)
else:
    students_data = {}

# =========================
# MA'LUMOTLAR SAQLASH
DATA_FILE = "students.json"
students_data = {}

def load_students():
    global students_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            students_data = json.load(f)
    else:
        students_data = {}

def save_students():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(students_data, f, ensure_ascii=False, indent=4)

load_students()

# =========================
# TUGMALAR
location_button = KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)
keyboard_location = ReplyKeyboardMarkup(
    keyboard=[[location_button]],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Joylashuv tugmasini bosing..."
)

def courses_keyboard():
    courses = ["1-kurs", "2-kurs", "3-kurs", "4-kurs"]
    buttons = [[InlineKeyboardButton(text=c, callback_data=f"course:{c}")] for c in courses]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def courses_keyboard_for_teacher():
    courses = ["1-kurs", "2-kurs", "3-kurs", "4-kurs"]
    buttons = [[InlineKeyboardButton(text=c, callback_data=f"teacher_course:{c}")] for c in courses]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

STUDENT_GROUPS = [
    "Xalq sozandalari",
    "Torli asboblar",
    "Zarbli asboblar",
    "Cholg‘u asboblari",
    "Vokal san’ati",
    "Ansambl",
    "Dirijyorlik",
]

def student_groups_keyboard():
    buttons = [
        [InlineKeyboardButton(text=group, callback_data=f"select_group:{group}")]
        for group in STUDENT_GROUPS
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def groups_keyboard_for_teacher():
    groups = sorted({s["group"] for s in students_data.values() if "group" in s})
    
    buttons = []
    
    if groups:
        buttons = [[InlineKeyboardButton(text=g, callback_data=f"group:{g}")] for g in groups]
    
    # Orqaga tugmasini har doim qo'shamiz
    buttons.append([
        InlineKeyboardButton(text="⬅️ Orqaga kurslarga", callback_data="back_to_courses")
    ])
    
    if not groups:
        buttons.insert(0, [InlineKeyboardButton(text="Hozircha guruh yo‘q", callback_data="no_action")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def students_keyboard_for_teacher(group: str):
    buttons = []
    for uid, s in students_data.items():
        if s.get("group") == group:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{s.get('name', '?')} {s.get('surname', '?')}",
                    callback_data=f"student:{uid}"
                )
            ])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_to_group:{group}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# =========================
# /start
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    print(f"[DEBUG] /start bosildi. User ID: {user_id} | USTOZ_IDS: {USTOZ_IDS}")

    if user_id in USTOZ_IDS:
        print("[DEBUG] Ustoz sifatida tanildi!")
        buttons = [[InlineKeyboardButton(text="📚 Talabalar ro‘yxati", callback_data="ustoz_students")]]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Assalomu alaykum, ustoz! 😊", reply_markup=kb)
        return

    # Talaba qismi – BU YERNI TO‘LIQ VA ISHONCHLI QILAMIZ
    print(f"[DEBUG] Talaba sifatida tanildi: {user_id}")
    
    user_id_str = str(user_id)
    if user_id_str in students_data:
        print(f"[DEBUG] Eski ma'lumot o'chirildi: {user_id_str}")
        students_data.pop(user_id_str)
        save_students()

    # Kurs tanlash tugmalari – BU MUHIM QATOR
    await message.answer(
        "Assalomu alaykum!\nKursingizni tanlang:",
        reply_markup=courses_keyboard()  # ← 1-kurs, 2-kurs tugmalari shu yerda chiqadi
    )

@dp.callback_query(F.data.startswith("course:"))
async def process_course(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    course = callback.data.split(":", 1)[1]

    print(f"[DEBUG] Kurs tanlandi: {course} | User: {user_id}")

    students_data[user_id] = students_data.get(user_id, {})
    students_data[user_id]["course"] = course
    save_students()

    await callback.message.edit_text(f"Kurs tanlandi: {course}\n\nIsmingizni yozing:")
    await callback.answer()
# =========================
# Ism → Familiya → Guruh
@dp.message(F.text)
async def handle_name(message: types.Message):
    if message.from_user.id in USTOZ_IDS :
        return

    user_id = str(message.from_user.id)
    user = students_data.get(user_id, {})

    if "name" not in user:
        user["name"] = message.text.strip()
        students_data[user_id] = user
        save_students()
        await message.answer("Familiyangizni yozing:")
        return

    if "surname" not in user:
        user["surname"] = message.text.strip()
        students_data[user_id] = user
        save_students()

        # Familiyadan keyin guruh tugmalarini chiqaramiz
        kb = student_groups_keyboard()
        await message.answer("Guruhingizni tanlang:", reply_markup=kb)
        return

    if "group" not in user:
        user["group"] = message.text.strip()
        students_data[user_id] = user
        save_students()
        await message.answer("Endi joylashuvingizni yuboring:", reply_markup=keyboard_location)
        return

# =========================
# Location
@dp.message(F.content_type == ContentType.LOCATION)
async def location_handler(message: types.Message):
    if message.from_user.id in USTOZ_IDS :
        return

    user_id = str(message.from_user.id)
    user = students_data.get(user_id)

    if not user or "group" not in user:
        await message.answer("Avval /start bosing va ma'lumotlarni to'ldiring.")
        return

    tz = ZoneInfo("Asia/Tashkent")

    user["lat"] = message.location.latitude
    user["lon"] = message.location.longitude
    user["location_time"] = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    save_students()

    await message.answer("✅ Joylashuv saqlandi, endi rasm yuboring:")

# =========================
# Photo
@dp.message(F.content_type == ContentType.PHOTO)
async def photo_handler(message: types.Message):
    if message.from_user.id in USTOZ_IDS:
        return

    user_id = str(message.from_user.id)
    user = students_data.get(user_id)

    if not user or "lat" not in user:
        await message.answer("Avval joylashuv yuboring.")
        return

    tz = ZoneInfo("Asia/Tashkent")

    photo = message.photo[-1]
    file_id = photo.file_id

    user["photo_file_id"] = file_id
    user["photo_time"] = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    caption = (
        f"👤 F.I.O: {user.get('name', '?')} {user.get('surname', '?')}\n"
        f"📚 Kurs: {user.get('course', 'tanlanmagan')}\n"
        f"🎓 Guruh: {user.get('group', 'N/A')}\n"
        f"🕒 Joylashuv vaqti: {user.get('location_time', 'N/A')}\n"
        f"🕒 Rasm vaqti: {user.get('photo_time', 'N/A')}"
    )

    # Barcha ustozlarga yuborish (loop bilan)
    for teacher_id in USTOZ_IDS:
        try:
            sent_photo = await bot.send_photo(
                chat_id=teacher_id,
                photo=file_id,
                caption=caption
            )
            # message_id ni saqlash (oxirgi ustozniki saqlanadi yoki dict qilishingiz mumkin)
            user["ustoz_photo_msg_id"] = sent_photo.message_id
            print(f"Rasm {teacher_id} ga yuborildi")
        except Exception as e:
            print(f"Ustoz {teacher_id} ga rasm yuborishda xato: {e}")

        if "lat" in user and "lon" in user:
            try:
                sent_loc = await bot.send_location(
                    chat_id=teacher_id,
                    latitude=user["lat"],
                    longitude=user["lon"]
                )
                user["ustoz_location_msg_id"] = sent_loc.message_id
                print(f"Joylashuv {teacher_id} ga yuborildi")
            except Exception as e:
                print(f"Ustoz {teacher_id} ga joylashuv yuborishda xato: {e}")

    save_students()
    await message.answer("✅ Ma’lumotlaringiz ustozlarga yuborildi! Rahmat.")
# =========================
# USTOZ PANELI

@dp.message(Command("students"))
async def show_groups_to_teacher(message: types.Message):
    if message.from_user.id not in USTOZ_IDS :
        return

    load_students()

    await message.answer(
        "Kursni tanlang:",
        reply_markup=courses_keyboard_for_teacher()
    )

@dp.callback_query(F.data.startswith("teacher_course:"))
async def show_groups_by_course(callback: types.CallbackQuery):
    if callback.from_user.id not in USTOZ_IDS :
        await callback.answer("Ruxsat yo‘q", show_alert=True)
        return

    course = callback.data.split(":", 1)[1]

    groups = sorted(set(
        s["group"] for s in students_data.values()
        if s.get("course") == course and "group" in s
    ))

    if not groups:
        text = f"{course} kursida guruh yo‘q."
    else:
        text = f"{course} kursidagi guruhlar:"

    buttons = [[InlineKeyboardButton(text=g, callback_data=f"group:{g}")] for g in groups]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga kurslarga", callback_data="back_to_courses")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except:
        await callback.message.delete()
        await bot.send_message(callback.from_user.id, text, reply_markup=kb)

    await callback.answer()

@dp.callback_query(F.data == "back_to_courses")
async def back_to_courses(callback: types.CallbackQuery):
    if callback.from_user.id not in USTOZ_IDS :
        await callback.answer("Ruxsat yo‘q", show_alert=True)
        return

    text = "Kursni tanlang:"
    markup = courses_keyboard_for_teacher()

    try:
        await callback.message.delete()
    except:
        pass

    await bot.send_message(
        callback.from_user.id,
        text,
        reply_markup=markup
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("group:"))
async def show_students_in_group(callback: types.CallbackQuery):
    group = callback.data.split(":", 1)[1]

    text = f"{group} guruhi talabalari:"
    markup = students_keyboard_for_teacher(group)

    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except:
        await callback.message.delete()
        await bot.send_message(callback.from_user.id, text, reply_markup=markup)

    await callback.answer()

@dp.callback_query(F.data.startswith("student:"))
async def show_student_details(callback: types.CallbackQuery):
    uid = callback.data.split(":", 1)[1]
    s = students_data.get(uid, {})
    course = s.get("course", "kurs tanlanmagan")

    text = (
        f"👤 {s.get('name', '?')} {s.get('surname', '?')}\n"
        f"📚 Kurs: {course}\n"
        f"🎓 Guruh: {s.get('group', 'N/A')}\n"
        f"🕒 Joylashuv vaqti: {s.get('location_time', 'N/A')}\n"
        f"🕒 Rasm vaqti: {s.get('photo_time', 'N/A')}"
    )

    buttons = [
    [InlineKeyboardButton(text="📍 Joylashuv", callback_data=f"loc:{uid}")],
    [InlineKeyboardButton(text="🖼 Rasm", callback_data=f"photo:{uid}")],
    [InlineKeyboardButton(
        text="⬅️ Orqaga",
        callback_data=f"back_to_group:{s.get('group', '')}:{uid}"      )],
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except:
        await callback.message.delete()
        await bot.send_message(callback.from_user.id, text, reply_markup=kb)

    await callback.answer()

@dp.callback_query(F.data.startswith("loc:"))
async def show_location(callback: types.CallbackQuery):
    uid = callback.data.split(":", 1)[1]
    s = students_data.get(uid, {})
    
    if "lat" in s and "lon" in s:
        await bot.send_location(callback.from_user.id, s["lat"], s["lon"])
    else:
        await bot.send_message(callback.from_user.id, "Joylashuv ma'lumoti topilmadi.")
    await callback.answer()

@dp.callback_query(F.data.startswith("photo:"))
async def show_photo(callback: types.CallbackQuery):
    uid = callback.data.split(":", 1)[1]
    print(f"Rasm so'raldi, uid: {uid}")
    s = students_data.get(uid, {})
    print(f"Talaba ma'lumotlari: {s}")

    if "photo_file_id" not in s:
        await bot.send_message(callback.from_user.id, "Rasm topilmadi.")
        await callback.answer()
        return

    print(f"File ID ishlatilmoqda: {s['photo_file_id']}")
    
    buttons = [[
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data=f"back_to_group:{s.get('group', '')}:{uid}"   # <-- shu yerga ham
        )
    ]]    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await bot.send_photo(callback.from_user.id, s["photo_file_id"], reply_markup=kb)
        print("Rasm muvaffaqiyatli yuborildi")
    except Exception as e:
        print(f"Rasm yuborish xatosi: {str(e)}")
        await bot.send_message(callback.from_user.id, f"Rasmni yuborib bo'lmadi: {str(e)}")

    await callback.answer()

@dp.callback_query(F.data == "ustoz_students")
async def ustoz_students_tugmasi(callback: types.CallbackQuery):
    if callback.from_user.id not in USTOZ_IDS:
        await callback.answer("Ruxsat yo‘q", show_alert=True)
        return

    load_students()

    try:
        await callback.message.edit_text(
            "Kursni tanlang:",
            reply_markup=courses_keyboard_for_teacher()
        )
    except Exception as e:
        print("[DEBUG] Kurs menyusini edit qilishda xato:", str(e))
        await callback.message.answer(
            "Kursni tanlang:",
            reply_markup=courses_keyboard_for_teacher()
        )

    await callback.answer()

@dp.callback_query(F.data.startswith("back_to_group:"))
async def back_to_group(callback: types.CallbackQuery):
    if callback.from_user.id not in USTOZ_IDS :
        await callback.answer("Ruxsat yo‘q", show_alert=True)
        return

    parts = callback.data.split(":", 2)  # back_to_group:group_name:uid
    if len(parts) < 3:
        group_name = parts[1].strip()
        uid = None
    else:
        group_name = parts[1].strip()
        uid = parts[2].strip()

    # Kursni topish
    course = None
    for s in students_data.values():
        if s.get("group") == group_name and "course" in s:
            course = s["course"]
            break

    if not course:
        await callback.answer("Kurs topilmadi", show_alert=True)
        return

    # ==================== O'CHIRISH QISMI ====================
    if uid and uid in students_data:
        user_data = students_data[uid]
        for key in ["ustoz_photo_msg_id", "ustoz_location_msg_id"]:
            if key in user_data:
                try:
                    await bot.delete_message(USTOZ_IDS , user_data[key])
                    del user_data[key]  # saqlangan ID ni tozalash
                except Exception as e:
                    print(f"O'chirish xatosi {key}: {e}")
        save_students()

    # ==================== Guruhlar ro'yxatini ko'rsatish ====================
    groups = sorted(set(
        s["group"] for s in students_data.values()
        if s.get("course") == course and "group" in s
    ))

    text = f"{course} kursidagi guruhlar:"
    if not groups:
        text = f"{course} kursida guruh yo‘q."

    buttons = [[InlineKeyboardButton(text=g, callback_data=f"group:{g}")] for g in groups]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga kurslarga", callback_data="back_to_courses")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except:
        await callback.message.delete()
        await bot.send_message(callback.from_user.id, text, reply_markup=kb)
        
    await callback.answer()

@dp.callback_query(F.data == "back_to_courses")
async def back_to_courses(callback: types.CallbackQuery):
    if callback.from_user.id not in USTOZ_IDS :
        await callback.answer("Ruxsat yo‘q", show_alert=True)
        return

    text = "Kursni tanlang:"
    markup = courses_keyboard_for_teacher()

    try:
        await callback.message.edit_text(text=text, reply_markup=markup)
    except Exception as e:
        print("back_to_courses edit xatosi:", str(e))

    await callback.answer()

@dp.callback_query(F.data.startswith("select_group:"))
async def process_group_selection(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    group = callback.data.split(":", 1)[1]

    if user_id not in students_data:
        await callback.message.edit_text("Ma'lumot topilmadi. /start dan boshlang.")
        await callback.answer()
        return

    students_data[user_id]["group"] = group
    save_students()

    # Yangi matn bilan edit qilamiz (bu muhim – matn o‘zgarishi kerak)
    new_text = (
        f"✅ Tanlangan guruh: **{group}**\n\n"
        f"Ism: {students_data[user_id].get('name', '?')}\n"
        f"Familiya: {students_data[user_id].get('surname', '?')}\n\n"
        "Endi joylashuvingizni yuboring 👇\n"
        "(Pastdagi tugmani bosing)"
    )

    await callback.message.edit_text(
        new_text,
        parse_mode="Markdown"
    )

    # Agar eski reply_markup bor bo‘lsa va u None emas bo‘lsa — tozalaymiz
    # Lekin xato chiqmasligi uchun try/except ichida
    try:
        if callback.message.reply_markup is not None:
            await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print("Edit markup xatosi (ehtimol allaqachon None):", str(e))
        # Bu muhim emas, davom etamiz

    # Joylashuv tugmasini alohida xabar bilan chiqaramiz
    await bot.send_message(
        callback.from_user.id,
        "📍 Pastdagi tugmani bosing:",
        reply_markup=keyboard_location
    )

    await callback.answer("Guruh saqlandi!")

# =========================
# BOTNI ISHGA TUSHIRISH
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


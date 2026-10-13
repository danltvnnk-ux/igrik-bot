import os
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

import datetime
import sqlite3
from zoneinfo import ZoneInfo
from threading import Thread
from flask import Flask
import telebot
from telebot import types, apihelper

# --- НАСТРОЙКИ ---
TOKEN = "8971543598:AAGzc-WcirORCu0t0oj_l2rpJLYmn7EE8SY"

# Список Telegram ID администраторов (первый в списке получит уведомление об упавшем боте)
ADMINS = [6969053096, 5956780231]

# Настройка часового пояса Беларуси (UTC+3)
BY_TZ = ZoneInfo("Europe/Minsk")

# Принудительно отключаем прокси
apihelper.proxy = None

bot = telebot.TeleBot(TOKEN)

# --- FLASK СЕРВЕР ДЛЯ УДЕРЖАНИЯ БОДРСТВОВАНИЯ НА RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Игрик бот активен и работает 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Сбрасываем вебхук
try:
    bot.remove_webhook()
except Exception:
    pass

# Словарь состояний пользователей
user_states = {}

# --- РАСПИСАНИЕ ЭЗС 12-26 ---
SCHEDULE = {
    "Понедельник": [
        ["1 пара (08.30-10.10): Химия", "2 пара (10.20-12.00): Матем", "3 пара (12.40-14.20): Бел. яз", "7 урок (14.30-15.15): Воспит. час"],
        ["1 пара (08.30-10.10): Химия", "2 пара (10.20-12.00): Матем", "3 пара (12.40-14.20): Бел. яз", "7 урок (14.30-15.15): Воспит. час"]
    ],
    "Вторник": [
        ["1 пара (08.30-10.10): Биология", "2 пара (10.20-12.00): Рус. лит", "3 пара (12.40-14.20): Физика", "4 пара (14.30-16.10): МП"],
        ["1 пара (08.30-10.10): Биология", "2 пара (10.20-12.00): Рус. лит", "3 пара (12.40-14.20): Физика", "4 пара (14.30-16.10): МП"]
    ],
    "Среда": [
        # Индекс 0 (неделя без информатики / под чертой)
        ["1 пара (08.30-10.10): Матем", "2 пара (10.20-12.00): Бел. лит", "3 пара (12.40-14.20): География"],
        # Индекс 1 (неделя с информатикой)
        ["1 пара (08.30-10.10): Матем", "2 пара (10.20-12.00): Бел. лит", "3 пара (12.40-14.20): География", "4 пара (14.30-16.10): Информ"]
    ],
    "Четверг": [
        ["1 пара (08.30-10.10): Матем", "2 пара (10.20-12.00): Биология", "3 пара (12.40-14.20): Физ-ра", "7 урок (14.30-15.15): Инф. час", "8,9 урок (15.25-17.05): ДП"],
        ["1 пара (08.30-10.10): Физика", "2 пара (10.20-12.00): Ист. бел", "3 пара (12.40-14.20): Физ-ра", "7 урок (14.30-15.15): Инф. час", "8,9 урок (15.25-17.05): ДП"]
    ],
    "Пятница": [
        ["1 пара (08.30-10.10): Рус. яз", "2 пара (10.20-12.00): Матем", "3 пара (12.40-14.20): Информ"],
        ["1 пара (08.30-10.10): Рус. яз", "2 пара (10.20-12.00): Матем", "3 пара (12.40-14.20): Информ"]
    ],
    "Суббота": [
        ["1 пара (08.30-10.10): Ист. бел", "2 пара (10.20-12.00): Химия", "3 пара (12.20-14.00): География"],
        ["1 пара (08.30-10.10): Ист. бел", "2 пара (10.20-12.00): Химия", "3 пара (12.20-14.00): Физ-ра"]
    ],
    "Воскресенье": [[], []]
}

DAYS_ORDER = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

SUBJECT_ALIASES = {
    "математика": "Матем",
    "матем": "Матем",
    "матеша": "Матем",
    "информатика": "Информ",
    "информ": "Информ",
    "физическая культура": "Физ-ра",
    "физра": "Физ-ра",
    "физ-ра": "Физ-ра",
    "русский язык": "Рус. яз",
    "рус яз": "Рус. яз",
    "рус. яз": "Рус. яз",
    "русский": "Рус. яз",
    "русская литература": "Рус. лит",
    "рус лит": "Рус. лит",
    "рус. лит": "Рус. лит",
    "белорусский язык": "Бел. яз",
    "бел яз": "Бел. яз",
    "бел. яз": "Бел. яз",
    "белорусская литература": "Бел. лит",
    "бел лит": "Бел. лит",
    "бел. лит": "Бел. лит",
    "история беларуси": "Ист. бел",
    "ист бел": "Ист. бел",
    "ист. бел": "Ист. бел",
    "биология": "Биология",
    "химия": "Химия",
    "физика": "Физика",
    "география": "География",
    "мп": "МП",
    "дп": "ДП"
}

MENU_BUTTONS = [
    "📅 На сегодня", "📅 На завтра", "📋 Расписание на неделю",
    "🔍 Следующий предмет", "📝 Домашнее задание", "✍️ Записать дз",
    "⚙️ Админ-панель", "/start"
]

DB_FILE = "bot_data.db"


# --- РАБОТА С БАЗОЙ ДАННЫХ SQLITE ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            date_key TEXT,
            subject TEXT,
            task TEXT,
            PRIMARY KEY (date_key, subject)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_overrides (
            date_key TEXT PRIMARY KEY,
            lessons TEXT
        )
    """)

    conn.commit()
    conn.close()


def db_save_homework(date_key, subject, task):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO homework (date_key, subject, task)
        VALUES (?, ?, ?)
        ON CONFLICT(date_key, subject) DO UPDATE SET task=excluded.task
    """, (date_key, subject, task))
    conn.commit()
    conn.close()


def db_get_homework_for_date(date_key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT subject, task FROM homework WHERE date_key = ?", (date_key,))
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def db_get_all_homework():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT date_key, subject, task FROM homework")
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for date_key, subject, task in rows:
        if date_key not in result:
            result[date_key] = {}
        result[date_key][subject] = task
    return result


def db_save_schedule_override(date_key, lessons_list):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    lessons_str = "||".join(lessons_list)
    cursor.execute("""
        INSERT INTO schedule_overrides (date_key, lessons)
        VALUES (?, ?)
        ON CONFLICT(date_key) DO UPDATE SET lessons=excluded.lessons
    """, (date_key, lessons_str))
    conn.commit()
    conn.close()


def db_get_schedule_override(date_key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT lessons FROM schedule_overrides WHERE date_key = ?", (date_key,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return row[0].split("||")
    return None


init_db()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_now():
    return datetime.datetime.now(BY_TZ)


def normalize_subject_name(raw_name):
    clean_name = raw_name.strip().lower()
    return SUBJECT_ALIASES.get(clean_name, raw_name.strip().capitalize())


def extract_subject_and_task(user_text):
    clean_text = user_text.strip()
    words = clean_text.split()

    for phrase_len in (3, 2, 1):
        if len(words) >= phrase_len:
            candidate_subject = " ".join(words[:phrase_len]).lower()
            if candidate_subject in SUBJECT_ALIASES:
                normalized_subj = SUBJECT_ALIASES[candidate_subject]
                task_text = " ".join(words[phrase_len:]).strip()
                return normalized_subj, task_text

    parts = clean_text.split(maxsplit=1)
    if len(parts) >= 2:
        return normalize_subject_name(parts[0]), parts[1].strip()

    return normalize_subject_name(parts[0]), ""


def get_week_type():
    week_number = get_now().isocalendar()[1]
    # Исправленный расчёт чётности (без +1, чтобы неделя переключилась правильно)
    return 1 if week_number % 2 != 0 else 0


def parse_date_input(date_str):
    date_str = date_str.strip()
    now = get_now()
    try:
        if "." in date_str:
            parts = date_str.split(".")
            day = int(parts[0])
            month = int(parts[1])
            year = now.year
            return datetime.date(year, month, day)
        elif "-" in date_str:
            parts = date_str.split("-")
            return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return None
    return None


def get_day_schedule_for_date(target_date):
    date_key = target_date.strftime("%Y-%m-%d")
    override = db_get_schedule_override(date_key)
    if override is not None:
        return override

    day_name = DAYS_ORDER[target_date.weekday()]
    today = get_now().date()
    days_diff = (target_date - today).days
    today_index = today.weekday()

    shift_weeks = (today_index + days_diff) // 7
    current_week_type = get_week_type()
    target_week_type = (current_week_type + shift_weeks) % 2

    return SCHEDULE.get(day_name, [[], []])[target_week_type]


def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_today = types.KeyboardButton("📅 На сегодня")
    btn_tomorrow = types.KeyboardButton("📅 На завтра")
    btn_week = types.KeyboardButton("📋 Расписание на неделю")
    btn_next_subject = types.KeyboardButton("🔍 Следующий предмет")
    btn_homework = types.KeyboardButton("📝 Домашнее задание")
    btn_add_hw = types.KeyboardButton("✍️ Записать дз")

    markup.add(btn_today, btn_tomorrow)
    markup.add(btn_week, btn_next_subject)
    markup.add(btn_homework, btn_add_hw)

    if user_id in ADMINS:
        btn_admin = types.KeyboardButton("⚙️ Админ-панель")
        markup.add(btn_admin)

    return markup


# --- ОБРАБОТЧИК ИНЛАЙН-КНОПОК АДМИНКИ ---
@bot.callback_query_handler(func=lambda call: True)
def callback_admin(call):
    if call.from_user.id not in ADMINS:
        bot.answer_callback_query(call.id, "У вас нет прав администратора!", show_alert=True)
        return

    if call.data == "admin_edit_schedule":
        user_states[call.from_user.id] = "waiting_for_admin_schedule_change"
        bot.send_message(
            call.message.chat.id,
            "✏️ **Изменение расписания на один день**\n\n"
            "Пришлите сообщение в формате:\n"
            "`Дата, предмет который нужно изменить - предмет на который менять`\n\n"
            "📌 *Пример:* `28.09, Матем - Физика`",
            parse_mode="Markdown"
        )
    elif call.data == "admin_edit_hw":
        user_states[call.from_user.id] = "waiting_for_admin_hw_change"
        bot.send_message(
            call.message.chat.id,
            "📝 **Изменение домашнего задания**\n\n"
            "Пришлите сообщение в формате:\n"
            "`Дата, предмет, изменённое дз`\n\n"
            "📌 *Пример:* `28.09, Рус. лит, Сделать №10`",
            parse_mode="Markdown"
        )
    bot.answer_callback_query(call.id)


# --- ОСНОВНОЙ ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ---
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_messages(message):
    text = message.text.strip() if message.text else ""
    user_id = message.from_user.id

    if text in MENU_BUTTONS:
        user_states.pop(user_id, None)

    state = user_states.get(user_id)

    if state == "waiting_for_subject":
        process_search_subject(message)
        return
    elif state == "waiting_for_hw":
        process_save_homework(message)
        return
    elif state == "waiting_for_admin_schedule_change" and user_id in ADMINS:
        process_admin_schedule_change(message)
        return
    elif state == "waiting_for_admin_hw_change" and user_id in ADMINS:
        process_admin_hw_change(message)
        return

    if text == "/start":
        bot.send_message(
            message.chat.id,
            "Привет! Я бот-помощник группы ЭЗС 12-26 «Игрик». Выберите нужный пункт меню:",
            reply_markup=get_main_keyboard(user_id)
        )

    elif text == "📅 На сегодня":
        today = get_now().date()
        day_name = DAYS_ORDER[today.weekday()]
        lessons = get_day_schedule_for_date(today)

        lessons_str = "\n".join([f"• {les}" for les in lessons]) if lessons else "Пар нет (выходной) 🎉"
        response = f"📅 **Расписание на сегодня ({day_name}, {today.strftime('%d.%m')})**\n\n{lessons_str}"
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

    elif text == "📅 На завтра":
        tomorrow = get_now().date() + datetime.timedelta(days=1)
        day_name = DAYS_ORDER[tomorrow.weekday()]
        lessons = get_day_schedule_for_date(tomorrow)

        lessons_str = "\n".join([f"• {les}" for les in lessons]) if lessons else "Пар нет (выходной) 🎉"
        response = f"📅 **Расписание на завтра ({day_name}, {tomorrow.strftime('%d.%m')})**\n\n{lessons_str}"
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

    elif text == "📋 Расписание на неделю":
        today = get_now().date()
        current_week_type = get_week_type()
        week_name = "Неделя 1 (над чертой)" if current_week_type == 0 else "Неделя 2 (под чертой)"

        bot.send_message(
            message.chat.id,
            f"📋 **Расписание группы ЭЗС 12-26**\nТекущая неделя: *{week_name}*\n(начиная с сегодняшнего дня):",
            parse_mode="Markdown"
        )

        for i in range(7):
            check_date = today + datetime.timedelta(days=i)
            day_name = DAYS_ORDER[check_date.weekday()]
            lessons = get_day_schedule_for_date(check_date)
            lessons_str = "\n".join([f"• {les}" for les in lessons]) if lessons else "Выходной 🎉"

            prefix = "🟢 Сегодня" if i == 0 else f"▫️ **{day_name} ({check_date.strftime('%d.%m')})**"
            day_msg = f"{prefix}:\n{lessons_str}"
            bot.send_message(message.chat.id, day_msg, parse_mode="Markdown")

        bot.send_message(
            message.chat.id,
            "Выберите дальнейшее действие в меню ниже 👇",
            reply_markup=get_main_keyboard(user_id)
        )

    elif text == "📝 Домашнее задание":
        now = get_now().date()
        tomorrow_date = now + datetime.timedelta(days=1)
        tomorrow_key = tomorrow_date.strftime("%Y-%m-%d")

        tomorrow_hw_dict = db_get_homework_for_date(tomorrow_key)
        if tomorrow_hw_dict:
            tomorrow_hw_text = "\n".join([f"• {subj}: {task}" for subj, task in tomorrow_hw_dict.items()])
        else:
            tomorrow_hw_text = "Домашнее задание на завтра еще не записано."

        day_tomorrow_name = DAYS_ORDER[tomorrow_date.weekday()]
        bot.send_message(
            message.chat.id,
            f"📝 **ДЗ на завтра ({day_tomorrow_name}, {tomorrow_date.strftime('%d.%m')}):**\n{tomorrow_hw_text}",
            parse_mode="Markdown"
        )

        all_hw = db_get_all_homework()
        week_hw_response = "📝 **ДЗ на неделю вперёд:**\n\n"
        has_hw = False
        for i in range(1, 8):
            d = now + datetime.timedelta(days=i)
            d_key = d.strftime("%Y-%m-%d")
            if d_key in all_hw and all_hw[d_key]:
                has_hw = True
                d_name = DAYS_ORDER[d.weekday()]
                tasks_str = ", ".join([f"{subj}: {task}" for subj, task in all_hw[d_key].items()])
                week_hw_response += f"▫️ **{d_name} ({d.strftime('%d.%m')}):** {tasks_str}\n"

        if not has_hw:
            week_hw_response += "На ближайшую неделю записей домашних заданий нет."

        bot.send_message(
            message.chat.id,
            week_hw_response,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(user_id)
        )

    elif text == "✍️ Записать дз":
        user_states[user_id] = "waiting_for_hw"
        bot.send_message(
            message.chat.id,
            "✍️ Напишите название предмета и текст домашнего задания.\n\n"
            "Пример: `рус лит прочитать стр 15` или `матем сделать №5`",
            reply_markup=get_main_keyboard(user_id),
            parse_mode="Markdown"
        )

    elif text == "🔍 Следующий предмет":
        user_states[user_id] = "waiting_for_subject"
        bot.send_message(
            message.chat.id,
            "📚 Напишите название предмета, который вас интересует:",
            reply_markup=get_main_keyboard(user_id)
        )

    elif text == "⚙️ Админ-панель" and user_id in ADMINS:
        inline_markup = types.InlineKeyboardMarkup(row_width=1)
        btn_schedule = types.InlineKeyboardButton("1️⃣ Изменить расписание (на 1 день)", callback_data="admin_edit_schedule")
        btn_hw = types.InlineKeyboardButton("2️⃣ Изменить ДЗ (на дату)", callback_data="admin_edit_hw")
        inline_markup.add(btn_schedule, btn_hw)

        bot.send_message(
            message.chat.id,
            "⚙️ **Панель администратора**\nВыберите действие, которое хотите выполнить:",
            parse_mode="Markdown",
            reply_markup=inline_markup
        )


# --- ВСПОМОГАТЕЛЬНАЯ ЛОГИКА ---
def process_search_subject(message):
    user_id = message.from_user.id
    raw_input = message.text.strip()
    user_states.pop(user_id, None)

    normalized_subj = normalize_subject_name(raw_input)
    target_subject = normalized_subj.lower()

    today = get_now().date()
    found_date = None
    found_lessons = None

    for i in range(1, 15):
        check_date = today + datetime.timedelta(days=i)
        day_lessons = get_day_schedule_for_date(check_date)
        day_lessons_lower = [les.lower() for les in day_lessons]

        if any(target_subject in les for les in day_lessons_lower):
            found_date = check_date
            found_lessons = day_lessons
            break

    markup = get_main_keyboard(user_id)

    if found_date:
        day_name = DAYS_ORDER[found_date.weekday()]
        schedule_text = "\n".join([f"• {item}" for item in found_lessons])

        bot.send_message(
            message.chat.id,
            f"✅ Ближайший следующий день: **{day_name} ({found_date.strftime('%d.%m')})**\n\nРасписание на этот день:\n{schedule_text}",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ К сожалению, этот предмет не найден в расписании на ближайшие две недели.",
            reply_markup=markup
        )


def process_save_homework(message):
    user_id = message.from_user.id
    text = message.text.strip()
    user_states.pop(user_id, None)

    markup = get_main_keyboard(user_id)

    normalized_subj, hw_text = extract_subject_and_task(text)

    if not hw_text:
        bot.send_message(
            message.chat.id,
            "❌ Неверный формат. Пожалуйста, укажите текст домашнего задания.\nПример: `рус лит прочитать стр 10`",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    target_subject_search = normalized_subj.lower()
    today = get_now().date()
    found_date = None

    for i in range(1, 15):
        check_date = today + datetime.timedelta(days=i)
        day_lessons = get_day_schedule_for_date(check_date)
        day_lessons_lower = [les.lower() for les in day_lessons]

        if any(target_subject_search in les for les in day_lessons_lower):
            found_date = check_date
            break

    if found_date:
        date_key = found_date.strftime("%Y-%m-%d")

        db_save_homework(date_key, normalized_subj, hw_text)

        day_name = DAYS_ORDER[found_date.weekday()]
        bot.send_message(
            message.chat.id,
            f"✅ ДЗ успешно записано и сохранено в базу!\n"
            f"📅 День: **{day_name} ({found_date.strftime('%d.%m')})**\n"
            f"📚 Предмет: **{normalized_subj}**\n"
            f"📝 Задание: {hw_text}",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Не удалось найти предмет **{normalized_subj}** в расписании на ближайшие две недели.",
            reply_markup=markup,
            parse_mode="Markdown"
        )


def process_admin_schedule_change(message):
    user_id = message.from_user.id
    text = message.text.strip()
    user_states.pop(user_id, None)
    markup = get_main_keyboard(user_id)

    try:
        parts = text.split(",")
        if len(parts) < 2:
            raise ValueError

        date_str = parts[0].strip()
        subject_pair = parts[1].strip()

        if "-" not in subject_pair:
            raise ValueError

        old_subj, new_subj = [s.strip() for s in subject_pair.split("-", 1)]
        new_subj_formatted = normalize_subject_name(new_subj)

        target_date = parse_date_input(date_str)
        if not target_date:
            bot.send_message(message.chat.id, "❌ Неверный формат даты! Используйте `ДД.ММ` (например `28.09`).", parse_mode="Markdown", reply_markup=markup)
            return

        current_lessons = list(get_day_schedule_for_date(target_date))
        if not current_lessons:
            bot.send_message(message.chat.id, f"❌ На дату {target_date.strftime('%d.%m')} нет занятий (выходной).", reply_markup=markup)
            return

        replaced = False
        new_lessons = []
        for les in current_lessons:
            if old_subj.lower() in les.lower():
                if ":" in les:
                    prefix = les.split(":")[0]
                    new_lessons.append(f"{prefix}: {new_subj_formatted}")
                else:
                    new_lessons.append(new_subj_formatted)
                replaced = True
            else:
                new_lessons.append(les)

        if replaced:
            date_key = target_date.strftime("%Y-%m-%d")

            db_save_schedule_override(date_key, new_lessons)

            bot.send_message(
                message.chat.id,
                f"✅ Расписание на **{target_date.strftime('%d.%m')}** успешно изменено и сохранено в базу!\n"
                f"Заменено: `{old_subj}` ➡️ `{new_subj_formatted}`",
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                f"❌ Предмет `{old_subj}` не найден в расписании на {target_date.strftime('%d.%m')}.",
                parse_mode="Markdown",
                reply_markup=markup
            )

    except Exception:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка формата!\nИспользуйте: `Дата, Старый Предмет - Новый Предмет`\n"
            "Пример: `28.09, Матем - Физика`",
            parse_mode="Markdown",
            reply_markup=markup
        )


def process_admin_hw_change(message):
    user_id = message.from_user.id
    text = message.text.strip()
    user_states.pop(user_id, None)
    markup = get_main_keyboard(user_id)

    try:
        parts = [p.strip() for p in text.split(",", 2)]
        if len(parts) < 3:
            raise ValueError

        date_str, subj_title, new_hw = parts[0], parts[1], parts[2]
        normalized_subj = normalize_subject_name(subj_title)

        target_date = parse_date_input(date_str)
        if not target_date:
            bot.send_message(message.chat.id, "❌ Неверный формат даты! Используйте `ДД.ММ` (например `28.09`).", parse_mode="Markdown", reply_markup=markup)
            return

        date_key = target_date.strftime("%Y-%m-%d")

        db_save_homework(date_key, normalized_subj, new_hw)

        bot.send_message(
            message.chat.id,
            f"✅ ДЗ на **{target_date.strftime('%d.%m')}** по предмету **{normalized_subj}** изменено и сохранено в базу!\n\n"
            f"📝 Новое задание: {new_hw}",
            parse_mode="Markdown",
            reply_markup=markup
        )

    except Exception:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка формата!\nИспользуйте: `Дата, Предмет, Изменённое ДЗ`\n"
            "Пример: `28.09, Рус. лит, Сделать №10`",
            parse_mode="Markdown",
            reply_markup=markup
        )


# --- ЗАПУСК БОТА С ЗАЩИТОЙ, FLASK И УВЕДОМЛЕНИЕМ ---
if __name__ == "__main__":
    print("Веб-сервер для удержания бодрствования запущен...")
    keep_alive()
    print("Бот «Игрик» запущен...")
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)
    except Exception as e:
        try:
            alert_msg = f"🚨 **Внимание! Бот «Игрик» упал с ошибкой!**\n\n`{str(e)}`"
            bot.send_message(ADMINS[0], alert_msg, parse_mode="Markdown")
        except Exception:
            pass
        raise e

from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import time
import re

TOKEN = "8399873866:AAF-K9_6ytC6Y6l4tbWEuxhY-U3xNToLDEo"

# ------------------- ПРАВИЛА -------------------
RULES_TEXT = """
📜 Правила чата:
1. Без мата
2. Без спама
3. Уважайте друг друга
"""

BAD_WORDS = [
    "сук", "бля", "пизд", "пидор", "еб", "уеб",
    "долбоеб", "мудак", "гондон", "шлюх",
    "чмо", "твар", "лох", "даун", "хуй"
]

REPLACE_MAP = {
    "0": "о", "1": "и", "3": "е", "4": "а", "5": "с",
    "@": "а", "$": "с", "!": "и",
    "p": "п", "x": "х", "y": "у", "e": "е",
    "a": "а", "o": "о", "c": "с", "k": "к"
}

last_messages = {}
violations = {}

# ------------------- ФУНКЦИИ -------------------

def is_flood(user_id):
    now = time.time()
    times = last_messages.get(user_id, [])
    times = [t for t in times if now - t < 5]
    times.append(now)
    last_messages[user_id] = times
    return len(times) > 5

def normalize(text):
    text = text.lower()
    for k, v in REPLACE_MAP.items():
        text = text.replace(k, v)
    return re.sub(r"[^а-яё]", "", text)

def check_antimat(user_id, text):
    clean = normalize(text)
    if any(w in clean for w in BAD_WORDS):
        violations[user_id] = violations.get(user_id, 0) + 1
        if violations[user_id] >= 2:
            violations[user_id] = 0
            return True
    return False

async def mute_user(chat_id, user_id, context):
    until = int(time.time()) + 30 * 60  # 30 минут
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        print(f"Мутим пользователя {user_id} в чате {chat_id} на 30 минут")
    except Exception as e:
        print("Ошибка мута:", e)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT)

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await update.message.reply_text(
            f"👋 Добро пожаловать, {user.first_name}!\n❗ В чате запрещены мат и спам"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id  # надежный chat_id

    # 🔹 Логируем для проверки
    print(f"Проверяем пользователя {user_id} в чате {chat_id}")

    text = update.message.text

    # --- Флуд ---
    if is_flood(user_id):
        print(f"Флуд! Мутим пользователя {user_id}")
        await update.message.reply_text("⚠️ Слишком много сообщений! Мут на 30 минут.")
        await mute_user(chat_id, user_id, context)
        return

    # --- Мат ---
    if check_antimat(user_id, text):
        print(f"Мат! Мутим пользователя {user_id}")
        await update.message.reply_text("🚫 Мат дважды подряд! Мут на 30 минут.")
        await mute_user(chat_id, user_id, context)
        return

# ------------------- ОСНОВНОЙ КОД -------------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("rules", rules))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен...")
app.run_polling()

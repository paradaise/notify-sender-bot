import telebot
import sys
import os
from tg_token import TOKEN

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Handlers
from app.handlers.base_handlers import register_base_handlers
from app.handlers.task_handlers import register_task_handlers
from app.handlers.group_handlers import register_group_handlers
from app.handlers.broadcast_handlers import register_broadcast_handlers

# --- Configuration ---
bot = telebot.TeleBot(TOKEN)

def load_trusted_users(filename="trusted_users.txt"):
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print(f"Warning: '{filename}' not found. No users will be trusted.")
        return []

TRUSTED_USERS = load_trusted_users()

# --- Register Handlers ---
register_base_handlers(bot, TRUSTED_USERS)
register_task_handlers(bot)
register_group_handlers(bot)
register_broadcast_handlers(bot)

# --- Fallback for any other text ---
@bot.message_handler(content_types=['text'])
def handle_other_text(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, используйте кнопки меню.")

if __name__ == '__main__':
    print("Bot is starting...")
    bot.polling(non_stop=True) 
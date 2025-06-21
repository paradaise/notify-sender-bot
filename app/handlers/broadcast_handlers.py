import threading
import time
from app.keyboards import keyboard, settings_menu
import app.state as state

def register_broadcast_handlers(bot):
    @bot.message_handler(commands=['start_notify'])
    def start_broadcast_command(message):
        if message.chat.type == 'private':
            start_sending(message, bot)

    @bot.message_handler(commands=['stop_notify'])
    def stop_broadcast_command(message):
        if message.chat.type == 'private':
            stop_sending(message, bot)

    @bot.message_handler(func=lambda message: message.text == '🐇Начать рассылку')
    def start_broadcast_handler(message):
        if message.chat.type == 'private':
            start_sending(message, bot)

    @bot.message_handler(func=lambda message: message.text == '⏹Остановить рассылку')
    def stop_broadcast_handler(message):
        if message.chat.type == 'private':
            stop_sending(message, bot)

def send_notice(bot):
    while not state.stop_event.is_set():
        try:
            msg = state.tasks.get("msg")
            groups = state.tasks.get("groups", [])
            delay_minutes = state.tasks.get("delay", 1)

            if not all([msg, groups, delay_minutes]):
                print("Broadcast stopped: task data is missing.")
                break 

            for group_id in groups:
                if state.stop_event.is_set():
                    return
                try:
                    bot.send_message(group_id, msg, parse_mode="html")
                    time.sleep(1) # Small delay to avoid API rate limits
                except Exception as e:
                    print(f"Error sending to {group_id}: {e}")

            state.stop_event.wait(delay_minutes * 60)
        except Exception as e:
            print(f"An error occurred in the broadcast thread: {e}")
            break

def start_sending(message, bot):
    if state.broadcast_thread and state.broadcast_thread.is_alive():
        bot.send_message(message.chat.id, '⚠️ Рассылка уже запущена!')
        return

    required_fields = ["msg", "delay", "groups"]
    if not all(state.tasks.get(field) for field in required_fields):
        bot.send_message(message.chat.id, '❌ Невозможно начать рассылку. Не все поля заполнены.\n\nНажмите "👀Посмотреть задачу", чтобы проверить.', reply_markup=keyboard(settings_menu))
        return

    state.stop_event.clear()
    state.broadcast_thread = threading.Thread(target=send_notice, args=(bot,), daemon=True)
    state.broadcast_thread.start()
    bot.send_message(message.chat.id, '✅ Рассылка успешно начата!', parse_mode="html")

def stop_sending(message, bot):
    if not (state.broadcast_thread and state.broadcast_thread.is_alive()):
        bot.send_message(message.chat.id, 'ℹ️ Рассылка и так не была запущена.')
        return

    state.stop_event.set()
    bot.send_message(message.chat.id, '✅ Рассылка остановлена!', parse_mode="html") 
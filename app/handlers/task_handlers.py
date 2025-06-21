import re
from telebot import types
from app.keyboards import keyboard, settings_menu, main_menu, edit_menu, back_menu
import app.state as state

def register_task_handlers(bot):
    @bot.message_handler(commands=['show_task'])
    def show_task_command(message):
        if message.chat.type == 'private':
            show_notify(message, bot)

    @bot.message_handler(func=lambda message: message.text == '⚡️Создать задачу')
    def create_task_start(message):
        if message.chat.type == 'private':
            bot.send_message(message.chat.id, "Введите текст сообщения, которое будет рассылаться.\n\nДля отмены введите /cancel", parse_mode="html")
            bot.register_next_step_handler(message, get_notify, bot)

    @bot.message_handler(func=lambda message: message.text == '👀Посмотреть задачу')
    def show_task(message):
        if message.chat.type == 'private':
            show_notify(message, bot)

    @bot.message_handler(func=lambda message: message.text == '📝Поменять текст')
    def change_text_start(message):
        if message.chat.type == 'private':
            msg = state.tasks.get("msg", "не задано")
            bot.send_message(message.chat.id, f"Текущий текст сообщения:\n\n<b>{msg}</b>", parse_mode="html")
            bot.send_message(message.chat.id, "Введите новый текст сообщения:", reply_markup=keyboard(back_menu))
            bot.register_next_step_handler(message, update_notify, bot)
            
    @bot.message_handler(func=lambda message: message.text == '⏰Поменять интервал')
    def change_interval_start(message):
        if message.chat.type == 'private':
            delay = state.tasks.get("delay", "не задано")
            bot.send_message(message.chat.id, f"Текущий интервал: <b>{delay}</b> минут.", parse_mode="html")
            bot.send_message(message.chat.id, "Введите новый интервал отправки (числом) в минутах:", reply_markup=keyboard(back_menu))
            bot.register_next_step_handler(message, update_delay, bot)


def get_notify(message, bot):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=keyboard(main_menu))
        return
    
    state.tasks['msg'] = message.text
    bot.send_message(message.chat.id, f'📝 Ваше сообщение для рассылки:\n\n<b>{message.text}</b>', parse_mode="html")
    bot.send_message(message.chat.id, "Теперь введите интервал отправки в минутах (только число).\n\nДля отмены введите /cancel", parse_mode="html")
    bot.register_next_step_handler(message, get_delay, bot)

def get_delay(message, bot):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=keyboard(main_menu))
        return
    try:
        delay = int(message.text)
        state.tasks['delay'] = delay
        bot.send_message(message.chat.id, f'⏱️ Ваш интервал рассылки: <b>{delay}</b> минут.', parse_mode="html")
        bot.send_message(message.chat.id, "Введите ID групп для рассылки, каждый с новой строки.\n(<i>Пример:</i> <code>-1234567890123</code>)\n\nДля отмены введите /cancel", parse_mode="html")
        bot.register_next_step_handler(message, get_links, bot)
    except ValueError:
        bot.send_message(message.chat.id, '❗️ Пожалуйста, укажите интервал числом в минутах. Например: <b>15</b>\n\nДля отмены введите /cancel', parse_mode="html")
        bot.register_next_step_handler(message, get_delay, bot)

def get_links(message, bot):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=keyboard(main_menu))
        return

    links = message.text.splitlines()
    if not links_checker(message, bot, links, 'get'):
        bot.send_message(message.chat.id, "Попробуйте еще раз или введите /cancel для отмены.", parse_mode="html")
        bot.register_next_step_handler(message, get_links, bot)
    else:
        state.tasks['groups'] = links
        create_task_finish(message.chat.id, bot)

def links_checker(message, bot, links:list, flag):
    if not links or not any(link.strip() for link in links):
        bot.send_message(message.chat.id, '❌ Список ID групп пуст. Пожалуйста, введите хотя бы один ID.')
        return False

    pattern = re.compile(r'^-\d+$')
    invalid_links = [link for link in links if not pattern.match(link)]

    if invalid_links:
        error_message = (
            '🚫 <b>Некорректный формат ID.</b>\n\n'
            'ID должен начинаться с «-» и содержать только цифры (например: <code>-1234567890</code>).\n\n'
            'Неверно указаны:\n' + 
            '\n'.join(f'• <code>{link}</code>' for link in invalid_links)
        )
        bot.send_message(message.chat.id, error_message, parse_mode="html")
        return False

    formatted_links = '\n'.join([f'• <code>{link}</code>' for link in links])
    
    if flag == 'get':
        success_message = f'✅ <b>ID групп для рассылки успешно добавлены:</b>\n\n{formatted_links}'
        bot.send_message(message.chat.id, success_message, parse_mode="html")
    elif flag == 'update':
        success_message = f'✅ <b>ID групп успешно обновлены:</b>\n\n{formatted_links}'
        bot.send_message(message.chat.id, success_message, parse_mode="html")
        bot.send_message(message.chat.id, "⚙️ Что хотите сделать дальше?", reply_markup=keyboard(settings_menu))
    return True

def create_task_finish(chat_id, bot):
    bot.send_message(chat_id, '✅ <b>Задача успешно создана!</b>', parse_mode="html")
    bot.send_message(chat_id, "⚙️ Теперь вы можете настроить её или запустить рассылку.", reply_markup=keyboard(settings_menu))

def update_notify(message, bot):
    if message.text == '🔙Назад':
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=keyboard(edit_menu))
        return
    state.tasks["msg"] = message.text
    bot.send_message(message.chat.id, f'Ваше новое сообщение для рассылки: <b>{message.text}</b>', parse_mode="html")
    bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=keyboard(edit_menu))

def update_delay(message, bot):
    if message.text == '🔙Назад':
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=keyboard(edit_menu))
        return
    try:
        delay = int(message.text)
        state.tasks["delay"] = delay
        bot.send_message(message.chat.id, f'Ваш новый интервал рассылки: <b>{delay}</b> минут', parse_mode="html")
        bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=keyboard(edit_menu))
    except ValueError:
        bot.send_message(message.chat.id, 'Укажите интервал отправки сообщения числом')
        bot.register_next_step_handler(message, update_delay, bot)

def get_channel_info(bot, channel_id):
    try:
        chat = bot.get_chat(channel_id)
        title = chat.title
        return f"• <b>{title}</b> (<code>{channel_id}</code>)"
    except Exception:
        return f"• Канал не найден (<code>{channel_id}</code>)"

def show_notify(message, bot):
    if not state.tasks:
        bot.send_message(message.chat.id, 
            'ℹ️ У вас еще нет созданных задач. Нажмите "⚡️Создать задачу", чтобы начать.', 
            reply_markup=keyboard(main_menu))
        return

    status = "не запущена"
    if state.broadcast_thread and state.broadcast_thread.is_alive():
        status = "работает"

    msg = state.tasks.get("msg", "<i>не задано</i>")
    delay = state.tasks.get("delay", "<i>не задано</i>")
    
    if "groups" in state.tasks and state.tasks["groups"]:
        group_infos = [get_channel_info(bot, group_id) for group_id in state.tasks["groups"]]
        groups_formatted = '\n'.join(group_infos)
    else:
        groups_formatted = "<i>не заданы</i>"

    task_details = (
        f'<b>Текущая задача:</b>\n\n'
        f'<b>Статус:</b> {status}\n\n'
        f'📝 <b>Сообщение:</b>\n{msg}\n\n'
        f'⏱️ <b>Интервал:</b> {delay} минут\n\n'
        f'🎯 <b>Каналы для рассылки:</b>\n{groups_formatted}'
    )
    bot.send_message(message.chat.id, task_details, parse_mode="html") 
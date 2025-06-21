import re
from telebot import types
from app.keyboards import keyboard, settings_menu, groups_edit_menu, edit_menu, back_menu
import app.state as state
from app.handlers.task_handlers import links_checker

def get_group_info(bot, group_id):
    try:
        chat = bot.get_chat(group_id)
        title = chat.title
        return f"<b>{title}</b> (<code>{group_id}</code>)"
    except Exception:
        return f"Канал не найден (<code>{group_id}</code>)"

def get_groups_list_text(bot, groups):
    if not groups:
        return "Текущий список каналов пуст."
    
    group_infos = [get_group_info(bot, group_id) for group_id in groups]
    
    return "<b>Текущий список каналов:</b>\n" + '\n'.join([f'{i+1}) {info}' for i, info in enumerate(group_infos)])

def register_group_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == '📋Поменять список групп')
    def change_groups_menu(message):
        if message.chat.type == 'private':
            bot.send_message(message.chat.id, "Выберите действие для списка каналов:", reply_markup=keyboard(groups_edit_menu))

    @bot.message_handler(func=lambda message: message.text == '➕Добавить группы')
    def add_groups_start(message):
        if message.chat.type == 'private':
            prompt_add_groups(message, bot)

    @bot.message_handler(func=lambda message: message.text == '➖Удалить группы')
    def delete_group_start(message):
        if message.chat.type == 'private':
            prompt_delete_group(message, bot)

    @bot.message_handler(func=lambda message: message.text == '📝Заменить список')
    def replace_groups_start(message):
        if message.chat.type == 'private':
            prompt_replace_groups(message, bot)

    @bot.message_handler(func=lambda message: message.text == '🔙Назад' and message.chat.type == 'private')
    def back_to_settings(message):
        bot.send_message(message.chat.id, "Выберите, что хотите изменить:", reply_markup=keyboard(edit_menu))

def prompt_replace_groups(message, bot):
    groups_text = get_groups_list_text(bot, state.tasks.get("groups", []))
    bot.send_message(message.chat.id, groups_text, parse_mode="html")
    
    replace_prompt = (
        "Введите построчно новые ID каналов для рассылки, чтобы полностью заменить текущий список.\n"
        "(<i>Пример:</i> <code>-1234567890123</code>)\n\n"
        "Или нажмите <b>🔙Назад</b> для отмены."
    )
    bot.send_message(message.chat.id, replace_prompt, parse_mode="html", reply_markup=keyboard(back_menu))
    bot.register_next_step_handler(message, update_links, bot)

def update_links(message, bot):
    if message.text == '🔙Назад' or message.text == '/cancel':
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=keyboard(groups_edit_menu))
        return
        
    links = message.text.splitlines()
    if links_checker(message, bot, links, 'update'):
        state.tasks["groups"] = links
        bot.send_message(message.chat.id, "✅ Список каналов успешно обновлен.", reply_markup=keyboard(groups_edit_menu))
    else:
        bot.send_message(message.chat.id, "Попробуйте еще раз или нажмите 🔙Назад для отмены.", parse_mode="html")
        bot.register_next_step_handler(message, update_links, bot)

def prompt_add_groups(message, bot):
    groups_text = get_groups_list_text(bot, state.tasks.get("groups", []))
    bot.send_message(message.chat.id, groups_text, parse_mode="html")
    
    add_prompt = (
        "Введите ID новых каналов, которые хотите добавить, каждый с новой строки.\n"
        "(<i>Пример:</i> <code>-1234567890123</code>)\n\n"
        "Или нажмите <b>🔙Назад</b> для отмены."
    )
    bot.send_message(message.chat.id, add_prompt, parse_mode="html", reply_markup=keyboard(back_menu))
    bot.register_next_step_handler(message, add_groups, bot)

def add_groups(message, bot):
    if message.text == '🔙Назад' or message.text == '/cancel':
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=keyboard(groups_edit_menu))
        return

    new_links_raw = message.text.splitlines()
    if not new_links_raw or not any(link.strip() for link in new_links_raw):
        bot.send_message(message.chat.id, '❌ Вы не ввели ни одного ID. Попробуйте снова или нажмите <b>🔙Назад</b> для отмены.')
        bot.register_next_step_handler(message, add_groups, bot)
        return

    pattern = re.compile(r'^-\d+$')
    valid_new_links = []
    invalid_links = []
    for link in new_links_raw:
        if pattern.match(link.strip()):
            valid_new_links.append(link.strip())
        else:
            invalid_links.append(link)
    
    if invalid_links:
        error_message = (
            '🚫 <b>Часть ID имеет некорректный формат.</b>\n\n'
            'ID должен начинаться с «-» и содержать только цифры.\n\n'
            'Неверно указаны:\n' + 
            '\n'.join(f'• <code>{link}</code>' for link in invalid_links) +
            '\n\nПопробуйте ввести корректные ID еще раз, или нажмите <b>🔙Назад</b> для отмены.'
        )
        bot.send_message(message.chat.id, error_message, parse_mode="html")
        bot.register_next_step_handler(message, add_groups, bot)
        return

    if "groups" not in state.tasks or not state.tasks["groups"]:
        state.tasks["groups"] = []
    
    added_count = 0
    duplicate_count = 0
    for link in valid_new_links:
        if link not in state.tasks["groups"]:
            state.tasks["groups"].append(link)
            added_count += 1
        else:
            duplicate_count += 1
            
    feedback_message = ""
    if added_count > 0:
        feedback_message += f"✅ Успешно добавлено новых каналов: {added_count}.\n"
    if duplicate_count > 0:
        feedback_message += f"ℹ️ Пропущено дубликатов: {duplicate_count}."
    
    if not feedback_message:
        feedback_message = "ℹ️ Все введенные ID уже есть в списке."

    bot.send_message(message.chat.id, feedback_message, reply_markup=keyboard(groups_edit_menu))

def prompt_delete_group(message, bot):
    groups = state.tasks.get("groups")
    if not groups:
        bot.send_message(message.chat.id, "ℹ️ Список каналов пуст, удалять нечего.", reply_markup=keyboard(groups_edit_menu))
        return

    groups_text = get_groups_list_text(bot, groups)
    delete_prompt = (
        f'{groups_text}\n\n'
        'Введите номер канала, который хотите удалить. Или нажмите 🔙 Назад для отмены.'
    )
    bot.send_message(message.chat.id, delete_prompt, parse_mode="html", reply_markup=keyboard(back_menu))
    bot.register_next_step_handler(message, process_group_deletion, bot)

def process_group_deletion(message, bot):
    if message.text == '🔙Назад' or message.text == '/cancel':
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=keyboard(groups_edit_menu))
        return

    try:
        group_index_to_delete = int(message.text) - 1
        if 0 <= group_index_to_delete < len(state.tasks["groups"]):
            deleted_group = state.tasks["groups"].pop(group_index_to_delete)
            bot.send_message(message.chat.id, f'✅ Канал <code>{deleted_group}</code> успешно удален.', parse_mode="html", reply_markup=keyboard(groups_edit_menu))
        else:
            bot.send_message(message.chat.id, '❗️ Неверный номер. Пожалуйста, введите номер из списка.\n\nИли нажмите <b>🔙Назад</b> для отмены.')
            bot.register_next_step_handler(message, process_group_deletion, bot)
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, '❗️ Пожалуйста, введите корректный номер канала.\n\nИли нажмите <b>🔙Назад</b> для отмены.')
        bot.register_next_step_handler(message, process_group_deletion, bot) 
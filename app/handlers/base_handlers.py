from app.keyboards import keyboard, main_menu, settings_menu, edit_menu

def register_base_handlers(bot, TRUSTED_USERS):
    @bot.message_handler(func=lambda message: message.from_user.username not in TRUSTED_USERS)
    def handle_untrusted_user(message):
        bot.send_message(message.chat.id, "У вас нет доступа к этому боту.")

    @bot.message_handler(commands=['start', 'help'])
    def start(message):
        if message.text == '/start':
            bot.reply_to(message, 'Я бот который делает рассылку сообщений в группы. Нажмите кнопку "⚡️Создать задачу" или "🆘Помощь"', reply_markup=keyboard(main_menu))
        elif message.text == '/help':
            help_command(message)

    @bot.message_handler(func=lambda message: message.text == '🆘Помощь')
    def help_command(message):
        if message.chat.type == 'private':
            bot.send_message(
                message.chat.id,
                "Я могу отправлять сообщения в группы по расписанию. Чтобы создать задачу, нажмите на соответствующую кнопку.\nЧто-то не работает?Напишите мне:<b>https://t.me/victor_gogolev</b>",
                parse_mode="html",
                reply_markup=keyboard(settings_menu)
            )
            
    @bot.message_handler(func=lambda message: message.text == '👨‍💻Изменить задачу')
    def edit_task_menu(message):
        if message.chat.type == 'private':
            bot.send_message(message.chat.id, "Выберите, что хотите изменить:", reply_markup=keyboard(edit_menu))

    @bot.message_handler(func=lambda message: message.text == '🔙Назад')
    def go_back(message):
        if message.chat.type == 'private':
            bot.send_message(message.chat.id, "⚙️ Что хотите сделать?", reply_markup=keyboard(settings_menu)) 
from telebot import types

main_menu = ('⚡️Создать задачу', '🆘Помощь')
settings_menu = ('👀Посмотреть задачу', '👨‍💻Изменить задачу', '🐇Начать рассылку', '⏹Остановить рассылку', '🆘Помощь')
edit_menu = ('📝Поменять текст', '⏰Поменять интервал', '📋Поменять список групп', '🔙Назад')
groups_edit_menu = ('➕Добавить группы', '➖Удалить группы', '📝Заменить список', '🔙Назад')
back_menu = ('🔙Назад',)

def keyboard(menu):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(0, len(menu), 2):
        markup.add(*[types.KeyboardButton(item) for item in menu[i:i+2]])
    return markup
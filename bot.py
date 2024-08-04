import telebot
import time
import threading
from telebot import types
from tg_token import TOKEN
import re


bot = telebot.TeleBot(TOKEN)
tasks = {}

main_menu = ('⚡️Создать задачу','🆘Помощь')
settings_menu = ('👀Посмотреть задачу', '👨‍💻Изменить задачу', '🐇Начать рассылку', '⏹Остановить рассылку', '🆘Помощь')
edit_menu = ('📝Поменять текст', '⏰Поменять интервал', '📋Поменять список групп', '🔙Назад')

stop_event = threading.Event()

def keyboard(menu):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(0, len(menu), 2):
        markup.add(*[types.KeyboardButton(item)
                      for item in menu[i:i+2]])
    return markup

def load_trusted_users(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file]

TRUSTED_USERS = load_trusted_users('trusted_users.txt')

@bot.message_handler(func=lambda message: message.from_user.username not in TRUSTED_USERS)
def handle_untrusted_user(message: telebot.types.Message):
    bot.send_message(message.chat.id, "У вас нет доступа к этому боту.")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Я бот который делает рассылку сообщений в группы. Нажмите кнопку "⚡️Создать задачу" или "🆘Помощь"', reply_markup=keyboard(main_menu))

@bot.message_handler(content_types=['text'])
def get_information(message):
    if message.chat.type == 'private':
        if message.text == '⚡️Создать задачу':
            bot.send_message(message.chat.id, "Введите текст сообщения которое будет рассылаться:")
            bot.register_next_step_handler(message, get_notify)
        elif message.text == '🆘Помощь':
            bot.send_message(message.chat.id, "Я могу отправлять сообщения в группы по расписанию. Чтобы создать задачу, нажмите на соответствующую кнопку.\nЧто-то не работает?Напишите мне:<b>https://t.me/wa55up</b>",reply_markup="html")
        elif message.text == '👀Посмотреть задачу':
            show_notify(message)
        elif message.text == '👨‍💻Изменить задачу':
            bot.send_message(message.chat.id, "Выберите, что хотите изменить:", reply_markup=keyboard(edit_menu))
        elif message.text == '🐇Начать рассылку':
            start_sending(message)
        elif message.text == '⏹Остановить рассылку':
            stop_sending(message)
        elif message.text == '📝Поменять текст':
            bot.send_message(message.chat.id, "Введите новый текст сообщения:")
            bot.register_next_step_handler(message, update_notify)
        elif message.text == '⏰Поменять интервал':
            bot.send_message(message.chat.id, "Введите новый интервал отправки (числом) в минутах:")
            bot.register_next_step_handler(message, update_delay)
        elif message.text == '📋Поменять список групп':
            bot.send_message(message.chat.id, "Введите построчно новые id групп для рассылки\n(id группы это число из тире и 13 цифр.\n<i>Пример:</i><b>-1234567890123</b>\n<i>Получить его можно тут:</i>\n<b>https://t.me/username_to_id_bot)</b>\nИли в URL-строке при просмотре группы/канала через веб версию ТГ",parse_mode="html")
            bot.register_next_step_handler(message, update_links)
        elif message.text == '🔙Назад':
            bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=keyboard(settings_menu))
        
def get_notify(message):
    global notify
    notify = message.text
    bot.send_message(message.chat.id, f'Ваше сообщение для рассылки: <b>{notify}</b>', parse_mode="html")
    bot.send_message(message.chat.id, "Введите интервал отправки (числом) в минутах:")
    bot.register_next_step_handler(message, get_delay)

def get_delay(message):
    try:
        global delay
        delay = int(message.text)
        bot.send_message(message.chat.id, f'Ваш интервал рассылки: <b>{delay}</b> минут', parse_mode="html")
        bot.send_message(message.chat.id, "Введите построчно id групп для рассылки\n(id группы это число из тире и 13 цифр.\n<i>Пример:</i><b>-1234567890123</b>\n<i>Получить его можно тут:</i>\n<b>https://t.me/username_to_id_bot)</b>\nИли в URL-строке при просмотре группы/канала через веб версию ТГ",parse_mode="html")
        bot.register_next_step_handler(message, get_links)
    except ValueError:
        bot.send_message(message.chat.id, 'Укажите интервал отправки сообщения(числом) в минутах')
        bot.register_next_step_handler(message, get_delay)

def get_links(message):
    global links
    links = message.text.splitlines()
    links_checker(message,links,'get')
    
def links_checker(message,links:list,flag):
    if not links:
        bot.send_message(message.chat.id, 'Список ID групп пуст.', parse_mode="html")
        bot.register_next_step_handler(message, get_links)
        return
    
    pattern = re.compile(r'^-\d{13}$')
    success = False
    for link in links:
        if pattern.match(link):
            global formatted_links
            formatted_links = '\n'.join([f'{i+1}) {link}' for i, link in enumerate(links)])
            if not success:
                if flag == 'get':
                    bot.send_message(message.chat.id, f'ID ваших групп для рассылки: \n<b>{formatted_links}</b>', parse_mode="html")
                    create_task(message.chat.id)
                elif flag == 'update':
                    bot.send_message(message.chat.id, f'Новые ID ваших групп для рассылки: \n<b>{formatted_links}</b>', parse_mode="html")
                    bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=keyboard(settings_menu))
                success = True
        else:
            bot.send_message(message.chat.id, 'Некорректный формат ID групп. ID должны начинаться с "-" и содержать 13 цифр.', parse_mode="html")
            bot.register_next_step_handler(message, get_links)
            return
        
def create_task(chat_id):
    try:
        global tasks
        tasks = {
            "msg": notify,
            "delay": delay,
            "groups": links
        }
        bot.send_message(chat_id, 'Задача создана!', parse_mode="html")
        bot.send_message(chat_id, "Что хотите сделать?", reply_markup=keyboard(settings_menu))
    except:
        bot.send_message(chat_id, 'Задача не создана, попробуйте еще раз, или напишите в поддержку!', parse_mode="html")

def update_notify(message):
    global notify
    notify = message.text
    tasks["msg"] = notify
    bot.send_message(message.chat.id, f'Ваше новое сообщение для рассылки: <b>{notify}</b>', parse_mode="html")
    bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=keyboard(settings_menu))

def update_delay(message):
    try:
        global delay
        delay = int(message.text)
        tasks["delay"] = delay
        bot.send_message(message.chat.id, f'Ваш новый интервал рассылки: <b>{delay}</b> минут', parse_mode="html")
        bot.send_message(message.chat.id, "Что хотите сделать?", reply_markup=keyboard(settings_menu))
    except ValueError:
        bot.send_message(message.chat.id, 'Укажите интервал отправки сообщения числом')
        bot.register_next_step_handler(message, update_delay)

def update_links(message):
    global links
    links = message.text.splitlines()
    try:
        links_checker(message,links,'update')
        tasks["groups"] = links
    except:
        bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте еще раз, или напишите в поддержку!', parse_mode="html")
    
def show_notify(message):
    required_fields = ["msg", "delay", "groups"]
    empty_fields = [field for field in required_fields if not tasks.get(field)]

    if empty_fields:
        bot.send_message(message.chat.id, 
            f'Вы не заполнили следующие поля: {", ".join(empty_fields)}')
    elif len(tasks) == 3:
        bot.send_message(message.chat.id, 
            f'Ваши текущие параметры уведомления:\n'
            f'<i>Сообщение для рассылки:</i> <b>{tasks["msg"]}</b>\n'
            f'<i>Интервал отправки:</i> <b>{tasks["delay"]}</b>\n'
            f'<i>Группы:\n</i> <b>{formatted_links}</b>'
            , parse_mode="html")

def send_notice():
    while not stop_event.is_set():
        for group_id in tasks["groups"]:
            bot.send_message(group_id, tasks["msg"])
        time.sleep(tasks["delay"] * 60)
      
def start_sending(message):
    global stop_event
    stop_event.clear()
    
    if len(tasks) != 3:
        bot.send_message(message.chat.id,'Вы заполнили не все поля(их 3),должно быть указано сообщение,интервал,и список групп.Нажмите кнопку Посмотреть задачу и проверьте правильность введенных данных ')

    else:
        bot.send_message(message.chat.id, 'Рассылка начата!', parse_mode="html")
        threading.Thread(target=send_notice).start()

def stop_sending(message):
    global stop_event
    stop_event.set()
    bot.send_message(message.chat.id, 'Рассылка остановлена!', parse_mode="html")

bot.polling(non_stop=True)
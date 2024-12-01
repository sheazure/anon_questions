import telebot
import sqlite3
import os
from encryptor import for_ref
from encryptor import key
from dotenv import load_dotenv
from os.path import join, dirname


def get_from_env(key):
    dotenv_path = join(dirname(__file__), "token.env")
    load_dotenv(dotenv_path)
    return os.environ.get(key)

token = get_from_env('TG_BOT_TOKEN')
bot = telebot.TeleBot(token)

recip = None
sender = None
sender_username = None
id_message = None
event_cancel_send = False


previous_messages = []


@bot.message_handler(commands=['start', 'hello'])
def start(message):
    global recip, id_message, sender, sender_username, event_cancel_send
    bot.delete_message(message.chat.id, message.id)
    check_user(message) # добавленме в бд пользователей
    create_all_databases()


    if " " not in message.text: # не по рефу
        link_user = 'https://t.me/AskYourFriendAnon_bot/?start=' + str(for_ref(message.from_user.id, int(key, 2)))
        bot.send_message(message.chat.id, f"🚀Начни получать анонимные сообщения прямо сейчас!\n\nВот твоя ссылка:\n👉 {link_user}\n\nРазмести эту ссылку в своих соц.сетях и начинай получать анонимные сообщения💬")
    else: # по рефу
        sender = message.from_user.id
        sender_username = message.from_user.username
        recip = message.text.split()[1]
        recip = for_ref(recip, int(key, 2)) # id получателя

        markup = telebot.types.InlineKeyboardMarkup()
        Button = telebot.types.InlineKeyboardButton("Отменить отправку", callback_data='cancel_send')

        markup.add(Button)

        bot.send_message(message.chat.id, "Напиши сообщение, которое ты хочешь отправить, владелец ссылки получит его, но не будет знать от кого оно!", reply_markup=markup)
        bot.register_next_step_handler(message, send_message)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    global event_cancel_send
    if callback.data == 'cancel_send':
        event_cancel_send = True
        bot.delete_message(callback.message.chat.id, callback.message.message_id)

        


@bot.message_handler(commands=['show_users'])
def show_users(message):
    if not check_admin(message):
        bot.send_message(message.chat.id, "Неизвестная команда!")
        return 0
    conn = sqlite3.connect(r'C:\Users\sheaz\Desktop\Anon_questions\users.sql')
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    info = ''

    for el in users:
        info += f'ID:{el[0]}\nUsername:{el[1]}\n\n'

    cur.close()
    conn.close()

    bot.send_message(message.chat.id, info)



@bot.message_handler(commands=['show_admins'])
def show_admins(message):
    if not check_admin(message):
        bot.send_message(message.chat.id, "Неизвестная команда!")
        return 0
    conn = sqlite3.connect(r'C:\Users\sheaz\Desktop\Anon_questions\admins.sql')
    cur = conn.cursor()

    cur.execute("SELECT * FROM admins")
    admins = cur.fetchall()

    info = ''

    for el in admins:
        info += f'ID:{el[0]}\nUsername:{el[1]}\n\n'

    bot.send_message(message.chat.id, info)



@bot.message_handler(commands=['show_ias'])
def show_ias(message):
    if not check_admin(message):
        bot.send_message(message.chat.id, "Неизвестная команда!")
        return 0

    conn = sqlite3.connect(r'ias.sql')
    cur = conn.cursor()

    a = cur.execute("SELECT * FROM ias")
    a = a.fetchall()

    info = ''

    file = open("show_ias.txt", "w")

    for el in a:
        file.write('ID RECIPIENT: ' + str(el[0]) + '\n' + "USERNAME RECIPIENT: " + str(el[1]) + '\n' + "ID MESSAGE: " + str(el[2]) + '\n' + "ID SENDER: " + str(el[3]) + "\n" + "USERNAME SENDER: " + str(el[4]) + "\n" + "TEXT: " + str(el[5]) + "\n\n")

    file.close()
    
    file = open("show_ias.txt", 'rb')
    bot.send_document(message.chat.id, file)

    cur.close()
    conn.close() 



def send_message(message):
    global id_message, sender, recip, sender_username, event_cancel_send
    if event_cancel_send:
        event_cancel_send = False
        return
    text = message.text

    if text[0] == '/':
        bot.send_message(message.chat.id, "Неизвестная команда")
        bot.register_next_step_handler(message, send_message)
        return

    
    bot.reply_to(message, "Сообщение отправлено! Ожидай ответа от получателя")
    bot.delete_message(message.chat.id, message.id - 1)
    link_user = 'https://t.me/AskYourFriendAnon_bot/?start=' + str(for_ref(message.from_user.id, int(key, 2)))
    bot.send_message(message.chat.id, f"🚀Начни получать анонимные сообщения прямо сейчас!\n\nВот твоя ссылка:\n👉 {link_user}\n\nРазмести эту ссылку в своих соц.сетях и начинай получать анонимные сообщения💬")
    id_message = bot.send_message(recip, "📩Тебе пришло новое анонимное сообщение🚀\n\n" + text + "\n\nСвайпни для ответа↩️\n")
    id_message = id_message.message_id
    
    #добавление в бд неотвеченных анонок
    conn = sqlite3.connect(r'ias.sql')
    cur = conn.cursor()
    chat = bot.get_chat(recip)
        # Возвращаем юзернейм
    cur.execute("INSERT INTO ias (id_owner, username_owner, id_message, id_sender, username_sender, text) VALUES ('%d', '%s', '%d', '%d', '%s', '%s')" % (recip, chat.username, id_message, sender, sender_username, text))
    conn.commit()

    cur.close()
    conn.close()
    
    previous_messages.append(message)


@bot.message_handler()
def get_answer(message):
    if message.text[0] == '/':
        bot.send_message(message.chat.id, "Неизвестная команда!")
        return 0
    if message.reply_to_message != None:

        conn = sqlite3.connect(r'ias.sql')
        cur = conn.cursor()

        info = cur.execute(f'SELECT * FROM ias WHERE id_owner={message.from_user.id}')

        a = info.fetchall()

        for el in a:
            if message.reply_to_message.message_id == el[2]:
                bot.send_message(el[0], "Ответ отправлен!")
                bot.send_message(el[3], "Тебе пришел ответ от человека, которому ты отправил анонимное сообщение:\n\n" + str(message.text))
                
                return 0
        
        bot.send_message(message.from_user.id, "Ты можешь отвечать только на анонимные сообщения🤓🤓🤓")
        
        cur.close()
        conn.close()
    else:
        link_user = 'https://t.me/AskYourFriendAnon_bot/?start=' + str(for_ref(message.from_user.id, int(key, 2)))
        bot.send_message(message.chat.id, f"🚀Начни получать анонимные сообщения прямо сейчас!\n\nВот твоя ссылка:\n👉 {link_user}\n\nРазмести эту ссылку в своих соц.сетях и начинай получать анонимные сообщения💬")



def check_admin(message):

    if message.from_user.id in [1404205394]:
        return True
    else:
        return False


        
def check_user(message): # добавление в список юзеров
    user_id = message.from_user.id
    username = message.from_user.username

    conn = sqlite3.connect(r'C:\Users\sheaz\Desktop\Anon_questions\users.sql')
    cur = conn.cursor()

    info = cur.execute(f"SELECT user_id FROM users WHERE user_id={user_id}")

    a = info.fetchall()
    
    if len(a) == 0:
        cur.execute("INSERT INTO users (user_id, username) VALUES ('%d', '%s')" % (user_id, username))
        conn.commit()



    cur.close()
    conn.close()



def create_all_databases():
    conn = sqlite3.connect(r'admins.sql')
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS admins (id INTEGER, username varchar(16))")
    conn.commit()

    cur.close()
    conn.close()



    conn = sqlite3.connect(r'users.sql')
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, username varchar(16))")
    conn.commit()

    cur.close()
    conn.close()




    conn = sqlite3.connect(r'ias.sql')
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS ias (id_owner INTEGER, username_owner varchar(16), id_message INTEGER, id_sender INTEGER, username_sender varchar(16), text varchar(1000))")
    conn.commit()

    cur.close()
    conn.close()

if __name__ == '__main__':
    bot.polling(none_stop=1)
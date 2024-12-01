import telebot
import sqlite3
from encryptor import for_ref
from encryptor import key


bot = telebot.TeleBot("7117210455:AAHgyrPSGZ1ML6htldUwtpPHj5bcpInC1II")

recip = None
sender = None
id_message = None


#айди сообщения которое отправил чел и его айди,чтобы ответить ему
ids_and_senders = {} # без ответа

@bot.message_handler(commands=['start', 'hello'])
def start(message):
    global recip, id_message, sender
    check_user(message) # добавленме в бд пользователей

    if " " not in message.text: # не по рефу
        link_user = 'https://t.me/AskYourFriendAnon_bot/?start=' + str(for_ref(message.from_user.id, int(key, 2)))
        bot.send_message(message.chat.id, f"чел вот твоя ссылка:\n{link_user}")
    else: # по рефу
        sender = message.from_user.id
        recip = message.text.split()[1]
        recip = for_ref(recip, int(key, 2)) # id получателя
        bot.send_message(message.chat.id, "Напиши сообщение, которое ты хочешь, владелец ссылки получит его, но не будет знать от кого оно!")
        bot.register_next_step_handler(message, send_message)

@bot.message_handler(['show_ids_and_senders'])
def show_ids_and_senders(message):
    if not check_admin(message):
        bot.send_message(message.chat.id, "Неизвестная команда!")
        return 0
    bot.send_message(message.chat.id, str(ids_and_senders))

@bot.message_handler(['show_users'])
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

@bot.message_handler(['show_admins'])
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


@bot.message_handler()
def get_answer(message):
    if message.reply_to_message != None:
        if message.reply_to_message.id in ids_and_senders.keys():
            bot.send_message(message.chat.id, "Ответ отправлен!")
            bot.send_message(ids_and_senders[message.reply_to_message.id], "Тебе пришел ответ от человека, которому ты отправил анонимное сообщение:\n\n" + message.text)
            ids_and_senders.pop(message.reply_to_message.id)

def send_message(message):
    global id_message, sender, recip
    text = message.text
    bot.send_message(sender, "Сообщение отправлено! Ожидай ответа от получателя")
    id_message = bot.send_message(recip, "⬇️Тебе пришло новое анонимное сообщение🚀\n\n" + text + "\n\nСвайпни для ответа↩️\n")
    id_message = id_message.message_id
    ids_and_senders[id_message] = sender


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




if __name__ == '__main__':
    bot.polling(none_stop=1)
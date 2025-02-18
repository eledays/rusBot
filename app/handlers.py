from app import bot, db, basedir, ai
from app.bot_utils import send_long_message

import telebot

import os
import shutil


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Привет\n\n'
                                      'Этот бот позволит тебе выучить любую тему\n\n<i>как это работает</i>\n\n'
                                      '<b>/create</b> — создать тему\n'
                                      '<b>/topics</b> — список существующих тем\n'
                                      '<b>/help</b> — полный список команд')
    

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, '<b>Основные команды</b>\n\n'
                                      '<b>/create</b> — создать тему\n'
                                      '<b>/topics</b> — список существующих тем')
    

@bot.message_handler(commands=['create'])
def create(message, step=0, data={}):
    if message.text == '/cancel':
        if data and 'id' in data:
            db.delete_topic(data['id'])
            shutil.rmtree(f'{basedir}/users_content/{data["id"]}')
        bot.send_message(message.chat.id, 'Отменено')
        return

    if step == 0:
        message = bot.send_message(message.chat.id, 'Отправь название темы, например, "Физика. Динамика. 9 класс"')
        bot.register_next_step_handler(message, create, 1)

    elif step == 1:
        name = message.text
        topic_id = db.add_topic(name, message.from_user.id)
    
        os.mkdir(f'{basedir}/users_content/{topic_id}')

        message = bot.send_message(message.chat.id, 'Сейчас мне нужно получить всю теорию, которую ты хочешь выучить. Для этого ты можешь присылать её текстом или попросить помощи у нейросети — <b>/ai</b>')
        bot.register_next_step_handler(message, create, 2, {'id': topic_id, 'name': name})

    elif step == 2:
        if message.text == '/ai':
            if os.path.exists(f'{basedir}/users_content/{data["id"]}/theory.txt'):
                bot.send_message(message.chat.id, 'Применить ИИ можно только при создании темы')
                bot.register_next_step_handler(message, create, 2, data)
                return
            
            create(message, 'ai-gen-text', data)
        elif message.text == '/next':
            bot.send_message(message.chat.id, 'Отлично. Сейчас нейросеть разобьет теорию на маленькие порции информации')
            with open(f'{basedir}/users_content/{data["id"]}/theory.txt', 'r') as file:
                text = file.read()
            pieces = ai.text_to_pieces(text)

            text = '\n\n'.join(f'<blockquote>{e}</blockquote>' for e in pieces)

            bot.send_message(message.chat.id, text)
        else:
            text = message.text
            with open(f'{basedir}/users_content/{data["id"]}/theory.txt', 'a') as file:
                file.write(text + '\n\n')
            message = bot.send_message(message.chat.id, 'Записал. Можешь прислать ещё или переходить к следующему шагу — <b>/next</b>')
            bot.register_next_step_handler(message, create, 2, data)

    elif step == 'ai-gen-text':
        name = data['name']
        topic_id = data['id']
        prompt = f'Напиши всю теорию по теме "{name}". Не обращайся к пользователю, пиши только то, что относится к теме, не используй вводный текст. Не используй markdown'
        message = bot.send_message(message.chat.id, 'Секундочку...')
        answer = ai.ask(prompt)
        bot.delete_message(message.chat.id, message.id)

        keyboard = telebot.types.InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            telebot.types.InlineKeyboardButton(text='✔️', callback_data=f'yes_{topic_id}'), 
            telebot.types.InlineKeyboardButton(text='✖️', callback_data=f'no_{topic_id}'),
            telebot.types.InlineKeyboardButton(text='🔄', callback_data=f'refresh_{topic_id}')
        )
        send_long_message(bot, message.chat.id, answer, reply_markup=keyboard, parse_mode='markdown')
    

@bot.message_handler(commands=['topics'])
def send_topics(message):
    bot.send_message(message.chat.id, '<tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data.startswith('yes'):
        topic_id = call.data.split('_')[1]
        name = db.get_topic_name_by_id(topic_id)
        text = call.message.text
        with open(f'{basedir}/users_content/{topic_id}/theory.txt', 'a') as file:
            file.write(text + '\n')
        message = bot.send_message(call.message.chat.id, 'Записал. Можешь прислать ещё или переходить к следующему шагу — <b>/next</b>')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        bot.register_next_step_handler(message, create, 2, {'id': topic_id, 'name': name})
    elif call.data.startswith('no'):
        topic_id = call.data.split('_')[1]
        name = db.get_topic_name_by_id(topic_id)
        message = bot.send_message(call.message.chat.id, 'Не записываю. Отправь свой текст')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        bot.register_next_step_handler(message, create, 2, {'id': topic_id, 'name': name})
    elif call.data.startswith('refresh'):
        bot.delete_message(call.message.chat.id, call.message.id)
        topic_id = call.data.split('_')[1]
        name = db.get_topic_name_by_id(topic_id)
        create(call.message, 'ai-gen-text', {'id': topic_id, 'name': name})
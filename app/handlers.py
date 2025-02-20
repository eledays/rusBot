from app import bot, db, basedir, ai
from app.bot_utils import send_long_message, send_pieces

import telebot

import os
import shutil


@bot.message_handler(commands=['start'])
def send_welcome(message):
    print(message.chat.id)
    bot.send_message(message.chat.id, 'Привет\n\n'
                                      'Этот бот позволит тебе выучить любую тему\n\n<i>как это работает</i>\n\n'
                                      '<b>/create</b> — создать тему\n'
                                      '<b>/topics</b> — список существующих тем\n'
                                      '<b>/help</b> — полный список команд')
    

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, '<b>Основные команды</b>\n\n'
                                      '<b>/study</b> — настройки обучения, выбор тем\n\n'
                                      '<b>Темы:</b>\n'
                                      '<b>/create</b> — создать тему\n'
                                      '<b>/topics</b> — список существующих тем'
                                      '<b>/edit</b> — редактировать тему\n'
                                      '<b>/pieces n</b> — порции теории темы n\n')
    

@bot.message_handler(commands=['create'])
def create_topic(message, step=0, data={}):
    if message.text == '/cancel':
        if data and 'topic_id' in data:
            db.delete_topic(data['topic_id'])
            shutil.rmtree(f'{basedir}/users_content/{data["topic_id"]}')
        bot.send_message(message.chat.id, 'Отменено')
        return

    if step == 0:
        message = bot.send_message(message.chat.id, 'Отправь название темы, например, "Физика. Динамика. 9 класс"')
        bot.register_next_step_handler(message, create_topic, 1)

    elif step == 1:
        name = message.text
        topic_id = db.add_topic(name, message.from_user.id)
    
        os.mkdir(f'{basedir}/users_content/{topic_id}')

        message = bot.send_message(message.chat.id, 'Сейчас мне нужно получить всю теорию, которую ты хочешь выучить. Для этого ты можешь присылать её текстом или попросить помощи у нейросети — <b>/ai</b>')
        bot.register_next_step_handler(message, create_topic, 2, {'topic_id': topic_id, 'name': name})

    elif step == 2:
        if message.text == '/ai':
            if os.path.exists(f'{basedir}/users_content/{data["topic_id"]}/theory.txt'):
                bot.send_message(message.chat.id, 'Применить ИИ можно только при создании темы')
                bot.register_next_step_handler(message, create_topic, 2, data)
                return
            print(data)
            create_topic(message, 'ai-gen-text', data)
        elif message.text == '/next':
            bot.send_message(message.chat.id, 'Отлично. Сейчас нейросеть разобьет теорию на маленькие порции информации')
            with open(f'{basedir}/users_content/{data["topic_id"]}/theory.txt', 'r') as file:
                text = file.read()
            pieces = ai.text_to_pieces(text)

            text = '\n\n'.join(f'<blockquote>{e}</blockquote>' for e in pieces)

            message = send_long_message(bot, message.chat.id, text + '\n\n<b>/save</b> — сохранить порции\n'
                                                                     '<b>/edit</b> — редактировать')

            data['pieces'] = pieces
            db.add_pieces(data['topic_id'], data['pieces'])

            bot.register_next_step_handler(message, create_topic, 3, data)
        else:
            text = message.text
            with open(f'{basedir}/users_content/{data["topic_id"]}/theory.txt', 'a') as file:
                file.write(text + '\n\n')
            message = bot.send_message(message.chat.id, 'Записал. Можешь прислать ещё или переходить к следующему шагу — <b>/next</b>')
            bot.register_next_step_handler(message, create_topic, 2, data)

    elif step == 3:
        if message.text == '/save':
            bot.send_message(message.chat.id, 'Сохранил')
        elif message.text == '/edit':
            bot.send_message(message.chat.id, '<b>Редактирование</b>\n\n'
                                                '<b>/edit_piece n</b> — изменить порцию номер n\n'
                                                '<b>/delete_piece n</b> — удалить порцию номер n\n'
                                                '<b>/add_piece</b> — добавить порцию\n'
                                                '<b>/show_pieces</b> — показать текущие порции\n\n'
                                                '<b>/finish</b> — завершить редактирование')
            bot.register_next_step_handler(message, edit_topic, 'piece_editing_cmd', data)

    elif step == 'ai-gen-text':
        name = data['name']
        topic_id = data['topic_id']
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


@bot.message_handler(commands=['edit'])
def edit_topic(message, step=0, data={}):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, 'Отменено')
        return
        
    if step == 0:
        message = bot.send_message(message.chat.id, 'Отправь id темы')
        bot.register_next_step_handler(message, edit_topic, 1)
    
    elif step == 1:
        topic_id = message.text
        if not topic_id.isdigit():
            bot.send_message(message.chat.id, 'Id должен быть числом')
            return
        topic_id = int(topic_id)
        topic = db.get_topic(topic_id)
        if not topic:
            bot.send_message(message.chat.id, 'Такой темы не существует')
            return
        
        if topic['author_id'] != message.from_user.id:
            bot.send_message(message.chat.id, 'Вы не можете редактировать эту тему')
            return
        
        pieces = db.get_pieces(topic_id)
        data['topic_id'] = topic_id
        data['pieces'] = [e['data'] for e in pieces]
        bot.send_message(message.chat.id, '<b>Редактирование</b>\n\n'
                                            '<b>/edit_piece n</b> — изменить порцию номер n\n'
                                            '<b>/delete_piece n</b> — удалить порцию номер n\n'
                                            '<b>/add_piece</b> — добавить порцию\n'
                                            '<b>/show_pieces</b> — показать текущие порции\n\n'
                                            '<b>/finish</b> — завершить редактирование')
        
        bot.register_next_step_handler(message, edit_topic, 'piece_editing_cmd', data)

    elif step == 'piece_editing_cmd':
        if message.text.startswith('/edit_piece'):
            n = message.text.split()[-1]
            if not n.isdigit():
                bot.send_message(message.chat.id, 'Номер должен быть числом')
                return
            
            n = int(n)
            
            if n < 1 or n > len(data['pieces']):
                bot.send_message(message.chat.id, 'Номер порции вне диапазона')
                return
            
            message = bot.send_message(message.chat.id, 'Отправь новую порцию')
            bot.register_next_step_handler(message, edit_topic, 'piece_editing_edit', {'n': n, **data})
        
        elif message.text.startswith('/delete_piece'):
            n = message.text.split()[-1]
            if not n.isdigit():
                bot.send_message(message.chat.id, 'Номер должен быть числом')
                return
            
            n = int(n)
            
            if n < 1 or n > len(data['pieces']):
                bot.send_message(message.chat.id, 'Номер порции вне диапазона')
                return
            
            del data['pieces'][n - 1]
            message = bot.send_message(message.chat.id, f'Порция {n} удалена')
            bot.register_next_step_handler(message, edit_topic, 'piece_editing_cmd', data)
        
        elif message.text.startswith('/add_piece'):
            message = bot.send_message(message.chat.id, 'Отправь новую порцию')
            bot.register_next_step_handler(message, edit_topic, 'piece_editing_add', data)
        
        elif message.text.startswith('/show_pieces'):
            pieces = data['pieces']
            text = '\n\n'.join(f'<b>{i+1}.</b> <blockquote>{piece}</blockquote>' for i, piece in enumerate(pieces))
            message = send_long_message(bot, message.chat.id, text)
            bot.register_next_step_handler(message, edit_topic, 'piece_editing_cmd', data)
        
        elif message.text.startswith('/finish'):
            db.add_pieces(data['topic_id'], data['pieces'])
            bot.send_message(message.chat.id, 'Редактирование завершено')
            return

    elif step == 'piece_editing_edit':
        n = data['n']
        new_piece = message.text
        data['pieces'][n - 1] = new_piece
        bot.send_message(message.chat.id, f'Порция {n} изменена')
        bot.register_next_step_handler(message, edit_topic, 'piece_editing_cmd', data)

    elif step == 'piece_editing_add':
        new_piece = message.text
        data['pieces'].append(new_piece)
        bot.send_message(message.chat.id, 'Новая порция добавлена')
        bot.register_next_step_handler(message, edit_topic, 'piece_editing_cmd', data)


@bot.message_handler(commands=['topics'])
def send_topics(message):
    topics = db.get_topics()[:50]
    topics = [f'{e["id"] + 1}. {e["name"]}' for e in topics]
    bot.send_message(message.chat.id, '<b>Темы</b>\n' + '\n'.join(topics))


@bot.message_handler(commands=['pieces'])
def pieces_cmd(message):
    topic_id = message.text.split()[1]
    if not topic_id.isdigit():
        bot.send_message(message.chat.id, 'Id должен быть числом')
        return
    
    pieces = db.get_pieces(int(topic_id))
    if not pieces:
        bot.send_message(message.chat.id, 'По вашему запросу ничего не найдено')
        return 
    
    send_pieces(bot, message.chat.id, pieces)


@bot.message_handler(commands=['study'])
def study(message):
    bot.send_message(message.chat.id, '')


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
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
        bot.register_next_step_handler(message, create_topic, 2, {'topic_id': topic_id, 'name': name})
    elif call.data.startswith('no'):
        topic_id = call.data.split('_')[1]
        name = db.get_topic_name_by_id(topic_id)
        message = bot.send_message(call.message.chat.id, 'Не записываю. Отправь свой текст')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
        bot.register_next_step_handler(message, create_topic, 2, {'topic_id': topic_id, 'name': name})
    elif call.data.startswith('refresh'):
        bot.delete_message(call.message.chat.id, call.message.id)
        topic_id = call.data.split('_')[1]
        name = db.get_topic_name_by_id(topic_id)
        create_topic(call.message, 'ai-gen-text', {'topic_id': topic_id, 'name': name})
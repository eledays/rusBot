from app import bot, db, basedir, ai

import schedule
import threading
import time

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def job():
    print('Sending scheduled pieces...')
    users = db.get_users()
    for user in users:
        piece = db.get_piece_to_send(user['user_id'])
        if piece:
            user_id, data, piece_id = piece

            if not db.can_send(user_id):
                continue

            keyboard = InlineKeyboardMarkup(row_width=3)
            keyboard.add(
                InlineKeyboardButton('🔴', callback_data=f'piece-reaction_red_{piece_id}'),
                InlineKeyboardButton('🟡', callback_data=f'piece-reaction_yellow_{piece_id}'),
                InlineKeyboardButton('🟢', callback_data=f'piece-reaction_green_{piece_id}'),
            )
            db.postpone_piece(piece_id, user_id, 1)
            bot.send_message(user_id, data, reply_markup=keyboard)


def run():
    while True:
        schedule.run_pending()
        time.sleep(1)


# send_schedule = schedule.every().hour.at(':00').do(job)
send_schedule = schedule.every(.25).minutes.do(job)
threading.Thread(target=run).start()
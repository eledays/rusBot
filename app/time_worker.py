from app import bot, db, basedir, ai

import schedule
import threading


def job():
    print('Sending scheduled pieces...')
    users = db.get_users()
    print(dict(users[0]))
    for user in users:
        piece = db.get_piece_to_send(user['user_id'])
        if piece:
            bot.send_message(piece['user_id'], piece['data'])


# send_schedule = schedule.every().hour.at(':00').do(job)
send_schedule = schedule.every().minute.at(':00').do(job)
threading.Thread(target=send_schedule.run).start()
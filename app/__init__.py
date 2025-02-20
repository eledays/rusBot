import telebot
from config import Config

bot = telebot.TeleBot(Config.BOT_TOKEN, parse_mode='HTML')

from app.databaser import Databaser
db = Databaser()

from app.ai import AI
ai = AI()

import os
import sys
basedir = os.path.abspath(os.path.dirname(__file__))

from app import handlers, time_worker
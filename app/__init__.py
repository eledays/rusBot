import telebot
from config import Config

bot = telebot.TeleBot(Config.BOT_TOKEN)

from app import handlers
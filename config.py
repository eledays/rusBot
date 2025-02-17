import os
import dotenv


dotenv.load_dotenv()


class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    GIGACODE_AUTH_KEY = os.getenv('GIGACODE_AUTH_KEY')
    CLIENT_ID = os.getenv('CLIENT_ID')
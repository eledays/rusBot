from app import bot, db
from config import Config

import requests
import json
import urllib3
import time
import os


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AI:

    def __init__(self):
        self.refresh_access_token()
        self.messages = []
        self.cache_file = 'ai_cache.json'
        self.cache = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=4)

    def refresh_access_token(self):
        self.ACCESS_TOKEN, self.TOKEN_EXPIRES_AT = get_access_token()

    def ask(self, text: str, use_history: bool = False):
        if text in self.cache:
            print('cache used')
            return self.cache[text]
        
        if self.TOKEN_EXPIRES_AT < time.time():
            self.refresh_access_token()

        answer = None
        if use_history:
            self.messages.append({
                'role': 'user',
                'content': text
            })
            answer = get_response(self.messages, self.ACCESS_TOKEN)
            self.messages.append({
                'role': 'assistant',
                'content': answer
            })
        else:
            answer = get_response([{
                'role': 'user',
                'content': text
            }], self.ACCESS_TOKEN)

        self.cache[text] = answer
        self.save_cache()

        return answer
    
    def text_to_pieces(self, text: str):
        prompt = f'{text}\n\n\nРазбей теорию, описанную в тексте на маленькие независимые порции информации (максимум несколько предложений). Не обращайся к пользователю, пиши только то, что относится к теме, не используй вводный текст. Не используй markdown. Между блоками должно быть две пустые строки. Ты должен использовать всю информацию'
        answer = self.ask(prompt)
        # print(answer)
        pieces = parse_pieces(answer)
        # print(pieces)
        return pieces


def get_access_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload = {
        'scope': 'GIGACHAT_API_PERS'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': 'dababd97-475f-4154-9c83-e94066f91071',
        'Authorization': f'Basic {Config.GIGACODE_AUTH_KEY}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)

    if response.status_code == 200:
        json_response = json.loads(response.text)

        return json_response['access_token'], json_response['expires_at']
    else:
        raise Exception(f'Error getting access token: {response.status_code} - {response.text}')


def get_response(messages: list[dict], access_token) -> str:
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat",
        "messages": messages,
        "stream": False,
        "repetition_penalty": 1
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    print(response)

    return response.json()['choices'][0]['message']['content']


def parse_pieces(text: str):
    pieces = text.split('\n\n')
    pieces = [piece.strip() for piece in pieces]
    pieces = [piece for piece in pieces if piece]
    return pieces

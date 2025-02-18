from app import bot, db
from config import Config

import requests
import json
import urllib3
import time


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AI:

    def __init__(self):
        self.refresh_access_token()
        self.messages = []

    def refresh_access_token(self):
        self.ACCESS_TOKEN, self.TOKEN_EXPIRES_AT = get_access_token()

    def ask(self, text: str, use_history: bool = False):
        if text == 'Напиши всю теорию по теме "/ai". Не обращайся к пользователю, пиши только то, что относится к теме, не используй вводный текст. Не используй markdown':
            return '''Правописание суффиксов "пре-/при-"

Суффиксы "пре-" и "при-" являются приставками, которые могут иметь как схожие, так и различные значения.

1. Приставка "пре-"

   - Имеет значение "очень", "превосходящий", "сверх-".
   - Примеры: превысить, преодолеть, превратить.
   - Обычно используется с глаголами и прилагательными, когда речь идет о чем-то, что значительно превосходит норму.

2. Приставка "при-"

   - Имеет множество значений, которые можно разделить на несколько групп:
     - Приближение, присоединение: приехать, пристроить.
     - Приближение по действию: приоткрыть, присмотреться.
     - Сближение, расположение: привокзальный, пришкольный.
     - Неполное действие, соучастие: приоткрыть, прислушаться.
     - Направление действия внутрь: приделать, пришить.
     - Совместное действие: приобщить, приготовить.

3. Сложные случаи

   - Если слово имеет значение, близкое к "очень", "сверх-", то используется "пре-": превысить, превратить.
   - Если слово имеет значение "близко", "приближенно", то также используется "пре-": превратить, превращать.
   - Если слово имеет значение "приближение", "присоединение", то используется "при-": приехать, приходить.

4. Особенности

   - В некоторых случаях выбор между "пре-" и "при-" может зависеть от конкретного значения слова, но в большинстве случаев можно руководствоваться общими правилами.
   - Слово "примитивный" имеет значение "самый простой", поэтому используется "при-".

5. Исключения

   - Есть слова, в которых выбор между "пре-" и "при-" является исключением:
     - Привыкнуть, приспособиться — используются "при-".
     - Преувеличить, превысить — используются "пре-".

Таким образом, выбор между "пре-" и "при-" зависит от значения слова и контекста его использования.'''

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

        return answer
    
    def text_to_pieces(self, text: str):
        prompt = f'{text}\n\n\nРазбей теорию, описанную в тексте на маленькие независимые порции информации (максимум несколько предложений). Не обращайся к пользователю, пиши только то, что относится к теме, не используй вводный текст. Не используй markdown. Между блоками должно быть две пустые строки. Ты должен использовать всю информацию'
        answer = self.ask(prompt)
        print(answer)
        pieces = parse_pieces(answer)
        print(pieces)
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
    json_response = json.loads(response.text)

    return json_response['access_token'], json_response['expires_at']


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

    return response.json()['choices'][0]['message']['content']


def parse_pieces(text: str):
    pieces = text.split('\n\n')
    pieces = [piece.strip() for piece in pieces]
    pieces = [piece for piece in pieces if piece]
    return pieces

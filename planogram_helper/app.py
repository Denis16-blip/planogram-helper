import json
import re

def extract_chat_id(raw_value):
    try:
        match = re.search(r'user=(\{.*?\})', raw_value)
        if match:
            user_json = match.group(1)
            user_data = json.loads(user_json)
            return str(user_data.get("id"))
    except Exception as e:
        print(f"Ошибка извлечения chat_id: {e}")
    return DEFAULT_CHAT_ID






from flask import Flask, request
import requests
from io import BytesIO

app = Flask(__name__)

TOKEN = '7522558346:AAFujER9qTT5FGwkWOu1fkKMZ5VggtGW_fA'
DEFAULT_CHAT_ID = '7760306280'
YANDEX_FOLDER_LINK = 'https://disk.yandex.ru/d/WkDN69OomEBY_g'
sent_not_found = set()

def normalize(value):
    if not value:
        return ''
    return str(value).strip().lower().replace(' ', '_')

def extract_text(field):
    value = field.get('value')
    options = field.get('options', [])
    if isinstance(value, list) and options:
        selected = next((opt['text'] for opt in options if opt['id'] == value[0]), '')
        return selected
    elif isinstance(value, (int, str)):
        return str(value)
    return ''

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    form_data = data.get('data', {})
    fields = form_data.get('fields', [])
    hidden = form_data.get('hiddenFields', {})

    chat_id = hidden.get('chat_id') or 'default_chat_id'
    if not chat_id:
        print(">>> ❌ chat_id не передан!")
        return 'Нет chat_id', 400

    form = {field['label']: extract_text(field) for field in fields}

    gender = normalize(form.get('Пол'))
    brand = normalize(form.get('Бренд'))
    articles_count = normalize(form.get('Количество артикулов'))
    equipment = normalize(form.get('Тип оборудования'))
    highlight_color = normalize(form.get('Выбери Highlight цвета'))
    basic_color = normalize(form.get('Выбери Basic цвета'))

    filename = f"{gender}_{brand}_{articles_count}_{equipment}_{highlight_color}_{basic_color}.jpg"
    print(f">>> filename: {filename}")

    if send_photo_from_yadisk(filename, chat_id):
        return 'Фото отправлено!', 200

    if filename not in sent_not_found:
        msg = (
            f"К сожалению, мы пока не нашли подходящее фото по заданным параметрам:\n\n"
            f"• Пол: {gender or '-'}\n"
            f"• Бренд: {brand or '-'}\n"
            f"• Артикулов: {articles_count or '-'}\n"
            f"• Оборудование: {equipment or '-'}\n"
            f"• Highlight: {highlight_color or '-'}\n"
            f"• Basic: {basic_color or '-'}\n\n"
            f"Мы дополним базу и сообщим, когда появится пример!"
        )
        send_message(msg, chat_id)
        sent_not_found.add(filename)

    return 'Фото не найдено', 404

def send_photo_from_yadisk(filename, chat_id):
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {
        "public_key": YANDEX_FOLDER_LINK,
        "path": f"/{filename}"
    }
    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        print(f">>> Yandex API error: {response.status_code} — {response.text}")
        return False

    download_url = response.json().get("href")
    if not download_url:
        print(">>> Нет ссылки для скачивания")
        return False

    photo = requests.get(download_url)
    if photo.status_code == 200:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={'chat_id': chat_id},
            files={'photo': (filename, BytesIO(photo.content))}
        )
        return True
    return False

def send_message(text, chat_id):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={'chat_id': chat_id, 'text': text}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
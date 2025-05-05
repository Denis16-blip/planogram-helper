from flask import Flask, request
import requests
import os
from io import BytesIO

app = Flask(__name__)

TOKEN = '7522558436:AAHSpCaEebx693mDunI4cMRJPCFfE0Krp7I0'
CHAT = '7760306280'

YANDEX_FOLDER_LINK = "https://disk.yandex.ru/d/WkDN69OomEBY_g"

def normalize(value):
    if not value:
        return ""
    return str(value).strip().lower().replace(' ', '_')

def extract_text(field):
    value = field.get('value')
    options = field.get('options', [])
    
    if isinstance(value, list) and options:
        selected = [opt['text'] for opt in options if opt['id'] == value[0]]
        return selected[0] if selected else ''
    if isinstance(value, (int, str)):
        return str(value)
    return ''

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    form_data = data.get('data', {})
    fields = form_data.get('fields', [])

    form = {field['label']: extract_text(field) for field in fields}

    gender = normalize(form.get('пол'))
    brand = normalize(form.get('бренд'))
    articles_count = form.get('количество артикулов')
    equipment = normalize(form.get('тип оборудования'))
    highlight_color = normalize(form.get('выбери highlight цвета'))
    basic_color = normalize(form.get('выбери basic цвета'))

    filename = f"{gender}{brand}{articles_count}{equipment}{highlight_color}_{basic_color}.jpg"

    send_photo_from_yadisk(filename)
    return "OK", 200

def get_download_link_from_yadisk(filename):
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {
        "public_key": YANDEX_FOLDER_LINK,
        "path": f"/{filename}"
    }
    response = requests.get(api_url, params=params)
    
    if response.status_code == 200:
        return response.json().get("href")
    return None

def send_photo_from_yadisk(filename):
    download_url = get_download_link_from_yadisk(filename)
    if not download_url:
        not_found_msg = (
            f"К сожалению, мы пока не нашли подходящее фото по заданным параметрам:\n\n"
            f"• Имя файла: {filename}\n"
            f"Мы дополним базу и сообщим, когда появится пример!"
        )
        send_message(not_found_msg)
        return

    response = requests.get(download_url)
    if response.status_code == 200:
        photo = BytesIO(response.content)
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={'chat_id': CHAT},
            files={'photo': (filename, photo)}
        )
    else:
        send_message("Ошибка при скачивании изображения.")

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT, 'text': text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
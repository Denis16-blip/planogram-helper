from flask import Flask, request
import requests
import os

app = Flask(__name__)
TOKEN = '7522558436:AAHSpCaEebx693mDunI4cMRJPCfFf0Kop710'
CHAT = '7760306280'
last_not_found = None  # чтобы избежать повторных сообщений

def normalize(value):
    if not value:
        return ''
    return str(value).strip().lower().replace(' ', '_')

def extract_text(field):
    value = field.get('value')
    options = field.get('options', [])
    if isinstance(value, list) and options:
        selected = [opt['text'] for opt in options if opt['id'] in value]
        return selected[0] if selected else ''
    elif isinstance(value, (int, str)):
        return str(value)
    return ''

def send_photo_from_yadisk(filename):
    global last_not_found
    public_url = 'https://disk.yandex.ru/d/WkDN69OomEBY_g'
    get_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download'
    params = {'public_key': public_url, 'path': f'/{filename}'}
    response = requests.get(get_url, params=params)
    data = response.json()
    download_url = data.get('href')

    if not download_url:
        if last_not_found == filename:
            return  # уже отправляли
        last_not_found = filename
        not_found_msg = (
            f"К сожалению, мы пока не нашли подходящее фото по заданным параметрам:\n\n"
            f"• Имя файла: {filename}\n"
            f"Мы дополним базу и сообщим, когда появится пример!"
        )
        send_message(not_found_msg)
        return

    last_not_found = None  # фото найдено — обнуляем
    photo = requests.get(download_url).content
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={'chat_id': CHAT},
        files={'photo': ('photo.jpg', photo)}
    )

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT, 'text': text})

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    form_data = data.get('data', {})
    fields = form_data.get('fields', [])
    form = {field['label']: extract_text(field) for field in fields}

    gender = normalize(form.get('Пол'))
    brand = normalize(form.get('Бренд'))
    articles_count = form.get('Количество артикулов')
    equipment = normalize(form.get('Тип оборудования'))
    highlight_color = normalize(form.get('Выбери Highlight цвета'))
    basic_color = normalize(form.get('Выбери Basic цвета'))

    filename = f"{gender}{brand}{articles_count}{equipment}{highlight_color}_{basic_color}.jpg"
    send_photo_from_yadisk(filename)
    return 'ok', 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
from flask import Flask, request
import requests
import os

app = Flask(__name__)

TOKEN = '7522558346:AAHspCaEebx693mDunI4cMRJPCfF0Kop710'
CHAT = '7760306280'

def normalize(value):
    if not value:
        return ''
    return str(value).strip().lower().replace(' ', '_')

def extract_text(field):
    value = field.get('value')
    options = field.get('options', [])

    if isinstance(value, list) and options:
        selected = [opt['text'] for opt in options if opt['id'] == value[0]]
        return selected[0] if selected else ''
    elif isinstance(value, (int, str)):
        return str(value)
    return ''

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    form_data = data.get('data', {})
    fields = form_data.get('fields', [])

    # превращаем список полей в словарь: {label: выбранный текст}
    form = {field['label']: extract_text(field) for field in fields}

    # вытаскиваем и нормализуем параметры
    gender = normalize(form.get('Пол'))
    brand = normalize(form.get('Бренд'))
    articles_count = form.get('Количество артикулов')
    equipment = normalize(form.get('Тип оборудования'))
    highlight_color = normalize(form.get('Выбери Highlight цвета'))
    basic_color = normalize(form.get('Выбери Basic цвета'))

    filename = f"{gender}_{brand}_{articles_count}_{equipment}_{highlight_color}_{basic_color}.jpg"
    filepath = os.path.join('photos', filename)

    if os.path.exists(filepath):
        send_photo(filepath)
        return 'Фото отправлено!', 200
    else:
        not_found_msg = (
            f"К сожалению, я пока не нашел подходящее фото по заданным параметрам:\n\n"
            f"• Пол: {gender or '-'}\n"
            f"• Бренд: {brand or '-'}\n"
            f"• Артикулов: {articles_count or '-'}\n"
            f"• Оборудование: {equipment or '-'}\n"
            f"• Highlight: {highlight_color or '-'}\n"
            f"• Basic: {basic_color or '-'}\n\n"
            "Я дополню базу и сообщу, когда появится пример!"
        )
        send_message(not_found_msg)
        return 'Фото не найдено', 404

def send_photo(path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(path, 'rb') as ph:
        requests.post(url, data={'chat_id': CHAT}, files={'photo': ph})

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT, 'text': text})

if __name__ == '__main__':
    app.run(debug=True)

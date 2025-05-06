from flask import Flask, request
import requests
from io import BytesIO

app = Flask(__name__)

TOKEN = '7522558346:AAFujER9qTT5FGwkWOu1fkKMZ5VggtGW_fA'
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

    # 🟡 Получаем chat_id из скрытого поля формы
    chat_id = hidden.get('chat_id')
    if not chat_id:
        print(">>> ❌ Ошибка: не передан chat_id")
        return 'No chat_id', 400

    # 🧩 Извлекаем поля формы
    form = {field['label']: extract_text(field) for field in fields}

    gender = normalize(form.get('Пол'))
    brand = normalize(form.get('Бренд'))
    articles_count = normalize(form.get('Количество артикулов'))
    equipment = normalize(form.get('Тип оборудования'))
    highlight_color = normalize(form.get('Выбери Highlight цвета'))
    basic_color = normalize(form.get('Выбери Basic цвета'))

    filename = f"{gender}_{brand}_{articles_count}_{equipment}_{highlight_color}_{basic_color}.jpg"
    print(f">>> Готовый filename: {filename}")

    success = send_photo_from_yadisk(chat_id, filename)
    if success:
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
        send_message(chat_id, msg)
        sent_not_found.add(filename)

    return 'Фото не найдено', 404

def send_photo_from_yadisk(chat_id, filename):
    print(f">>> Yandex путь: {filename}")

    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {
        "public_key": YANDEX_FOLDER_LINK,
        "path": f"/{filename}"
    }

    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        print(f">>> ❌ Ответ Яндекса: {response.status_code} — {response.text}")
        return False

    download_url = response.json().get("href")
    print(f">>> ✅ Получен download URL: {download_url}")
    if not download_url:
        print(">>> ❌ Ошибка: не удалось получить ссылку для скачивания")
        return False

    photo = requests.get(download_url)
    if photo.status_code != 200:
        print(">>> ❌ Фото не удалось скачать")
        return False

    tg_response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={'chat_id': chat_id},
        files={'photo': (filename, BytesIO(photo.content))}
    )
    print(f">>> 📤 Telegram ответ: {tg_response.status_code} — {tg_response.text}")
    return tg_response.status_code == 200

def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={'chat_id': chat_id, 'text': text}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)





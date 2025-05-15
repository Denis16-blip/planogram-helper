
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

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print(f">>> Получен запрос: {data}")

    chat_id = data.get("chat_id")
    if not chat_id:
        print(">>> ❌ chat_id не передан!")
        return 'Нет chat_id', 400

    gender = normalize(data.get("gender"))
    brand = normalize(data.get("brand"))
    articles_count = normalize(data.get("articles"))
    equipment = normalize(data.get("equipment"))
    highlight_color = normalize(data.get("highlight"))
    basic_color = normalize(data.get("basic"))

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
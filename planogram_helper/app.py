from flask import Flask, request
import requests
from io import BytesIO
import urllib.parse

app = Flask(__name__)

# Твой токен и публичная ссылка на папку
TOKEN = "7522558346:AAFujER9qTT5FGwkWOu1fkKMZ5VggtGW_fA"
YANDEX_FOLDER_LINK = "https://disk.yandex.ru/d/WkDN69OomEBY_g"

def normalize_text(text):
    return text.strip().lower().replace(" ", "_")

def build_filename(data):
    gender = normalize_text(data.get("gender", ""))
    brand = normalize_text(data.get("brand", ""))
    articles = normalize_text(data.get("articles", ""))
    equipment = normalize_text(data.get("equipment", ""))
    highlight = normalize_text(data.get("highlight", ""))
    basic = normalize_text(data.get("basic", ""))
    return f"{gender}_{brand}_{articles}_{equipment}_{highlight}_{basic}.jpg"

def send_photo_from_yadisk(filename, chat_id):
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"

    # 🧠 ВАЖНО: кодируем путь файла для API-запроса
    encoded_filename = urllib.parse.quote(filename, encoding="utf-8", safe="")

    params = {
        "public_key": YANDEX_FOLDER_LINK,
        "path": encoded_filename
    }

    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        print(f">>> Ошибка API Яндекса: {response.status_code} — {response.text}")
        return False

    download_url = response.json().get("href")
    if not download_url:
        print(">>> Нет ссылки для скачивания")
        return False

    photo = requests.get(download_url)
    if photo.status_code == 200:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={"chat_id": chat_id},
            files={"photo": (filename, BytesIO(photo.content))}
        )
        return True
    else:
        print(f">>> Ошибка при скачивании фото: {photo.status_code}")
        return False

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(">>> Получен запрос:", data)

    chat_id = data.get("chat_id") or data.get("chatId")
    filename = build_filename(data)
    print(f">>> filename: {filename}")

    success = send_photo_from_yadisk(filename, chat_id)

    if not success:
        message = f"❌ Фото не найдено: {filename}"
        print(">>>", message)
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": message}
        )
    return "", 200

if __name__ == "__main__":
    app.run(debug=True)
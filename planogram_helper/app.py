from flask import Flask, request
import requests
from io import BytesIO
import re

app = Flask(__name__)

TOKEN = "7522558346:AAEdZfdvAEoDntjAf0kmxdp0DSd5iDamRcc"  # 🔁 Вставь сюда актуальный Telegram-токен
YANDEX_FOLDER_LINK = "https://disk.yandex.ru/d/WkDN69OomEBY_g"  # 🔁 Убедись, что ссылка публичная

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

def extract_numeric_chat_id(chat_id):
    if not chat_id:
        return None
    html_match = re.search(r'>(\d+)<', str(chat_id))
    if html_match:
        return html_match.group(1)
    digits = re.sub(r'\D', '', str(chat_id))
    return digits if digits else None

def send_photo_from_yadisk(filename, chat_id):
    print(f">>> Пытаемся найти файл на Я.Диске: {filename}")
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {
        "public_key": YANDEX_FOLDER_LINK,
        "path": filename
    }
    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        print(f">>> Яндекс.Диск API error: {response.status_code} — {response.text}")
        return False

    download_url = response.json().get("href")
    if not download_url:
        print(">>> Нет ссылки на загрузку файла")
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
    print(">>> [DEBUG] RAW REQUEST DATA:", data)

    chat_id_raw = data.get("USER_ID_TEXT") or data.get("chat_id") or data.get("chatId")
    chat_id = extract_numeric_chat_id(chat_id_raw)

    filename = build_filename(data)
    print(f">>> итоговое имя файла: {filename}")

    success = send_photo_from_yadisk(filename, chat_id)

    if not success and chat_id:
        message = f"❌ Фото не найдено: {filename}"
        print(">>>", message)
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": str(chat_id), "text": message}
        )
        print(">>> Ответ Telegram:", response.status_code, response.text)

    return "", 200

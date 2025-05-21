from flask import Flask, request
import requests
from io import BytesIO
import re

app = Flask(__name__)

TOKEN = "7522558346:AAEdZfdvAEoDntjAf0kmxdp0DSd5iDamRcc"
YANDEX_PUBLIC_URL = "https://disk.yandex.ru/d/WkDN69OomEBY_g"

def normalize_text(text):
    return text.strip().lower().replace(" ", "_")

def build_filename(data):
    gender    = normalize_text(data.get("gender", ""))
    brand     = normalize_text(data.get("brand", ""))
    articles  = normalize_text(data.get("articles", ""))
    equipment = normalize_text(data.get("equipment", ""))
    highlight = normalize_text(data.get("highlight", ""))
    basic     = normalize_text(data.get("basic", ""))
    return f"{gender}_{brand}_{articles}_{equipment}_{highlight}_{basic}.jpg"

def extract_numeric_chat_id(chat_id):
    if not chat_id:
        return None
    # сначала из <a>…</a>
    m = re.search(r'>(\d+)<', str(chat_id))
    if m:
        return m.group(1)
    # иначе просто цифры
    digits = re.sub(r'\D', '', str(chat_id))
    return digits or None

def send_photo_from_yadisk(filename, chat_id):
    print(f">>> Пытаемся найти файл на Я.Диске: {filename}")
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {
        "public_key": YANDEX_PUBLIC_URL,
        "path": f"/{filename}"   # <-- ведущий слэш обязателен
    }
    resp = requests.get(api_url, params=params)
    print(">>> Запрос к Я.Диску:", resp.url)
    if resp.status_code != 200:
        print(f">>> Яндекс.Диск API error: {resp.status_code} — {resp.text}")
        return False

    href = resp.json().get("href")
    if not href:
        print(">>> Нет поля href в ответе Яндекс.Диска")
        return False

    photo = requests.get(href)
    if photo.status_code == 200:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={ "chat_id": chat_id },
            files={ "photo": (filename, BytesIO(photo.content)) }
        )
        return True
    else:
        print(f">>> Ошибка скачивания по href: {photo.status_code}")
        return False

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(">>> [DEBUG] RAW REQUEST DATA:", data)

    chat_id_raw = data.get("USER_ID_TEXT") or data.get("chat_id") or data.get("chatId")
    chat_id = extract_numeric_chat_id(chat_id_raw)

    filename = build_filename(data)
    print(f">>> Итоговое имя файла: {filename}")

    if not send_photo_from_yadisk(filename, chat_id) and chat_id:
        msg = f"❌ Фото не найдено: {filename}"
        print(">>>", msg)
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={ "chat_id": chat_id, "text": msg }
        )
        print(">>> Ответ Telegram:", r.status_code, r.text)

    return "", 200





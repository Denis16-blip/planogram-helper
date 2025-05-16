from flask import Flask, request
import requests
from io import BytesIO
import re

app = Flask(__name__)

TOKEN = "7522558346:AAFujER9qTT5FGwkW0u1fkKMZ5VggtGW_fA"
GITHUB_BASE_URL = "https://raw.githubusercontent.com/Denis16-blip/planogram-images/main/"

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
    """Извлекает числовой chat_id из HTML-ссылки или строки"""
    if not chat_id:
        return None

    match = re.search(r'>(\d{6,15})<', str(chat_id))  # сначала пробуем вытащить ID из HTML
    if match:
        return match.group(1)

    digits = re.sub(r'\D', '', str(chat_id))  # если просто строка — оставляем только цифры
    return digits if digits else None

def send_photo_from_github(filename, chat_id):
    if not chat_id:
        print(">>> Ошибка: chat_id отсутствует, невозможно отправить фото.")
        return False

    photo_url = GITHUB_BASE_URL + filename
    print(f">>> Сформированная ссылка на фото: {photo_url}")

    response = requests.get(photo_url)
    if response.status_code != 200:
        print(f">>> Ошибка загрузки фото с GitHub: {response.status_code}")
        return False

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={"chat_id": chat_id},
        files={"photo": (filename, BytesIO(response.content))}
    )
    return True

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(">>> [DEBUG] RAW REQUEST DATA:", data)

    chat_id_raw = data.get("chat_id") or data.get("chatId") or data.get("USER_ID_TEXT")  # <- вот ключевое изменение
    chat_id = extract_numeric_chat_id(chat_id_raw)

    filename = build_filename(data)
    print(f">>> имя файла: {filename}")

    success = send_photo_from_github(filename, chat_id)
    if not success and chat_id:
        message = f"❌ Фото не найдено: {filename}"
        print(">>>", message)
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": message}
        )

    return "", 200

if __name__ == "__main__":
    app.run(debug=True
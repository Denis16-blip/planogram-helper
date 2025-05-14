import os
import json
import requests
from flask import Flask, request
from urllib.parse import unquote, parse_qs

app = Flask(__name__)

BOT_TOKEN = os.getenv('7522558346:AAFujER9qTT5FGwkWOu1fkKMZ5VggtGW_fA')

YANDEX_PUBLIC_FOLDER = "https://disk.yandex.ru/d/photos_planogram_helper"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"


def extract_chat_id(raw_chat_id):
    """
    Извлекает числовой chat_id из строки вида {{user.id}}#tgWebAppData=...
    """
    if isinstance(raw_chat_id, str):
        if "user=" in raw_chat_id:
            raw_chat_id = unquote(raw_chat_id)
            try:
                user_block = raw_chat_id.split("user=")[-1]
                user_json = user_block.split("&")[0]
                user_data = json.loads(user_json)
                return str(user_data.get("id"))
            except Exception as e:
                print("Ошибка при извлечении chat_id:", e)
                return None
        if raw_chat_id.isdigit():
            return raw_chat_id
    return None


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(">>> Входящие данные от Tally:")
    print(data)

    try:
        fields = {field["key"]: field["value"]["label"] if isinstance(field["value"], dict) else field["value"]
                  for field in data["fields"]}
        gender = fields.get("gender", "").lower()
        brand = fields.get("brand", "").lower()
        num_items = fields.get("num_items", "").lower()
        equipment = fields.get("equipment", "").lower()
        highlight_colors = "_".join(sorted(fields.get("highlight_colors", [])))
        base_colors = "_".join(sorted(fields.get("base_colors", [])))
        raw_chat_id = fields.get("chat_id")

        chat_id = extract_chat_id(raw_chat_id)
        print(f">>> chat_id: {chat_id}")

        if not chat_id:
            print("❌ Ошибка: chat_id не извлечён")
            return "Missing chat_id", 400

        filename = f"{gender}_{brand}_{num_items}_{equipment}_{highlight_colors}_{base_colors}.jpg"
        filename = filename.replace(" ", "_").replace(",", "").lower()
        print(">>> Имя файла:", filename)

        photo_url = f"{YANDEX_PUBLIC_FOLDER}/{filename}"

        response = requests.post(
            TELEGRAM_API_URL,
            data={"chat_id": chat_id, "photo": photo_url}
        )

        print(">>> Telegram ответ:", response.text)
        return "OK", 200

    except Exception as e:
        print("❌ Ошибка обработки запроса:", e)
        return "Internal Server Error", 500


if __name__ == "__main__":
    app.run(debug=True)
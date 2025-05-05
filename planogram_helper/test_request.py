import requests

url = "https://every-trams-jam.loca.lt/webhook"  # <-- сюда вставляешь свой URL от lt
headers = {"Content-Type": "application/json"}
data = {
    "data": {
        "store_type": "дисконт",
        "gender": "женский"
    }
}

response = requests.post(url, json=data, headers=headers)
print("Ответ от сервера:", response.text)
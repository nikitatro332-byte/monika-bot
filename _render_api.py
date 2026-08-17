import requests
import json

API_KEY = "rnd_dezhbInCTzzwDDhQbjXTHYmHgQOJ"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}

# Получаем все сервисы
r = requests.get("https://api.render.com/v1/services", headers=HEADERS, timeout=30)
services = r.json()

for item in services:
    s = item.get("service", item)
    sid = s.get("id")
    name = s.get("name")
    status = s.get("status")
    url = s.get("serviceUrl")
    print(f"ID: {sid}")
    print(f"Name: {name}")
    print(f"Status: {status}")
    print(f"URL: {url}")
    print()

    # Триггерим деплой для каждого
    if sid:
        print(f"  Деплою {name}...")
        dep = requests.post(
            f"https://api.render.com/v1/services/{sid}/deploys",
            headers=HEADERS,
            json={"clearCache": "clear"},
            timeout=30
        )
        print(f"  Deploy status: {dep.status_code}")
        if dep.status_code in (200, 201):
            print(f"  Deploy ID: {dep.json().get('id')}")
        print()
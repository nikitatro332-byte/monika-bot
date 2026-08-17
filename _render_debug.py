import requests
import json
import time

API_KEY = "rnd_dezhbInCTzzwDDhQbjXTHYmHgQOJ"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "Content-Type": "application/json"}
SERVICE_ID = "srv-da16n0e1egvs73a3i0n0"
PROXY = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}

# Получаем полные детали сервиса
r = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}", headers=HEADERS, timeout=30, proxies=PROXY)
print("=== Полный ответ сервиса ===")
print(json.dumps(r.json(), indent=2)[:2000])

# Получаем все деплои
print("\n=== Последние деплои ===")
r2 = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=5", headers=HEADERS, timeout=30, proxies=PROXY)
deploys = r2.json()
for item in deploys:
    d = item.get("deploy", item)
    print(f"  ID: {d.get('id')}")
    print(f"  Status: {d.get('status')}")
    print(f"  Commit: {d.get('commit', {}).get('id', '?')}")
    print(f"  Error: {d.get('errorMessage', 'нет')}")
    print(f"  Started: {d.get('startedAt')}")
    print(f"  Finished: {d.get('finishedAt')}")
    print()

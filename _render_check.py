import requests
import time

API_KEY = "rnd_dezhbInCTzzwDDhQbjXTHYmHgQOJ"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
SERVICE_ID = "srv-da16n0e1egvs73a3i0n0"
PROXY = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}

# Проверяем статус деплоя
r = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys", headers=HEADERS, timeout=30, proxies=PROXY)
deploys = r.json()
if deploys:
    latest = deploys[0] if isinstance(deploys, list) else deploys
    deploy = latest.get("deploy", latest)
    print(f"Deploy status: {deploy.get('status')}")
    print(f"Deploy ID: {deploy.get('id')}")

# Проверяем статус сервиса
r2 = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}", headers=HEADERS, timeout=30, proxies=PROXY)
svc = r2.json().get("service", r2.json())
print(f"Service status: {svc.get('status')}")
print(f"Service URL: {svc.get('serviceUrl')}")

# Проверяем keep-alive
url = svc.get("serviceUrl")
if url:
    if not url.startswith("http"):
        url = f"https://{url}"
    try:
        r3 = requests.get(url, timeout=60, proxies=PROXY)
        print(f"Keep-alive: {r3.status_code} — {r3.text[:100]}")
    except Exception as e:
        print(f"Keep-alive error: {e}")

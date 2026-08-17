import requests
import json
import time

API_KEY = "rnd_dezhbInCTzzwDDhQbjXTHYmHgQOJ"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "Content-Type": "application/json"}
SERVICE_ID = "srv-da16n0e1egvs73a3i0n0"
PROXY = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}

# 1. Получаем детали сервиса
print("=== Детали сервиса ===")
r = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}", headers=HEADERS, timeout=30, proxies=PROXY)
svc = r.json().get("service", r.json())
print(f"Name: {svc.get('name')}")
print(f"Type: {svc.get('type')}")
print(f"Status: {svc.get('status')}")
print(f"URL: {svc.get('serviceUrl')}")
print(f"Branch: {svc.get('branch')}")
print(f"AutoDeploy: {svc.get('autoDeploy')}")

# 2. Получаем env vars
print("\n=== Env vars ===")
r2 = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars", headers=HEADERS, timeout=30, proxies=PROXY)
env_vars = r2.json()
for ev in env_vars:
    key = ev.get("envVar", ev).get("key")
    val = ev.get("envVar", ev).get("value", "")
    # Скрываем значения, показываем только ключи и первые 5 символов
    print(f"  {key} = {val[:5]}...")

# 3. Деплой без очистки кэша
print("\n=== Деплой (без clear cache) ===")
dep = requests.post(
    f"https://api.render.com/v1/services/{SERVICE_ID}/deploys",
    headers=HEADERS,
    json={},
    timeout=30,
    proxies=PROXY
)
print(f"Status: {dep.status_code}")
if dep.status_code in (200, 201):
    deploy_id = dep.json().get("id")
    print(f"Deploy ID: {deploy_id}")

    # Ждём и проверяем
    for i in range(6):
        time.sleep(30)
        r3 = requests.get(
            f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}",
            headers=HEADERS, timeout=30, proxies=PROXY
        )
        d = r3.json().get("deploy", r3.json())
        status = d.get("status")
        print(f"  [{(i+1)*30}s] Status: {status}")
        if status in ("live", "build_failed", "deactivated"):
            if status == "build_failed":
                print(f"  Error: {d.get('errorMessage', 'нет')}")
            break

    # Проверяем сервис
    r4 = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}", headers=HEADERS, timeout=30, proxies=PROXY)
    svc2 = r4.json().get("service", r4.json())
    print(f"\nService status: {svc2.get('status')}")
    print(f"Service URL: {svc2.get('serviceUrl')}")

    url = svc2.get("serviceUrl")
    if url and status == "live":
        if not url.startswith("http"):
            url = f"https://{url}"
        try:
            r5 = requests.get(url, timeout=60, proxies=PROXY)
            print(f"Keep-alive: {r5.status_code} — {r5.text[:100]}")
        except Exception as e:
            print(f"Keep-alive: {e}")
else:
    print(f"Error: {dep.text[:300]}")

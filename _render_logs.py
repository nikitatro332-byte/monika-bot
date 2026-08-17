import requests

API_KEY = "rnd_dezhbInCTzzwDDhQbjXTHYmHgQOJ"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
SERVICE_ID = "srv-da16n0e1egvs73a3i0n0"
DEPLOY_ID = "dep-da16pj5bedkc73c6o1v0"
PROXY = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}

# Получаем логи деплоя
r = requests.get(
    f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{DEPLOY_ID}",
    headers=HEADERS, timeout=30, proxies=PROXY
)
deploy = r.json()
deploy = deploy.get("deploy", deploy)
print(f"Status: {deploy.get('status')}")
print(f"Error: {deploy.get('errorMessage', 'нет')}")
print(f"Started: {deploy.get('startedAt')}")
print(f"Finished: {deploy.get('finishedAt')}")

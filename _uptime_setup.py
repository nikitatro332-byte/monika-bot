import requests

API_KEY = "u3715450-12bcf8f0f853b4df02ab2e4b"
PROXY = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}
MONITOR_ID = "803754273"

# Обновляем URL монитора на актуальный
print("=== Обновление монитора ===")
r = requests.post(
    "https://api.uptimerobot.com/v2/editMonitor",
    data={
        "api_key": API_KEY,
        "format": "json",
        "id": MONITOR_ID,
        "friendly_name": "Hori Bot",
        "url": "https://monika-bot-pqn5.onrender.com",
        "interval": "300",
    },
    timeout=30,
    proxies=PROXY
)
print(f"Status: {r.status_code}")
print(r.json())
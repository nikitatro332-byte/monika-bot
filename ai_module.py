"""
🤖 AI Module — единый модуль для всех ИИ-провайдеров
Используется telegram_bot.py и model_viewer.py

Провайдеры:
  - xAI (Grok)      — grok-2-latest (нужны кредиты на console.x.ai)
  - Gemini (Google)  — gemini-flash-latest (нужен VPN/прокси для РФ)
  - Groq             — llama-3.3-70b (бесплатно, ключ может быть заблокирован)
  - OpenRouter       — deepseek:free, llama:free (бесплатно, ключ может быть заблокирован)

⚠️ Статус ключей на момент создания:
  - xAI:     ключ валиден, но нет кредитов → пополнить на console.x.ai
  - Gemini:  ключ валиден, но регион заблокирован → нужен VPN
  - Groq:    403 Forbidden → проверить/перевыпустить ключ
  - OpenRouter: 403 → проверить/перевыпустить ключ
"""

import requests
import json
import os
import subprocess
import time
import socket
import sys

# =====================================================
# 🔑 КЛЮЧИ
# =====================================================

XAI_API_KEY    = os.environ.get("XAI_API_KEY", "xai-wlr7wOJMrUtHO82avCn2dKYmiw5PWPv7kQCPzpSzu6bcMoINerOi4LLLULE0CB6oz1ACE52vjHLJT7MZ")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6KWiCNI3vK-4CgFLR9XLnkwWpmc5fvl1rLICg2S8u5aAg")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "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")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

# =====================================================
# 🌐 ПРОКСИ (Xray VLESS → SOCKS5)
# На Render/облаке прокси НЕ нужен (сервер вне РФ)
# =====================================================

# Автоопределение: облако (Render, Railway, etc.) или локально
IS_CLOUD = os.environ.get("RENDER") or os.environ.get("RAILWAY_SERVICE_ID") or os.path.isdir("/app") or not sys.platform.startswith("win")

if IS_CLOUD:
    PROXY = None
    print("☁️ Облачная среда — прокси не нужен")
else:
    PROXY = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}

_xray_proc = None

def _ensure_proxy():
    """Проверяет и запускает Xray прокси если нужно (только на Windows)."""
    global _xray_proc

    if IS_CLOUD:
        return True  # В облаке прокси не нужен

    # Проверяем открыт ли порт
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex(("127.0.0.1", 10808)) == 0:
            s.close()
            return True
        s.close()
    except:
        pass

    # Ищем xray.exe
    xray_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xray", "xray.exe")
    xray_cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xray", "config.json")
    if not os.path.exists(xray_exe):
        print("⚠️ Xray не найден. Выполни _setup_xray.py")
        return False

    print("🌐 Запускаю Xray прокси...")
    _xray_proc = subprocess.Popen(
        [xray_exe, "run", "-config", xray_cfg],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    time.sleep(2)

    # Проверяем
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        ok = s.connect_ex(("127.0.0.1", 10808)) == 0
        s.close()
        if ok:
            print("✅ Xray прокси запущен (SOCKS5 :10808)")
        return ok
    except:
        return False

# =====================================================
# 📋 МОДЕЛИ
# =====================================================

MODELS = {
    # xAI Grok (нужны кредиты)
    "grok-2-latest":  {"provider": "xai",    "free": False},
    "grok-2":         {"provider": "xai",    "free": False},

    # Gemini (нужен VPN для РФ)
    "gemini-flash-latest":     {"provider": "gemini", "free": True},
    "gemini-2.5-flash":        {"provider": "gemini", "free": True},

    # Groq (бесплатно)
    "llama-3.3-70b-versatile":  {"provider": "groq",   "free": True},
    "llama-3.1-8b-instant":     {"provider": "groq",   "free": True},

    # OpenRouter (бесплатные)
    "deepseek-r1:free":         {"provider": "openrouter", "free": True, "full": "deepseek/deepseek-r1:free"},
    "llama-3.3-70b:free":       {"provider": "openrouter", "free": True, "full": "meta-llama/llama-3.3-70b-instruct:free"},
}

FREE_MODELS = {k: v for k, v in MODELS.items() if v["free"]}


# =====================================================
# 🧠 AI ENGINE
# =====================================================

class AIEngine:
    def __init__(self, default_model="gemini-flash-latest"):
        self.current_model = default_model
        self.history = []  # контекст диалога
        self.system_prompt = ""
        _ensure_proxy()

    def set_system(self, prompt):
        self.system_prompt = prompt

    def reset_history(self):
        self.history = []

    def chat(self, user_message, max_tokens=500, temperature=0.8):
        """Главный метод — отправляет сообщение и возвращает ответ."""
        self.history.append({"role": "user", "content": user_message})

        model_info = MODELS.get(self.current_model)
        if not model_info:
            return f"❌ Модель '{self.current_model}' не найдена"

        provider = model_info["provider"]

        try:
            if provider == "xai":
                reply = self._xai(user_message, max_tokens, temperature)
            elif provider == "gemini":
                reply = self._gemini(user_message, max_tokens, temperature)
            elif provider == "groq":
                reply = self._groq(user_message, max_tokens, temperature)
            elif provider == "openrouter":
                reply = self._openrouter(user_message, max_tokens, temperature, model_info["full"])
            else:
                return "❌ Неизвестный провайдер"
        except Exception as e:
            reply = f"⚠️ Ошибка ({provider}): {e}"

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def switch(self, model_name):
        if model_name in MODELS:
            self.current_model = model_name
            return True
        return False

    def list_models(self, free_only=False):
        models = FREE_MODELS if free_only else MODELS
        result = []
        for name, info in models.items():
            tag = "🆓" if info["free"] else "💰"
            active = "⭐" if name == self.current_model else "  "
            result.append(f"{active} {tag} {name} [{info['provider']}]")
        return "\n".join(result)

    # ===== xAI (Grok) =====
    def _xai(self, message, max_tokens, temperature):
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend(self.history)
        r = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": self.current_model, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature},
            timeout=30, proxies=PROXY
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    # ===== Gemini =====
    def _gemini(self, message, max_tokens, temperature):
        contents = []
        for h in self.history[:-1]:
            role = "user" if h["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": h["content"]}]})
        contents.append({"role": "user", "parts": [{"text": message}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.current_model}:generateContent?key={GEMINI_API_KEY}"
        r = requests.post(url, json={
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            "systemInstruction": {"parts": [{"text": self.system_prompt}]} if self.system_prompt else None
        }, timeout=30, proxies=PROXY)
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    # ===== Groq =====
    def _groq(self, message, max_tokens, temperature):
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend(self.history)
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": self.current_model, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature},
            timeout=30, proxies=PROXY
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    # ===== OpenRouter =====
    def _openrouter(self, message, max_tokens, temperature, full_name):
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend(self.history)
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={"model": full_name, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature},
            timeout=60, proxies=PROXY
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


# =====================================================
# 🎭 ПОВЕДЕНИЕ МОДЕЛИ (для model_viewer.py)
# =====================================================

class ModelBehavior:
    """Связывает ИИ с анимациями 3D-модели."""

    def __init__(self, engine=None):
        self.engine = engine or AIEngine(default_model="gemini-flash-latest")
        self.engine.set_system(
            "Ты — Моника, живой анимированный персонаж. "
            "Отвечай коротко (1-2 предложения). "
            "В конце ответа добавь [анимация: idle|wave|dance|happy] "
            "чтобы выбрать анимацию. Пример: 'Привет! Я так рада тебя видеть! [анимация: wave]'"
        )

    def react(self, user_input):
        """Возвращает (текст, анимация)."""
        reply = self.engine.chat(user_input, max_tokens=150, temperature=0.9)

        # Парсим анимацию из ответа
        anim = "idle"
        for a in ["wave", "dance", "happy", "idle"]:
            tag = f"[анимация: {a}]"
            if tag in reply.lower():
                anim = a
                reply = reply.replace(tag, "").replace(tag.capitalize(), "").strip()
                break

        return reply, anim


# =====================================================
# 🚀 ТЕСТ
# =====================================================

if __name__ == "__main__":
    print("🤖 AI Module — ТЕСТ\n")
    engine = AIEngine(default_model="gemini-flash-latest")
    print("📚 Бесплатные модели:")
    print(engine.list_models(free_only=True))
    print()

    print("💬 Тест Gemini (нужен VPN для РФ):")
    try:
        r = engine.chat("Привет! Как дела?", max_tokens=100)
        print(f"  → {r}\n")
    except Exception as e:
        print(f"  ❌ {e}\n")

    print("💬 Тест Groq:")
    engine.switch("llama-3.3-70b-versatile")
    engine.reset_history()
    try:
        r = engine.chat("Привет! Как дела?", max_tokens=100)
        print(f"  → {r}\n")
    except Exception as e:
        print(f"  ❌ {e}\n")

    print("💬 Тест xAI (нужны кредиты):")
    engine.switch("grok-2-latest")
    engine.reset_history()
    try:
        r = engine.chat("Привет! Как дела?", max_tokens=100)
        print(f"  → {r}\n")
    except Exception as e:
        print(f"  ❌ {e}\n")

    print("🎭 Тест ModelBehavior:")
    behavior = ModelBehavior()
    text, anim = behavior.react("Привет Моника!")
    print(f"  Текст: {text}")
    print(f"  Анимация: {anim}")

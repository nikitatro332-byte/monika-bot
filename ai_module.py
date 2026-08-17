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
import uuid

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
    "openrouter:free":          {"provider": "openrouter", "free": True, "full": "openrouter/free"},
    "gpt-oss-20b:free":         {"provider": "openrouter", "free": True, "full": "openai/gpt-oss-20b:free"},
    "nemotron-3-super:free":    {"provider": "openrouter", "free": True, "full": "nvidia/nemotron-3-super-120b-a12b:free"},
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
        """Главный метод — отправляет сообщение и возвращает ответ с fallback."""
        self.history.append({"role": "user", "content": user_message})

        model_info = MODELS.get(self.current_model)
        if not model_info:
            # Модель не найдена — пробуем никнейм через OpenRouter/Gemini
            return f"❌ Модель '{self.current_model}' не найдена"

        provider = model_info["provider"]
        original_model = self.current_model

        # Цепочка fallback при ошибках: groq → gemini → openrouter
        fallback_chain = {
            "groq": ["gemini-flash-latest", "openrouter:free"],
            "gemini": ["openrouter:free", "llama-3.3-70b-versatile"],
            "openrouter": ["gemini-flash-latest", "llama-3.3-70b-versatile"],
            "xai": ["gemini-flash-latest", "openrouter:free"],
        }

        attempts = 0
        last_err = None
        tried = set()

        try:
            while attempts < 3:
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

                    self.history.append({"role": "assistant", "content": reply})
                    return reply
                except Exception as e:
                    last_err = f"({provider}: {self.current_model}): {e}"
                    attempts += 1
                    if "429" in str(e) or "503" in str(e) or "502" in str(e) or "timeout" in str(e).lower() or "404" in str(e) or "401" in str(e) or "403" in str(e):
                        print(f"⚠️ {last_err} → пробую запасную модель")
                        # Перебираем цепочку
                        switched = False
                        for fb in fallback_chain.get(provider, []):
                            if fb not in tried and fb in MODELS:
                                self.switch(fb)
                                tried.add(fb)
                                switched = True
                                break
                        if not switched:
                            # Все исчерпаны — остаёмся на исходной
                            self.switch(original_model)
                            raise
                    else:
                        # Ошибка не rate-limit — не пробуем другие модели
                        self.history.append({"role": "assistant", "content": f"⚠️ Ошибка: {e}"})
                        return f"⚠️ Ошибка: {e}"

            # Возвращаем исходную модель после использования fallback
            self.switch(original_model)
            reply = f"⚠️ Ошибка: {last_err}"
        except Exception as e:
            reply = f"⚠️ Ошибка ({provider}): {e}"
            # Пробуем Gemini как последний шанс
            try:
                self.switch("gemini-flash-latest")
                return self._gemini(user_message, max_tokens, temperature)
            except Exception as e2:
                pass

        self.switch(original_model)
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
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens + 200},
            "systemInstruction": {"parts": [{"text": self.system_prompt}]} if self.system_prompt else None
        }, timeout=30, proxies=PROXY)
        r.raise_for_status()
        data = r.json()

        # Gemini 3.x может вернуть пустой content (мысли съели токены) — пробуем достать текст безопасно
        try:
            candidate = data["candidates"][0]["content"]
            parts = candidate.get("parts", [])
            for p in parts:
                if "text" in p and p["text"].strip():
                    return p["text"]
            # Fallback: мысли
            for p in parts:
                if "thought" in p:
                    return p["thought"]
            raise KeyError("no text in parts")
        except (KeyError, IndexError) as e:
            raise Exception(f"Gemini пустой ответ: {e}")

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
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/nikitatro332-byte/monika-bot",
                "X-Title": "Monika Bot"
            },
            json={"model": full_name, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature},
            timeout=60, proxies=PROXY
        )
        r.raise_for_status()
        data = r.json()
        try:
            msg = data["choices"][0]["message"]
            content = msg.get("content")
            if content and content.strip():
                return content
            # Модель-рассуждатель вернула пустой content — пробуем reasoning
            reasoning = msg.get("reasoning")
            if reasoning and reasoning.strip():
                return reasoning.strip()
            raise Exception("OpenRouter пустой ответ (content и reasoning пусты)")
        except (KeyError, IndexError, TypeError) as e:
            print(f"⚠️ OpenRouter ответ: {str(data)[:300]}")
            raise Exception(f"OpenRouter пустой ответ: {e}")

    # ===== Gemini Vision (распознавание фото) =====
    def vision(self, image_bytes, prompt="Опиши что на фото. Коротко, 2-3 предложения."):
        """Распознаёт изображение через Gemini (с ретраями)."""
        import base64
        b64 = base64.b64encode(image_bytes).decode()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
            ]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300}
        }

        last_err = None
        for attempt in range(3):
            try:
                r = requests.post(url, json=payload, timeout=30, proxies=PROXY)
                if r.status_code == 200:
                    data = r.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                elif r.status_code in (429, 500, 503):
                    last_err = f"{r.status_code}"
                    time.sleep(2 * (attempt + 1))
                else:
                    r.raise_for_status()
            except Exception as e:
                last_err = str(e)
                time.sleep(2 * (attempt + 1))

        raise Exception(f"Gemini Vision недоступен: {last_err}")

    # ===== Поиск в интернете (DuckDuckGo) =====
    def web_search(self, query, max_results=5):
        """Ищет в интернете через DuckDuckGo."""
        results = []
        proxy_str = None
        if PROXY:
            proxy_str = PROXY.get("https") or PROXY.get("http")

        # Попытка 1: duckduckgo_search (DDGS)
        try:
            from duckduckgo_search import DDGS
            with DDGS(proxy=proxy_str) as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({"title": r["title"], "body": r["body"], "href": r["href"]})
            if results:
                return results
        except Exception as e:
            print(f"⚠️ Поиск DDGS: {e}")

        # Попытка 2: прямой запрос к DuckDuckGo HTML
        try:
            import requests as req
            from urllib.parse import quote
            from bs4 import BeautifulSoup
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = req.get(url, timeout=20, proxies=PROXY, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            for item in soup.select(".result__body")[:max_results]:
                title_tag = item.select_one(".result__a")
                snippet_tag = item.select_one(".result__snippet")
                if title_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "body": snippet_tag.get_text(strip=True) if snippet_tag else "",
                        "href": title_tag.get("href", "")
                    })
        except Exception as e:
            print(f"⚠️ Поиск HTML: {e}")

        return results

    # ===== Генерация картинок (Pollinations.ai) =====
    def generate_image_url(self, prompt):
        """Возвращает URL сгенерированной картинки через Pollinations.ai."""
        from urllib.parse import quote
        encoded = quote(prompt)
        return f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"

    # ===== Транскрипция голоса (Groq Whisper) =====
    def transcribe_audio(self, audio_bytes, filename="audio.ogg"):
        """Распознаёт голосовое сообщение через Groq Whisper."""
        import io
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        files = {"file": (filename, io.BytesIO(audio_bytes), "audio/ogg")}
        data = {"model": "whisper-large-v3", "language": "ru"}
        r = requests.post(url, headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                          files=files, data=data, timeout=60, proxies=PROXY)
        r.raise_for_status()
        return r.json().get("text", "")

    # ===== TTS (gTTS natural → fallback) =====
    async def tts_realistic(self, text, filename=None, as_ogg=True):
        """Генерирует голос через gTTS с естественной скоростью."""
        safe_name = filename or f"voice_{uuid.uuid4().hex}"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        mp3_path = os.path.join(base_dir, f"{safe_name}.mp3")
        out_path = os.path.join(base_dir, f"{safe_name}.ogg")

        # gTTS — slow=True для более естественной речи
        try:
            from gtts import gTTS
            clean_text = text.replace("\n", " ").replace("\r", " ")
            tts = gTTS(text=clean_text, lang="ru", tld="com", slow=True)
            tts.save(mp3_path)
            if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 500:
                raise Exception("gTTS вернул пустой файл")
            print(f"🎤 gTTS natural: {os.path.getsize(mp3_path)} bytes")
        except Exception as e:
            print(f"⚠️ gTTS: {e}")
            return None

        if as_ogg and os.path.exists(mp3_path):
            try:
                import imageio_ffmpeg
                import subprocess
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
                cmd = [ffmpeg, "-y", "-i", mp3_path, "-c:a", "libopus", "-b:a", "48k", "-ar", "24000", out_path]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if r.returncode == 0 and os.path.exists(out_path):
                    print(f"🎤 Конвертировано в OGG: {os.path.getsize(out_path)} bytes")
                    os.remove(mp3_path)
                    return out_path
                else:
                    print(f"⚠️ Конвертация не удалась: {r.stderr[-200:]}")
            except Exception as e:
                print(f"⚠️ ffmpeg: {e}")

        return mp3_path if os.path.exists(mp3_path) else None

    # ===== Генерация фото Моники (DDLC style) =====
    def generate_monika_photo(self, mood="casual", filename="monika_generated.png"):
        """
        Генерирует фото Моники в стиле DDLC с точным промптом.
        mood: casual, happy, sad, thinking, cooking, piano
        """
        base_desc = (
            "young woman, 18 years old, 2D anime / visual novel style, "
            "long coral-brown hair, high ponytail tied with a large white bow, "
            "two long side strands framing her face, big emerald-green eyes, light skin, slim build, "
            "school uniform: white shirt, brown vest, grey-blue blazer, blue pleated skirt, red ribbon at collar, "
            "black thigh-high stockings, white-pink school slippers, Doki Doki Literature Club aesthetic"
        )

        prompts = {
            "casual": (
                f"{base_desc}, soft lighting, gentle smile, relaxed posture, clean lineart, detailed eyes"
            ),
            "happy": (
                f"{base_desc}, bright happy smile, waving hand, cheerful pose, sparkling eyes, warm daylight"
            ),
            "sad": (
                f"{base_desc}, sad expression, looking down, glossy eyes, melancholic soft light"
            ),
            "thinking": (
                f"{base_desc}, thoughtful expression, hand near chin, calm classroom background, soft light"
            ),
            "cooking": (
                f"{base_desc}, white apron over uniform, cooking in kitchen, holding wooden spoon, cozy warm lighting"
            ),
            "piano": (
                f"{base_desc}, sitting at piano, focused serious look, stage-like soft spotlight"
            )
        }
        prompt = prompts.get(mood, prompts["casual"])
        from urllib.parse import quote
        encoded = quote(prompt)
        seed = int(time.time()) % 1000000
        base_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(base_dir, filename)
        # Без model=flux — Pollinations надёжно генерирует только базовой моделью
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=512&height=768&nologo=true&seed={seed}"
        )
        r = requests.get(url, timeout=120, proxies=PROXY)
        r.raise_for_status()
        if len(r.content) < 1000:
            raise Exception("Pollinations вернул пустую картинку")
        with open(out_path, "wb") as f:
            f.write(r.content)
        return out_path


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

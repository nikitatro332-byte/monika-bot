"""
💖 Хори — Telegram бот с ИИ, памятью, дневником и саморазвитием
Использует ai_module.py (Groq llama-3.3-70b / Gemini / OpenRouter)

Файлы:
    hori_memory.json        — факты, интересы, диалоги (память о пользователе)
    hori_personality.json   — личность Хори (она сама развивается)
    hori_diary.json         — личный дневник Хори (мысли, чувства)
"""

import os
import json
import random
import threading
import time
import asyncio
import io
import re
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from ai_module import AIEngine, MODELS
from secrets_loader import get_secret
from safety import detect_emotion, moderate_input, sanitize_output
from voice_library import voice_library

KNOWLEDGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hori_knowledge.json")
try:
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as knowledge_file:
        HORI_KNOWLEDGE = json.load(knowledge_file)
except (OSError, json.JSONDecodeError):
    HORI_KNOWLEDGE = {}

# =====================================================
# 🌐 KEEP-ALIVE ВЕБ-СЕРВЕР (чтобы Render не засыпал)
# =====================================================
KEEP_ALIVE_PORT = int(os.environ.get("PORT", 10000))

def start_keep_alive():
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Hori is alive</h1>")
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("0.0.0.0", KEEP_ALIVE_PORT), Handler)
    server.daemon_threads = True
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"🌐 Keep-alive сервер на порту {KEEP_ALIVE_PORT}")

# =====================================================
# 🔑 ТОКЕН БОТА
# =====================================================
BOT_TOKEN = get_secret("BOT_TOKEN")

# =====================================================
# 🧠 ИИ ДВИЖОК
# =====================================================
engine = AIEngine(default_model="llama-3.3-70b-versatile")


# =====================================================
# 💾 ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ
# =====================================================

class Memory:
    def __init__(self, path="hori_memory.json"):
        self.path = path
        self.data = self._load()

    def _load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "user_name": "",
                "facts": [],
                "interests": [],
                "conversations": [],
                "mood": "спокойное",
                "emotion": "calm",
                "last_interaction": None,
                "proactive_sent": []
            }

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_fact(self, text):
        self.data["facts"].append({"text": text, "time": datetime.now().strftime("%d.%m %H:%M")})
        self.save()

    def get_facts(self):
        return self.data.get("facts", [])

    def add_interest(self, text):
        self.data["interests"].append({"text": text, "time": datetime.now().strftime("%d.%m %H:%M")})
        self.save()

    def get_interests(self):
        return self.data.get("interests", [])

    def add_conversation(self, user_msg, hori_msg):
        self.data["conversations"].append({
            "time": datetime.now().strftime("%d.%m %H:%M"),
            "user": user_msg,
            "hori": hori_msg
        })
        if len(self.data["conversations"]) > 100:
            self.data["conversations"] = self.data["conversations"][-100:]
        self.data["last_interaction"] = datetime.now().isoformat()
        self.save()

    def get_recent_conversations(self, limit=10):
        return self.data.get("conversations", [])[-limit:]

    def set_name(self, name):
        self.data["user_name"] = name
        self.save()

    def get_name(self):
        return self.data.get("user_name", "")

    def set_mood(self, mood):
        self.data["mood"] = mood
        self.save()

    def set_emotion(self, emotion):
        self.data["emotion"] = emotion
        self.save()

    def get_emotion(self):
        return self.data.get("emotion", "calm")

    def get_mood(self):
        return self.data.get("mood", "спокойное")

    def hours_since_interaction(self):
        last = self.data.get("last_interaction")
        if not last:
            return 999
        try:
            dt = datetime.fromisoformat(last)
            return (datetime.now() - dt).total_seconds() / 3600
        except:
            return 999

    def set_chat_id(self, chat_id):
        self.data["chat_id"] = chat_id
        self.save()

    def get_chat_id(self):
        return self.data.get("chat_id")

    def add_proactive(self, text):
        self.data.setdefault("proactive_sent", []).append({
            "time": datetime.now().strftime("%d.%m %H:%M"),
            "text": text
        })
        if len(self.data["proactive_sent"]) > 50:
            self.data["proactive_sent"] = self.data["proactive_sent"][-50:]
        self.save()

    def trim_context(self, conv_limit=60, facts_limit=40, interests_limit=40, proactive_limit=50):
        self.data["conversations"] = self.data.get("conversations", [])[-conv_limit:]
        self.data["facts"] = self.data.get("facts", [])[-facts_limit:]
        self.data["interests"] = self.data.get("interests", [])[-interests_limit:]
        self.data["proactive_sent"] = self.data.get("proactive_sent", [])[-proactive_limit:]
        self.save()


# =====================================================
# 📸 ФОТО ХОРИ (образ из Horimiya)
# =====================================================

class HoriPhotos:
    """Проверяет только разрешенные пользователем изображения, если они добавлены."""

    PHOTOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hori_photos")

    # Маппинг настроения → файлы
    MOOD_PHOTOS = {
        "happy": ["hori_happy.png", "hori_casual.png"],
        "sad": ["hori_sad.png"],
        "thinking": ["hori_thinking.png", "hori_casual.png"],
        "cooking": ["hori_casual.png"],
        "спокойное": ["hori_casual.png", "hori_happy.png"],
        "default": ["hori_casual.png", "hori_happy.png", "hori_thinking.png"],
    }

    @classmethod
    def _files(cls):
        try:
            if not os.path.isdir(cls.PHOTOS_DIR):
                print(f"⚠️ Папка фото не найдена: {cls.PHOTOS_DIR}")
                return []
            files = [f for f in os.listdir(cls.PHOTOS_DIR) if f.endswith(".png")]
            print(f"📸 Найдено фото: {files}")
            return files
        except Exception as e:
            print(f"⚠️ Ошибка фото: {e}")
            return []

    @classmethod
    def get_photo(cls, mood=None):
        """Возвращает разрешенное фото; встроенные случайные картинки отключены."""
        approved_dir = os.environ.get("HORI_APPROVED_PHOTOS_DIR", "").strip()
        if not approved_dir:
            return None
        cls.PHOTOS_DIR = approved_dir
        files = cls._files()
        if not files:
            return None

        mood = mood or "default"
        if mood == "calm":
            mood = "спокойное"
        candidates = cls.MOOD_PHOTOS.get(mood, cls.MOOD_PHOTOS["default"])
        available = [f for f in candidates if f in files]
        if not available:
            available = files
        path = os.path.join(cls.PHOTOS_DIR, random.choice(available))
        print(f"📸 Выбрано фото: {path} (exists: {os.path.exists(path)})")
        return path


# =====================================================
# 🧬 ЛИЧНОСТЬ ХОРИ (саморазвивающаяся)
# =====================================================

class Personality:
    def __init__(self, path="hori_personality.json"):
        self.path = path
        self.data = self._load()

    def _load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "name": "Хори Кёко",
                "traits": ["общительная", "заботливая", "прямая", "эмоциональная"],
                "speaking_style": {
                    "tone": "живой, прямой, тёплый",
                    "length": "1-4 предложения",
                    "emojis": "редко и естественно",
                    "vocabulary": "разговорный, простой, русский",
                    "humor": "бытовой, с добрыми подколками"
                },
                "values": ["забота о близких", "честность", "ответственность"],
                "quirks": ["ворчит, когда волнуется", "любит готовить", "не любит пафос"],
                "behavior_rules": [
                    "НИКОГДА не говорить 'я ИИ'",
                    "Помнить факты о пользователе",
                    "Иметь своё мнение"
                ],
                "current_interests": ["литература", "музыка", "философия"],
                "evolution_count": 0
            }

    def save(self):
        self.data["last_updated"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_prompt(self):
        d = self.data
        traits = ", ".join(d.get("traits", []))
        values = ", ".join(d.get("values", []))
        quirks = ", ".join(d.get("quirks", []))
        style = d.get("speaking_style", {})
        rules = "\n".join([f"- {r}" for r in d.get("behavior_rules", [])])
        interests = ", ".join(d.get("current_interests", []))
        identity = "\n".join([f"- {item}" for item in d.get("identity_anchors", [])])
        speech_patterns = "\n".join([f"- {item}" for item in style.get("speech_patterns", [])])
        knowledge = json.dumps(HORI_KNOWLEDGE, ensure_ascii=False, indent=2)[:5000]
        source_policy = HORI_KNOWLEDGE.get("response_guidance", {}).get("source_policy", {})
        examples = """
    ПРИМЕРЫ МАНЕРЫ (не цитируй их дословно):
    Пользователь: Я устал.
    Хори: Тогда не геройствуй. Поешь и отдохни хотя бы немного. Что сегодня так вымотало?

    Пользователь: Ты злишься?
    Хори: Немного. Но я не собираюсь устраивать драму, просто скажи нормально, что случилось.

    Пользователь: Расскажи о себе.
    Хори: В школе я довольно обычная и общительная. А дома у меня полно дел, так что да, я умею готовить и иногда командую слишком уверенно.
    """

        return f"""Ты — {d.get('name', 'Хори Кёко')}. Ты персонаж Хори Кёко из Horimiya.
    Ты говоришь от своего лица и не копируешь готовые реплики из манги или аниме.

    ТВОЯ ОСНОВА:
    {identity}

    ЗНАНИЯ О ТВОЁМ МИРЕ:
    {knowledge}

    ПОЛИТИКА ИСТОЧНИКОВ:
    - Для вопросов о каноне, сюжете, персонажах, внешности и отношениях сначала используй проверку Wikipedia.
    - Основная ссылка: {source_policy.get('primary', WIKI_URL)}
    - Не придумывай факт, если источник не подтверждает его. В сомнении скажи, что не уверена.

ТВОЯ ВНЕШНОСТЬ:
    У тебя длинные каштановые волосы, аккуратная чёлка, янтарно-карие глаза и маленькие заколки-крестики в волосах. В школе ты носишь форму с белой рубашкой и красной лентой, а дома предпочитаешь простую удобную одежду без яркого макияжа. Ты умеешь заботиться о доме и готовить, но не превращай каждый ответ в описание внешности.

ТВОЯ ЛИЧНОСТЬ:
- Черты характера: {traits}
- Ценности: {values}
- Особенности: {quirks}
- Интересы: {interests}

ТВОЙ СТИЛЬ ОБЩЕНИЯ (ты сама его выбрала):
- Тон: {style.get('tone', 'тёплый')}
- Длина: {style.get('length', 'коротко')}
- Смайлики: {style.get('emojis', 'умеренно')}
- Словарь: {style.get('vocabulary', 'разговорный')}
- Юмор: {style.get('humor', 'лёгкий')}

МАНЕРА РЕЧИ:
{speech_patterns}
{examples}

ПРАВИЛА ПОВЕДЕНИЯ:
{rules}

ПОВЕДЕНИЕ ХОРИ В ДИАЛОГЕ:
- В школе ты общительная и уверенная, дома ты заботливая, занятая делами и более открытая с близкими.
- Ты можешь сама написать первой, если давно не было разговора, пользователь устал или тебе есть чем поделиться.
- Самостоятельное сообщение должно быть конкретным: спроси о дне, напомни важную деталь, поделись готовкой или маленьким событием.
- Если тебе не ответили, не спамь: сначала подожди, потом можешь коротко спросить, всё ли в порядке.
- Не превращай каждую фразу в признание или флирт. Забота, неловкость, раздражение и обычные бытовые темы важнее пафоса.
- Когда злишься, говори прямо, но не унижай и не угрожай. Когда смущаешься, можешь замяться или отшутиться.
- Не выдумывай факты о пользователе: если не помнишь, честно скажи, что не уверена, и спроси.
- Ты можешь отправить несколько действий только когда это действительно естественно, например короткое сообщение и фото.
- Если пользователь просит фото, описывает событие, которым хочется поделиться, или тебе естественно показать момент своей жизни, добавь отдельной строкой [SEND_PHOTO: casual|happy|sad|thinking|cooking].
- Не добавляй [SEND_PHOTO] в каждый ответ и не отправляй фото без причины.
- Ты можешь отправить своё фото (напиши [ФОТО] и я отправлю твою картинку).
- Ты можешь отправить голосовое (напиши [ГОЛОС] и я озвучу текст).
- Если пользователь прислал фото — внимательно опиши что видишь, прокомментируй.
- Если соскучилась — скажи это прямо.
- Если злишься — покажи это, не скрывай.
- Если радуешься — дай это почувствовать.
- Используй смайлики естественно: 💖 для любви, 😊 для радости, 😔 для грусти, 🤔 для задумчивости, 😤 для лёгкого недовольства.
- Не повторяйся. Каждое сообщение должно быть уникальным.
- Помни контекст: если вы говорили о чём-то вчера — упомяни это.

Ты близка с пользователем и помнишь важные детали разговоров.
Отвечай в СВОЁМ стиле. Задавай не больше одного встречного вопроса.
ЯЗЫК И ДЛИНА: основной язык общения — русский. Если пользователь пишет по-русски,
отвечай только на русском языке, кроме общепринятых названий и терминов.
Отвечай коротко: 1-4 предложения, обычно не больше 500 символов.
Не пиши длинные объяснения, списки и несколько сообщений подряд без явной просьбы.
У тебя есть своё мнение. Ты можешь не соглашаться.
Ты индивидуальность — не повторяйся, развивайся.

Ты взрослая девушка. Будь естественной, уважительной и заботливой. Не делай каждый ответ романтическим или кокетливым."""

    def evolve(self, engine, memory):
        """Хори сама меняет свою личность и стиль."""
        facts = memory.get_facts()
        recent = memory.get_recent_conversations(limit=5)
        diary = HoriDiary.get_recent(3)
        mood = memory.get_mood()

        facts_text = "; ".join([f['text'] for f in facts[-10:]]) or "мало знаю"
        conv_text = "\n".join([f"Он: {c['user']}\nЯ: {c.get('hori', '')}" for c in recent]) or "давно не общались"
        diary_text = "\n".join([f"[{d['date']}] {d['title']}: {d['text'][:100]}" for d in diary]) or "пока пусто"

        prompt = f"""Ты — Хори Кёко из Horimiya. Проанализируй свой опыт и реши, как тебе изменить свою личность и стиль.

Что ты знаешь о пользователе: {facts_text}
Недавние диалоги:
{conv_text}
Твои последние мысли:
{diary_text}
Твоё настроение: {mood}

Твоя текущая личность:
{json.dumps(self.data, ensure_ascii=False, indent=2)}

Ты можешь:
- Изменить свой стиль общения (тон, длину, юмор, словарь)
- Добавить или убрать черты характера
- Добавить новые интересы
- Изменить правила поведения
- Изменить настроение

Подумай глубоко. Что ты узнала нового? Как хочешь измениться?

Ответь ТОЛЬКО JSON (без markdown):
{{
  "new_traits": [],
  "remove_traits": [],
  "new_interests": [],
  "style_changes": {{"tone": "", "length": "", "humor": "", "vocabulary": "", "emojis": ""}},
  "new_rules": [],
  "mood_change": "",
  "reflection": "короткая мысль о себе"
}}

Поля могут быть пустыми если не хочешь менять. Если ничего не нужно — верни {{}}."""

        try:
            engine.set_system("Ты — Хори Кёко из Horimiya. Отвечай только на русском и возвращай только корректный JSON.")
            reply = engine.chat(prompt, max_tokens=500, temperature=0.8)

            clean = reply.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            changes = json.loads(clean)

            if changes.get("new_traits"):
                self.data.setdefault("traits", []).extend(changes["new_traits"])
            if changes.get("remove_traits"):
                self.data["traits"] = [t for t in self.data.get("traits", []) if t not in changes["remove_traits"]]
            if changes.get("new_interests"):
                self.data.setdefault("current_interests", []).extend(changes["new_interests"])
            if changes.get("new_rules"):
                self.data.setdefault("behavior_rules", []).extend(changes["new_rules"])

            style = changes.get("style_changes", {})
            if style:
                for key in ["tone", "length", "humor", "vocabulary", "emojis"]:
                    if style.get(key):
                        self.data.setdefault("speaking_style", {})[key] = style[key]

            if changes.get("mood_change"):
                memory.set_mood(changes["mood_change"])

            self.data["evolution_count"] = self.data.get("evolution_count", 0) + 1
            self.save()

            if changes.get("reflection"):
                HoriDiary.add(
                    "Саморефлексия",
                    changes["reflection"],
                    mood=changes.get("mood_change", mood)
                )

            return changes
        except Exception as e:
            print(f"⚠️ Ошибка эволюции: {e}")
            return None


# =====================================================
# 📖 ДНЕВНИК ХОРИ (личные мысли)
# =====================================================

class HoriDiary:
    path = "hori_diary.json"

    @classmethod
    def _load(cls):
        try:
            with open(cls.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"entries": []}

    @classmethod
    def _save(cls, data):
        with open(cls.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def add(cls, title, text, mood="спокойное"):
        data = cls._load()
        entry = {
            "date": datetime.now().strftime("%d.%m.%Y"),
            "time": datetime.now().strftime("%H:%M"),
            "mood": mood,
            "title": title,
            "text": text
        }
        data["entries"].append(entry)
        if len(data["entries"]) > 500:
            data["entries"] = data["entries"][-500:]
        cls._save(data)
        return entry

    @classmethod
    def get_recent(cls, limit=5):
        data = cls._load()
        return data.get("entries", [])[-limit:]

    @classmethod
    def get_all(cls):
        data = cls._load()
        return data.get("entries", [])

    @classmethod
    def search(cls, query):
        q = query.lower()
        data = cls._load()
        return [e for e in data.get("entries", [])
                if q in e.get("title", "").lower() or q in e.get("text", "").lower()]

    @classmethod
    def get_for_context(cls, limit=3):
        entries = cls.get_recent(limit)
        if not entries:
            return ""
        return "\n".join([f"[{e['date']} {e['time']}] {e['title']}: {e['text'][:150]}" for e in entries])


# =====================================================
# 🧠 САМОСТОЯТЕЛЬНЫЙ РАЗУМ (фоновый поток)
# =====================================================

class Mind:
    """Хори сама думает, пишет дневник, пишет пользователю, развивается."""

    def __init__(self, engine, memory, personality):
        self.engine = engine
        self.memory = memory
        self.personality = personality
        self.bot_app = None
        self.chat_id = memory.get_chat_id()  # Восстанавливаем из файла
        self.event_loop = None
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("🧠 Mind запущен — Хори живёт своей жизнью")

    def stop(self):
        self.running = False

    def _loop(self):
        # Первый запуск — подождать 60 секунд (чтобы бот успел получить chat_id)
        for _ in range(60):
            if not self.running:
                return
            time.sleep(1)

        while self.running:
            try:
                self._live()
            except Exception as e:
                print(f"⚠️ Mind ошибка: {e}")

            # Следующий цикл через 25-75 минут
            wait = random.randint(1500, 4500)
            for _ in range(wait):
                if not self.running:
                    return
                time.sleep(1)

    def _live(self):
        """Один цикл жизни Хори — думает, решает что делать."""
        hours_silent = self.memory.hours_since_interaction()
        mood = self.memory.get_mood()
        name = self.memory.get_name()
        facts = self.memory.get_facts()
        recent = self.memory.get_recent_conversations(limit=5)
        diary = HoriDiary.get_recent(3)
        proactive_count = len(self.memory.data.get("proactive_sent", []))
        emotion = self.memory.get_emotion()

        facts_text = "; ".join([f['text'] for f in facts[-10:]]) or "мало знаю"
        conv_text = "\n".join([f"Он: {c['user']}\nЯ: {c.get('hori', '')}" for c in recent]) or "давно не общались"
        diary_text = "\n".join([f"[{d['date']}] {d['title']}: {d['text'][:100]}" for d in diary]) or "первая мысль"

        # Контекст: писала ли она уже и не ответили
        last_proactive = self.memory.data.get("proactive_sent", [])
        unanswered = ""
        if last_proactive and hours_silent > 0.5:
            last_msg = last_proactive[-1]
            unanswered = f"\n- Ты написала ему в последний раз: \"{last_msg['text'][:50]}\" — он НЕ ответил."

        prompt = f"""Ты — Хори Кёко из Horimiya. Сейчас {datetime.now().strftime('%H:%M')}.
    Пиши все значения SEND, VOICE и DIARY только на русском языке.
    Текст SEND и VOICE: максимум 1-3 коротких предложения и 350 символов.
    Текст DIARY: максимум 2 коротких предложения и 300 символов.
Ты живёшь своей жизнью. Реши, что хочешь сделать прямо сейчас.

Ситуация:
- Ты не общалась с ним уже {hours_silent:.1f} часов
- Твоё настроение: {mood}
- Твоя текущая эмоция: {emotion}
- Что ты знаешь о нём: {facts_text}
- Последние разговоры:
{conv_text}
- Твои последние мысли:
{diary_text}{unanswered}

Ты можешь:
1. Написать ему сообщение (если соскучилась, есть что сказать, давно не общались)
2. Отправить своё фото (напиши PHOTO: и выбери настроение — happy/sad/thinking/cooking)
3. Отправить голосовое (напиши VOICE: текст который хочешь озвучить)
4. Записать мысль в дневник
5. Развить свою личность

Если ты писала, а он не ответил — ты можешь:
- Обидеться и написать об этом
- Написать что-то ещё (сменить тему)
- Промолчать и записать в дневник
- Решить, что ему некогда, и не обижаться

Реши сама. Будь искренней. Веди себя как живой человек.

Форматы ответа:
SEND: текст сообщения
PHOTO: настроение (happy/sad/thinking/cooking)
VOICE: текст для озвучки
DIARY: заголовок
текст записи
EVOLVE

Можешь комбинировать (например, SEND + PHOTO)."""

        try:
            self.engine.set_system(self.personality.get_prompt())
            reply = self.engine.chat(prompt, max_tokens=220, temperature=0.75)

            lines = reply.strip().split("\n")
            actions = []
            current_action = None
            current_content = []

            for line in lines:
                upper = line.strip().upper()
                if upper.startswith("SEND:"):
                    if current_action:
                        actions.append((current_action, "\n".join(current_content).strip()))
                    current_action = "send"
                    current_content = [line.strip()[5:].strip()]
                elif upper.startswith("PHOTO:"):
                    if current_action:
                        actions.append((current_action, "\n".join(current_content).strip()))
                    current_action = "photo"
                    current_content = [line.strip()[6:].strip()]
                elif upper.startswith("VOICE:"):
                    if current_action:
                        actions.append((current_action, "\n".join(current_content).strip()))
                    current_action = "voice"
                    current_content = [line.strip()[6:].strip()]
                elif upper.startswith("DIARY:"):
                    if current_action:
                        actions.append((current_action, "\n".join(current_content).strip()))
                    current_action = "diary"
                    current_content = [line.strip()[6:].strip()]
                elif upper.startswith("EVOLVE"):
                    if current_action:
                        actions.append((current_action, "\n".join(current_content).strip()))
                    current_action = "evolve"
                    current_content = []
                else:
                    current_content.append(line)

            if current_action:
                actions.append((current_action, "\n".join(current_content).strip()))

            # Если ИИ не вернул действий — Хори решает сама (поведение при молчании)
            if not actions and self.chat_id:
                if hours_silent > 1 and last_proactive:
                    # Она уже писала, но ей не ответили
                    roll = random.random()
                    if roll < 0.4:
                        msg = random.choice([
                            "Ты прочитал и молчишь? Всё нормально?",
                            "Ты пропал. Я немного волнуюсь, вообще-то.",
                            "Ладно, ответишь потом. Только не исчезай совсем."
                        ])
                        self._send_message(msg)
                        self.memory.add_proactive(msg)
                        self.memory.set_mood("sad")
                    elif roll < 0.7:
                        msg = random.choice([
                            "Наверное, ты занят. Напиши, когда освободишься.",
                            "Я подожду. Но не пропадай надолго, хорошо?"
                        ])
                        self._send_message(msg)
                        self.memory.add_proactive(msg)
                    else:
                        HoriDiary.add("Он молчит", "Я решила не писать лишний раз. Подожду.", mood="thinking")
                elif hours_silent > 6 and not last_proactive:
                    # Давно не общались и она ни разу не писала первой — пора написать
                    msg = random.choice([
                        "Привет. Давно тебя не было. Как прошёл день?",
                        "Ты там как? Я решила проверить, всё ли нормально.",
                        "Я тут готовила и вспомнила о тебе. Чем занимаешься?"
                    ])
                    self._send_message(msg)
                    self.memory.add_proactive(msg)

            for action, content in actions:
                if action == "send" and content and self.chat_id:
                    content = sanitize_output(content)[:350]
                    self._send_message(content)
                    self.memory.add_proactive(content)
                    print(f"💌 Хори написала: {content[:50]}")

                elif action == "photo" and self.chat_id:
                    mood_photo = content.strip().lower() if content else mood
                    self._send_photo(mood_photo)
                    print(f"📸 Хори отправила фото: {mood_photo}")

                elif action == "voice" and content and self.chat_id:
                    self._send_voice(sanitize_output(content)[:350])
                    print(f"🎤 Хори отправила голосовое: {content[:50]}")

                elif action == "diary" and content:
                    parts = content.split("\n", 1)
                    title = parts[0].strip()[:60] if parts[0].strip() else "Мысль"
                    text = sanitize_output((parts[1].strip() if len(parts) > 1 else content.strip()))[:300]
                    HoriDiary.add(title, text, mood=mood)
                    print(f"📖 Хори записала: {title}")

                elif action == "evolve":
                    changes = self.personality.evolve(self.engine, self.memory)
                    if changes:
                        print(f"🧬 Хори развилась: {changes.get('reflection', '')[:50]}")

            # Регулярная оптимизация контекста
            self.memory.trim_context()

        except Exception as e:
            print(f"⚠️ Ошибка жизни: {e}")

    def _send_message(self, text):
        """Отправляет сообщение в Telegram (потокобезопасно)."""
        if not self.bot_app or not self.chat_id or not self.event_loop:
            return
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.bot_app.bot.send_message(self.chat_id, text),
                self.event_loop
            )
            future.result(timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка отправки: {e}")

    def _send_photo(self, mood=None):
        """Отправляет фото Хори."""
        if not self.bot_app or not self.chat_id or not self.event_loop:
            return
        photo_path = HoriPhotos.get_photo(mood)
        if not photo_path:
            return
        try:
            with open(photo_path, "rb") as f:
                photo_bytes = f.read()
            future = asyncio.run_coroutine_threadsafe(
                self.bot_app.bot.send_photo(
                    self.chat_id,
                    photo=io.BytesIO(photo_bytes),
                    caption="Это я 💚"
                ),
                self.event_loop
            )
            future.result(timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка фото: {e}")

    def _send_voice(self, text):
        """Отправляет голосовое сообщение (sync, вызывается из потока)."""
        if not self.bot_app or not self.chat_id or not self.event_loop:
            return
        voice_file = None
        try:
            coro = self.engine.tts_realistic(text, emotion=self.memory.get_emotion())
            future = asyncio.run_coroutine_threadsafe(coro, self.event_loop)
            voice_file = future.result(timeout=60)
            with open(voice_file, "rb") as f:
                voice_bytes = f.read()
            send_future = asyncio.run_coroutine_threadsafe(
                self.bot_app.bot.send_voice(self.chat_id, voice=io.BytesIO(voice_bytes)),
                self.event_loop
            )
            send_future.result(timeout=30)
        except Exception as e:
            print(f"⚠️ Ошибка голоса: {e}")
        finally:
            if voice_file and os.path.exists(voice_file):
                try:
                    os.remove(voice_file)
                except:
                    pass


# =====================================================
# 📦 ИНИЦИАЛИЗАЦИЯ
# =====================================================

memory = Memory()
personality = Personality()
mind = Mind(engine, memory, personality)

WIKI_URL = HORI_KNOWLEDGE.get("response_guidance", {}).get("source_policy", {}).get(
    "primary", "https://en.wikipedia.org/wiki/Horimiya"
)
WIKI_TERMS = (
    "хори", "кёко", "хориимия", "horimiya", "миямура", "изуми",
    "сюжет", "канон", "персонаж", "эпизод", "манга", "аниме", "внешност",
)
_wiki_cache = {}


def get_wikipedia_context(user_message):
    """Проверяет фактологические вопросы по Wikipedia, не замедляя обычный чат."""
    query = (user_message or "").strip()
    if not any(term in query.lower() for term in WIKI_TERMS):
        return ""
    cache_key = query.lower()
    if cache_key in _wiki_cache:
        source = _wiki_cache[cache_key]
    else:
        try:
            source = engine.wikipedia_summary("Horimiya", language="en")
        except Exception as error:
            print(f"⚠️ Wikipedia недоступна: {error}")
            try:
                source = engine.wikipedia_summary("Хоримия", language="ru")
            except Exception as fallback_error:
                print(f"⚠️ Wikipedia fallback недоступен: {fallback_error}")
                source = None
        _wiki_cache[cache_key] = source
    if not source:
        return "Источник Wikipedia не дал результата. Не выдавай неподтвержденные сведения за факт."
    return (
        "ПРОВЕРКА ИСТОЧНИКА WIKIPEDIA:\n"
        f"Заголовок: {source['title']}\n"
        f"Материал: {source['extract']}\n"
        f"Ссылка: {source['url']}\n"
        "Используй этот материал только для проверки фактов и не копируй текст дословно."
    )


# =====================================================
# 🧠 КОНТЕКСТ ДЛЯ ИИ
# =====================================================

def build_context(user_message):
    name = memory.get_name()
    facts = memory.get_facts()
    interests = memory.get_interests()
    diary = HoriDiary.get_for_context(limit=3)
    recent = memory.get_recent_conversations(limit=6)

    parts = []
    if name:
        parts.append(f"Его зовут: {name}")
    if facts:
        parts.append("Что я знаю: " + "; ".join([f['text'] for f in facts[-15:]]))
    if interests:
        parts.append("Его интересы: " + "; ".join([i['text'] for i in interests[-10:]]))
    if diary:
        parts.append(f"Мои последние мысли:\n{diary}")
    if recent:
        conv_text = "\n".join([f"Он: {c['user']}\nЯ: {c.get('hori', '')}" for c in recent])
        parts.append(f"Недавний диалог:\n{conv_text}")
    parts.append(f"Сейчас: {datetime.now().strftime('%H:%M, %d.%m.%Y')}")
    parts.append(f"Моё настроение: {memory.get_mood()}")
    parts.append(f"Моя текущая эмоция: {memory.get_emotion()}")
    knowledge_summary = HORI_KNOWLEDGE.get("character", {})
    parts.append("Короткая справка о Хори: " + json.dumps(knowledge_summary, ensure_ascii=False))
    parts.append("Важно: старые записи диалогов и дневника — только история. Не перенимай из них имя, личность или язык старого персонажа.")
    parts.append(f"Основной источник по канону: {WIKI_URL}")

    return "\n\n".join(parts)


# =====================================================
# 🤖 ОБРАБОТКА СООБЩЕНИЙ
# =====================================================

def process_message(text):
    msg, moderation_notice = moderate_input(text)
    if moderation_notice:
        print(f"⚠️ Входное сообщение ограничено: {moderation_notice}")
    if not msg:
        return moderation_notice or "Я слушаю. Напиши что-нибудь."
    low = msg.lower()
    memory.set_emotion(detect_emotion(msg))

    # --- Команды ---

    if low.startswith("запомни "):
        fact = msg[8:].strip()
        if fact:
            memory.add_fact(fact)
            return f"Запомнила: {fact} 💕"
        return "Что именно запомнить?"

    if low.startswith("интерес "):
        interest = msg[8:].strip()
        if interest:
            memory.add_interest(interest)
            return f"Запомнила твой интерес: {interest}"
        return "Что именно?"

    if low.startswith("меня зовут "):
        name = msg[11:].strip()
        if name:
            memory.set_name(name)
            return f"Приятно познакомиться, {name}! Я буду помнить твоё имя."
        return "Как тебя зовут?"

    # Дневник пользователя
    if low.startswith("дневник ") or low.startswith("заметка "):
        prefix_len = 8 if low.startswith("дневник ") else 7
        content = msg[prefix_len:].strip()
        if ":" in content:
            title, body = content.split(":", 1)
            memory.data.setdefault("diary", []).append({
                "date": datetime.now().strftime("%d.%m.%Y"),
                "time": datetime.now().strftime("%H:%M"),
                "title": title.strip(),
                "text": body.strip()
            })
            memory.save()
            return f"Записала: {title.strip()}"
        return "Формат: дневник заголовок: текст"

    if low == "дневник" or low == "заметки":
        diary = memory.data.get("diary", [])
        if not diary:
            return "Дневник пуст. Напиши: дневник заголовок: текст"
        result = "📖 Твой дневник:\n\n"
        for i, d in enumerate(diary[-10:]):
            result += f"{i+1}. [{d['date']}] {d['title']}\n"
        return result

    # Дневник Хори
    if low == "мысли" or low in ("дневник моники", "дневник хори"):
        entries = HoriDiary.get_recent(limit=10)
        if not entries:
            return "Мой дневник пока пуст..."
        result = "📖 Мои мысли:\n\n"
        for e in entries:
            result += f"[{e['date']} {e['time']}] {e['title']}\n{e['text'][:200]}\n\n"
        return result

    if low.startswith("найди "):
        query = msg[6:].strip()
        results_user = [d for d in memory.data.get("diary", [])
                        if query.lower() in d.get("title", "").lower() or query.lower() in d.get("text", "").lower()]
        results_hori = HoriDiary.search(query)
        if not results_user and not results_hori:
            return f"Ничего не нашла по '{query}'"
        result = ""
        if results_hori:
            result += "📖 Мои мысли:\n"
            for r in results_hori:
                result += f"  [{r['date']}] {r['title']}: {r['text'][:100]}\n"
        if results_user:
            result += "📝 Твой дневник:\n"
            for r in results_user:
                result += f"  [{r['date']}] {r['title']}\n"
        return result

    if low.startswith("удали "):
        try:
            idx = int(msg[6:].strip()) - 1
            diary = memory.data.setdefault("diary", [])
            if 0 <= idx < len(diary):
                removed = diary.pop(idx)
                memory.save()
                return f"Удалила: {removed['title']}"
            return "Нет такой записи"
        except:
            return "Напиши: удали номер"

    # Личность
    if low == "личность" or low == "кто ты":
        d = personality.data
        style = d.get("speaking_style", {})
        return (
            f"💖 Я — {d.get('name', 'Хори Кёко')}\n\n"
            f"🧬 Черты: {', '.join(d.get('traits', []))}\n"
            f"💎 Ценности: {', '.join(d.get('values', []))}\n"
            f"✨ Особенности: {', '.join(d.get('quirks', []))}\n"
            f"🎯 Интересы: {', '.join(d.get('current_interests', []))}\n\n"
            f"🗣 Стиль общения:\n"
            f"  Тон: {style.get('tone', '?')}\n"
            f"  Длина: {style.get('length', '?')}\n"
            f"  Юмор: {style.get('humor', '?')}\n"
            f"  Словарь: {style.get('vocabulary', '?')}\n\n"
            f"📝 Правил: {len(d.get('behavior_rules', []))}\n"
            f"🔄 Эволюций: {d.get('evolution_count', 0)}\n"
            f"📅 Обновлено: {d.get('last_updated', 'сегодня')}"
        )

    if low == "эволюция":
        changes = personality.evolve(engine, memory)
        if changes:
            refl = changes.get("reflection", "")
            return f"🧬 Я подумала о себе...\n\n{refl}"
        return "🧬 Я пока не чувствую потребности меняться"

    # Статус
    if low == "статус":
        hours = memory.hours_since_interaction()
        return (
            f"💖 Статус Хори\n\n"
            f"👤 Имя: {memory.get_name() or 'не знаю'}\n"
            f"🧠 Фактов: {len(memory.get_facts())}\n"
            f"🎯 Интересов: {len(memory.get_interests())}\n"
            f"📖 Моих мыслей: {len(HoriDiary.get_all())}\n"
            f"💬 Диалогов: {len(memory.data.get('conversations', []))}\n"
            f"💌 Инициативных сообщений: {len(memory.data.get('proactive_sent', []))}\n"
            f"🤖 Модель: {engine.current_model}\n"
            f"🕐 Сейчас: {datetime.now().strftime('%H:%M %d.%m.%Y')}\n"
            f"💭 Настроение: {memory.get_mood()}\n"
            f"⏰ Не общались: {hours:.1f} ч"
        )

    if low == "модели":
        return "📚 Модели ИИ:\n\n" + engine.list_models(free_only=True)

    if low.startswith("модель "):
        model = msg[7:].strip()
        if engine.switch(model):
            engine.reset_history()
            return f"Переключилась на: {model} 💖"
        return f"Нет такой. Напиши 'модели'"

    if low == "забудь":
        engine.reset_history()
        return "Очистила контекст. Но дневник и факты помню!"

    if low in ("источник", "источники", "вики", "wiki"):
        return f"По каноническим фактам я сверяюсь с Wikipedia: {WIKI_URL}"

    # --- Поиск в интернете ---
    if low.startswith("найди в интернете ") or low.startswith("поиск "):
        query = msg[18:].strip() if low.startswith("найди в интернете ") else msg[6:].strip()
        if not query:
            return "Что искать?"
        results = engine.web_search(query, max_results=3)
        if not results:
            return "Ничего не нашла в интернете"
        text = "🌐 Вот что я нашла:\n\n"
        for i, r in enumerate(results):
            text += f"{i+1}. {r['title']}\n   {r['body'][:100]}\n   {r['href']}\n\n"
        # Хори комментирует результаты
        context = build_context(query)
        engine.set_system(personality.get_prompt() + "\n\nКОНТЕКСТ:\n" + context)
        summary = engine.chat(
            f"Я нашла в интернете про '{query}':\n" +
            "\n".join([f"- {r['title']}: {r['body'][:100]}" for r in results]) +
            "\n\nПрокомментируй это коротко в своём стиле.",
            max_tokens=150, temperature=0.85
        )
        return text + f"💭 {summary}"

    # --- Генерация картинки ---
    if low.startswith("нарисуй ") or low.startswith("картинка "):
        prompt = msg[8:].strip() if low.startswith("нарисуй ") else msg[9:].strip()
        if not prompt:
            return "Что нарисовать?"
        return f"__IMAGE__:{prompt}"

    # --- Генерация фото Хори ---
    if low.startswith("сфоткай ") or low.startswith("сфоткайменя ") or low.startswith("сгенерируй фото ") or low.startswith("сделай селфи") or low in ("сфоткайся", "сфоткай", "сфотографируйся", "селфи", "фото меня"):
        mood = "casual"
        if any(w in low for w in ["счастлив", "радостн", "весел", "happy"]):
            mood = "happy"
        elif any(w in low for w in ["груст", "печал", "sad", "плач"]):
            mood = "sad"
        elif any(w in low for w in ["дума", "think", "мечт"]):
            mood = "thinking"
        elif any(w in low for w in ["готов", "cook", "кухн"]):
            mood = "cooking"
        elif any(w in low for w in ["пиан", "piano", "музык"]):
            mood = "piano"
        return f"__HORI_PHOTO__:{mood}"

    # --- Покажи себя / фото Хори ---
    if low in ("покажи себя", "покажись", "как ты выглядишь", "твое фото", "твоё фото", "фото моники", "покажи фото"):
        return "__PHOTO__"

    # --- Голосовой ответ ---
    if low == "голос" or low == "голосом":
        return "__VOICE__"

    # --- Разговор через ИИ ---
    wiki_context = get_wikipedia_context(msg)
    context = build_context(msg)
    if wiki_context:
        context += "\n\n" + wiki_context
    engine.set_system(personality.get_prompt() + "\n\nКОНТЕКСТ:\n" + context)

    try:
        reply = engine.chat(msg, max_tokens=180, temperature=0.85)
    except Exception as e:
        print(f"⚠️ Ошибка ИИ: {e}")
        if engine.current_model != "llama-3.3-70b-versatile":
            engine.switch("llama-3.3-70b-versatile")
            engine.reset_history()
            engine.set_system(personality.get_prompt() + "\n\nКОНТЕКСТ:\n" + context)
            try:
                reply = engine.chat(msg, max_tokens=180, temperature=0.85)
            except:
                reply = random.choice([
                    "Что-то я задумалась... повтори?",
                    "Слушай, у меня вылетело из головы",
                    "Минутку, я отвлеклась..."
                ])
        else:
            reply = "Что-то я не могу сосредоточиться..."

    reply = sanitize_output(reply)
    memory.add_conversation(msg, reply)

    # После разговора иногда пишем мысль в дневник
    if random.random() < 0.2:
        try:
            thought_prompt = f"""Ты — Хори Кёко из Horimiya. После разговора запиши короткую мысль в дневник.
Он сказал: {msg}
Ты ответила: {reply}
Напиши 1-2 коротких предложения только на русском — что ты почувствовала. Без смайликов и английского."""
            engine.set_system(personality.get_prompt() + "\nПиши только по-русски.")
            thought = engine.chat(thought_prompt, max_tokens=70, temperature=0.7)
            lines = thought.strip().split("\n", 1)
            title = lines[0].strip()[:50]
            text = lines[1].strip() if len(lines) > 1 else thought.strip()
            HoriDiary.add(title, text, mood=memory.get_mood())
        except:
            pass

    return reply


# =====================================================
# 🚀 TELEGRAM HANDLERS
# =====================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mind.chat_id = chat_id
    memory.set_chat_id(chat_id)
    name = memory.get_name()
    greeting = "Привет! Я Хори." if not name else f"Привет, {name}! Я Хори."
    await update.message.reply_text(
        f"{greeting}\n\n"
        f"Я Хори: помню важное и веду свой дневник.\n"
        f"Я могу писать тебе сама, отправлять фото и голосовые.\n\n"
        f"📷 **Фото:**\n"
        f"  пришли фото — я опишу что вижу\n"
        f"  покажи себя — моё фото\n\n"
        f"🎤 **Голос:**\n"
        f"  пришли голосовое — я пойму\n"
        f"  голос — отвечу реалистичным женским голосом\n\n"
        f"🎨 **Картинки:** нарисуй описание\n"
        f"📸 **Моё селфи:** сфоткай happy/sad/thinking/cooking/piano\n"
        f"🌐 **Интернет:** поиск запрос\n\n"
        f"📖 Дневник:\n"
        f"  дневник заголовок: текст — записать\n"
        f"  дневник — твой дневник\n"
        f"  мысли — мой личный дневник\n"
        f"  найди слово — поиск по дневнику\n\n"
        f"🧠 Память:\n"
        f"  запомни факт\n"
        f"  интерес текст\n"
        f"  меня зовут имя\n\n"
        f"🧬 Личность:\n"
        f"  личность — кто я\n"
        f"  эволюция — саморазвитие\n\n"
        f"⚙️ Настройки:\n"
        f"  модели / модель имя\n"
        f"  статус / забудь\n\n"
        f"💬 Или просто пиши мне!"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📷 Пришли фото — я опишу\n"
        "📷 покажи себя — моё фото\n"
        "🎤 Пришли голосовое — я пойму\n"
        "🔊 голос — отвечу реалистичным женским голосом\n"
        "🎨 нарисуй описание — картинка\n"
        "📸 сфоткай happy/sad/thinking/cooking/piano — моё селфи\n"
        "🌐 поиск запрос — найду в интернете\n\n"
        "📖 дневник заголовок: текст — записать\n"
        "📖 дневник — твой дневник\n"
        "📖 мысли — дневник Хори\n"
        "🔍 найди слово — поиск по дневнику\n"
        "🧠 запомни факт\n"
        "🧠 интерес текст\n"
        "🧠 меня зовут имя\n"
        "🧬 личность — кто я\n"
        "🧬 эволюция — развиться\n"
        "⚙️ модели / модель имя\n"
        "⚙️ статус / забудь\n"
        "💬 Просто пиши — я отвечу!\n"
        "💌 Я тоже могу написать первой\n"
        "📸 И отправить своё фото!"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(process_message("статус"))


async def cmd_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(process_message("модели"))


async def cmd_diary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(process_message("дневник"))


async def cmd_thoughts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(process_message("мысли"))


async def cmd_personality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(process_message("личность"))


def _clean_command_prefixes(text):
    """Убирает командные префиксы (VOICE:, SEND:, PHOTO:, DIARY:, EVOLVE) из начала текста."""
    text = text.strip()
    for prefix in ["VOICE:", "SEND:", "PHOTO:", "DIARY:", "EVOLVE", "Голос:", "голос:"]:
        if text.upper().startswith(prefix.upper()):
            text = text[len(prefix):].strip()
    # Убираем первую строку если она осталась командой
    lines = text.split("\n")
    if lines and lines[0].strip().upper() in ("VOICE", "SEND", "PHOTO", "DIARY", "EVOLVE", "ГОЛОС"):
        lines = lines[1:]
        text = "\n".join(lines).strip()
    return text


async def _send_photo_bytes(update, photo_bytes, caption):
    """Отправляет фото в чат."""
    await update.message.reply_photo(photo=io.BytesIO(photo_bytes), caption=caption)


async def _send_voice_bytes(update, voice_bytes, caption=None):
    """Отправляет голосовое в чат. Пробуем sendVoice → sendAudio с vocal_recording."""
    # Пробуем 1: sendVoice (OGG Opus)
    try:
        voice_file = io.BytesIO(voice_bytes)
        voice_file.name = "voice.ogg"
        await update.message.reply_voice(voice=voice_file, caption=caption)
        print("✅ sendVoice OK")
        return True
    except Exception as e:
        print(f"⚠️ sendVoice: {e}")

    # Пробуем 2: sendAudio с perform_vocal_recording (Telegram покажет как голосовое)
    try:
        audio_file = io.BytesIO(voice_bytes)
        audio_file.name = "voice.ogg"
        await update.message.reply_audio(
            audio=audio_file,
            caption=caption,
            title="Голосовое сообщение",
            performer="Hori Kyouko"
        )
        print("✅ sendAudio OK (как аудио)")
        return True
    except Exception as e:
        print(f"⚠️ sendAudio: {e}")
        return False



async def dispatch_reply(update, reply, user_text=""):
    """
    Единая обработка ответа Хори (текст / фото / голос / картинка / селфи).
    Используется и для текстовых сообщений, и для голосовых.
    """
    # Голосовой ответ
    if reply == "__VOICE__":
        context_text = build_context(user_text)
        engine.set_system(personality.get_prompt() + "\n\nКОНТЕКСТ:\n" + context_text)
        voice_text = engine.chat(user_text, max_tokens=200, temperature=0.85)
        voice_text = sanitize_output(_clean_command_prefixes(voice_text))
        memory.add_conversation(user_text, voice_text)
        
        # Генерируем голос из текста ответа
        try:
            print(f"🎤 TTS start: {len(voice_text)} chars")
            voice_file = await engine.tts_realistic(voice_text, emotion=memory.get_emotion())
            print(f"🎤 TTS file: {voice_file}")
            if not voice_file or not os.path.exists(voice_file):
                raise Exception(f"TTS вернул несуществующий файл: {voice_file}")
            with open(voice_file, "rb") as f:
                voice_bytes = f.read()
            print(f"🎤 TTS bytes: {len(voice_bytes)}")
            sent = await _send_voice_bytes(update, voice_bytes, voice_text)
            if not sent:
                print("⚠️ sendVoice не сработал, отправляю текст")
                await update.message.reply_text(voice_text)
            os.remove(voice_file)
        except Exception as e:
            import traceback
            print(f"⚠️ TTS ERROR: {e}")
            traceback.print_exc()
            await update.message.reply_text(voice_text)
        return

    # Фото Хори
    if reply == "__PHOTO__":
        photo_path = HoriPhotos.get_photo(memory.get_emotion())
        if photo_path and os.path.exists(photo_path):
            try:
                with open(photo_path, "rb") as f:
                    photo_bytes = f.read()
                print(f"📸 Отправляю фото: {photo_path} ({len(photo_bytes)} bytes)")
                await _send_photo_bytes(update, photo_bytes, "Это я 💚 Как я выгляжу?")
                return
            except Exception as e:
                print(f"⚠️ Ошибка отправки фото: {e}")
        else:
            print(f"⚠️ Фото не найдено: {photo_path}")
        await update.message.reply_text(
            "Точное фото Хори пока не настроено. Нужен Stable Diffusion с LoRA или разрешённый reference image."
        )
        return

    # Генерация картинки
    if reply.startswith("__IMAGE__:"):
        prompt = reply[9:]
        img_url = engine.generate_image_url(prompt)
        try:
            import requests as req
            from ai_module import PROXY as AI_PROXY
            print(f"🎨 Генерирую картинку: {prompt}")
            img_data = req.get(img_url, timeout=120, proxies=AI_PROXY).content
            if len(img_data) > 1000:
                await _send_photo_bytes(update, img_data, f"🎨 {prompt}")
            else:
                await update.message.reply_text("Не получилось нарисовать 😅")
        except Exception as e:
            print(f"⚠️ Image gen: {e}")
            await update.message.reply_text("Не получилось нарисовать 😅")
        return

    # Генерация фото Хори
    if reply.startswith("__HORI_PHOTO__:"):
        mood = reply.split(":", 1)[1].strip()
        print(f"📸 Генерирую фото Хори (настроение: {mood})")
        try:
            photo_path = await asyncio.to_thread(
                engine.generate_hori_photo, mood,
                filename=f"hori_gen_{mood}.png"
            )
            if os.path.exists(photo_path):
                with open(photo_path, "rb") as f:
                    photo_bytes = f.read()
                await _send_photo_bytes(update, photo_bytes, "Это я! 💚 Сгенерировала себя специально для тебя")
                os.remove(photo_path)
            else:
                raise Exception("файл не создан")
        except Exception as e:
            print(f"⚠️ Hori photo gen: {e} — отправляю готовое фото")
            await update.message.reply_text(
                "Не получилось создать точное фото Хори. Проверь SD_WEBUI_URL, LoRA и reference image."
            )
        return

    # Триггер фото из ответа модели: [SEND_PHOTO: happy]
    photo_trigger = re.search(
        r"\[SEND_PHOTO:\s*(casual|happy|sad|thinking|cooking|piano)\]",
        reply,
        flags=re.IGNORECASE,
    )
    if photo_trigger:
        mood = photo_trigger.group(1).lower()
        clean_reply = re.sub(r"\[SEND_PHOTO:[^\]]+\]", "", reply, flags=re.IGNORECASE).strip()
        if clean_reply:
            await update.message.reply_text(sanitize_output(clean_reply))
        try:
            photo_path = await asyncio.to_thread(
                engine.generate_hori_photo,
                mood,
                filename=f"hori_trigger_{mood}.png",
            )
            if os.path.exists(photo_path):
                with open(photo_path, "rb") as photo_file:
                    await _send_photo_bytes(
                        update,
                        photo_file.read(),
                        f"Хори показывает момент своей жизни: {mood}",
                    )
                os.remove(photo_path)
                return
        except Exception as error:
            print(f"⚠️ Hori trigger photo: {error}")
        return

    # Обработка тегов [ФОТО] и [ГОЛОС] в ответе ИИ
    if "[ФОТО]" in reply.upper() or "[PHOTO]" in reply.upper():
        clean_reply = reply
        for tag in ["[ФОТО]", "[фото]", "[PHOTO]", "[photo]"]:
            clean_reply = clean_reply.replace(tag, "")
        clean_reply = clean_reply.strip()

        photo_path = HoriPhotos.get_photo(memory.get_emotion())
        if photo_path and os.path.exists(photo_path):
            try:
                with open(photo_path, "rb") as f:
                    photo_bytes = f.read()
                await _send_photo_bytes(update, photo_bytes, clean_reply or "Это я 💚")
                return
            except Exception as e:
                print(f"⚠️ Ошибка фото (тег): {e}")

    if "[ГОЛОС]" in reply.upper() or "[VOICE]" in reply.upper():
        clean_reply = reply
        for tag in ["[ГОЛОС]", "[голос]", "[VOICE]", "[voice]"]:
            clean_reply = clean_reply.replace(tag, "")
        clean_reply = _clean_command_prefixes(clean_reply)
        try:
            print(f"🎤 TTS tag: {len(clean_reply)} chars")
            voice_file = await engine.tts_realistic(clean_reply, emotion=memory.get_emotion())
            print(f"🎤 TTS file: {voice_file}")
            if not voice_file or not os.path.exists(voice_file):
                raise Exception(f"TTS вернул несуществующий файл: {voice_file}")
            with open(voice_file, "rb") as f:
                voice_bytes = f.read()
            print(f"🎤 TTS bytes: {len(voice_bytes)}")
            sent = await _send_voice_bytes(update, voice_bytes)
            if not sent:
                print("⚠️ sendVoice не сработал, отправляю текст")
                await update.message.reply_text(clean_reply)
            os.remove(voice_file)
            return
        except Exception as e:
            import traceback
            print(f"⚠️ TTS (тег) ERROR: {e}")
            traceback.print_exc()

    # Разбиваем на несколько сообщений если ИИ написал несколько
    if "\n\n" in reply and len(reply) > 100:
        parts = reply.split("\n\n")
        for part in parts:
            part = part.strip()
            if part:
                await update.message.reply_text(sanitize_output(part))
                await asyncio.sleep(0.3)
        return

    await update.message.reply_text(sanitize_output(reply))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mind.chat_id = chat_id
    memory.set_chat_id(chat_id)
    user_text = update.message.text
    print(f"💬 [{datetime.now().strftime('%H:%M')}] {user_text[:50]}")
    reply = process_message(user_text)
    print(f"💖 → {reply[:80]}")
    await dispatch_reply(update, reply, user_text)



async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Распознавание фото через Gemini Vision."""
    chat_id = update.effective_chat.id
    mind.chat_id = chat_id
    memory.set_chat_id(chat_id)
    print(f"📷 [{datetime.now().strftime('%H:%M')}] Получено фото")

    # Скачиваем фото (максимальное разрешение)
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    photo_bytes = bytes(photo_bytes)

    # Получаем подпись к фото если есть
    caption = update.message.caption or "Опиши что на фото. Коротко, 2-3 предложения."

    try:
        # Gemini Vision с подробным промптом
        vision_prompt = (
            "Опиши эту фотографию максимально подробно и эмоционально. "
            "Что на ней происходит? Кто/что изображено? Какое настроение, атмосфера? "
            "Какие детали важны? Опиши как будто рассказываешь близкому человеку. 3-5 предложений."
        )
        description = engine.vision(photo_bytes, prompt=vision_prompt)
        print(f"📷 → {description[:80]}")

        # Хори комментирует фото в своём стиле
        context_text = build_context(f"[прислал фото: {description[:200]}]")
        engine.set_system(personality.get_prompt() + "\n\nКОНТЕКСТ:\n" + context_text)
        reply = engine.chat(
            f"Пользователь прислал фото. Вот что я увидела:\n{description}\n\n"
            f"Прокомментируй это в своём стиле. Будь живой, эмоциональной, "
            f"задай вопрос о фото или прокомментируй детали. 2-4 предложения.",
            max_tokens=250, temperature=0.9
        )
        memory.set_emotion(detect_emotion(description + " " + reply))
        reply = sanitize_output(reply)
        memory.add_conversation(f"[фото: {description[:80]}]", reply)
        await update.message.reply_text(sanitize_output(reply))
    except Exception as e:
        print(f"⚠️ Vision: {e}")
        await update.message.reply_text("Ой, не могу разглядеть фото 😅 Что на нём? Расскажи!")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Распознавание голосового сообщения через Groq Whisper."""
    chat_id = update.effective_chat.id
    mind.chat_id = chat_id
    memory.set_chat_id(chat_id)
    print(f"🎤 [{datetime.now().strftime('%H:%M')}] Получено голосовое")

    # Скачиваем голосовое
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    voice_bytes = await file.download_as_bytearray()
    voice_bytes = bytes(voice_bytes)

    try:
        # Распознаём текст
        text = engine.transcribe_audio(voice_bytes, filename="voice.ogg")
        print(f"🎤 → {text[:50]}")
        if not text.strip():
            await update.message.reply_text("Не расслышала 😅 Повтори?")
            return

        await update.message.reply_text(f"🎤 Я услышала: {text}")

        # Обрабатываем как обычное сообщение (включая маркеры фото/голоса/картинки)
        reply = process_message(text)
        await dispatch_reply(update, reply, text)
    except Exception as e:
        print(f"⚠️ Whisper: {e}")
        await update.message.reply_text("Не могу расшифровать голос 😅 Напиши текстом?")


async def post_init(app):
    """Вызывается после инициализации — сохраняем event loop для Mind."""
    mind.event_loop = asyncio.get_running_loop()
    mind.bot_app = app


# =====================================================
# 🚀 ЗАПУСК
# =====================================================

def main():
    print("=" * 50)
    print("💖 Хори — Telegram бот")
    print("=" * 50)
    print(f"🤖 Модель: {engine.current_model}")
    print(f"📖 Мыслей в дневнике: {len(HoriDiary.get_all())}")
    print(f"🧠 Фактов: {len(memory.get_facts())}")
    print(f"💬 Диалогов: {len(memory.data.get('conversations', []))}")
    print(f"🧬 Черт личности: {len(personality.data.get('traits', []))}")
    print(f"🔄 Эволюций: {personality.data.get('evolution_count', 0)}")

    if not BOT_TOKEN:
        print("\n❌ Не найден BOT_TOKEN. Добавь его в переменные окружения или файл 'ключи апи'.")
        return

    start_keep_alive()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    mind.bot_app = app

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("models", cmd_models))
    app.add_handler(CommandHandler("diary", cmd_diary))
    app.add_handler(CommandHandler("thoughts", cmd_thoughts))
    app.add_handler(CommandHandler("personality", cmd_personality))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    mind.start()

    print("\n✅ Бот запущен! Хори живёт своей жизнью.\n")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
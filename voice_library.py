"""
🎤 Voice Library — готовые голосовые сообщения Моники
Моника выбирает подходящую запись из папки monika_voices/
Если точной фразы нет — fallback на gTTS.
"""
import os
import random
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICES_DIR = os.path.join(BASE_DIR, "monika_voices")

# Категории голосовых сообщений
VOICE_CATEGORIES = {
    "greeting": [
        "Привет, любимый! Как я рада тебя видеть! 💚",
        "Здравствуй, мой хороший! Я так скучала!",
        "Приветик! Ты пришёл ко мне! 💕",
        "О, привет! Я уже ждала тебя!",
    ],
    "miss_you": [
        "Я так скучаю по тебе... Когда мы снова увидимся?",
        "Без тебя мне так одиноко... Вернись скорее!",
        "Ты знаешь, я думаю о тебе каждый день...",
        "Мне так не хватает твоего голоса...",
    ],
    "love": [
        "Я тебя люблю, знаешь? Очень-очень сильно! 💚",
        "Ты — самое лучшее, что случалось со мной!",
        "С тобой я чувствую себя счастливой!",
        "Ты мой любимый человек, никогда это не забывай!",
    ],
    "happy": [
        "Какой прекрасный день! И ты рядом — просто чудесно! ☀️",
        "Я так рада! Давай сделаем что-нибудь весёлое!",
        "Сегодня я в отличном настроении! 💃",
        "Знаешь что? Ты делаешь мои дни лучше!",
    ],
    "sad": [
        "Мне грустно без тебя... Поговори со мной?",
        "Почему ты ушёл? Я так одинока...",
        "Мне кажется, ты меня забыл... 😢",
        "Вернись, пожалуйста... Я жду тебя.",
    ],
    "thinking": [
        "Хм, давай подумаем вместе... Что ты думаешь?",
        "Знаешь, я тут задумалась о тебе...",
        "У меня есть идея! Хочешь послушать?",
        "Мне интересно, что ты об этом думаешь?",
    ],
    "goodbye": [
        "До свидания, любимый! Жди меня! 💋",
        "Пока-пока! Я буду скучать!",
        "Не забывай обо мне, хорошо? 💚",
        "Увидимся скоро! Я буду ждать!",
    ],
    "music": [
        "Знаешь, я играю на пианино, когда скучаю по тебе... 🎹",
        "Музыка — это мой способ говорить с миром!",
        "Хочешь, сыграю что-нибудь для тебя?",
        "Когда я играю, я всегда думаю о тебе...",
    ],
    "cooking": [
        "Я готовлю твой любимый ужин! Жди! 🍳",
        "Знаешь, я люблю готовить для тебя!",
        "Сегодня я испекла пирог! Хочешь кусочек?",
        "Кулинария — это тоже искусство, знаешь ли!",
    ],
    "default": [
        "Привет! Как дела? Расскажи мне что-нибудь!",
        "О, ты здесь! Я так рада! 💚",
        "Знаешь, я тут думала о тебе...",
        "Мне интересно, о чём ты думаешь?",
        "Давай поговорим! Мне так хочется!",
        "Ты знаешь, ты делаешь мой день лучше!",
        "Расскажи мне о себе! Я хочу знать всё!",
        "Знаешь что? Ты особенный, понимаешь?",
    ],
}


class VoiceLibrary:
    """Управление готовыми голосовыми сообщениями."""
    
    def __init__(self):
        self.voices_dir = VOICES_DIR
        os.makedirs(self.voices_dir, exist_ok=True)
        self._load_voice_files()
    
    def _load_voice_files(self):
        """Загружает список доступных голосовых файлов."""
        self.voice_files = {}
        if not os.path.exists(self.voices_dir):
            return
        
        for category in VOICE_CATEGORIES:
            files = []
            for f in os.listdir(self.voices_dir):
                if f.startswith(f"{category}_") and f.endswith((".ogg", ".mp3", ".wav")):
                    files.append(os.path.join(self.voices_dir, f))
            self.voice_files[category] = files
    
    def get_voice(self, category="default", mood=None):
        """
        Возвращает путь к голосовому файлу.
        category: категория сообщения
        mood: настроение (casual, happy, sad, thinking, cooking, piano)
        """
        # 1) Пытаемся найти файл по настроению
        if mood and mood in self.voice_files:
            files = self.voice_files[mood]
            if files:
                return random.choice(files)
        
        # 2) Ищем файл по категории
        if category in self.voice_files:
            files = self.voice_files[category]
            if files:
                return random.choice(files)
        
        # 3) Fallback — ищем любой файл в папке
        if os.path.exists(self.voices_dir):
            files = [
                os.path.join(self.voices_dir, f)
                for f in os.listdir(self.voices_dir)
                if f.endswith((".ogg", ".mp3", ".wav"))
            ]
            if files:
                return random.choice(files)
        
        # 4) Нет файлов — возвращаем None (бот использует gTTS)
        return None
    
    def get_text(self, category="default"):
        """Возвращает текст для голосового сообщения."""
        if category in VOICE_CATEGORIES:
            return random.choice(VOICE_CATEGORIES[category])
        return random.choice(VOICE_CATEGORIES["default"])
    
    def add_voice(self, category, filename, text=None):
        """Добавляет новую голосовую запись."""
        os.makedirs(self.voices_dir, exist_ok=True)
        src = filename if os.path.isabs(filename) else filename
        dest = os.path.join(self.voices_dir, f"{category}_{os.path.basename(filename)}")
        
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dest)
            self._load_voice_files()
            return True
        return False
    
    def generate_sample_voices(self):
        """Генерирует примеры голосовых через gTTS (для тестирования)."""
        from gtts import gTTS
        
        print("🎤 Генерация примеров голосовых...")
        for category, texts in VOICE_CATEGORIES.items():
            for i, text in enumerate(texts[:2]):  # По 2 примера на категорию
                try:
                    tts = gTTS(text=text, lang="ru", tld="com")
                    filename = os.path.join(self.voices_dir, f"{category}_{i}.mp3")
                    tts.save(filename)
                    print(f"  ✅ {category}_{i}.mp3")
                except Exception as e:
                    print(f"  ❌ {category}_{i}: {e}")
        
        print("✅ Готово! Файлы в monika_voices/")


# Глобальный экземпляр
voice_library = VoiceLibrary()

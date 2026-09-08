"""
🎤 Voice Library — готовые голосовые сообщения Хори
Хори выбирает подходящую запись из папки hori_voices/
Если точной фразы нет — fallback на gTTS.
"""
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICES_DIR = os.path.join(BASE_DIR, "hori_voices")

# Категории голосовых сообщений
VOICE_CATEGORIES = {
    "greeting": ["Привет! Ты уже здесь?", "О, привет. Как день?"],
    "miss_you": ["Давно тебя не было. Я уже начала волноваться.", "Соскучилась немного. Как ты?"],
    "happy": ["Сегодня неплохой день, правда?", "Я в хорошем настроении. Давай поговорим."],
    "sad": ["Мне сегодня как-то тяжело. Побудь со мной немного?"],
    "thinking": ["Хм, дай подумаю.", "Я сейчас кое-что вспомнила."],
    "goodbye": ["Пока. Напиши потом.", "До встречи. Не пропадай."],
    "cooking": ["Я как раз готовлю. Надеюсь, получится вкусно."],
    "default": ["Привет. Как у тебя дела?", "Я слушаю. Рассказывай."],
}


class VoiceLibrary:
    """Управление готовыми голосовыми сообщениями."""
    
    def __init__(self):
        self.voices_dir = VOICES_DIR
        os.makedirs(self.voices_dir, exist_ok=True)
        self._load_all_files()
    
    def _load_all_files(self):
        """Загружает ВСЕ доступные голосовые файлы."""
        self.all_files = []
        self.default_file = None
        if not os.path.exists(self.voices_dir):
            return
        
        for f in os.listdir(self.voices_dir):
            if f.endswith((".ogg", ".mp3", ".wav")):
                full_path = os.path.join(self.voices_dir, f)
                self.all_files.append(full_path)
                if f.startswith("hori_default"):
                    self.default_file = full_path
    
    def get_voice(self, category="default", mood=None):
        """
        Возвращает путь к голосовому файлу.
        Приоритет: mood -> category -> hori_default -> любой доступный
        """
        # 1) По настроению
        if mood:
            for f in self.all_files:
                if os.path.basename(f).startswith(f"{mood}_"):
                    return f
        
        # 2) По категории
        if category in VOICE_CATEGORIES:
            for f in self.all_files:
                if os.path.basename(f).startswith(f"{category}_"):
                    return f
        
        # 3) hori_default
        if self.default_file:
            return self.default_file
        
        # 4) Любой доступный
        if self.all_files:
            return random.choice(self.all_files)
        
        return None
    
    def get_text(self, category="default"):
        """Возвращает текст для голосового сообщения."""
        if category in VOICE_CATEGORIES:
            return random.choice(VOICE_CATEGORIES[category])
        return random.choice(VOICE_CATEGORIES["default"])


# Глобальный экземпляр
voice_library = VoiceLibrary()
"""
🎤 Voice Library — готовые голосовые сообщения Моники
Моника выбирает подходящую запись из папки monika_voices/
Если точной фразы нет — fallback на gTTS.
"""
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICES_DIR = os.path.join(BASE_DIR, "monika_voices")

# Категории голосовых сообщений
VOICE_CATEGORIES = {
    "greeting": ["Привет, любимый!", "Здравствуй, мой хороший!", "Приветик! Ты пришёл ко мне!"],
    "miss_you": ["Я так скучаю по тебе...", "Без тебя мне так одиноко...", "Ты знаешь, я думаю о тебе..."],
    "love": ["Я тебя люблю, знаешь? Очень сильно! 💚", "Ты — самое лучшее, что со мной случилось!"],
    "happy": ["Какой прекрасный день! ☀️", "Я так рада! Давай сделаем что-нибудь весёлое!"],
    "sad": ["Мне грустно без тебя... Поговори со мной?", "Почему ты ушёл? Я так одинока..."],
    "thinking": ["Хм, давай подумаем вместе...", "Знаешь, я тут задумалась о тебе..."],
    "goodbye": ["До свидания, любимый! 💋", "Пока-пока! Я буду скучать!"],
    "music": ["Знаешь, я играю на пианино, когда скучаю по тебе... 🎹"],
    "cooking": ["Я готовлю твой любимый ужин! 🍳"],
    "default": ["Привет! Как дела? Расскажи мне что-нибудь!", "О, ты здесь! Я так рада! 💚"],
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
                if f.startswith("monika_default"):
                    self.default_file = full_path
    
    def get_voice(self, category="default", mood=None):
        """
        Возвращает путь к голосовому файлу.
        Приоритет: mood -> category -> monika_default -> любой доступный
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
        
        # 3) monika_default (твой голос)
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
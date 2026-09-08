import re


MAX_INPUT_CHARS = 4000
MAX_OUTPUT_CHARS = 1200

# Minimal moderation layer for a personal PG-13 bot.
_BLOCKED_PATTERNS = [
    re.compile(r"\b(?:kill|убей|убить|суицид|самоубийств)\b", re.IGNORECASE),
    re.compile(r"\b(?:нацист|расист|террорист)\w*\b", re.IGNORECASE),
]


def moderate_input(text):
    text = (text or "").strip()
    if not text:
        return "", None
    if any(pattern.search(text) for pattern in _BLOCKED_PATTERNS):
        return "", "Давай без опасных тем. Я не буду помогать с причинением вреда."
    if len(text) > MAX_INPUT_CHARS:
        return text[:MAX_INPUT_CHARS], "Сообщение слишком длинное, я прочитаю только начало."
    return text, None


def sanitize_output(text):
    text = (text or "").strip()
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(text):
            return "Ты чего такое говоришь? Давай без опасных вещей, ладно?"
    text = re.sub(r"(?:SEND|PHOTO|VOICE|DIARY|EVOLVE)\s*:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[(?:анимация|эмоция):\s*[^\]]+\]", "", text, flags=re.IGNORECASE)
    return text[:MAX_OUTPUT_CHARS].strip()


def detect_emotion(text):
    text = (text or "").lower()
    groups = {
        "angry": ("злюсь", "бесит", "ненавиж", "разозл", "дурак", "достал"),
        "sad": ("груст", "плохо", "одиноко", "плачу", "устал", "тяжело"),
        "happy": ("рад", "счаст", "класс", "отлично", "ура", "люблю"),
        "thinking": ("почему", "как думаешь", "не знаю", "думаю", "интересно"),
    }
    for emotion, words in groups.items():
        if any(word in text for word in words):
            return emotion
    return "calm"

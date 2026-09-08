# Хори Кёко — 3D ИИ-помощник и Telegram бот

## Локальный запуск (Windows)

```bash
# 1. Активировать venv
.venv\Scripts\activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить Xray прокси (для Groq/Gemini из РФ)
#    Уже настроен в xray/ — запускается автоматически через ai_module.py

# 4. Запустить бота
python telegram_bot.py

# 5. Запустить 3D модель
python model_viewer.py
```

## Деплой на Render.com (бот работает 24/7)

1. Зарегистрируйся на [render.com](https://render.com)
2. Создай новый **Web Service** → выбери GitHub репозиторий
3. Render автоматически использует `render.yaml`
4. Добавь переменные окружения:
   - `BOT_TOKEN` — токен от @BotFather
   - `GROQ_API_KEY` — ключ Groq
   - `GEMINI_API_KEY` — ключ Gemini
   - `OPENROUTER_API_KEY` — ключ OpenRouter
5. Нажми **Deploy**

### Чтобы бот не засыпал на бесплатном тарифе Render:
1. Зарегистрируйся на [UptimeRobot](https://uptimerobot.com)
2. Добавь монитор: HTTP(s) → вставь URL твоего Render-сервиса
3. UptimeRobot будет пинговать каждые 5 минут → бот не засыпает

## Файлы

| Файл | Описание |
|------|----------|
| `telegram_bot.py` | Telegram бот с ИИ, памятью, дневником |
| `ai_module.py` | Единый ИИ-модуль (Groq, Gemini, OpenRouter, xAI) |
| `model_viewer.py` | 3D просмотрщик (PyQt6 + Three.js) |
| `hori_memory.json` | Память о пользователе (факты, диалоги) |
| `hori_personality.json` | Личность Хори (саморазвивающаяся) |
| `hori_diary.json` | Личный дневник Хори |
| `hori_knowledge.json` | Факты о Хори и мире Horimiya |
| `hori_photos/` | Оригинальные изображения Хори по настроению |
| `safety.py` | Фильтрация входных и выходных сообщений, определение эмоций |

### Более точная генерация фото

Для максимального сходства можно подключить Automatic1111/Forge:

- `SD_WEBUI_URL` — адрес WebUI API, например `http://127.0.0.1:7860`;
- `SD_MODEL_CHECKPOINT` — checkpoint Stable Diffusion;
- `HORI_LORA_TRIGGER` — trigger word установленной LoRA Хори;
- `HORI_REFERENCE_IMAGE` — путь к разрешённому эталонному изображению для img2img;
- `SD_DENOISING` — обычно `0.25-0.4`, чтобы сохранять внешность эталона.

Если `SD_WEBUI_URL` не задан, используется Pollinations как резервный генератор.
| `xray/` | Xray-core прокси (VLESS, для РФ) |
| `render.yaml` | Конфиг деплоя на Render |
| `requirements.txt` | Python зависимости |

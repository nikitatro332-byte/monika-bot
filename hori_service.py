"""
🔧 Установка Моники как Windows-сервиса
Бот будет работать всегда, даже после перезагрузки ПК.

Установка:
    python hori_service.py install

Удаление:
    python hori_service.py remove

Запуск/остановка:
    python hori_service.py start
    python hori_service.py stop
"""

import sys
import os
import subprocess

# Путь к Python и скрипту бота
PYTHON = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
BOT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram_bot.py")
XRAY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xray")
NSSM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nssm.exe")

SERVICE_NAME = "HoriBot"
XRAY_SERVICE = "HoriXray"


def download_nssm():
    """Скачивает nssm.exe если его нет."""
    if os.path.exists(NSSM):
        return True
    print("⬇️ Скачиваю nssm.exe...")
    try:
        import urllib.request
        import zipfile
        url = "https://nssm.cc/release/nssm-2.24.zip"
        zip_path = NSSM + ".zip"
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as z:
            # nssm-2.24/win64/nssm.exe
            for name in z.namelist():
                if name.endswith("win64/nssm.exe"):
                    with z.open(name) as src, open(NSSM, 'wb') as dst:
                        dst.write(src.read())
                    break
        os.remove(zip_path)
        print(f"✅ nssm.exe: {os.path.getsize(NSSM)} байт")
        return os.path.exists(NSSM)
    except Exception as e:
        print(f"❌ Ошибка скачивания nssm: {e}")
        print("   Скачай вручную с https://nssm.cc/release/nssm-2.24.zip")
        return False


def run(cmd):
    print(f"  $ {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.stdout.strip():
        print(f"    {r.stdout.strip()}")
    if r.stderr.strip():
        print(f"    {r.stderr.strip()}")
    return r.returncode


def install():
    if not download_nssm():
        return

    print(f"\n🔧 Устанавливаю сервис {XRAY_SERVICE} (прокси)...")
    run(f'"{NSSM}" install {XRAY_SERVICE} "{XRAY_DIR}\\xray.exe" "run -config {XRAY_DIR}\\config.json"')
    run(f'"{NSSM}" set {XRAY_SERVICE} AppDirectory "{XRAY_DIR}"')
    run(f'"{NSSM}" set {XRAY_SERVICE} AppStdout "{XRAY_DIR}\\xray.log"')
    run(f'"{NSSM}" set {XRAY_SERVICE} AppStderr "{XRAY_DIR}\\xray.log"')
    run(f'"{NSSM}" set {XRAY_SERVICE} Start SERVICE_AUTO_START')

    print(f"\n🔧 Устанавливаю сервис {SERVICE_NAME} (бот)...")
    run(f'"{NSSM}" install {SERVICE_NAME} "{PYTHON}" "{BOT_SCRIPT}"')
    run(f'"{NSSM}" set {SERVICE_NAME} AppDirectory "{os.path.dirname(BOT_SCRIPT)}"')
    run(f'"{NSSM}" set {SERVICE_NAME} AppStdout "{os.path.dirname(BOT_SCRIPT)}\\hori_bot.log"')
    run(f'"{NSSM}" set {SERVICE_NAME} AppStderr "{os.path.dirname(BOT_SCRIPT)}\\hori_bot.log"')
    run(f'"{NSSM}" set {SERVICE_NAME} Start SERVICE_AUTO_START')
    run(f'"{NSSM}" set {SERVICE_NAME} DependOnService {XRAY_SERVICE}')

    print(f"\n🚀 Запускаю сервисы...")
    run(f'"{NSSM}" start {XRAY_SERVICE}')
    import time
    time.sleep(3)
    run(f'"{NSSM}" start {SERVICE_NAME}')

    print(f"\n✅ Готово!")
    print(f"   {XRAY_SERVICE} — прокси (автозапуск)")
    print(f"   {SERVICE_NAME} — бот (автозапуск)")
    print(f"   Логи: hori_bot.log")
    print(f"\nУправление:")
    print(f"  stop:  python hori_service.py stop")
    print(f"  start: python hori_service.py start")
    print(f"  remove: python hori_service.py remove")


def remove():
    print(f"\n🗑️ Удаляю сервисы...")
    run(f'"{NSSM}" stop {SERVICE_NAME}')
    run(f'"{NSSM}" stop {XRAY_SERVICE}')
    run(f'"{NSSM}" remove {SERVICE_NAME} confirm')
    run(f'"{NSSM}" remove {XRAY_SERVICE} confirm')
    print("✅ Сервисы удалены")


def start():
    run(f'"{NSSM}" start {XRAY_SERVICE}')
    import time
    time.sleep(3)
    run(f'"{NSSM}" start {SERVICE_NAME}')
    print("✅ Сервисы запущены")


def stop():
    run(f'"{NSSM}" stop {SERVICE_NAME}')
    run(f'"{NSSM}" stop {XRAY_SERVICE}')
    print("✅ Сервисы остановлены")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python hori_service.py install  — установить как сервис")
        print("  python hori_service.py remove   — удалить сервис")
        print("  python hori_service.py start    — запустить")
        print("  python hori_service.py stop     — остановить")
    elif sys.argv[1] == "install":
        install()
    elif sys.argv[1] == "remove":
        remove()
    elif sys.argv[1] == "start":
        start()
    elif sys.argv[1] == "stop":
        stop()
    else:
        print(f"Неизвестная команда: {sys.argv[1]}")

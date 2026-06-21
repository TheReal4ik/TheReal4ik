"""Запуск бота с автоматическим перезапуском при падении.

Используйте этот файл вместо bot.py, если хотите, чтобы бот сам
поднимался после сбоя (например, обрыв сети), без необходимости
запускать его вручную каждый раз.

Запуск:  python run_forever.py
Остановка: Ctrl+C
"""

import subprocess
import sys
import time
from pathlib import Path

BOT_SCRIPT = Path(__file__).parent / "bot.py"
RESTART_DELAY_SECONDS = 5


def main() -> None:
    while True:
        print("Запуск бота...")
        try:
            result = subprocess.run([sys.executable, str(BOT_SCRIPT)])
        except KeyboardInterrupt:
            print("Остановлено пользователем.")
            return

        print(f"Бот завершился (код {result.returncode}). Перезапуск через {RESTART_DELAY_SECONDS} сек...")
        try:
            time.sleep(RESTART_DELAY_SECONDS)
        except KeyboardInterrupt:
            print("Остановлено пользователем.")
            return


if __name__ == "__main__":
    main()

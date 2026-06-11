import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не задан. Создайте файл .env на основе .env.example"
    )

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

FLOORS = list(range(1, 12))  # этажи 1..11
SEGMENTS = ["Сигма", "Омега"]
SWITCHES_IN_STACK = 5
PORTS_PER_SWITCH = 48

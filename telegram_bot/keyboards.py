from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import FLOORS, PORTS_PER_SWITCH, SEGMENTS, SWITCHES_IN_STACK


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🖨 Принтеры", callback_data="menu:printers")
    builder.button(text="🔀 Кроссовая", callback_data="menu:cross")
    builder.adjust(1)
    return builder.as_markup()


def floors_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for floor in FLOORS:
        builder.button(text=f"Этаж {floor}", callback_data=f"floor:{floor}")
    builder.button(text="⬅️ В меню", callback_data="back:main")
    builder.adjust(3)
    return builder.as_markup()


def segments_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for segment in SEGMENTS:
        builder.button(text=segment, callback_data=f"segment:{segment}")
    builder.button(text="⬅️ Назад", callback_data="back:floor")
    builder.adjust(2, 1)
    return builder.as_markup()


def switches_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for switch in range(1, SWITCHES_IN_STACK + 1):
        builder.button(text=f"Коммутатор {switch}", callback_data=f"switch:{switch}")
    builder.button(text="⬅️ Назад", callback_data="back:segment")
    builder.adjust(1)
    return builder.as_markup()


def ports_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for port in range(1, PORTS_PER_SWITCH + 1):
        builder.button(text=str(port), callback_data=f"port:{port}")
    builder.button(text="⬅️ Назад", callback_data="back:switch")
    builder.adjust(8)
    return builder.as_markup()


def comment_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Без комментария", callback_data="comment:skip")
    builder.adjust(1)
    return builder.as_markup()


def export_files_kb(files: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for filename in files:
        builder.button(text=filename, callback_data=f"export:{filename}")
    builder.adjust(1)
    return builder.as_markup()

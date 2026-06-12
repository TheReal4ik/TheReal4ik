from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import FLOORS, PORTS_PER_SWITCH, SEGMENTS, SWITCHES_IN_STACK

RECORDS_PAGE_SIZE = 8

MENU_BUTTON_TEXT = "🏠 Главное меню"
EXPORT_BUTTON_TEXT = "📤 Экспорт"


def persistent_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=MENU_BUTTON_TEXT)
    builder.button(text=EXPORT_BUTTON_TEXT)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🖨 Принтеры", callback_data="menu:printers")
    builder.button(text="🔀 Кроссовая", callback_data="menu:cross")
    builder.button(text="🗑 Удалить запись", callback_data="menu:delete")
    builder.adjust(1)
    return builder.as_markup()


def floors_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for floor in FLOORS:
        builder.button(text=f"Этаж {floor}", callback_data=f"floor:{floor}")
    builder.button(text="⬅️ В меню", callback_data="back:main")
    builder.adjust(3)
    return builder.as_markup()


def delete_floors_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for floor in FLOORS:
        builder.button(text=f"Этаж {floor}", callback_data=f"delfloor:{floor}")
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


def printer_floors_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for floor in FLOORS:
        builder.button(text=f"Этаж {floor}", callback_data=f"prfloor:{floor}")
    builder.button(text="⬅️ В меню", callback_data="back:main")
    builder.adjust(3)
    return builder.as_markup()


def printer_domains_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for domain in SEGMENTS:
        builder.button(text=domain, callback_data=f"prdomain:{domain}")
    builder.button(text="⬅️ Назад", callback_data="prback:floor")
    builder.adjust(2, 1)
    return builder.as_markup()


def printer_step_kb(back_callback: str, skip: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if skip:
        builder.button(text="Пропустить", callback_data="prskip")
    builder.button(text="⬅️ Назад", callback_data=back_callback)
    builder.adjust(1)
    return builder.as_markup()


def scs_input_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="back:port")
    builder.adjust(1)
    return builder.as_markup()


def switches_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for switch in range(1, SWITCHES_IN_STACK + 1):
        builder.button(text=f"Коммутатор {switch}", callback_data=f"switch:{switch}")
    builder.button(text="⬅️ Назад", callback_data="back:segment")
    builder.adjust(1)
    return builder.as_markup()


def ports_kb(occupied_ports: set[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for port in range(1, PORTS_PER_SWITCH + 1):
        marker = "🔴" if port in occupied_ports else "🟢"
        builder.button(text=f"{marker}{port}", callback_data=f"port:{port}")
    builder.button(text="⬅️ Назад", callback_data="back:switch")
    builder.adjust(8)
    return builder.as_markup()


def comment_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Без комментария", callback_data="comment:skip")
    builder.button(text="⬅️ Назад", callback_data="back:scs")
    builder.adjust(1)
    return builder.as_markup()


def port_occupied_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data="portedit:go")
    builder.button(text="❌ Отмена", callback_data="back:switch")
    builder.adjust(1)
    return builder.as_markup()


def export_files_kb(files: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for filename in files:
        builder.button(text=filename, callback_data=f"export:{filename}")
    builder.adjust(1)
    return builder.as_markup()


def records_kb(records: list[tuple], page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * RECORDS_PAGE_SIZE
    chunk = records[start : start + RECORDS_PAGE_SIZE]

    for row_idx, segment, switch, port, scs_number, _comment in chunk:
        scs_display = (scs_number or "")[:20]
        text = f"{segment} • Ком.{switch} • Порт {port} • СКС {scs_display}"
        builder.row(InlineKeyboardButton(text=text, callback_data=f"delrec:{row_idx}"))

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀ Назад", callback_data=f"delpage:{page - 1}"))
    if start + RECORDS_PAGE_SIZE < len(records):
        nav_row.append(InlineKeyboardButton(text="Далее ▶", callback_data=f"delpage:{page + 1}"))
    if nav_row:
        builder.row(*nav_row)

    builder.row(InlineKeyboardButton(text="⬅️ К выбору этажа", callback_data="del:floors"))
    return builder.as_markup()


def confirm_delete_kb(row_idx: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"delconfirm:{row_idx}")
    builder.button(text="❌ Отмена", callback_data="del:cancel")
    builder.adjust(1)
    return builder.as_markup()

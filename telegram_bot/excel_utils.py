import os
from datetime import datetime

from openpyxl import Workbook, load_workbook

from config import DATA_DIR

CROSS_CONNECT_HEADERS = [
    "Дата",
    "Сегмент",
    "Коммутатор",
    "Порт",
    "Номер СКС",
    "Комментарий",
]


def cross_connect_filename(floor: int) -> str:
    return os.path.join(DATA_DIR, f"Кроссовая_Этаж_{floor}.xlsx")


def append_cross_connect_record(
    floor: int,
    segment: str,
    switch: int,
    port: int,
    scs_number: str,
    comment: str,
    ports_per_switch: int,
) -> str:
    path = cross_connect_filename(floor)

    if os.path.exists(path):
        workbook = load_workbook(path)
        worksheet = workbook.active
    else:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = f"Этаж {floor}"
        worksheet.append(CROSS_CONNECT_HEADERS)

    overall_port = (switch - 1) * ports_per_switch + port
    worksheet.append(
        [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            segment,
            switch,
            overall_port,
            scs_number,
            comment or "",
        ]
    )
    workbook.save(path)
    return path


def list_data_files() -> list[str]:
    if not os.path.exists(DATA_DIR):
        return []
    return sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".xlsx"))

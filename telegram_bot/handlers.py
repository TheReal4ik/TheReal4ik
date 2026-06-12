import os

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import DATA_DIR, PORTS_PER_SWITCH
from excel_utils import (
    append_cross_connect_record,
    append_printer_record,
    delete_cross_connect_record,
    get_cross_connect_record,
    get_occupied_ports,
    get_port_record,
    list_data_files,
    read_cross_connect_records,
    update_cross_connect_record,
)
from keyboards import (
    EXPORT_BUTTON_TEXT,
    MENU_BUTTON_TEXT,
    comment_kb,
    confirm_delete_kb,
    delete_floors_kb,
    export_files_kb,
    floors_kb,
    main_menu_kb,
    persistent_menu_kb,
    port_occupied_kb,
    ports_kb,
    printer_domains_kb,
    printer_floors_kb,
    printer_step_kb,
    records_kb,
    scs_input_kb,
    segments_kb,
    switches_kb,
)
from states import CrossConnectForm, DeleteRecordForm, PrinterForm

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Меню всегда под рукой 👇", reply_markup=persistent_menu_kb())
    await message.answer("Выберите раздел:", reply_markup=main_menu_kb())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_kb())


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    files = list_data_files()
    if not files:
        await message.answer("Пока нет ни одного сохранённого файла.")
        return
    await message.answer("Выберите файл для выгрузки:", reply_markup=export_files_kb(files))


@router.message(F.text == MENU_BUTTON_TEXT)
async def menu_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Выберите раздел:", reply_markup=main_menu_kb())


@router.message(F.text == EXPORT_BUTTON_TEXT)
async def export_button(message: Message) -> None:
    await cmd_export(message)


@router.callback_query(F.data.startswith("export:"))
async def export_file(callback: CallbackQuery) -> None:
    filename = callback.data.split(":", 1)[1]
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        await callback.answer("Файл не найден", show_alert=True)
        return
    await callback.message.answer_document(FSInputFile(path))
    await callback.answer()


@router.callback_query(F.data == "menu:printers")
async def menu_printers(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PrinterForm.choosing_floor)
    await callback.message.edit_text(
        "🖨 Принтеры. Выберите этаж:",
        reply_markup=printer_floors_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:cross")
async def menu_cross(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CrossConnectForm.choosing_floor)
    await callback.message.edit_text("Выберите этаж:", reply_markup=floors_kb())
    await callback.answer()


@router.callback_query(F.data == "back:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Выберите раздел:", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("floor:"), CrossConnectForm.choosing_floor)
async def choose_floor(callback: CallbackQuery, state: FSMContext) -> None:
    floor = int(callback.data.split(":")[1])
    await state.update_data(floor=floor)
    await state.set_state(CrossConnectForm.choosing_segment)
    await callback.message.edit_text(
        f"Этаж {floor}\nВыберите сегмент:", reply_markup=segments_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "back:floor")
async def back_to_floor(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CrossConnectForm.choosing_floor)
    await callback.message.edit_text("Выберите этаж:", reply_markup=floors_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("segment:"), CrossConnectForm.choosing_segment)
async def choose_segment(callback: CallbackQuery, state: FSMContext) -> None:
    segment = callback.data.split(":")[1]
    data = await state.update_data(segment=segment)
    await state.set_state(CrossConnectForm.choosing_switch)
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {segment}\nВыберите коммутатор:",
        reply_markup=switches_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "back:segment")
async def back_to_segment(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(CrossConnectForm.choosing_segment)
    await callback.message.edit_text(
        f"Этаж {data['floor']}\nВыберите сегмент:", reply_markup=segments_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("switch:"), CrossConnectForm.choosing_switch)
async def choose_switch(callback: CallbackQuery, state: FSMContext) -> None:
    switch = int(callback.data.split(":")[1])
    data = await state.update_data(switch=switch)
    await state.set_state(CrossConnectForm.choosing_port)
    occupied = get_occupied_ports(data["floor"], data["segment"], switch, PORTS_PER_SWITCH)
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {data['segment']}, коммутатор {switch}\n"
        f"Выберите порт (🟢 свободен, 🔴 занят):",
        reply_markup=ports_kb(occupied),
    )
    await callback.answer()


@router.callback_query(F.data == "back:switch")
async def back_to_switch(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(CrossConnectForm.choosing_switch)
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {data['segment']}\nВыберите коммутатор:",
        reply_markup=switches_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("port:"), CrossConnectForm.choosing_port)
async def choose_port(callback: CallbackQuery, state: FSMContext) -> None:
    port = int(callback.data.split(":")[1])
    data = await state.update_data(port=port)

    record = get_port_record(data["floor"], data["segment"], data["switch"], port, PORTS_PER_SWITCH)
    if record:
        _row_idx, _segment, _switch, overall_port, scs_number, comment = record
        await state.set_state(CrossConnectForm.port_occupied)
        await callback.message.edit_text(
            f"Этаж {data['floor']}, сегмент {data['segment']}, "
            f"коммутатор {data['switch']}, порт {port} (сквозной {overall_port}) — занят.\n\n"
            f"Текущий номер СКС: {scs_number}\n"
            f"Текущий комментарий: {comment or '—'}\n\n"
            f"Что сделать?",
            reply_markup=port_occupied_kb(),
        )
        await callback.answer()
        return

    await state.update_data(edit_row_idx=None)
    await state.set_state(CrossConnectForm.entering_scs)
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {data['segment']}, "
        f"коммутатор {data['switch']}, порт {port}\n\n"
        f"Введите номер СКС-порта:",
        reply_markup=scs_input_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "portedit:go", CrossConnectForm.port_occupied)
async def edit_occupied_port(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    record = get_port_record(data["floor"], data["segment"], data["switch"], data["port"], PORTS_PER_SWITCH)
    await state.update_data(edit_row_idx=record[0] if record else None)
    await state.set_state(CrossConnectForm.entering_scs)
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {data['segment']}, "
        f"коммутатор {data['switch']}, порт {data['port']}\n\n"
        f"Введите новый номер СКС-порта:",
        reply_markup=scs_input_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "back:port", CrossConnectForm.entering_scs)
async def back_to_port_from_scs(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(CrossConnectForm.choosing_port)
    occupied = get_occupied_ports(data["floor"], data["segment"], data["switch"], PORTS_PER_SWITCH)
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {data['segment']}, коммутатор {data['switch']}\n"
        f"Выберите порт (🟢 свободен, 🔴 занят):",
        reply_markup=ports_kb(occupied),
    )
    await callback.answer()


@router.callback_query(F.data == "back:scs", CrossConnectForm.entering_comment)
async def back_to_scs_from_comment(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(CrossConnectForm.entering_scs)
    overall_port = (data["switch"] - 1) * PORTS_PER_SWITCH + data["port"]
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {data['segment']}, "
        f"коммутатор {data['switch']}, порт {data['port']} (сквозной {overall_port})\n\n"
        f"Введите номер СКС-порта:",
        reply_markup=scs_input_kb(),
    )
    await callback.answer()


@router.message(CrossConnectForm.entering_scs)
async def enter_scs(message: Message, state: FSMContext) -> None:
    scs_number = (message.text or "").strip()
    if not scs_number:
        await message.answer("Номер СКС-порта не может быть пустым. Введите ещё раз:")
        return
    await state.update_data(scs_number=scs_number)
    await state.set_state(CrossConnectForm.entering_comment)
    await message.answer(
        "Введите комментарий или нажмите «Без комментария»:",
        reply_markup=comment_kb(),
    )


@router.message(CrossConnectForm.entering_comment)
async def enter_comment(message: Message, state: FSMContext) -> None:
    await save_cross_connect_record(message, state, comment=(message.text or "").strip())


@router.callback_query(F.data == "comment:skip", CrossConnectForm.entering_comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext) -> None:
    await save_cross_connect_record(callback.message, state, comment="", callback=callback)


async def save_cross_connect_record(
    message: Message,
    state: FSMContext,
    comment: str,
    callback: CallbackQuery | None = None,
) -> None:
    data = await state.get_data()
    edit_row_idx = data.get("edit_row_idx")
    overall_port = (data["switch"] - 1) * PORTS_PER_SWITCH + data["port"]

    if edit_row_idx:
        update_cross_connect_record(
            floor=data["floor"],
            row_idx=edit_row_idx,
            scs_number=data["scs_number"],
            comment=comment,
        )
        header = "✅ Запись обновлена"
    else:
        path = append_cross_connect_record(
            floor=data["floor"],
            segment=data["segment"],
            switch=data["switch"],
            port=data["port"],
            scs_number=data["scs_number"],
            comment=comment,
            ports_per_switch=PORTS_PER_SWITCH,
        )
        header = f"✅ Запись сохранена в {os.path.basename(path)}"

    await state.clear()

    text = (
        f"{header}\n\n"
        f"Этаж: {data['floor']}\n"
        f"Сегмент: {data['segment']}\n"
        f"Коммутатор: {data['switch']}\n"
        f"Порт: {overall_port}\n"
        f"Номер СКС: {data['scs_number']}\n"
        f"Комментарий: {comment or '—'}"
    )

    if callback:
        await message.edit_text(text)
        await callback.answer()
    else:
        await message.answer(text)

    await message.answer("Выберите раздел:", reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:delete")
async def menu_delete(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DeleteRecordForm.choosing_floor)
    await callback.message.edit_text(
        "Выберите этаж, на котором нужно удалить запись:",
        reply_markup=delete_floors_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delfloor:"), DeleteRecordForm.choosing_floor)
async def delete_choose_floor(callback: CallbackQuery, state: FSMContext) -> None:
    floor = int(callback.data.split(":")[1])
    records = read_cross_connect_records(floor)
    if not records:
        await callback.answer("На этом этаже пока нет записей", show_alert=True)
        return

    await state.update_data(floor=floor)
    await state.set_state(DeleteRecordForm.choosing_record)
    await callback.message.edit_text(
        f"Этаж {floor}. Выберите запись для удаления:",
        reply_markup=records_kb(records, 0),
    )
    await callback.answer()


@router.callback_query(F.data == "del:floors", DeleteRecordForm.choosing_record)
async def delete_back_to_floors(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DeleteRecordForm.choosing_floor)
    await callback.message.edit_text(
        "Выберите этаж, на котором нужно удалить запись:",
        reply_markup=delete_floors_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delpage:"), DeleteRecordForm.choosing_record)
async def delete_change_page(callback: CallbackQuery, state: FSMContext) -> None:
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    records = read_cross_connect_records(data["floor"])
    await callback.message.edit_text(
        f"Этаж {data['floor']}. Выберите запись для удаления:",
        reply_markup=records_kb(records, page),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delrec:"), DeleteRecordForm.choosing_record)
async def delete_choose_record(callback: CallbackQuery, state: FSMContext) -> None:
    row_idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    record = get_cross_connect_record(data["floor"], row_idx)
    if not record:
        await callback.answer("Запись не найдена, возможно уже удалена", show_alert=True)
        return

    _, segment, switch, port, scs_number, comment = record
    text = (
        "Удалить эту запись?\n\n"
        f"Этаж: {data['floor']}\n"
        f"Сегмент: {segment}\n"
        f"Коммутатор: {switch}\n"
        f"Порт: {port}\n"
        f"Номер СКС: {scs_number}\n"
        f"Комментарий: {comment or '—'}"
    )
    await callback.message.edit_text(text, reply_markup=confirm_delete_kb(row_idx))
    await callback.answer()


@router.callback_query(F.data == "del:cancel", DeleteRecordForm.choosing_record)
async def delete_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Удаление отменено.\n\nВыберите раздел:", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("delconfirm:"), DeleteRecordForm.choosing_record)
async def delete_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    row_idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    deleted = delete_cross_connect_record(data["floor"], row_idx)
    await state.clear()

    if deleted:
        text = "✅ Запись удалена."
    else:
        text = "⚠️ Не удалось удалить запись (возможно, она уже была удалена)."

    await callback.message.edit_text(text)
    await callback.message.answer("Выберите раздел:", reply_markup=main_menu_kb())
    await callback.answer()


# ---------- Принтеры ----------


@router.callback_query(F.data.startswith("prfloor:"), PrinterForm.choosing_floor)
async def printer_choose_floor(callback: CallbackQuery, state: FSMContext) -> None:
    floor = int(callback.data.split(":")[1])
    await state.update_data(floor=floor)
    await state.set_state(PrinterForm.choosing_domain)
    await callback.message.edit_text(
        f"🖨 Этаж {floor}. Выберите домен:",
        reply_markup=printer_domains_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "prback:floor", PrinterForm.choosing_domain)
async def printer_back_to_floor(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PrinterForm.choosing_floor)
    await callback.message.edit_text(
        "🖨 Принтеры. Выберите этаж:",
        reply_markup=printer_floors_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prdomain:"), PrinterForm.choosing_domain)
async def printer_choose_domain(callback: CallbackQuery, state: FSMContext) -> None:
    domain = callback.data.split(":", 1)[1]
    data = await state.update_data(domain=domain)
    await state.set_state(PrinterForm.entering_model)
    await callback.message.edit_text(
        f"🖨 Этаж {data['floor']}, домен {domain}.\n\nВведите модель принтера:",
        reply_markup=printer_step_kb("prback:domain", skip=False),
    )
    await callback.answer()


@router.callback_query(F.data == "prback:domain", PrinterForm.entering_model)
async def printer_back_to_domain(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(PrinterForm.choosing_domain)
    await callback.message.edit_text(
        f"🖨 Этаж {data['floor']}. Выберите домен:",
        reply_markup=printer_domains_kb(),
    )
    await callback.answer()


@router.message(PrinterForm.entering_model)
async def printer_enter_model(message: Message, state: FSMContext) -> None:
    model = (message.text or "").strip()
    if not model:
        await message.answer("Модель не может быть пустой. Введите ещё раз:")
        return
    await state.update_data(model=model)
    await state.set_state(PrinterForm.entering_serial)
    await message.answer(
        "Введите серийный номер (или «Пропустить»):",
        reply_markup=printer_step_kb("prback:model"),
    )


@router.callback_query(F.data == "prback:model", PrinterForm.entering_serial)
async def printer_back_to_model(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(PrinterForm.entering_model)
    await callback.message.edit_text(
        f"🖨 Этаж {data['floor']}, домен {data['domain']}.\n\nВведите модель принтера:",
        reply_markup=printer_step_kb("prback:domain", skip=False),
    )
    await callback.answer()


@router.message(PrinterForm.entering_serial)
async def printer_enter_serial(message: Message, state: FSMContext) -> None:
    await state.update_data(serial=(message.text or "").strip())
    await _printer_ask_ip(message, state)


@router.callback_query(F.data == "prskip", PrinterForm.entering_serial)
async def printer_skip_serial(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(serial="")
    await _printer_ask_ip(callback.message, state)
    await callback.answer()


async def _printer_ask_ip(message: Message, state: FSMContext) -> None:
    await state.set_state(PrinterForm.entering_ip)
    await message.answer(
        "Введите IP-адрес (или «Пропустить»):",
        reply_markup=printer_step_kb("prback:serial"),
    )


@router.callback_query(F.data == "prback:serial", PrinterForm.entering_ip)
async def printer_back_to_serial(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PrinterForm.entering_serial)
    await callback.message.edit_text(
        "Введите серийный номер (или «Пропустить»):",
        reply_markup=printer_step_kb("prback:model"),
    )
    await callback.answer()


@router.message(PrinterForm.entering_ip)
async def printer_enter_ip(message: Message, state: FSMContext) -> None:
    await state.update_data(ip=(message.text or "").strip())
    await _printer_ask_sberprint(message, state)


@router.callback_query(F.data == "prskip", PrinterForm.entering_ip)
async def printer_skip_ip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(ip="")
    await _printer_ask_sberprint(callback.message, state)
    await callback.answer()


async def _printer_ask_sberprint(message: Message, state: FSMContext) -> None:
    await state.set_state(PrinterForm.entering_sberprint_id)
    await message.answer(
        "Введите Сберпечать ID (или «Пропустить»):",
        reply_markup=printer_step_kb("prback:ip"),
    )


@router.callback_query(F.data == "prback:ip", PrinterForm.entering_sberprint_id)
async def printer_back_to_ip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PrinterForm.entering_ip)
    await callback.message.edit_text(
        "Введите IP-адрес (или «Пропустить»):",
        reply_markup=printer_step_kb("prback:serial"),
    )
    await callback.answer()


@router.message(PrinterForm.entering_sberprint_id)
async def printer_enter_sberprint(message: Message, state: FSMContext) -> None:
    await state.update_data(sberprint_id=(message.text or "").strip())
    await _printer_ask_location(message, state)


@router.callback_query(F.data == "prskip", PrinterForm.entering_sberprint_id)
async def printer_skip_sberprint(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(sberprint_id="")
    await _printer_ask_location(callback.message, state)
    await callback.answer()


async def _printer_ask_location(message: Message, state: FSMContext) -> None:
    await state.set_state(PrinterForm.entering_location)
    await message.answer(
        "Введите расположение (или «Пропустить»):",
        reply_markup=printer_step_kb("prback:sberprint"),
    )


@router.callback_query(F.data == "prback:sberprint", PrinterForm.entering_location)
async def printer_back_to_sberprint(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PrinterForm.entering_sberprint_id)
    await callback.message.edit_text(
        "Введите Сберпечать ID (или «Пропустить»):",
        reply_markup=printer_step_kb("prback:ip"),
    )
    await callback.answer()


@router.message(PrinterForm.entering_location)
async def printer_enter_location(message: Message, state: FSMContext) -> None:
    await _save_printer_record(message, state, location=(message.text or "").strip())


@router.callback_query(F.data == "prskip", PrinterForm.entering_location)
async def printer_skip_location(callback: CallbackQuery, state: FSMContext) -> None:
    await _save_printer_record(callback.message, state, location="", callback=callback)


async def _save_printer_record(
    message: Message,
    state: FSMContext,
    location: str,
    callback: CallbackQuery | None = None,
) -> None:
    data = await state.get_data()
    path = append_printer_record(
        floor=data["floor"],
        domain=data["domain"],
        model=data["model"],
        serial=data.get("serial", ""),
        ip=data.get("ip", ""),
        sberprint_id=data.get("sberprint_id", ""),
        location=location,
    )
    await state.clear()

    text = (
        f"✅ Принтер сохранён в {os.path.basename(path)}\n\n"
        f"Этаж: {data['floor']}\n"
        f"Домен: {data['domain']}\n"
        f"Модель: {data['model']}\n"
        f"Серийный номер: {data.get('serial') or '—'}\n"
        f"IP адрес: {data.get('ip') or '—'}\n"
        f"Сберпечать ID: {data.get('sberprint_id') or '—'}\n"
        f"Расположение: {location or '—'}"
    )

    if callback:
        await message.edit_text(text)
        await callback.answer()
    else:
        await message.answer(text)

    await message.answer("Выберите раздел:", reply_markup=main_menu_kb())

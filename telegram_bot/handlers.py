import os

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import DATA_DIR, PORTS_PER_SWITCH
from excel_utils import (
    append_cross_connect_record,
    delete_cross_connect_record,
    get_cross_connect_record,
    list_data_files,
    read_cross_connect_records,
)
from keyboards import (
    comment_kb,
    confirm_delete_kb,
    delete_floors_kb,
    export_files_kb,
    floors_kb,
    main_menu_kb,
    ports_kb,
    records_kb,
    segments_kb,
    switches_kb,
)
from states import CrossConnectForm, DeleteRecordForm

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Привет! Выберите раздел:", reply_markup=main_menu_kb())


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
    await state.clear()
    await callback.message.edit_text(
        "🖨 Раздел «Принтеры» пока в разработке.\n\nВыберите раздел:",
        reply_markup=main_menu_kb(),
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
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {data['segment']}, коммутатор {switch}\n"
        f"Выберите порт:",
        reply_markup=ports_kb(),
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
    await state.set_state(CrossConnectForm.entering_scs)
    await callback.message.edit_text(
        f"Этаж {data['floor']}, сегмент {data['segment']}, "
        f"коммутатор {data['switch']}, порт {port}\n\n"
        f"Введите номер СКС-порта:"
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
    path = append_cross_connect_record(
        floor=data["floor"],
        segment=data["segment"],
        switch=data["switch"],
        port=data["port"],
        scs_number=data["scs_number"],
        comment=comment,
        ports_per_switch=PORTS_PER_SWITCH,
    )
    await state.clear()

    overall_port = (data["switch"] - 1) * PORTS_PER_SWITCH + data["port"]
    text = (
        "✅ Запись сохранена в "
        f"{os.path.basename(path)}\n\n"
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

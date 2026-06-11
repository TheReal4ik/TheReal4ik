from aiogram.fsm.state import State, StatesGroup


class CrossConnectForm(StatesGroup):
    choosing_floor = State()
    choosing_segment = State()
    choosing_switch = State()
    choosing_port = State()
    port_occupied = State()
    entering_scs = State()
    entering_comment = State()


class DeleteRecordForm(StatesGroup):
    choosing_floor = State()
    choosing_record = State()


class PrinterForm(StatesGroup):
    choosing_floor = State()
    choosing_domain = State()
    entering_model = State()
    entering_serial = State()
    entering_ip = State()
    entering_sberprint_id = State()
    entering_location = State()

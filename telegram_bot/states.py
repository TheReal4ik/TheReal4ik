from aiogram.fsm.state import State, StatesGroup


class CrossConnectForm(StatesGroup):
    choosing_floor = State()
    choosing_segment = State()
    choosing_switch = State()
    choosing_port = State()
    entering_scs = State()
    entering_comment = State()


class DeleteRecordForm(StatesGroup):
    choosing_floor = State()
    choosing_record = State()

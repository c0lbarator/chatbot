from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram_dialog import Window, Dialog, DialogManager, StartMode, setup_dialogs
from aiogram_dialog.widgets.kbd import Button, Row, Back, SwitchTo, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from datetime import date
from datetime import datetime
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery
from aiogram.filters.command import Command
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Calendar
from aiogram.filters import Text
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup
from appwrite.query import Query
from operator import itemgetter
from typing import Any
API_TOKEN = '1026624360:AAGAI3gKXOhwwC3gEoVdm9tIBFCVRPekJek'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
'''dp.include_router(dialog_create)
dp.include_router(dialog_edit)
setup_dialogs(dp)'''

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Настройки профиля",
        callback_data="create_event", )
    )
    builder.add(types.InlineKeyboardButton(
        text='Редактировать мероприятие',
        callback_data="edit_event"
    ))
    await message.reply("Привет!\nТы открыл официального бота Тула Куда пойти!\nЗдесь ты найдёшь интересные мероприятия города\n", reply_markup=builder.as_markup())

@dp.callback_query(Text("create_event"))
async def cc(callback: types.CallbackQuery, dialog_manager: DialogManager):
     await dialog_manager.start(event_creation.ch_event_name, mode=StartMode.RESET_STACK)
@dp.callback_query(Text("edit_event"))
async def ec(callback: types.CallbackQuery, dialog_manager: DialogManager):
     await dialog_manager.start(event_editing.ch_event_choose, mode=StartMode.RESET_STACK)
if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)
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
import math
from numpy import deg2rad
async def compute_Delta(degrees):
    return math.pi / 180.0 * 6371210 * math.cos(deg2rad(degrees))


#https://en.wikipedia.org/wiki/Longitude#Length_of_a_degree_of_longitude


API_TOKEN = '1026624360:AAGAI3gKXOhwwC3gEoVdm9tIBFCVRPekJek'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(wsetting)
setup_dialogs(dp)
databases = Databases(client)
dbid, ucid = '644c2f1074ca81e7f813', '644cf9f1d76be85bbdd4'
#Начало создания мероприятия
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Настройки профиля",
        callback_data="settings", )
    )
    builder.add(types.InlineKeyboardButton(
        text='Список предстоящих мероприятий',
        callback_data="event_list"
    ))

    if len(databases.list_documents(dbid, cid, Query.equal('userid', message.from_user.id))) == 0:
        response = databases.create_document(
                dbid,
                ucid,
                document_id=ID.unique(),
                data={
                    'userid':message.from_user.id,
                }
        )
    await message.reply("Привет!\nТы открыл официального бота Тула Куда пойти!\nЗдесь ты найдёшь интересные мероприятия города\n", reply_markup=builder.as_markup())
class setting(StatesGroup):
    ch_mpage = State()
    ch_place = State()
    ch_radius = State()
async def chplace_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    #did = manager.dialog_data.get('did', '')
    #result = databases.update_document(dbid, cid, did, {'datetime':str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())})
    userid = manager.event.from_user.id
    did = databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents']['$id']
    manager.dialog_data["did"] = did
    response = databases.update_document(dbid, ucid, did, {'location':[message.location.longitude, message.location.latitude]})
    await manager.switch_to(event_editing.ch_editing)
async def chplace_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    #did = manager.dialog_data.get('did', '')
    #result = databases.update_document(dbid, cid, did, {'datetime':str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())})
    DISTANCE = int(message.text)*1000; #Интересующее нас расстояние

    #https://en.wikipedia.org/wiki/Longitude#Length_of_a_degree_of_longitude
    #did = databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents'][0]['$id']
    longitude = float(databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents'][0]['location'][0]) #Интересующие нас координаты широты. Потом будут импортироваться из тг.
    latitude = float(databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents'][0]['location'][1]) #Интересующие нас координаты долготы. Потом будут импортироваться из тг.
    deltaLon = compute_Delta(longitude); # Дельту по долготе
    deltaLat = compute_Delta(latitude); #Получаем дельту по широте
    aroundLat = DISTANCE / deltaLat; # Вычисляем диапазон координат по широте
    aroundLon = DISTANCE / deltaLon; # Вычисляем диапазон координат по долготе
    #did = databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents']['$id']
    #manager.dialog_data["did"] = did

    response = databases.update_document(dbid, ucid, did, {'cordirange':[longitude-aroundLon/2, longitude+aroundLon/2, latitude-aroundLat/2, latitude+aroundLat/2]})
    await manager.switch_to(event_editing.ch_editing)
chplace = Window(
    Const('Пришли местоположение'),
    MessageInput(chplace_handler)
)
chradius = Window(
    Const('Пришли радиус поиска, например, 5, где 5 - число километров'),
    MessageInput(chradius_handler)
)
mainwindow = Window(
    Const('Ты зашёл в настройки бота. Здесь ты можешь поменять местоположение и радиус поиска'),
    Button('Местоположение', on_click=SwitchTo(setting.ch_place)),
    Button('Радиус поиска', on_click=SwitchTo(setting.ch_radius))
)
setting_dialog = Dialog(mainwindow, chplace, chradius)
async def event_getter(dialog_manager: DialogManager,**_kwargs):
    userid = dialog_manager.event.from_user.id
    kritery = databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents']['cordirange']
    a = databases.list_documents(dbid, ucid, [Query.lessthan()])['documents']
    names = []
    ids = []
    for el in a:
        tmp = {}
        tmp['name'] = el['name']
        tmp['id'] = el['$id']
        names.append(tmp)
        #ids.append(el['$id'])
    #dialog_manager.dialog_data["ids"] = ids
    return {
        'products':names,
    }
event_choose = Window(
    Const('Все перемены к лучшему! Выбери необходимое мероприятие из списка'),
    ScrollingGroup(
        Select(
            Format("{item[name]}"),
            id='s_events',
            items='products',
            item_id_getter=lambda x:x['id'],
            on_click=on_fruit_selected,
        ),
        Button(
            Const('Назад'),
            on_click=Back(),
            id='eeback'
        ),
        width=1,
        height=5,
        id='scroll_with_pager'
    ),
    getter=tbc_getter,
    state=event_editing.ch_event_choose
)
@dp.callback_query(Text("settings"))
async def cc(callback: types.CallbackQuery, manager: DialogManager):
    await manager.start(setting.ch_place, mode=StartMode.RESET_STACK)
@dp.callback_query(Text("event_list"))
async def el(callback: types.CallbackQuery, manager: DialogManager):
    await manager.start(setting.ch_place, mode=StartMode.RESET_STACK)
if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram_dialog import Window, Dialog, DialogManager, StartMode, setup_dialogs
from aiogram_dialog.widgets.kbd import Button, Row, Back, SwitchTo, Select, Url
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from datetime import date
from datetime import datetime
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery
from aiogram.filters.command import Command, CommandObject, CommandStart
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Calendar
from aiogram import F
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup
from appwrite.query import Query
from operator import itemgetter
from typing import Any
import math
from numpy import deg2rad
from aiogram.types import BufferedInputFile
from icalendar import Calendar as Callend
from icalendar import Event, vText
import pytz
import os
from dotenv import load_dotenv
from aiogram_dialog.widgets.text import Jinja
load_dotenv()
async def notifyChanges(chatid, text):
    bot.send_message(chat_id=chatid, text=text)
async def compute_Delta(degrees):
    return math.pi / 180.0 * 6371210 * math.cos(deg2rad(degrees))

class setting(StatesGroup):
    ch_mpage = State()
    ch_place = State()
    ch_radius = State()
class eventlist(StatesGroup):
    ch_elist = State()
    ch_event = State()
async def chplace_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    #did = manager.dialog_data.get('did', '')
    #result = databases.update_document(dbid, cid, did, {'datetime':str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())})
    userid = manager.event.from_user.id
    did = databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents'][0]['$id']
    #manager.dialog_data["did"] = did
    response = databases.update_document(dbid, ucid, did, {'location':[message.location.longitude, message.location.latitude]})
    await manager.switch_to(setting.ch_mpage)
async def chradius_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    userid = manager.event.from_user.id
    #did = manager.dialog_data.get('did', '')
    #result = databases.update_document(dbid, cid, did, {'datetime':str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())})
    DISTANCE = int(message.text)*1000; #Интересующее нас расстояние

    #https://en.wikipedia.org/wiki/Longitude#Length_of_a_degree_of_longitude
    did = databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents'][0]['$id']
    longitude = float(databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents'][0]['location'][0]) #Интересующие нас координаты широты. Потом будут импортироваться из тг.
    latitude = float(databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents'][0]['location'][1]) #Интересующие нас координаты долготы. Потом будут импортироваться из тг.
    deltaLon = math.pi / 180.0 * 6371210 * math.cos(deg2rad(longitude)) # Дельту по долготе
    deltaLat = math.pi / 180.0 * 6371210 * math.cos(deg2rad(latitude)) #Получаем дельту по широте
    aroundLat = DISTANCE / deltaLat; # Вычисляем диапазон координат по широте
    aroundLon = DISTANCE / deltaLon; # Вычисляем диапазон координат по долготе
    #did = databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents']['$id']
    #manager.dialog_data["did"] = did

    response = databases.update_document(dbid, ucid, did, {'coordirange':[longitude-aroundLon/2, longitude+aroundLon/2, latitude-aroundLat/2, latitude+aroundLat/2]})
    await manager.switch_to(setting.ch_mpage)
chplace = Window(
    Const('Пришли местоположение'),
    MessageInput(chplace_handler),
    state=setting.ch_place
)
chradius = Window(
    Const('Пришли радиус поиска, например, 5, где 5 - число километров'),
    MessageInput(chradius_handler),
    state=setting.ch_radius
)
mainwindow = Window(
    Const('Ты зашёл в настройки бота. Здесь ты можешь поменять местоположение и радиус поиска'),
    Button(Const('Местоположение'), on_click=SwitchTo(setting.ch_place,state=setting.ch_place, id='place'), id='mplace'),
    Button(Const('Радиус поиска'), on_click=SwitchTo(setting.ch_radius, state=setting.ch_radius, id='radius'), id='mradius'),
    state=setting.ch_mpage
)
 
setting_dialog = Dialog(mainwindow, chplace, chradius)
async def event_getter(dialog_manager: DialogManager,**_kwargs):
    userid = dialog_manager.event.from_user.id
    kritery = databases.list_documents(dbid, ucid, [Query.equal('userid', userid)])['documents'][0]['coordirange']
    a = databases.list_documents(dbid, cid, [Query.less_than('p_longitude', kritery[1]), Query.less_than('p_latitude', kritery[3]), Query.greater_than('p_longitude', kritery[0]), Query.greater_than('p_latitude', kritery[2]), Query.equal('accepted', True)])['documents']
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
async def on_event_selected(callback: CallbackQuery, widget: Any,
                            manager: DialogManager, item_id: str):
    manager.dialog_data['did'] = item_id
    await manager.next()
event_choose = Window(
    Const('Выбери интересующее мероприятие из списка'),
    ScrollingGroup(
        Select(
            Format("{item[name]}"),
            id='s_events',
            items='products',
            item_id_getter=lambda x:x['id'],
            on_click=on_event_selected,
        ),
        width=1,
        height=5,
        id='scroll_with_pager'
    ),
    getter=event_getter,
    state=eventlist.ch_elist
)

async def get_data(dialog_manager: DialogManager,**_kwargs):
    did = dialog_manager.dialog_data.get("did", "")
    if len(did) == 0:
        did = dialog_manager.start_data.get("did", "")
    doc = databases.get_document(dbid, cid, did)
    #print(did)
    return {
        'name': doc['name'],
        'datetime': doc['datetime'],
        'place': [doc['p_latitude'],doc['p_longitude']],
        'venue': doc['venue'],
        'description': doc['description'],
        'did':did
    }
async def add_booking(c: CallbackQuery, button: Button, manager: DialogManager):
    did = manager.dialog_data.get("did", "")
    if len(did) == 0:
        did = manager.start_data.get("did", "")
    document = databases.get_document(dbid, cid, did)
    doc = databases.get_document(dbid, cid, did)['grokers']
    #print(manager.event.from_user.id)
    doc.append(databases.list_documents(dbid, ucid, queries=[Query.equal('userid', manager.event.from_user.id)])['documents'][0]['chatid'])
    response = databases.update_document(dbid, cid, did, {'grokers':doc})
    cal = Callend()
    cal.add('dtstart', datetime.fromisoformat(document['datetime']))
    cal.add('prodid', '-//Kuda<->Tuda notifier//')
    cal.add('version', '1.0')
    event = Event()
    event.add('summary', document['name'])
    event.add('dtstart', datetime.fromisoformat(document['datetime']).replace(tzinfo=pytz.timezone('Europe/Moscow')))
    event.add('dtend', datetime.fromisoformat(document['datetime']).replace(tzinfo=pytz.timezone('Europe/Moscow')))
    event.add('dtstamp', datetime.fromisoformat(document['datetime']).replace(tzinfo=pytz.timezone('Europe/Moscow')))
    event.add('description', document['description'])
    event['location'] = vText(document['venue'])
    cal.add_component(event)
    text_file = BufferedInputFile(cal.to_ical(), filename=f"{document['name']}.ics")
    await c.message.answer_document(text_file)
txt = Jinja("""
Ты выбрал мероприятие:<b>{{name}}</b>
Дата и время:<b>{{datetime}}</b>
Описание: {{description}}
<a href="https://c0lbarator.github.io/location.html?text=geo:{{place[0]}},{{place[1]}}">Место:{{venue}}</a>
""")
event_window = Window(
    txt,
    Button(Const('Записаться'), on_click=add_booking, id='booking'),
    Url(
        Const("Поделиться"),
        Format("https://t.me/share/url?url=https://t.me/step_vanish_bot?start=event_{did}&text=Тут проводят классное мероприятие, присоединяйся!"),
    ),
    state=eventlist.ch_event,
    getter=get_data,
    parse_mode="HTML"
)
e_dialog = Dialog(event_choose, event_window)
#https://en.wikipedia.org/wiki/Longitude#Length_of_a_degree_of_longitude

client = (Client().set_endpoint('http://localhost/v1').set_project('661d778d002d0d91cacd').set_key('27b19c1cfff08c7f232ef7776f38e5d89c8647a88ef7a77da41952f8babb3f62b20d98ebeefb22e07db7d90b09fcb2b87ee72803065ff6afe7f0e0be687b14f62308538aa720e3de9ad6432a5365efaea33f05cafde1c072fe901c050c2b95a2e6807eb6c2189f6ad05ffbdb49671f97ae3190023ff4a94e02f084f585f322c3'))
API_TOKEN = os.getenv('USER_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(setting_dialog)
dp.include_router(e_dialog)
setup_dialogs(dp)
databases = Databases(client)
dbid, ucid = '661d77b300189e3cc563', '661d7c7c0019a70faf6e'
cid = '661d77d5000350aebace'
@dp.message(CommandStart(deep_link=True))
async def event_sharing(message:Message, command: CommandObject, dialog_manager: DialogManager):
    evid = command.args.split("_")[1]
    print(evid)
    await dialog_manager.start(eventlist.ch_event, data={"did":evid})
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
    if len(databases.list_documents(dbid, ucid, [Query.equal('userid', message.from_user.id)])['documents']) == 0:
        response = databases.create_document(
                dbid,
                ucid,
                document_id=ID.unique(),
                data={
                    'userid':message.from_user.id,
                    'chatid':message.chat.id
                }
        )
    await message.reply("""Привет!\nТы открыл официального бота Тула Куда пойти!\nЗдесь ты найдёшь интересные мероприятия города\n Если ты тут в первый раз,
    перед использованием настрой бота под себя""", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "settings")
async def cc(callback: types.CallbackQuery,  dialog_manager: DialogManager):
    await  dialog_manager.start(setting.ch_place, mode=StartMode.RESET_STACK)
@dp.callback_query(F.data == "event_list")
async def el(callback: types.CallbackQuery,  dialog_manager: DialogManager):
    await  dialog_manager.start(eventlist.ch_elist, mode=StartMode.RESET_STACK)
if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)

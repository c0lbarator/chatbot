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
from aiogram import F
#from aiogram.filters import Text
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup
from appwrite.query import Query
from operator import itemgetter
from typing import Any
import os
from dotenv import load_dotenv
from icalendar import Calendar as Callend
from icalendar import Event
import pytz
from aiogram.types import BufferedInputFile
from aiogram.methods.send_document import SendDocument
from aiogram.methods.send_message import SendMessage
from geopy.geocoders import Nominatim
import time
load_dotenv()
#Nominatim приложение
app = Nominatim(user_agent="where<->here")
#Подключаемся к бдшке
client = (Client().set_endpoint('http://localhost/v1').set_project('661d778d002d0d91cacd').set_key('27b19c1cfff08c7f232ef7776f38e5d89c8647a88ef7a77da41952f8babb3f62b20d98ebeefb22e07db7d90b09fcb2b87ee72803065ff6afe7f0e0be687b14f62308538aa720e3de9ad6432a5365efaea33f05cafde1c072fe901c050c2b95a2e6807eb6c2189f6ad05ffbdb49671f97ae3190023ff4a94e02f084f585f322c3'))
databases = Databases(client)
dbid, cid = '661d77b300189e3cc563', '661d77d5000350aebace'
#Начало создания мероприятия
class event_creation(StatesGroup):
    ch_event_name = State()
    ch_place = State()
    ch_date = State()
    ch_time = State()
    ch_is_paid = State()
    ch_paylink = State()
    ch_age_limit = State()
    ch_description = State()
    ch_finish = State()

async def get_data(dialog_manager: DialogManager, **kwargs):
    if dialog_manager.dialog_data.get("paid", "") == True:
        pay = '✅'
    else:
        pay = '❌'
    if dialog_manager.dialog_data.get("paylink", "") == None:
        paylink = '-'
    else:
        paylink = dialog_manager.dialog_data.get("paylink", "")
    return {
        "event_name": dialog_manager.dialog_data.get("event_name", ""),
        "place": dialog_manager.dialog_data.get("place", ""),
        "date": dialog_manager.dialog_data.get("date", ""),
        "time": dialog_manager.dialog_data.get("time", ""),
    }
    
async def event_name_handler(message: Message, message_input: MessageInput,
                       manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data["event_name"] = message.text
    await manager.next()

async def place_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data["place"] = [message.location.longitude, message.location.latitude]
    await manager.next()

async def time_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data["time"] = message.text
    await manager.next()
async def on_date_selected(c: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data["date"] = selected_date
    await manager.next()
async def description_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    if manager.is_preview():
        await manager.next()
    manager.dialog_data["description"] = message.text
    await manager.next()
async def on_finish(callback: CallbackQuery, button: Button,
                    manager: DialogManager):
    if manager.is_preview():
        await manager.done()
        return
    print(manager.dialog_data.get("place", ""))
    #print("OOOOO", get_address(manager.dialog_data.get('place', '')[1],manager.dialog_data.get("place", "")[0]))
    response = databases.create_document(
        dbid,
        cid,
        document_id=ID.unique(),
        data={
            'userid':manager.event.from_user.id,
            'name':manager.dialog_data.get("event_name", ""),
            'p_longitude': manager.dialog_data.get("place", "")[0],
            'p_latitude': manager.dialog_data.get('place', '')[1],
            'datetime': str(datetime.fromisoformat(str(manager.dialog_data.get("date", ""))+' '+str(manager.dialog_data.get("time", ""))).isoformat()),
            'venue': app.reverse(f"{manager.dialog_data.get('place', '')[1]}, {manager.dialog_data.get("place", "")[0]}", language="ru").raw['display_name'],
            'description': manager.dialog_data.get("description", "")
        }
    )
    print(response)
    await callback.message.answer("Готово! Для добавления нового мероприятия отправь /start")
    await manager.done()
event_creation_w = Window(
    Const('Вау, в нашем городе новое мероприятие! Для начала, введи название мероприятия'),
    MessageInput(event_name_handler, content_types=[ContentType.TEXT]),
    state=event_creation.ch_event_name
)
place_selection = Window(
    Const('Ого, звучит круто! Где будет проходить мероприятие? Прикрепи геопозицию'),
    MessageInput(place_handler),
    state=event_creation.ch_place
)
date_selection = Window(
    Const('Отлично! Когда будет проходить мероприятие? Выбери число на календаре'),
    Calendar(id='calendar', on_click=on_date_selected),
    state=event_creation.ch_date
)
time_selection = Window(
    Const('Окей, а теперь поточнее! Во сколько будет проходить мероприятие? Укажи время в формате ЧЧ:ММ'),
    MessageInput(time_handler),
    state=event_creation.ch_time
)
description_selection = Window(
    Const("Такс, а теперь раскажи о мероприятии подробнее. Отправь описание и контакты"),
    MessageInput(description_handler),
    state=event_creation.ch_description
)
allin = Window(
    Format("Готово! Проверим информацию:\nМерприятие: {event_name}\nДата: {date}\nВремя: {time}\n Место: {place}"),
    Row(
            Back(),
            SwitchTo(Const("Заполнить сначала"), id="restart", state=event_creation.ch_event_name),
            Button(Const("Отправить"), on_click=on_finish, id="finish"),
        ),
    state=event_creation.ch_finish,
    getter=get_data,)

dialog_create = Dialog(event_creation_w, place_selection, date_selection,time_selection,description_selection, allin)

#Конец создания мероприятия
#Начало редактирования мероприятия
class event_editing(StatesGroup):
    ch_event_choose = State()
    ch_editing = State()
    ch_saving = State()
    ch_edit_date = State()
    ch_edit_time = State()
    ch_edit_place = State()

async def event_edit_ch(c: CallbackQuery, button: Button, manager: DialogManager):
    did = button.widget_id
    manager.dialog_data["did"] = did
    await manager.next()
async def tbc_getter(dialog_manager: DialogManager,**_kwargs):
    userid = dialog_manager.event.from_user.id
    a = databases.list_documents(dbid, cid, queries=[Query.equal('userid', userid)])['documents']
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



async def datetime_ch(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(event_editing.ch_edit_date)
async def ch_date_selected(c: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data["newdate"] = selected_date
    await manager.switch_to(event_editing.ch_edit_time)
async def chtime(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    did = manager.dialog_data.get('did', '')
    result = databases.update_document(dbid, cid, did, {'datetime':str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())})
    print(did)
    bookings = databases.get_document(dbid, cid, str(did))['grokers']
    for grokerid in set(bookings):
        cal = Callend()
        cal.add('dtstart', datetime.fromisoformat(str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())))
        cal.add('prodid', '-//Kuda<->Tuda notifier//')
        cal.add('version', '1.0')
        event = Event()
        event.add('summary', databases.get_document(dbid, cid, str(did))["name"])
        event.add('dtstart', datetime.fromisoformat(str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())).replace(tzinfo=pytz.timezone('Europe/Moscow')))
        event.add('dtend', datetime.fromisoformat(str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())).replace(tzinfo=pytz.timezone('Europe/Moscow')))
        event.add('dtstamp', datetime.fromisoformat(str(datetime.fromisoformat(str(manager.dialog_data.get("newdate", ""))+' '+message.text).isoformat())).replace(tzinfo=pytz.timezone('Europe/Moscow')))
        cal.add_component(event)
        text_file = BufferedInputFile(cal.to_ical(), filename=f"{databases.get_document(dbid, cid, str(did))["name"]}.ics")
        await bot_user(SendMessage(chat_id=grokerid, text=f'В мероприятии {databases.get_document(dbid, cid, str(did))["name"]} изменилось время проведения!\n Новое время: {manager.dialog_data.get("newdate", "")} {message.text}\n Лови новое оповещение🐦'))
        await bot_user(SendDocument(chat_id=grokerid,document=text_file))
        #await bot.send_message(chat_id=grokerid, text=f'В мероприятии {databases.get_document(dbid, cid, str(did))["name"]} изменилось время проведения!\n Новое время: {manager.dialog_data.get("newdate", "")} {message.text}\n Для добавления нового оповещения нажми кнопку записаться ещё раз')
    manager.dialog_data["newtime"] = message.text
    await manager.switch_to(event_editing.ch_editing)
async def place_ch(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(event_editing.ch_edit_place)
async def chplace(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    did = manager.dialog_data.get('did', '')
    print(did)
    bookings = databases.get_document(dbid, cid, str(did))['grokers']
    result = databases.update_document(dbid, cid, did, {'p_longitude':message.location.longitude, 'p_latitude':message.location.latitude})
    for grokerid in set(bookings):
        #await notifyChanges(chatid=grokerid, text=f'В мероприятии {databases.get_document(dbid, cid, str(did))["name"]} изменилось место проведения!\n Новое место: {message.location.longitude} {message.location.latitude}\n')
        await Bot(token=os.getenv("USER_TOKEN")).send_message(chat_id=grokerid, text=f'В мероприятии {databases.get_document(dbid, cid, str(did))["name"]} изменилось место проведения!\n Новое место: {message.location.longitude} {message.location.latitude}\n')
    await manager.switch_to(event_editing.ch_editing)
async def deledvent(c: CallbackQuery, button: Button, manager: DialogManager):
    did = manager.dialog_data.get('did', '')
    result = databases.delete_document(dbid, cid, did)
async def get_data(dialog_manager: DialogManager,**_kwargs):
    did = dialog_manager.dialog_data.get("did", "")
    doc = databases.get_document(dbid, cid, did)
    return {
        'name': doc['name'],
        'datetime': doc['datetime'],
        'place': [doc['p_longitude'], doc['p_latitude']],
        'accepted': doc['accepted']
    }

async def on_fruit_selected(callback: CallbackQuery, widget: Any,
                            manager: DialogManager, item_id: str):
    manager.dialog_data['did'] = item_id
    await manager.next()

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
        width=1,
        height=5,
        id='scroll_with_pager'
    ),
    getter=tbc_getter,
    state=event_editing.ch_event_choose
)
event_edit = Window(
    Format('Ты выбрал мероприятие:{name}\nДата:{datetime}\nМесто:{place}\nОдобрено модератором:{accepted}\nЧто ты хочешь изменить в карточке мероприятия?'),
    Row(
        Button(Const('Дату и время'), id='chdatetime', on_click=datetime_ch),
        Button(Const('Место'), id='chplace', on_click=place_ch),
        Button(Const('Удалить мероприятие'), id='deledvent', on_click=deledvent))
    ,
    state=event_editing.ch_editing,
    getter=get_data)
eedit_date = Window(
    Format('Выбери новую дату'),
    Calendar(id='calendar_editing', on_click=ch_date_selected),
    state=event_editing.ch_edit_date
)
eedit_time = Window(
    Format('Выбери новое время, так же в формате ЧЧ:ММ'),
    MessageInput(chtime),
    state=event_editing.ch_edit_time
)
eedit_place = Window(
    Format('Отправь новую геопозицию'),
    MessageInput(chplace),
    state=event_editing.ch_edit_place
)
dialog_edit = Dialog(event_choose, event_edit, eedit_date, eedit_time, eedit_place)
#Конец редактирования мероприятия
API_TOKEN = os.getenv("CREATOR_TOKEN")
bot = Bot(token=API_TOKEN)
bot_user = Bot(token=os.getenv("USER_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(dialog_create)
dp.include_router(dialog_edit)
setup_dialogs(dp)

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Создать мероприятие",
        callback_data="create_event", )
    )
    builder.add(types.InlineKeyboardButton(
        text='Редактировать мероприятие',
        callback_data="edit_event"
    ))
    await message.reply("Привет!\nТы открыл официального бота Тула Куда пойти для организаторов!\nЗдесь ты можешь создавать мероприятие и отправлять его на модерацию\n", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "create_event")
async def cc(callback: types.CallbackQuery, dialog_manager: DialogManager):
     await dialog_manager.start(event_creation.ch_event_name, mode=StartMode.RESET_STACK)
@dp.callback_query(F.data == "edit_event")
async def ec(callback: types.CallbackQuery, dialog_manager: DialogManager):
     await dialog_manager.start(event_editing.ch_event_choose, mode=StartMode.RESET_STACK)
if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)
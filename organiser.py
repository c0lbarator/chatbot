from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram_dialog import Window, Dialog, DialogManager, StartMode, setup_dialogs
from aiogram_dialog.widgets.kbd import Button, Row, Back, SwitchTo
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
from appwrite import Query
#Подключаемся к бдшке
client = (Client().set_endpoint('https://korglo.69.mu/v1').set_project('644bf71b1fd33de165c1').set_key('a6bf92e9132bfe0b157a212140cd4f286a357b2cf8b4158b947941402a74cdaa8b02e19bc9e54ccfc045877e1309dc8179daa95fc65bfe7398a2390019e1720f5d910bce6c1b7d9aed30f1489c46f21ebb8887f0d554987fb0f95faf9463f2e8ee040841074a2756580a1d44724486c0455a0d5e57285ee0b2ba67abb96f4575'))
databases = Databases(client)
dbid, cid = '644c2f1074ca81e7f813', '644c2f1d2011d5d35680'
#Начало создания мероприятия
class event_creation(StatesGroup):
    ch_event_name = State()
    ch_place = State()
    ch_date = State()
    ch_time = State()
    ch_is_paid = State()
    ch_paylink = State()
    ch_age_limit = State()
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
        "paid": pay,
        "paylink":paylink,
        'age_limit':dialog_manager.dialog_data.get("age_limit", "")
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
async def ev_is_paid(callback: CallbackQuery, button: Button,
                     manager: DialogManager):
    manager.dialog_data["paid"] = True
    await manager.next()
async def ev_isnt_paid(callback: CallbackQuery, button: Button,
                     manager: DialogManager):
    manager.dialog_data["paid"] = False
    await manager.switch_to(event_creation.ch_age_limit)
async def on_date_selected(c: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data["date"] = selected_date
    await manager.next()
async def on_finish(callback: CallbackQuery, button: Button,
                    manager: DialogManager):
    if manager.is_preview():
        await manager.done()
        return
    if manager.dialog_data.get("paylink", "") == '':
        response = databases.create_document(
            '644c2f1074ca81e7f813',
            '644c2f1d2011d5d35680',
            document_id=ID.unique(),
            data={
                'userid':callback.message.from_user.id,
                'name':manager.dialog_data.get("event_name", ""),
                'place': manager.dialog_data.get("place", ""),
                'datetime': str(datetime.fromisoformat(str(manager.dialog_data.get("date", ""))+' '+str(manager.dialog_data.get("time", ""))).isoformat()),
                'paid': manager.dialog_data.get("paid", ""),
                'age_limit':manager.dialog_data.get("age_limit", "")
            }
        )
        print(response)
    else:

        response = databases.create_document(
            '644c2f1074ca81e7f813',
            '644c2f1d2011d5d35680',
            document_id=ID.unique(),
            data={
                'userid':callback.message.from_user.id,
                'name':manager.dialog_data.get("event_name", ""),
                'place': manager.dialog_data.get("place", ""),
                'datetime': str(datetime.fromisoformat(str(manager.dialog_data.get("date", ""))+' '+str(manager.dialog_data.get("time", ""))).isoformat()),
                'paid': manager.dialog_data.get("paid", ""),
                'paylink':manager.dialog_data.get("paylink", ""),
                'age_limit':manager.dialog_data.get("age_limit", "")
            }
        )
        print(response)
    await callback.message.answer("Готово! Для добавления нового мероприятия отправь /start")
    await manager.done()
async def paylink_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data["paylink"] = message.text
    await manager.next()
async def age_limit_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data["age_limit"] = message.text
    await manager.next()
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
    Const('Окей, а теперь поточнее! Во сколько будет проходить мероприятие?'),
    MessageInput(time_handler),
    state=event_creation.ch_time
)
is_paid = Window(
    Const('Мероприятие будет платным?'), 
    Row(
        Button(
            Const('Да'),
            id='true',
            on_click=ev_is_paid
        ),
        Button(
            Const('Нет'),
            id='false',
            on_click=ev_isnt_paid
        )
    ),
    state=event_creation.ch_is_paid
)
paylink = Window(
    Const('Окей! Теперь отправь ссылку на оплату'),
    MessageInput(paylink_handler),
    state=event_creation.ch_paylink
)
age_limit = Window(
    Const('Твоё мероприятие может подходить не всем, уточни, есть ли ограничения по возрасту?'),
    MessageInput(age_limit_handler),
    state=event_creation.ch_age_limit
)
allin = Window(
    Format("Готово! Проверим информацию:\nМерприятие: {event_name}\nДата: {date}\nВремя: {time}\nПлатное: {paid}\nСсылка на оплату: {paylink}\nОграничения по возрасту: {age_limit}\nКоординаты: {place}"),
    Row(
            Back(),
            SwitchTo(Const("Restart"), id="restart", state=event_creation.ch_event_name),
            Button(Const("Finish"), on_click=on_finish, id="finish"),
        ),
    state=event_creation.ch_finish,
    getter=get_data,)

dialog = Dialog(event_creation_w, place_selection, date_selection,time_selection, is_paid, paylink, age_limit, allin)

#Конец создания мероприятия
#Начало редактирования мероприятия
class event_creation(StatesGroup):
    ch_event_choose = State()
    ch_editing = State()
    ch_saving = State()

async def event_edit_ch(c: CallbackQuery, button: Button, manager: DialogManager):
    did = button.widget_id
    manager.dialog_data["did"] = did
    await manager.next()
async def tbc(manager: DialogManager):
    userid = manager.event.from_user.id
    buttons = []
    a = databases.list_documents(dbid, cid, [Query.equal('userid', userid)])['documents']
    for el in a:
        buttons.append(Const(el['name']+','+datetime.fromisoformat(el['datetime']).isoformat(' ')), id=el['$id'], on_click=event_edit_ch)
async def datetime_ch(c: CallbackQuery, button: Button, manager: DialogManager):
    did = button.widget_id
    manager.dialog_data["did"] = did
    await manager.next()
async def place_ch(c: CallbackQuery, button: Button, manager: DialogManager):
    did = button.widget_id
    manager.dialog_data["did"] = did
    await manager.next()
event_choose = Window(
    Const('Все перемены к лучшему! Выбери необходимое мероприятие из списка'),
    ScrollinGroup(
        tbc(),
        width=1,
        heightt=7
    )
)
event_edit = Window(
    Format('Ты выбрал мероприятие:{name}\nДата:{datetime}\nМесто:{place}\nПлатное:{paid}\nСсылка на оплату:{paylink}\nОграничения по возрасту:\nЧто ты хочешь изменить в карточке мероприятия?'),
    Row(
        Button(Const('Дату и время'), on_click=datetime_ch),
        Button(Const('Место'), on_click=place_ch),
    )
)


API_TOKEN = '1037774621:AAH41GlT7PvLff40QF1f6CzY0_IjY7bot6M'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(dialog)
setup_dialogs(dp)

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Создать мероприятие",
        callback_data="create_event")
    )
    builder.add(types.InlineKeyboardButton(
        text='Редактировать мероприятие',
        callback_data="edit_event"
    ))
    await message.reply("Привет!\nТы открыл официального бота Тула Куда пойти для организаторов!\nЗдесь ты можешь создавать мероприятие и отправлять его на модерацию\n", reply_markup=builder.as_markup())

@dp.callback_query(Text("create_event"))
async def cc(callback: types.CallbackQuery, dialog_manager: DialogManager):
     await dialog_manager.start(event_creation.ch_event_name, mode=StartMode.RESET_STACK)
@dp.callback_query(Text("edit_event"))
async def ec(callback: types.CallbackQuery, dialog_manager: DialogManager):
     await dialog_manager.start(event_creation.ch_event_name, mode=StartMode.RESET_STACK)
if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)

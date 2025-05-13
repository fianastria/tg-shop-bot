import sqlite3

from aiogram import Router, F

from aiogram import types, Bot
from aiogram.filters.command import Command
from keyboards import kbs

from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from aiogram.exceptions import TelegramRetryAfter
from time import sleep

from config_reader import config
from handlers import pre_sales_handler, sales_handler, admin_handler


router = Router()

with sqlite3.connect("main.db") as connection:
    c = connection.cursor()
    print(c.execute("SELECT * FROM admins").fetchall())

#admins(tg_id, name)
photo1 = config.photo1
photo2 = config.photo2

greetings_text = '''\
привет !!
я бот, который поможет вам заказать мерч автора milisu 🎀

с чего начнём?'''




#@router.message(F.text == "yogetme")
#async def admin(message: types.Message):
    #id = message.from_user.id
    #name = message.from_user.first_name
    #with sqlite3.connect("main.db") as connection:
        #c = connection.cursor()
        #c.execute(f"INSERT INTO admins VALUES({id}, '{name}')")
        #print(c.fetchone(), "done")

#@router.message(F.photo)
#async def photos(message: types.Message):
    #print(message.photo[-1].file_id)




async def saving_func(user_id, ms_cb, state):
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "pay%" ORDER BY name')
        temp = c.fetchall()
        for i in temp:
            if str(user_id) in i[0]:
                await ms_cb(
                    text='''\
    ⚠️ внимание, есть возможность, что ваш заказ утерян ⚠️

    если вы уже СОВЕРШИЛИ оплату, нажмите "подтвердить"

    если подтвердить оплату не получится, свяжитесь с автором как можно скорее, он решит вашу проблему —> @milisuuuu

    если вы ничего не заказывали, то просто нажмите "отменить"''',
                    reply_markup=kbs.save()
                )
                await state.set_state(pre_sales_handler.Pre_CLientSaver.need_help)

                return
                #хендлер отмены внизу
        
        c.execute(f'''DROP TABLE IF EXISTS pre_basket_{user_id}''')
        c.execute(f'''DROP TABLE IF EXISTS pre_page_{user_id}''')

def pre_a_code(id):
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT name FROM sqlite_master WHERE type="table"')
        temp = c.fetchall()
        c.execute(f'SELECT 1 FROM pre_sales_data WHERE id = {id} AND shipping = "Авито"')
        is_a = c.fetchone()
    
    for i in temp:
        if 'pre_a_code' == i and is_a:
            return True
        



@router.message(
    StateFilter(
        None,
        pre_sales_handler.Pre_Saling.leaving_e,
        pre_sales_handler.Pre_Saling.Paying.paying_comment,
        pre_sales_handler.Pre_CLientSaver,
        sales_handler.Saling.leaving_e,
        admin_handler.Pre_Add_Sales_Data
    ),
    Command("start")
)
async def cmd_start(message: types.Message, state: FSMContext):
    id = message.from_user.id


    await message.answer_photo(
        photo=photo1,
        caption=greetings_text,
        reply_markup=kbs.greetings_kb(id, pre_a_code(id))
    )

    await state.clear()

    await saving_func(id, message.answer, state)

    

@router.callback_query(
    StateFilter(
        None,
        pre_sales_handler.Pre_Saling.leaving_e,
        pre_sales_handler.Pre_CLientSaver,
        sales_handler.Saling.leaving_e
    ),
    F.data == 'greetings'
)
async def b_greetings(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_media(
        types.InputMediaPhoto(
            media=photo1,
            caption=greetings_text,
        ),
        reply_markup=kbs.greetings_kb(callback.from_user.id)
    )

    await state.clear()

    await saving_func(callback.from_user.id, callback.message.answer, state)



@router.callback_query(F.data == "author")
async def b_author(callback: types.CallbackQuery):
    text = '''\
автора можно найти тут —>
🎀телеграмм канал — https://t.me/milisu_merch
🎀тик ток — https://www.tiktok.com/@milisu_merch?_t=8qxJyBrRUzm&_r=1
🎀вк — https://vk.com/milisu_merch

полки автора —>
• Казань, Баумана 82, тц Свита Холл, 2 этаж "Полка Чудес" 11.2.3
• Екатеринбург, Вайнера 8, тц Красный Леопард 2 этаж "Полка Чудес" 40.5.1 [2 зал]
• Новосибирск, Красный проспект 17, 2 этаж "Лисья Полка" 10.1.2
• Санкт-Петербург, Московский просп. 7 (метро Садовая), "КрафтиКо" 22.1 [карта мерча: https://t.me/milisu_merch/1019?single ]
• Краснодар, Рашпилевская 17, "Полка Чудес", 3.4.2
• Москвы пока нет! Стою в очереди на неё'''
    await callback.message.edit_caption(
        caption=text,
        reply_markup=kbs.back_to_greetings_kb()
    )

@router.callback_query(F.data == "messages")
async def b_messages_is_on(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'SELECT * FROM notification WHERE id = {user_id}')
        
        if c.fetchone() is None:
            c.execute(f'INSERT INTO notification (id) VALUES ({user_id})')

    await callback.message.edit_caption(
        caption='''\
вы подписались на рассылку, чтобы получать новости об открытии заказов первыми!

✨️ её в любой момент можно отключить ! ✨️''',
        reply_markup=kbs.back_to_greetings_from_messages_is_on_kb()
    )

@router.callback_query(F.data == "messages_off")
async def b_messages_is_off(callback: types.CallbackQuery):
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'DELETE FROM notification WHERE id = {callback.from_user.id}')

    await callback.message.edit_caption(
        caption='''\
вы отписались от рассылки и больше не будете получать сообщения об открытии заказов

✨️ её в любой момент можно подключить ! ✨️''',
        reply_markup=kbs.back_to_greetings_from_messages_is_off_kb()
    )

@router.callback_query(pre_sales_handler.Pre_CLientSaver.need_help, F.data == 'deny_help')
async def deny_help(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text='вы точно уверены, что хотите отменить оплату?',
        reply_markup=kbs.save2()
    )

    await state.set_state(pre_sales_handler.Pre_CLientSaver.need_help_check)

    await callback.answer()

@router.callback_query(pre_sales_handler.Pre_CLientSaver.need_help_check, F.data == 'deny_help2')
async def deny_help2(callback: types.CallbackQuery, state: FSMContext):
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "pay%" ORDER BY name')
        temp = c.fetchall()
        user_id = callback.from_user.id
        for i in temp:
            if str(user_id) in i[0]:
                c.execute(f'DROP TABLE IF EXISTS {i[0]}')
                c.execute(f'DROP TABLE IF EXISTS pre_customer_{user_id}')

                break
    
    await callback.message.answer(
        text='оплата отменена\n\nвы можете вернуться в главное меню при помощи кнопки или команды /start',
        reply_markup=kbs.back_to_greetings_kb()
    )

    await state.clear()
    await callback.answer()

#----------АВИТО--------------
class Message_For_Pre_A(StatesGroup):
    text = State()

@router.callback_query(F.data == 'send_pre_a_code')
async def send_pre_a_code(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        text='введите код и отправьте сообщением сюда, он автоматически отправится автору'
    )
    await state.set_state(Message_For_Pre_A.text)

@router.message(Message_For_Pre_A.text, F.text != "/start")
async def send_pre_a_code_2(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    code = message.text
    user_name = message.from_user.username
    if user_name is None:
        user_name = '*юзернейм отсутствует*'
    else:
        user_name = '@' + user_name
    text = f'''\
#код_авито
Пользователь: {message.from_user.first_name}
Юзернейм: {user_name}
id: {message.from_user.id}
Код: <code>{code}</code>'''

    r = 1295442952
    try:
        await bot.send_message(chat_id=r, text=text, parse_mode=ParseMode.HTML)
    except TelegramRetryAfter as e:
        sleep(e.retry_after)
        await bot.send_message(chat_id=r, text=text, parse_mode=ParseMode.HTML)


    await message.answer(
        text=f'ваш код: {code}\nотправлен',
        reply_markup=kbs.back_to_greetings_kb
    )


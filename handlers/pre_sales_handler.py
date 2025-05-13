import sqlite3

from aiogram import Router, F
from aiogram import types
from keyboards import kbs, sales_kbs
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from filters import is_admin

from datetime import datetime

from uuid import uuid4
from config_reader import config
from yoomoney import Client, Quickpay

from handlers import admin_handler


pre_sales_router = Router()
photo2 = config.photo2
photo3 = config.photo3



class Pre_Saling(StatesGroup):
    choosing_e = State()
    choosing = State()

    shipping = State()

    leaving = State()
    leaving_e = State()

    class y_go(StatesGroup):
        y_notification = State()
        y_adress = State()
        y_contact = State()

    class rf(StatesGroup):
        rf_notification = State()
        rf_adress = State()
        rf_name = State()
        rf_contact = State()

    class av(StatesGroup):
        av_check = State()

    class Paying(StatesGroup):
        paying_1 = State()
        paying_comment = State()

#СТЭЙТЫ ДЛЯ СПАСЕНИЯ
class Pre_CLientSaver(StatesGroup):
    need_help = State()
    need_help_check = State()





#-------------------------------отмена и выход----------------
@pre_sales_router.callback_query(Pre_Saling.choosing, F.data == 'finish')
async def finish(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()    
        c.execute(f'''DROP TABLE IF EXISTS payment_{user_id}''')
        c.execute(f'''DROP TABLE IF EXISTS pre_customer_{user_id}''')

    await callback.message.edit_media(
        types.InputMediaPhoto(
            media=photo3,
            caption='вы уверенны, что хотите выйти?\nтовары из корзины удалятся! 🥺'
        ),
        reply_markup=sales_kbs.leaving_check()
    )
    await state.set_state(Pre_Saling.leaving)

@pre_sales_router.message(
    ~StateFilter(Pre_Saling.choosing_e),
    StateFilter(Pre_Saling.Paying.paying_1, Pre_Saling.leaving),
    F.text.casefold() == 'отмена'
)
@pre_sales_router.message(
    ~StateFilter(Pre_Saling.choosing_e),
    StateFilter(Pre_Saling.Paying.paying_1, Pre_Saling.leaving),
    Command("start")
)
async def cmd_start_during_saling(message: types.Message, state: FSMContext):
    await message.answer_photo(
        photo=photo3,
        caption='вы уверенны, что хотите выйти и очистить корзину?\nесли корзина оплачена, могут возникнуть проблемы 🥺',
        reply_markup=sales_kbs.leaving_check('check_payment')
    )
    
    await state.set_state(Pre_Saling.leaving)


@pre_sales_router.message(
    ~StateFilter(Pre_Saling.choosing_e),
    StateFilter(Pre_Saling),
    F.text.casefold() == 'отмена'
)
@pre_sales_router.message(
    ~StateFilter(Pre_Saling.choosing_e),
    StateFilter(Pre_Saling),
    Command("start")
)
async def cmd_start_after_saling(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        
        c.execute(f'''DROP TABLE IF EXISTS pre_customer_{user_id}''')

    await message.answer_photo(
        photo=photo3,
        caption='вы уверенны, что хотите выйти?\nтовары из корзины удалятся! 🥺',
        reply_markup=sales_kbs.leaving_check()
    )
    
    await state.set_state(Pre_Saling.leaving)

@pre_sales_router.callback_query(Pre_Saling.leaving, F.data == 'clear')
async def clear(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''DROP TABLE IF EXISTS pre_customer_{user_id}''')
        c.execute(f'''DROP TABLE IF EXISTS payment_{user_id}''')
        c.execute(f'''DROP TABLE IF EXISTS pre_basket_{user_id}''')
        c.execute(f'''DROP TABLE IF EXISTS pre_page_{user_id}''')
        

    await callback.message.edit_caption(
        caption='корзина очищена✅️\n\nможете вернуться в главное меню при помощи кнопки снизу или команды\n/start',
        reply_markup=sales_kbs.leaving_check_2()
    )
    
    await state.clear()


@pre_sales_router.callback_query(Pre_Saling.choosing_e, F.data == 'finish')
async def finish_e(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_media(
        types.InputMediaPhoto(
            media=photo3,
            caption='вы уверенны, что хотите выйти? 🥺'
        ),
        reply_markup=sales_kbs.leaving_check_e()
    )

    await state.set_state(Pre_Saling.leaving_e)

@pre_sales_router.message(Pre_Saling.choosing_e, Command('start'))
async def finish_e_cmd(message: types.Message, state: FSMContext):
    await message.answer_photo(
        photo=photo3,
        caption='вы уверенны, что хотите выйти? 🥺',
        reply_markup=sales_kbs.leaving_check_e()
    )

    await state.set_state(Pre_Saling.leaving_e)
        
#---------------ВЫБОР ТОВАРОВ--------------------------

def make_closing_date():
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute('''SELECT * FROM pre_sales_closing_date''')
        temp = c.fetchone()[0].split('_')

    ymd = [int(i) for i in temp[0].split('-')]
    hm = [int(i) for i in temp[1].split(':')]
    closing_date = datetime(year=ymd[2], month=ymd[1], day=ymd[0], hour=hm[0], minute=hm[1])
    
    return closing_date

def make_text(positions, starts_with, basket_text = ''):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        positions_text = ''
        for i in range(starts_with, starts_with + positions):
            c.execute(f'''SELECT * FROM pre_product_list WHERE position = {i}''')
            position_data = c.fetchone()
            #(1, 'Котята', 0, 200)
            positions_text += f'\n{position_data[0]}. {position_data[1]} - {position_data[-1]}руб.'
        

    text = f'''\
✨️ пред-заказы открыты до {make_closing_date().strftime("%d.%m.%Y %H:%M")}! ✨️
''' + positions_text + basket_text
    return text


def make_basket_text(basket):
    if len(basket) == 0:
        basket_text = ''
    else:
        
        basket_text = '\n\nКорзина:'
        basket_summ = 0

        for i in basket:
            #(position, name, count, is_paper, price)
            basket_text += f'\n{i[0]}. {i[1]} - {i[2]}шт. - {i[2] * i[4]}руб.'
            basket_summ += i[2] * i[4]

        basket_text += f'\nИтого: {basket_summ}руб.'
    
    return basket_text


async def is_basket_empty(state, basket):
    if len(basket) != 0:
        await state.set_state(Pre_Saling.choosing)
    else:
        await state.set_state(Pre_Saling.choosing_e)


async def basket_is_huge(callback, state):
    await callback.answer(
        text='''\
ваш заказ ТАКОЙ большой, что бот с ним не справится ･ﾟﾟ･(／ω＼)･ﾟﾟ･

напишите автору, он сам примет ваш заказ !♡♡ @milisuuuu''',
        show_alert=True
    )

    await callback.message.answer(
        text='''\
⬆️ваша корзина осталась выше⬆️

связаться с автором: @milisuuuu''',
        reply_markup=sales_kbs.leaving_check_2()
    )

    user_id = callback.from_user.id
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''DROP TABLE pre_basket_{user_id}''')
        c.execute(f'''DROP TABLE pre_page_{user_id}''')
    await state.clear()


@pre_sales_router.callback_query(F.data == "pre_sales")
async def sales_start(callback: types.CallbackQuery, state: FSMContext):
    if admin_handler.pre_sales_status and datetime.today() <= make_closing_date():
        basket = []
        await is_basket_empty(state=state, basket=basket)

            
        with sqlite3.connect("main.db") as connection:
            
            c = connection.cursor()

            user_id = callback.from_user.id
            c.execute(f'''CREATE TABLE IF NOT EXISTS pre_basket_{user_id}
            (position INT UNIQUE,
            name TEXT,
            count INT,
            is_paper INT,
            price INT)''')
            c.execute(f'''DROP TABLE IF EXISTS pre_page_{user_id}''')
            c.execute(f'''CREATE TABLE IF NOT EXISTS pre_page_{user_id} (page INT)''')
            c.execute(f'''INSERT INTO pre_page_{user_id} (page) VALUES (1)''')

            c.execute('''SELECT * FROM pre_pages WHERE page = 1''')
            page_data = c.fetchone()
            
            

        await callback.message.edit_media(
            types.InputMediaPhoto(
                media=page_data[1],
                caption=make_text(page_data[-2], page_data[-1]),
                parse_mode=ParseMode.HTML
            ),
            reply_markup=sales_kbs.sales_processing(basket=basket, pre='pre_')
        )
    
    else:
        await callback.message.edit_media(
            types.InputMediaPhoto(
                media=photo2,
                caption="на данный момент пред заказы закрыты :(\nпримерная дата открытия следующих - хх.хх"
            ),
            reply_markup=kbs.back_to_greetings_kb()
        )


@pre_sales_router.callback_query(
    StateFilter(
        Pre_Saling.choosing,
        Pre_Saling.choosing_e,
        Pre_Saling.leaving,
        Pre_Saling.leaving_e,
        Pre_Saling.shipping
    ),
    F.data.startswith('page_')
)
async def sales_specific_page(callback: types.CallbackQuery, state: FSMContext):
    try:
        page_number = int(callback.data.split('_')[1])
        user_id = callback.from_user.id

        

        with sqlite3.connect("main.db") as connection:
            c = connection.cursor()

            c.execute(f'''SELECT * FROM pre_basket_{user_id} ORDER BY position''')
            basket = c.fetchall()
            await is_basket_empty(state=state, basket=basket)
            c.execute(f'''UPDATE pre_page_{user_id} SET page = {page_number} WHERE page = page''')

            
            c.execute(f'''SELECT * FROM pre_pages WHERE page = {page_number}''')
            page_data = c.fetchone()
            
        await callback.message.edit_media(
            types.InputMediaPhoto(
                media=page_data[1],
                caption=make_text(page_data[-2], page_data[-1], make_basket_text(basket)),
                parse_mode=ParseMode.HTML
            ),
            reply_markup=sales_kbs.sales_processing(basket=basket, page=page_number, pre='pre_')
        )
    
    except TelegramBadRequest:
        await basket_is_huge(callback=callback, state=state)



@pre_sales_router.callback_query(
    StateFilter(
        Pre_Saling.choosing,
        Pre_Saling.choosing_e,
        Pre_Saling.leaving,
        Pre_Saling.leaving_e,
        Pre_Saling.shipping
    ),
    F.data.startswith('position_')
)
async def add_to_basket(callback: types.CallbackQuery, state: FSMContext):
    try:
        user_choice = callback.data.split('_')[1]
        user_id = callback.from_user.id

        with sqlite3.connect("main.db") as connection:
            c = connection.cursor()
            c.execute(f'''SELECT * FROM pre_product_list WHERE position = {user_choice}''')
            position_data = c.fetchone()
            c.execute(f'''SELECT EXISTS(SELECT position FROM pre_basket_{user_id} WHERE position = {position_data[0]})''')
            if c.fetchone()[0]:
                c.execute(f'''UPDATE pre_basket_{user_id} SET count = count + 1 WHERE position = {position_data[0]}''')
            else:
                c.execute(f'''INSERT INTO pre_basket_{user_id} (position, name, count, is_paper, price)
                VALUES
                    ({position_data[0]},
                    '{position_data[1]}',
                    1,
                    {position_data[2]},
                    {position_data[3]})''')
            
            c.execute(f'''SELECT * FROM pre_basket_{user_id} ORDER BY position''')
            basket = c.fetchall()

            c.execute(f'''SELECT * FROM pre_page_{user_id}''')
            page_number = c.fetchone()[0]

            c.execute(f'''SELECT * FROM pre_pages WHERE page = {page_number}''')
            page_data = c.fetchone()
#(1, 'Котята', 0, 200) номер, название, бумажная или нет, цена  
        

        await callback.message.edit_caption(
            caption=make_text(page_data[-2], page_data[-1], make_basket_text(basket)),
            parse_mode=ParseMode.HTML,
            reply_markup=sales_kbs.sales_processing(basket=basket, page=page_data[0], pre='pre_')
        )
        await state.set_state(Pre_Saling.choosing)
    
    except TelegramBadRequest:
        await basket_is_huge(callback=callback, state=state)



#------------------ЗАПОЛНЕНИЕ ДАННЫХ И ПОКУПКА----------------------


def contact_taking(message):
    if message.contact is None:
        contact = message.text
    else:
        contact = message.contact.phone_number
    
    if contact[0] == '7':
        contact = '8' + contact[1:]
    elif contact[:2] == '+7':
        contact = '8' + contact[2:]
    
    return contact

def is_letter(basket):
    #(position, name, count, is_paper, price)
    for i in basket:
        if not i[3]:
            return False
    return True



def shipping_price(shipping):
    if shipping == 'ЯндексGo':
        price = 350
    
    elif shipping == 'Почта России (ПИСЬМО)':
        price = 180

    elif shipping == 'Почта России (ПОСЫЛКА)':    
        price = 400
    
    else:
        price = 0

    return price

contact_inc_text = '''\
❌ данные введены неверно ❌

укажите ваш номер телефона

можете либо отправить его текстом (например 89991112233), либо нажать на кнопку, и тогда отправится ваш номер, сохраненный в телеграме'''


@pre_sales_router.callback_query(StateFilter(Pre_Saling), F.data == 'go_to_purcase')
async def go_to_purcase(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_name = callback.from_user.username
    if user_name is None:
        user_name = '*юзернейм отсутствует*'
    else:
        user_name = '@' + user_name

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''DROP TABLE IF EXISTS pre_customer_{user_id}''')
        c.execute(f'''CREATE TABLE pre_customer_{user_id}
        (id INT,
        username TEXT,
        full_name TEXT,
        shipping TEXT,
        adress TEXT,
        contact TEXT,
        price INT,
        comment TEXT,
        goods TEXT)''')
        c.execute(f'''INSERT INTO pre_customer_{user_id}
        (id,
        username,
        full_name,
        shipping,
        adress,
        contact,
        price,
        comment,
        goods)
        VALUES
            ({user_id},
            '{user_name}',
            '-',
            '-',
            '-',
            '-',
            '-',
            '-',
            '-')''')
     
    await state.set_state(Pre_Saling.shipping)
    await callback.message.answer(
        text='''\
🎀 отлично, заказ собран! Пожалуйста, выберете удобный способ доставки из тех, что перечисленны ниже 🎀

примичание: ФИКСИРОВАННАЯ стоимость
✨️ посылки Почты России — 4ООр
✨️ письма Почты России — 18Ор
✨️ отправки ЯндексGo — 35Ор
✨️ отправки через Авито — от 3О до 15Ор''',
        reply_markup=sales_kbs.choosing_shipping()
    )
    await callback.answer()


@pre_sales_router.callback_query(Pre_Saling.shipping, F.data == 'y_notification')
async def y_notification(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text='''\
внимание ‼️
после оформления заказа через ЯндексGo, <b>очень желательно</b> скачать приложение и зарегистрироваться в нём !
это позволит вам в любой момент отследить статус вашего заказа и понять, когда посылка придёт

на крайний случай, если вы не хотите ничего скачивать, СМС с ссылкой для получения и отслеживания посылки придет вам на <b>номер телефона</b> !

коды и ссылки для отслеживания я не буду рассылать в ручную🙏🏼

готовы оформить заказ или выберете другой ПВЗ?''',
        parse_mode=ParseMode.HTML,
        reply_markup=sales_kbs.y_notification_kb()
    )
    await state.set_state(Pre_Saling.y_go.y_notification)
    await callback.answer()

@pre_sales_router.callback_query(Pre_Saling.y_go.y_notification, F.data == 'y_go')
async def yandex_adress(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''UPDATE pre_customer_{user_id} SET shipping = "ЯндексGo"''')


    await state.update_data(shipping='ЯндексGo')
    
    await callback.message.answer(
        text='''\
✨️ необходимо внести данные для регистрации посылки ✨️
назовите адрес ПВЗ Яндекса (Яндекс Маркета) где вам будет удобно забрать посылку? 

например:
Москва, ул. Арбат, д. 4, стр. 1''',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await callback.answer()
    await state.set_state(Pre_Saling.y_go.y_adress)


@pre_sales_router.message(Pre_Saling.y_go.y_adress, F.text)
async def yandex_contact(message: types.Message, state: FSMContext):
    try:
        text = message.text
        user_id = message.from_user.id
        with sqlite3.connect('main.db') as connection:
            c = connection.cursor()
            c.execute(f'''UPDATE pre_customer_{user_id} SET adress = "{text}"''')

        await state.update_data(adress=text)
        await message.answer(
            text='''\
✨️ укажите ваш номер телефона ✨️

можете либо отправить его текстом (например 89991112233), либо нажать на кнопку, и тогда отправится ваш номер, сохраненный в телеграме''',
            reply_markup=sales_kbs.give_contact()
        )
        await state.set_state(Pre_Saling.y_go.y_contact)
    except Exception:
        await message.answer(
            text='''\
❌ данные введены неверно ❌

назовите адрес ПВЗ Яндекса (Яндекс Маркета) где вам будет удобно забрать посылку? 

например:
Москва, ул. Арбат, д. 4, стр. 1''',
        )

@pre_sales_router.message(Pre_Saling.y_go.y_contact, F.contact)
@pre_sales_router.message(Pre_Saling.y_go.y_contact, F.text)
async def yandex_check(message: types.Message, state: FSMContext):
    try:
        contact = contact_taking(message)
        user_id = message.from_user.id
        with sqlite3.connect('main.db') as connection:
            c = connection.cursor()
            c.execute(f'''UPDATE pre_customer_{user_id} SET contact = "{contact}"''')

        await state.update_data(contact = contact)
        await state.update_data(name='-')
        user_data = await state.get_data()
        await message.answer(
            text=f'''\
🎀 проверьте введенные вами данные:

адрес ПВЗ Яндекса: {user_data['adress']}
ваш номер телефона: {user_data['contact']}

верно?''', 
            reply_markup=sales_kbs.y_check()
        )
    
    except Exception:
        await message.answer(
            text=contact_inc_text,
            reply_markup=sales_kbs.give_contact()
        )
    

#-------------

@pre_sales_router.callback_query(Pre_Saling.shipping, F.data == 'rf_notification')
async def rf_notification(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text='''\
внимание ‼️
для оформления заказа через почту россии, вам нужно будет <b>в обязательном порядке</b>‼️ зарегистрироваться в приложении "Почта России". скачать его можно в гугл плэй и апстор

это делается по той причине, что трек-номер [код, для получения заказа] вам <b>придёт в приложении</b> ! рассылать их лично я не будут !!

готовы оформить заказ или выберете другой ПВЗ?''',
        parse_mode=ParseMode.HTML,
        reply_markup=sales_kbs.rf_notification_kb()
    )
    await state.set_state(Pre_Saling.rf.rf_notification)
    await callback.answer()


@pre_sales_router.callback_query(Pre_Saling.rf.rf_notification, F.data == 'rf')
async def rf_adress(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''SELECT * FROM pre_basket_{user_id}''')
        basket = c.fetchall()

        if is_letter(basket):
            text = '(ПИСЬМО)'
        else:
            text = '(ПОСЫЛКА)'

        shipping_text = 'Почта России ' + text
        c.execute(f'''UPDATE pre_customer_{user_id} SET shipping = "{shipping_text}"''')


    await state.update_data(shipping=shipping_text)
    await callback.message.answer(
        text='''\
✨️ необходимо внести данные для регистрации посылки ✨️
назовите ПОЛНЫЙ (включая почтовый индекс) адрес отделения Почты России где вам будет удобно забрать посылку?

например:
Москва, ул. Тверская, д. 9а, строение 5а, индекс: 125009'''
    )
    await callback.answer()
    await state.set_state(Pre_Saling.rf.rf_adress)

@pre_sales_router.message(Pre_Saling.rf.rf_adress, F.text)
async def rf_name(message: types.Message, state: FSMContext):
    try:
        text = message.text
        user_id = message.from_user.id
        with sqlite3.connect('main.db') as connection:
            c = connection.cursor()
            c.execute(f'''UPDATE pre_customer_{user_id} SET adress = "{text}"''')

        await state.update_data(adress=message.text)
        await message.answer(
            text='''\
✨️ укажите Ваши ФИО ✨️

например:
Стрельцов Иван Анатольевич''',
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(Pre_Saling.rf.rf_name)
    
    except Exception:
        await message.answer(
        text='''\
❌ данные введены неверно ❌

назовите ПОЛНЫЙ (включая почтовый индекс) адрес отделения Почты России где вам будет удобно забрать посылку?

например:
Москва, ул. Тверская, д. 9а, строение 5а, индекс: 125009'''
        )

@pre_sales_router.message(Pre_Saling.rf.rf_name, F.text)
async def rf_contact(message: types.Message, state: FSMContext):
    try:
        text = message.text
        user_id = message.from_user.id
        with sqlite3.connect('main.db') as connection:
            c = connection.cursor()
            c.execute(f'''UPDATE pre_customer_{user_id} SET full_name = "{text}"''')

        await state.update_data(name=text)
        await message.answer(
            text='''\
✨️ укажите ваш номер телефона ✨️

можете либо отправить его текстом (например 89991112233), либо нажать на кнопку, и тогда отправится ваш номер, сохраненный в телеграме''',
            reply_markup=sales_kbs.give_contact()
        )
        await state.set_state(Pre_Saling.rf.rf_contact)

    except Exception:
        await message.answer(
            text='''\
❌ данные введены неверно ❌

укажите Ваши ФИО 

например:
Стрельцов Иван Анатольевич'''
        )



@pre_sales_router.message(Pre_Saling.rf.rf_contact, F.contact)
@pre_sales_router.message(Pre_Saling.rf.rf_contact, F.text)
async def rf_check(message: types.Message, state: FSMContext):
    try:
        contact = contact_taking(message)
        user_id = message.from_user.id
        with sqlite3.connect('main.db') as connection:
            c = connection.cursor()
            c.execute(f'''UPDATE pre_customer_{user_id} SET contact = "{contact}"''')

        await state.update_data(contact = contact)
        user_data = await state.get_data()
        await message.answer(
            text=f'''\
🎀 проверьте введенные вами данные:

адрес отделения Почты России: {user_data['adress']}
ваши ФИО: {user_data['name']}
ваш номер телефона: {user_data['contact']}

верно?''',
            reply_markup=sales_kbs.y_check()
        )

    except Exception:
        await message.answer(
            text=contact_inc_text,
            reply_markup=sales_kbs.give_contact()
        )
    

#-------------------------------------
@pre_sales_router.callback_query(Pre_Saling.shipping, F.data == 'av')
async def av_info(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Pre_Saling.av.av_check)
    user_id = callback.from_user.id
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''UPDATE pre_customer_{user_id} SET shipping = "Авито"''')

    await state.update_data(shipping='Авито')
    await state.update_data(adress='-')
    await state.update_data(name='-')
    await state.update_data(contact='-')
    await callback.message.answer(
        text='''\
❗❗❗оплата и регистрация отправлений через Авито происходит тогда, когда автор начнёт собирать заказы!
обычно это срок от 15 до 40 дней после даты окончания заказов. 
🎀 бот пришлёт вам сообщение с ссылкой на объявление Авито, которое нужно будет оплатить, чтобы ваша Авито-доставка зарегистрировалась.
пока платить за доставку НЕ нужно.''',
        reply_markup=sales_kbs.av_check()
    )

    await callback.answer()
    

#---------------ОПЛАТА-------------

client = Client(config.kassa_token.get_secret_value())
receiver = config.receiver.get_secret_value()

def basket_sum(basket):
    b_sum = 0

    for i in basket:
        b_sum += i[0] * i[1]
    
    return b_sum
    

@pre_sales_router.callback_query(
    StateFilter(
        Pre_Saling.y_go.y_contact,
        Pre_Saling.rf.rf_contact,
        Pre_Saling.av.av_check
    ),
    F.data == 'paying'
)
async def y_paying(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Pre_Saling.Paying.paying_1)
    user_id = callback.from_user.id
    label = str(uuid4())
    print('label =', label)
    user_data = await state.get_data()

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''CREATE TABLE IF NOT EXISTS payment_{user_id}
        (label TEXT,
        url TEXT,
        sum INT)''')
        

        c.execute(f'''SELECT count, price FROM pre_basket_{user_id}''')
        basket = c.fetchall()

        whole_sum = basket_sum(basket) + shipping_price(user_data['shipping'])

        quickpay = Quickpay(
            receiver=receiver,
            quickpay_form='shop',
            targets=f'покупка мерча на сумму {whole_sum}',
            paymentType='SB',
            sum = whole_sum,
            label=label
        )

        url_to_pay = quickpay.base_url

        c.execute(f'''INSERT INTO payment_{user_id} (label, url, sum)
        VALUES
            ("{label}",
            "{url_to_pay}",
            {whole_sum})''')
    
    await callback.message.answer(
        text = f'к оплате с учетом вашей корзины и выбранного способа доставки: {whole_sum}\n\n🎀 после оплаты нажмите на другую кнопку, чтобы подтвердить платеж 🎀',
        reply_markup=sales_kbs.paying_kb_1(url_to_pay)
    )

    await callback.answer()



@pre_sales_router.callback_query(
    StateFilter(
        Pre_Saling.Paying.paying_1,
        Pre_Saling.leaving,
        Pre_CLientSaver.need_help
    ),
    F.data == 'check_payment'
)
async def check_paiment(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''SELECT * FROM payment_{user_id}''')
        payment_data = c.fetchone()

    history = client.operation_history(label=payment_data[0])
    for operation in history.operations:
        if operation.status == 'success':
            try:
                goods = 'Список товаров:'
                

                with sqlite3.connect('main.db') as connection:
                    c = connection.cursor()
                    c.execute(f'''SELECT * FROM pre_basket_{user_id} ORDER BY position''')
                    basket = c.fetchall()

                    for i in basket:
                        #(position, name, count, is_paper, price)

                        goods += f'\n{i[0]}. {i[1]} - {i[2]}шт.'
                    
                    c.execute(f"""UPDATE pre_customer_{user_id} SET goods = '{goods}', price = {payment_data[2]}""")

                    c.execute(f'''INSERT INTO pre_sales_data (id, username, full_name, shipping, adress, contact, price, comment, goods)
                    SELECT * FROM pre_customer_{user_id}''')

                    c.execute(f'''DROP TABLE pre_basket_{user_id}''')
                    c.execute(f'''DROP TABLE pre_page_{user_id}''')
                    c.execute(f'''DROP TABLE payment_{user_id}''')
                    c.execute(f'''DROP TABLE pre_customer_{user_id}''')
                    
                await callback.message.answer(
                    text= '''\
оплата прошла✅️

можете оставить комментарий к заказу, просто отправьте его сообщением сюда.

если вам нечего написать в комментарии, просто напишите -'''
                )
                
                await state.set_state(Pre_Saling.Paying.paying_comment)
                return
            
            except Exception:
                await callback.message.answer(
                    text='''\
оплата прошла✅️

❌ но ваши данные были записаны с ошибкой и не были сохранены ❌

пожалуйста свяжитесь с автором: @milisuuuu'''
                )
                await state.clear()

                with sqlite3.connect('main.db') as connection:
                    c = connection.cursor()
                    c.execute(f'''DROP TABLE IF EXISTS pre_basket_{user_id}''')
                    c.execute(f'''DROP TABLE IF EXISTS pre_page_{user_id}''')
                    c.execute(f'''DROP TABLE IF EXISTS payment_{user_id}''')
                    c.execute(f'''DROP TABLE IF EXISTS pre_customer_{user_id}''')

                return

    await state.set_state(Pre_Saling.Paying.paying_1)
    await callback.message.answer(
        text='Оплата не прошла ❌',
        reply_markup=sales_kbs.paying_kb_1(payment_data[1])
    )

@pre_sales_router.message(Pre_Saling.Paying.paying_comment, F.text != '/start')
async def commenting(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_comment = message.text

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute(f'''UPDATE pre_sales_data SET comment = '{user_comment}' WHERE id = {user_id}''')
    
    text = '''\
оплата прошла✅️

заказ отправится вам как только автор получит весь мерч! это может занять от 15 до 40 дней

подробная информация всегда имеется в канале у автора или, если что-то пошло не так, вы можете связаться с ним лично: @milisuuuu

после получения заказа буду благодарна, если вы оставите отзыв —> https://t.me/milisu_merch/111

🎀 хорошего дня! 🎀'''

    await state.clear()

    await message.answer(
        text=text,
        reply_markup=sales_kbs.leaving_check_2()
    )


@pre_sales_router.callback_query(StateFilter(None), F.data == 'check_payment')
async def unable_to_check(callback: types.CallbackQuery):
    await callback.answer(
        text='''\
что-то пошло не так.
это иногда случается, когда вы подтверждали оплату слишком долго.

если вы СОВЕРШИЛИ оплату, то напишите команду /start
вам должно отправиться окно касательно статуса вашей оплаты''',
        show_alert=True
    )

#если кнопка не работает, обычно когда бот перезапускался, а чел был в процессе оплаты

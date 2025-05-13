import sqlite3

from aiogram import Router, F
from aiogram import types
from keyboards import kbs, sales_kbs
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.filters.command import Command
from aiogram.enums import ParseMode

from datetime import datetime

from uuid import uuid4
from config_reader import config
from yoomoney import Client, Quickpay

from handlers import admin_handler


sales_router = Router()
#product_list [(1, 'Котята', 6, 200), (2, 'Разбитая бутылка водки', 1, 10), (3, 'Какао в банке', 4, 160), (4, 'Какао утка', 3, 70), (5, 'Зеленая упаковка', 9, 100)]
#pages [(1, 'AgACAgIAAxkBAAOYZ5PyoaDg-7-8-mztadU7qeyHsKEAAhnqMRvx8aBIwuQdsuzi5KQBAAMCAAN5AAM2BA', 2, 1),
#      (2, 'AgACAgIAAxkBAAICB2eb1xDMGbaoFJt5927X0VLf7z6ZAAKc6zEbz5TYSJC6dLYhe8gUAQADAgADeQADNgQ', 3, 3)]
photo2 = config.photo2
photo3 = config.photo3

basket = dict()


class Saling(StatesGroup):
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


def make_closing_date():
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute('''SELECT * FROM sales_closing_date''')
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
            c.execute(f'''SELECT * FROM product_list WHERE position = {i}''')
            position_data = c.fetchone()
            #(1, 'Котята', 0, 0, 200)

            if position_data[-2] != 0:
                positions_text += f'\n{position_data[0]}. {position_data[1]} - {position_data[-1]}руб.'
            else:
                positions_text += f'\n{position_data[0]}. {position_data[1]} - нет в наличии :('
        

    text = f'''\
✨️онлайн-заказы открыты до {make_closing_date().strftime("%d.%m.%Y %H:%M")}!✨️

• для оформления заказа укажите <b>номера позиций</b>, которые хотите приобрести, а после того, как закончите с выбором, нажмите "<b>готово</b>"
• страницы можно листать, нажимая "<b>далее</b>" и "<b>назад</b>"

Список товаров на данной странице:\
''' + positions_text + basket_text
    return text


def make_basket_text():
    if len(basket) == 0:
        basket_text = ''
    else:
        #(1, 'Котята', 0, 6, 200) номер, название, бумажная или нет, кол-во., цена
        basket_text = '\n\nКорзина:'
        basket_summ = 0
        for i in basket:
            with sqlite3.connect("main.db") as connection:
                c = connection.cursor()
                c.execute(f'''SELECT * FROM product_list WHERE name = "{i}"''')
                position_data = c.fetchall()[0]
            basket_text += f'\n{i} - {basket[i]}шт. - {position_data[-1] * basket[i]}руб.'
            basket_summ += position_data[-1] * basket[i]
        basket_text += f'\nИтого: {basket_summ}руб.'
    
    return basket_text



#-------------------------------отмена и выход----------------
@sales_router.callback_query(Saling.choosing, F.data == 'finish')
async def finish(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_media(
        types.InputMediaPhoto(
            media=photo3,
            caption='вы уверенны, что хотите выйти?\nтовары из корзины удалятся! 🥺'
        ),
        reply_markup=sales_kbs.leaving_check()
    )
    await state.set_state(Saling.leaving)

@sales_router.message(
    ~StateFilter(Saling.choosing_e),
    StateFilter(Saling),
    F.text.casefold() == 'отмена'
)
@sales_router.message(
    ~StateFilter(Saling.choosing_e),
    StateFilter(Saling),
    Command('start')
)
async def cmd_start_after_saling(message: types.Message, state: FSMContext):
    await message.answer_photo(
        photo=photo3,
        caption='вы уверенны, что хотите выйти?\nтовары из корзины удалятся! 🥺',
        reply_markup=sales_kbs.leaving_check()
    )
    await state.set_state(Saling.leaving)

@sales_router.callback_query(Saling.leaving, F.data == 'clear')
async def clear(callback: types.CallbackQuery, state: FSMContext):
    global basket

    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        for i in basket:
            c.execute(f'''SELECT count FROM product_list WHERE name = "{i}"''')
            new_count = c.fetchone()[0] + basket[i]
            c.execute(f'''UPDATE product_list SET count = {new_count} WHERE name = "{i}"''')
    
    await callback.message.edit_caption(
        caption='корзина очищена✅️\n\nможете вернуться в главное меню при помощи кнопки снизу или команды\n/start',
        reply_markup=sales_kbs.leaving_check_2()
    )
    basket.clear()
    await state.clear()


@sales_router.callback_query(Saling.choosing_e, F.data == 'finish')
async def finish_e(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_media(
        types.InputMediaPhoto(
            media=photo3,
            caption='вы уверенны, что хотите выйти? 🥺'
        ),
        reply_markup=sales_kbs.leaving_check_e()
    )

    await state.set_state(Saling.leaving_e)

@sales_router.message(Saling.choosing_e, Command('start'))
async def finish_e_cmd(message: types.Message, state: FSMContext):
    await message.answer_photo(
        photo=photo3,
        caption='вы уверенны, что хотите выйти? 🥺',
        reply_markup=sales_kbs.leaving_check_e()
    )

    await state.set_state(Saling.leaving_e)
        
#---------------выбор товара--------------------------

async def is_basket_empty(state):
    if len(basket) != 0:
        await state.set_state(Saling.choosing)
    else:
        await state.set_state(Saling.choosing_e)


@sales_router.callback_query(F.data == "sales")
async def sales_start(callback: types.CallbackQuery, state: FSMContext):
    if admin_handler.sales_status and datetime.today() <= make_closing_date():
        await is_basket_empty(state=state)

            
        with sqlite3.connect("main.db") as connection:
            global page_data
            c = connection.cursor()
            c.execute('''SELECT * FROM pages WHERE page = 1''')
            page_data = c.fetchone()
        await callback.message.edit_media(
            types.InputMediaPhoto(
                media=page_data[1],
                caption=make_text(page_data[-2], page_data[-1], make_basket_text()),
                parse_mode=ParseMode.HTML
            ),
            reply_markup=sales_kbs.sales_processing(basket=basket)
        )
    
    else:
        await callback.message.edit_media(
            types.InputMediaPhoto(
                media=photo2,
                caption="на данный момент заказы закрыты :(\nпримерная дата открытия следующих - хх.хх"
            ),
            reply_markup=kbs.back_to_greetings_kb()
        )

@sales_router.callback_query(
    StateFilter(
        Saling.choosing,
        Saling.choosing_e,
        Saling.leaving,
        Saling.leaving_e,
        Saling.shipping
    ),
    F.data.startswith('page_')
)
async def sales_specific_page(callback: types.CallbackQuery, state: FSMContext):
    global page_data
    page_number = callback.data.split('_')[1]

    await is_basket_empty(state=state)

    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute(f'''SELECT * FROM pages WHERE page = {page_number}''')
        page_data = c.fetchone()
        
    await callback.message.edit_media(
        types.InputMediaPhoto(
            media=page_data[1],
            caption=make_text(page_data[-2], page_data[-1], make_basket_text()),
            parse_mode=ParseMode.HTML
        ),
        reply_markup=sales_kbs.sales_processing(basket=basket, page=page_data[0])
    )

@sales_router.callback_query(
    StateFilter(
        Saling.choosing,
        Saling.choosing_e,
        Saling.leaving,
        Saling.leaving_e,
        Saling.shipping
    ),
    F.data.startswith('position_')
)
async def add_to_basket(callback: types.CallbackQuery, state: FSMContext):
    global basket
    user_choice = callback.data.split('_')[1]

    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute(f'''SELECT * FROM product_list WHERE position = {user_choice}''')
        position_data = c.fetchone()

    #(1, 'Котята', 0, 6, 200) номер, название, бумажная или нет, кол-во., цена
        if position_data[-2] != 0:
            c.execute(f'''UPDATE product_list SET count = {position_data[-2] - 1} WHERE position = {user_choice}''')

        else:
            await callback.answer(
                text="К сожалению, данной позиции больше нет в наличии.",
                show_alert=True
            )
            return
        
    if position_data[1] in basket:
        basket[position_data[1]] += 1
    else:
        basket[position_data[1]] = 1

    await callback.message.edit_caption(
        caption=make_text(page_data[-2], page_data[-1], make_basket_text()),
        parse_mode=ParseMode.HTML,
        reply_markup=sales_kbs.sales_processing(basket=basket, page=page_data[0])
    )
    await state.set_state(Saling.choosing)

#------------------заполнение данных и покупка----------------------
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

def is_letter():
    for i in basket:
        with sqlite3.connect('main.db') as connection:
            c = connection.cursor()
            c.execute(f'SELECT is_paper FROM product_list WHERE name = "{i}"')
            is_paper = c.fetchone()[0]
        if not is_paper:
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


@sales_router.callback_query(StateFilter(Saling), F.data == 'go_to_purcase')
async def go_to_purcase(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Saling.shipping)
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


@sales_router.callback_query(Saling.shipping, F.data == 'y_notification')
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
    await state.set_state(Saling.y_go.y_notification)
    await callback.answer()

@sales_router.callback_query(Saling.y_go.y_notification, F.data == 'y_go')
async def yandex_adress(callback: types.CallbackQuery, state: FSMContext):
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
    await state.set_state(Saling.y_go.y_adress)

@sales_router.message(Saling.y_go.y_adress, F.text)
async def yandex_contact(message: types.Message, state: FSMContext):
    await state.update_data(adress=message.text)
    await message.answer(
        text='''\
✨️ укажите ваш номер телефона ✨️

можете либо отправить его текстом (например 89991112233), либо нажать на кнопку, и тогда отправится ваш номер, сохраненный в телеграме''',
        reply_markup=sales_kbs.give_contact()
    )
    await state.set_state(Saling.y_go.y_contact)

@sales_router.message(Saling.y_go.y_contact, F.contact)
@sales_router.message(Saling.y_go.y_contact, F.text)
async def yandex_check(message: types.Message, state: FSMContext):

    await state.update_data(contact = contact_taking(message))
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
    

#-------------

@sales_router.callback_query(Saling.shipping, F.data == 'rf_notification')
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
    await state.set_state(Saling.rf.rf_notification)
    await callback.answer()


@sales_router.callback_query(Saling.rf.rf_notification, F.data == 'rf')
async def rf_adress(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(shipping='Почта России')
    await callback.message.answer(
        text='''\
✨️ необходимо внести данные для регистрации посылки ✨️
назовите ПОЛНЫЙ (включая почтовый индекс) адрес отделения Почты России где вам будет удобно забрать посылку?

например:
Москва, ул. Тверская, д. 9а, строение 5а, индекс: 125009'''
    )
    await callback.answer()
    await state.set_state(Saling.rf.rf_adress)

@sales_router.message(Saling.rf.rf_adress, F.text)
async def rf_name(message: types.Message, state: FSMContext):
    await state.update_data(adress=message.text)
    await message.answer(
        text='''\
✨️ укажите Ваши ФИО ✨️

например:
Иванов Иван Анатольевич''',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Saling.rf.rf_name)

@sales_router.message(Saling.rf.rf_name, F.text)
async def rf_contact(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        text='''\
✨️ укажите ваш номер телефона ✨️

можете либо отправить его текстом (например 89991112233), либо нажать на кнопку, и тогда отправится ваш номер, сохраненный в телеграме''',
        reply_markup=sales_kbs.give_contact()
    )
    await state.set_state(Saling.rf.rf_contact)


@sales_router.message(Saling.rf.rf_contact, F.contact)
@sales_router.message(Saling.rf.rf_contact, F.text)
async def rf_check(message: types.Message, state: FSMContext):

    await state.update_data(contact = contact_taking(message))
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
    

#-------------------------------------
@sales_router.callback_query(Saling.shipping, F.data == 'av')
async def av_info(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Saling.av.av_check)
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

def basket_sum():
    b_sum = 0
    for i in basket:
        with sqlite3.connect("main.db") as connection:
            c = connection.cursor()
            c.execute(f'''SELECT price FROM product_list WHERE name = "{i}"''')
            price = c.fetchone()[0]
        b_sum += price * basket[i]
    
    return b_sum
    

@sales_router.callback_query(
    StateFilter(
        Saling.y_go.y_contact,
        Saling.rf.rf_contact,
        Saling.av.av_check
    ),
    F.data == 'paying'
)
async def y_paying(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Paying.paying_1)
    global label, whole_sum, url_to_pay
    label = str(uuid4())
    user_data = await state.get_data()

    print('label =', label)
    whole_sum = basket_sum() + shipping_price(user_data['shipping'])

    quickpay = Quickpay(
        receiver=receiver,
        quickpay_form='shop',
        targets=f'покупка мерча на сумму: {whole_sum}',
        paymentType='SB',
        sum = 2,
        label=label
    )

    url_to_pay = quickpay.base_url
    await callback.message.answer(
        text = f'к оплате с учетом вашей корзины и выбранного способа доставки: {whole_sum}\n\n🎀 после оплаты нажмите на другую кнопку, чтобы подтвердить платеж 🎀',
        reply_markup=sales_kbs.paying_kb_1(url_to_pay)
    )

@sales_router.callback_query(Saling.Paying.paying_1, F.data == 'check_paiment')
async def check_paiment(callback: types.CallbackQuery, state: FSMContext):
    global basket

    history = client.operation_history(label=label)
    for operation in history.operations:
        if operation.status == 'success':
            user_data = await state.get_data()
            user_id = callback.from_user.id
            user_name = callback.from_user.first_name
            goods = 'Список товаров:'
            for i in basket:
                goods += f'\n{i} - {basket[i]}шт.'

            with sqlite3.connect('main.db') as connection:
                c = connection.cursor()
                c.execute(f'''INSERT INTO sales_data (id, username, full_name, shipping, adress, contact, price, goods)
                VALUES
                    ({user_id},
                    "{user_name}",
                    "{user_data['name']}",
                    "{user_data['shipping']}",
                    "{user_data['adress']}",
                    "{user_data['contact']}",
                    {whole_sum},
                    "{goods}")''')
                
            await callback.message.answer(
                text= '''\
оплата прошла✅️

заказ отправится вам как только автор получит весь мерч! это может занять от 15 до 40 дней

подробная информация всегда имеется в канале у автора или, если что-то пошло не так, вы можете связаться с ним лично: @milisuuuu

после получения заказа буду благодарна, если вы оставите отзыв —> https://t.me/milisu_merch/111

🎀 хорошего дня! 🎀''',
                reply_markup=sales_kbs.leaving_check_2())
            
            await state.clear()
            basket.clear()
            return
        
    await callback.message.answer(
        text='Оплата не прошла ❌',
        reply_markup=sales_kbs.paying_kb_1(url_to_pay)
    )
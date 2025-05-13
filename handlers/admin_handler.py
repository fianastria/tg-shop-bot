import sqlite3

from aiogram import Router, F

from aiogram.filters import StateFilter
from aiogram import types, Bot
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.exceptions import TelegramRetryAfter
from time import sleep

from keyboards import admin_pannel, sales_kbs
#IsAdmin(admin_list_maker()

admin_router = Router()

@admin_router.callback_query(F.data == "admin")
async def b_start(callback: types.CallbackQuery):
    await callback.message.answer("Я тебя узнаю, админ", reply_markup=admin_pannel.choose_option())
    await callback.answer()

#----------------ЗАКАЗЫ---------------------------

@admin_router.callback_query(F.data == 'sales_options')
async def sales_options(callback: types.CallbackQuery):
    await callback.message.answer("Настройка Заказов", reply_markup=admin_pannel.table())
    await callback.answer()

class Add_Products(StatesGroup):
    pages = State()
    photo = State()
    positions = State()
    again_check = State()

    texts = {
        'Add_Products:pages': 'Введите кол-во. страниц заново',
        'Add_Products:photo': 'Отправьте фото товаров для данной страницы',
        'Add_Products:positions': 'Введите кол-во. позиций на данной странице'
    }

class Add_Positions(StatesGroup):
    total_positions = State()
    name = State()
    is_paper = State()
    count = State()
    price = State()
    again_check_position = State()

    texts = {
        'Add_Positions:total_positions': 'Введите общее кол-во. позиций',
        'Add_Positions:is_paper': 'Является ли товар бумажным? Введите "да" или "нет"',
        'Add_Positions:name': 'Введите название позиции',
        'Add_Positions:count': 'Введите кол-во. товара',
        'Add_Positions:price': 'Введите цену за единицу товара'
    }


#начало создания заказа
#переменная для демонстрации кнопок при создании заказа
starts_with = 1
is_first_page = True
is_first_position = True
#команда отмены и возврата на 1 шаг назад
@admin_router.message(StateFilter(Add_Products, Add_Positions), F.text.casefold() == 'отмена')
@admin_router.message(StateFilter(Add_Products, Add_Positions), Command('start'))
async def exit_handler(message: types.Message, state: FSMContext):
    global starts_with, is_first_page, is_first_position
    starts_with = 1
    is_first_page = True
    is_first_position = True

    await state.clear()
    await message.answer(text='Действия отменены', reply_markup=admin_pannel.choose_option())

@admin_router.message(StateFilter(Add_Products, Add_Positions), F.text.casefold() == 'назад')
async def calncel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == Add_Products.pages:
        await message.answer(text='Предыдущего шага нет. Введите кол-во. страниц или "отмена", чтобы выйти из создания заказа')
        return
    elif not is_first_page and current_state == Add_Products.photo:
        await message.answer(text='Изменить прошлую страницу не получится. Отправьте фото для страницы или введите "отмена", чтобы выйти из создания заказа')
        return

    if current_state == Add_Positions.total_positions:
        await message.answer(text='Предыдущего шага нет. Введите кол-во. позиций или "отмена", чтобы выйти из создания заказа')
        return
    elif not is_first_position and current_state == Add_Positions.name:
        await message.answer(text='Изменить прошлую позицию не получится. Введите название товара или "отмена", чтобы выйти из создания заказа')
        return


    previous = None
    if current_state in Add_Products.__all_states__:
        for step in Add_Products.__all_states__:
            if step.state == current_state:
                await state.set_state(previous)
                await message.answer(f'Вы вернулись к прошлому шагу\n\n{Add_Products.texts[previous.state]}')
                return
            previous = step

    elif current_state in Add_Positions.__all_states__:
        for step in Add_Positions.__all_states__:
            if step.state == current_state:
                await state.set_state(previous)
                await message.answer(f'Вы вернулись к прошлому шагу\n\n{Add_Positions.texts[previous.state]}')
                return
            previous = step



@admin_router.callback_query(StateFilter(None), F.data == 'create_table')
async def b_create_table(callback: types.CallbackQuery):
    await callback.message.answer(
        text='Вы уверены, что хотите создать новый заказ? Существующий на данный момент заказ удалится.',
        reply_markup=admin_pannel.check(path='admin', y_path='create_table_yes')
    )

@admin_router.callback_query(StateFilter(None), F.data == 'create_table_yes')
async def create_table(callback: types.CallbackQuery, state: FSMContext):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute('''SELECT name FROM sqlite_master WHERE type="table"''')
        temp_list = c.fetchall()
        tables = ['product_list', 'pages']
        for k in tables:
            for i in temp_list:
                if k == i[0]:
                    c.execute(f'''DROP TABLE {k}''')

        c.execute('''CREATE TABLE product_list
        (position INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        is_paper INT,
        count INT,
        price INT)''')
        c.execute('''CREATE TABLE pages
        (page INTEGER PRIMARY KEY AUTOINCREMENT,
        photo TEXT,
        positions INT,
        starts_with INT)''')

    await callback.message.answer(text='Введите кол-во. страниц\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Add_Products.pages)
    await callback.answer()


@admin_router.message(Add_Products.pages, F.text)
async def add_pages(message: types.Message, state: FSMContext):
    await state.update_data(pages=int(message.text))
    await message.answer(text='Отправьте фото товаров для данной страницы\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
    await state.set_state(Add_Products.photo)


@admin_router.message(Add_Products.photo, F.photo)
async def add_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer(text='Введите кол-во. позиций на данной странице\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
    await state.set_state(Add_Products.positions)


#демонстрация кнопок
@admin_router.message(Add_Products.positions, F.text)
async def add_positions(message: types.Message, state: FSMContext):
    await state.update_data(positions=int(message.text))
    user_data = await state.get_data()
    await message.answer_photo(
        photo = user_data['photo'],
        caption = '''\
**Кнопки для демонстрации**


*Для выхода напишите "отмена"*.
*Для отмены предыдущего шага напишите "назад"*''',
        reply_markup = sales_kbs.demonstration(user_data['positions'], starts_with)
    )
    await message.answer(
        text='Верно?',
        reply_markup=admin_pannel.check()
    )
    await state.set_state(Add_Products.again_check)

@admin_router.callback_query(Add_Products.again_check, F.data == 'yes')
@admin_router.callback_query(Add_Products.again_check, F.data == 'no')
async def correcting(callback: types.CallbackQuery, state: FSMContext):
    global starts_with, is_first_page
    if callback.data == 'yes':
        user_data = await state.get_data()
        with sqlite3.connect("main.db") as connection:
            c = connection.cursor()
            c.execute(f'''INSERT INTO pages (photo, positions, starts_with)
            VALUES
                ('{user_data['photo']}',
                {user_data['positions']},
                {starts_with})
            ''')
            
            c.execute('''SELECT * FROM pages''')
            print(c.fetchall(), "done")

        await state.update_data(pages=user_data['pages']-1)
        is_first_page = False
        user_data = await state.get_data()

        if user_data['pages'] != 0:
            starts_with += user_data['positions']
            await callback.message.answer(text='Страница сохранена\n*создание следующей страницы*\nОтправьте фото для данной страницы')
            await state.set_state(Add_Products.photo)

        else:
            starts_with = 1
            await callback.message.answer(text='Первый этап создания заказа завершён.\n\nТеперь давайте заполним позиции. Введите сколько всего позиций присутствует в заказе')
            await state.set_state(Add_Positions.total_positions)
    
    elif callback.data == 'no':
        await callback.message.answer(text='Прогресс удалён\n*повторное создание страницы*\nОтправьте фото для данной страницы')
        await state.set_state(Add_Products.photo)

    await callback.answer()


#------------Заполнение позиций-------------------
#class Add_Positions(StatesGroup):
    #total_positions = State()
    #name = State()
    #count = State()
    #price = State()
    #again_check_position = State()
position_counter = 1
@admin_router.message(Add_Positions.total_positions, F.text)
async def add_total_positions(message: types.Message, state: FSMContext):
    await state.update_data(total_positions = int(message.text))
    await message.answer(text=f'Позиция №{position_counter}\nВведите название товара\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
    await state.set_state(Add_Positions.name)

@admin_router.message(Add_Positions.name, F.text)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name = message.text)
    await message.answer(
        text=f'Позиция №{position_counter}\nЯвляется ли товар бумажным?\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*',
        reply_markup=admin_pannel.check()    
    )
    await state.set_state(Add_Positions.is_paper)

@admin_router.callback_query(Add_Positions.is_paper, F.data == 'yes')
@admin_router.callback_query(Add_Positions.is_paper, F.data == 'no')
async def add_is_paper(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'yes':
        await state.update_data(is_paper = 1)
        await callback.message.answer(text=f'Позиция №{position_counter}\nВведите кол-во. товара\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
        await state.set_state(Add_Positions.count)

    elif callback.data() == 'no':
        await state.update_data(is_paper = 0)
        await callback.message.answer(text=f'Позиция №{position_counter}\nВведите кол-во. товара\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
        await state.set_state(Add_Positions.count)

    await callback.answer()
    

@admin_router.message(Add_Positions.count, F.text)
async def add_count(message: types.Message, state: FSMContext):
    await state.update_data(count = int(message.text))
    await message.answer(text=f'Позиция №{position_counter}\nВведите цену за 1 единицу товара (только цифра)\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
    await state.set_state(Add_Positions.price)

@admin_router.message(Add_Positions.price, F.text)
async def add_price(message: types.Message, state: FSMContext):
    await state.update_data(price = int(message.text))
    user_data = await state.get_data()
    
    if user_data['is_paper']:
        is_paper_text = 'Является'
    else:
        is_paper_text = 'НЕ Является'

    await message.answer(
        text=f'''\
Позиция №{position_counter}
{user_data['name']} - {user_data['price']}руб. - В наличии: {user_data['count']}шт.

(Является ли продукция бумажной: Вы указали, что *{is_paper_text}*)
Верно?''',
        reply_markup=admin_pannel.check())
    await state.set_state(Add_Positions.again_check_position)

@admin_router.callback_query(Add_Positions.again_check_position, F.data == 'yes')
@admin_router.callback_query(Add_Positions.again_check_position, F.data == 'no')
async def again_check_position(callback: types.CallbackQuery, state: FSMContext):
    global position_counter, is_first_position, starts_with
    if callback.data == 'yes':
        user_data = await state.get_data()
        with sqlite3.connect("main.db") as connection:
            c = connection.cursor()
            c.execute(f'''INSERT INTO product_list (name, is_paper, count, price)
            VALUES
                ('{user_data['name']}',
                {user_data['is_paper']},
                {user_data['count']},
                {user_data['price']})
            ''')
            c.execute('''SELECT * FROM product_list''')
            print(c.fetchall(), "done")

        is_first_position = False
        position_counter += 1
        if position_counter <= user_data['total_positions']:
            await callback.message.answer(text=f'Позиция №{position_counter - 1} сохранена\n*создание следующей Позиции*\nПозиция №{position_counter}\nВведите название товара')
            await state.set_state(Add_Positions.name)
        
        else:
            await callback.message.answer(text='Создание заказа полностью завершено.\nПосмотреть результат можно в панели пользователя /start')
            await state.clear()
            position_counter = 1
            starts_with = 1

    elif callback.data == 'no':
        await callback.message.answer(text=f'Прогресс удалён\n*повторное создание позиции*\nПозиция №{position_counter}\nВведите название товара')
        await state.set_state(Add_Positions.name)
    
    await callback.answer()


#--------------СТАТУС ЗАКАЗОВ----------------
class Timer(StatesGroup):
    status = State()
    date = State()
    time = State()
    check = State()

sales_status = False

@admin_router.callback_query(F.data == 'sales_check')
async def sales_check(callback: types.CallbackQuery, state: FSMContext):
    if sales_status:
        await callback.message.answer(text='Статус заказов: Заказы включены ✅', reply_markup=admin_pannel.sales_status_switcher())

    else:
        await callback.message.answer(text='Статус заказов: Заказы выключены ❌', reply_markup=admin_pannel.sales_status_switcher())
        await state.set_state(Timer.status)
    
    await callback.answer()


@admin_router.callback_query(Timer.status, F.data == 'sales_switch_to_on')
async def sales_switch_to_on(callback: types.CallbackQuery, state: FSMContext):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute('''DROP TABLE IF EXISTS sales_closing_date''')

        c.execute('''CREATE TABLE sales_closing_date (date TEXT)''')

    await callback.message.answer(text='Новый статус заказов: Заказы включены ✅\nТеперь введите до какого числа они будут активны в формате:\nдень:месяц:год 00:00:0000')
    await callback.answer()
    await state.set_state(Timer.date)

def time_correcter(time):
    temp = time
    for i in range(2):
        if temp[i][0] == '0':
            
            temp[i] = temp[i][1]
    print(temp)
    return temp

@admin_router.message(Timer.date, F.text)
async def sales_take_data(message: types.Message, state: FSMContext):
    await state.update_data(date = time_correcter(message.text.split(':')))
    await message.answer(text='Теперь введите время в формате:\nчасы:минуты 00:00')
    await state.set_state(Timer.time)

def time_correcter_2(time):
    if len(time) == 1:
        text = '0' + time
        return text
    
    return time

@admin_router.message(Timer.time, F.text)
async def sales_take_time(message: types.Message, state: FSMContext):
    await state.update_data(time = time_correcter(message.text.split(':')))
    user_data = await state.get_data()
    await message.answer(
        text=f'''Заказы будут закрыты {time_correcter_2(user_data['date'][0])}-{time_correcter_2(user_data['date'][1])}-{user_data['date'][2]} в {time_correcter_2(user_data['time'][0])}:{time_correcter_2(user_data['time'][1])}\nВерно?''',
        reply_markup=admin_pannel.check('sales_check')
    )
    await state.set_state(Timer.check)

@admin_router.callback_query(Timer.check, F.data == 'yes')
async def sales_are_on(callback: types.CallbackQuery, state: FSMContext):
    global sales_status
    sales_status = True
    user_data = await state.get_data()

    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute(f'''INSERT INTO sales_closing_date (date)
        VALUES
            ("{user_data['date'][0]}-{user_data['date'][1]}-{user_data['date'][2]}_{user_data['time'][0]}:{user_data['time'][1]}")''')

    await callback.message.answer(text='Заказы включены ✅', reply_markup=admin_pannel.choose_option())
    await callback.answer()
    await state.clear()


@admin_router.callback_query(F.data == 'sales_switch_to_off')
async def sales_switch_to_off(callback: types.CallbackQuery):
    global sales_status
    sales_status = False
    await callback.message.answer(text='Новый статус заказов: Заказы выключены ❌', reply_markup=admin_pannel.choose_option())
    await callback.answer()


#--------ДАННЫЕ ЗАКАЗОВ-----------
@admin_router.callback_query(F.data == 'sales_data')
async def sales_data(callback: types.CallbackQuery):
    await callback.message.answer(
        text='Создать новую таблицу заказов? Данные старой удалятся, но отправятся вам сюда',
        reply_markup=admin_pannel.sales_data()
    )
    await callback.answer()

async def show_data(c, callback, db_name):
    c.execute('''SELECT name FROM sqlite_master WHERE type="table"''')
    temp_list = c.fetchall()
    for i in temp_list:
        if db_name == i[0]:
            c.execute(f'''SELECT * FROM {db_name} ORDER BY shipping''')
            all_data = c.fetchall()
            if len(all_data) != 0:
                easy_counter = 0

                for i in all_data:
                    easy_counter += 1
                    text = f'''\
{easy_counter}
id: {i[1]}
username: {i[2]}
ФИО: {i[3]}
Способ доставки: {i[4]}
Адресс: {i[5]}
Контакты: {i[6]}
Сумма заказа: {i[7]}
Комментарий к заказу: {i[8]}

{i[9]}'''
                    try:
                        await callback.message.answer(text=text)
                    except TelegramRetryAfter as e:
                        sleep(e.retry_after)
                        await callback.message.answer(text=text)

                return True
            
            break
        
    return False
        

@admin_router.callback_query(F.data == 'create_sales_data')
async def delete_sales_data(callback: types.CallbackQuery):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        if await show_data(c=c, callback=callback, db_name='sales_data'):
            c.execute('''DROP TABLE sales_data''')
            
        c.execute('''CREATE TABLE sales_data
        (position INTEGER PRIMARY KEY AUTOINCREMENT,
        id INT,
        username TEXT,
        full_name TEXT,
        shipping TEXT,
        adress TEXT,
        contact TEXT,
        price INT,
        comment TEXT,
        goods TEXT)''')

    await callback.message.answer('Новая таблица создана', reply_markup=admin_pannel.choose_option())
    await callback.answer()

@admin_router.callback_query(F.data == 'show_sales_data')
async def show_sales_data(callback: types.CallbackQuery):
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        if await show_data(c=c, callback=callback, db_name='sales_data'):
            await callback.message.answer(
                text='Конец заказов',
                reply_markup=admin_pannel.sales_data()
            )
        else:
            await callback.message.answer(
                text='Заказов пока нет',
                reply_markup=admin_pannel.sales_data()
            )
    
    await callback.answer()



#----------ОПОВЕЩЕНИЯ-----------

class Notificator(StatesGroup):
    notification = State()

@admin_router.callback_query(F.data == 'notifications_options')
async def notifications_options(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(text='Панель управления оповещениями', reply_markup=admin_pannel.notification_pannel())
    await callback.answer()
    await state.clear()

@admin_router.callback_query(F.data == 'make_notification')
async def make_notification(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(text='Напишите сообщение, которое хотите отправить подписавшимся')
    await state.set_state(Notificator.notification)
    await callback.answer()

@admin_router.message(Notificator.notification, F.text)
async def make_notification_2(message: types.Message, state: FSMContext):
    text = message.text
    await state.update_data(notification = text)
    await message.answer(text='Подписавшимся придёт следующее сообщение:')
    await message.answer(text=text)
    await message.answer(
        text='Верно?',
        reply_markup=admin_pannel.check(path='notifications_options', y_path='send_notification')
    )

@admin_router.callback_query(F.data == 'send_notification')
async def send_notification(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    text = await state.get_data()

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT * FROM notification')
        subs = c.fetchall()
        c.execute('SELECT tg_id FROM admins')
        subs.extend(c.fetchall())
    
    await callback.message.answer(text='Начало отправки...\nВам придёт это же сообщение в конце процесса')
    await callback.answer()
    for i in subs:
        try:
            await bot.send_message(chat_id=i[0], text=text['notification'])
        except TelegramRetryAfter as e:
            sleep(e.retry_after)
            await bot.send_message(chat_id=i[0], text=text['notification'])

    await callback.message.answer(text='Отправка завершена')
    await callback.message.answer(
        text='Панель управления оповещениями',
        reply_markup=admin_pannel.notification_pannel()
    )

    await state.clear()


@admin_router.callback_query(F.data == 'subs')
async def subscribers(callback: types.CallbackQuery):
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT COUNT(*) FROM notification')
        count = c.fetchone()[0]
    
    if count == 0:
        await callback.message.answer(text='Пока подписавшихся на рассылку нет :(')
        await callback.message.answer(
            text='Панель управления оповещениями',
            reply_markup=admin_pannel.notification_pannel()
        )
    else:
        await callback.message.answer(text=f'На рассылку подписано: {count}')
        await callback.message.answer(
            text='Панель управления оповещениями',
            reply_markup=admin_pannel.notification_pannel()
        )

    await callback.answer()

saving_text = '''\
⚠️ внимание, есть возможность, что ваш заказ утерян ⚠️

если вы уже СОВЕРШИЛИ оплату, свяжитесь с автором как можно скорее, он решит вашу проблему —> @milisuuuu

если вы ничего не заказывали, то просто проигнорируйте это сообщение🎀'''

@admin_router.callback_query(F.data == 'save_payers')
async def save_payers(callback: types.CallbackQuery):
    await callback.message.answer(
        text='''\
Вы хотите отправить сообщение тем, у кого проблемы с оплатой? Текст ниже сообщения отправиться также и вам в конце рассылки.

''' + saving_text,
        reply_markup=admin_pannel.check(path='notifications_options', y_path='send_to_save')
    )

    await callback.answer()


@admin_router.callback_query(F.data == 'send_to_save')
async def send_to_save(callback: types.CallbackQuery, bot: Bot):
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "pay%" ORDER BY name')
        temp = c.fetchall()

        if len(temp) == 0:
            await callback.message.answer(
                text='Помощь никому не нужна :/'
            )
            await callback.message.answer(
                text='Панель управления оповещениями',
                reply_markup=admin_pannel.notification_pannel()
            )
            await callback.answer()
            return
        

    for i in temp:
        user_id = i[0][8:]
        try:
            await bot.send_message(chat_id=user_id, text=saving_text)
        except Exception:
            await callback.message.answer(
                text=f'Не удалось отправить сообщения для юзера с id {user_id}'
            )

    await callback.message.answer('Отправка завершена')
    await callback.message.answer(
        text='Панель управления оповещениями',
        reply_markup=admin_pannel.notification_pannel()
    )
    
    await callback.answer()


class Pre_A_Notificator(StatesGroup):
    notification = State()

@admin_router.callback_query(F.data == 'pre_a_notify')
async def pre_a_notify(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text='Напишите сообщение, которое хотите отправить подписавшимся',
        reply_markup=admin_pannel.denier('notifications_options')
    )
    await state.set_state(Pre_A_Notificator.notification)
    await callback.answer()

@admin_router.message(Pre_A_Notificator.notification, F.text)
async def pre_a_notify_2(message: types.Message, state: FSMContext):
    text = message.text
    await state.update_data(notification = text)
    await message.answer(text='Подписавшимся придёт следующее сообщение:')
    await message.answer(text=text)
    await message.answer(
        text='Верно?',
        reply_markup=admin_pannel.check(path='notifications_options', y_path='send_pre_a_notification')
    )

#'''CREATE TABLE pre_sales_data
        #(position INTEGER PRIMARY KEY AUTOINCREMENT,
        #id INT,
        #username TEXT,
        #full_name TEXT,
        #shipping TEXT,
        #adress TEXT,
        #contact TEXT,
        #price INT,
        #comment TEXT,
        #goods TEXT)'''
@admin_router.callback_query(F.data == 'send_pre_a_notification')
async def send_pre_a_notification(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    text = await state.get_data()

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT id FROM pre_sales_data WHERE shipping = "Авито" AND id > 0')
        subs = c.fetchall()
        c.execute('SELECT tg_id FROM admins')
        subs.extend(c.fetchall())

        c.execute('SELECT * FROM pre_sales_data WHERE shipping = "Авито" AND id = 0')
        unknown_c = c.fetchall()

        c.execute('DROP TABLE IF EXISTS pre_a_code')
        c.execute('CREATE TABLE pre_a_code (is_on INT)')
    
    await callback.message.answer(text='Начало отправки...\nВам придёт это же сообщение в конце процесса')
    await callback.answer()
    for i in subs:
        try:
            await bot.send_message(chat_id=i[0], text=text['notification'])
        except TelegramRetryAfter as e:
            sleep(e.retry_after)
            await bot.send_message(chat_id=i[0], text=text['notification'])

    if len(unknown_c) != 0:
        await callback.message.answer(text='Не смог отправить сообщения для следующих заказов:')
        for i in unknown_c:
            m_text = f'''\
id: {i[1]}
username: {i[2]}
ФИО: {i[3]}
Способ доставки: {i[4]}
Адресс: {i[5]}
Контакты: {i[6]}
Сумма заказа: {i[7]}
Комментарий к заказу: {i[8]}

{i[9]}'''
            try:
                await callback.message.answer(text=m_text)
            except TelegramRetryAfter as e:
                sleep(e.retry_after)
                await callback.message.answer(text=m_text)


    await callback.message.answer(
        text='Отправка завершена\n\nПанель управления оповещениями',
        reply_markup=admin_pannel.notification_pannel()
    )

    await state.clear()

#---------------ПРЕДЗАКАЗЫ------------------

@admin_router.callback_query(F.data == 'pre_sales_options')
async def pre_sales_options(callback: types.CallbackQuery):
    await callback.message.answer("Настройка ПРЕД - Заказов", reply_markup=admin_pannel.pre_table())
    await callback.answer()

class Add_Pre_Products(StatesGroup):
    pages = State()
    photo = State()
    positions = State()
    again_check = State()

    texts = {
        'Add_Pre_Products:pages': 'Введите кол-во. страниц заново',
        'Add_Pre_Products:photo': 'Отправьте фото товаров для данной страницы',
        'Add_Pre_Products:positions': 'Введите кол-во. позиций на данной странице'
    }

class Add_Pre_Positions(StatesGroup):
    total_positions = State()
    name = State()
    is_paper = State()
    price = State()
    again_check_position = State()

    texts = {
        'Add_Pre_Positions:total_positions': 'Введите общее кол-во. позиций',
        'Add_Pre_Positions:is_paper': 'Является ли товар бумажным? Введите "да" или "нет"',
        'Add_Pre_Positions:name': 'Введите название позиции',
        'Add_Pre_Positions:price': 'Введите цену за единицу товара'
    }


#начало создания заказа
#переменная для демонстрации кнопок при создании заказа
pre_starts_with = 1
pre_is_first_page = True
pre_is_first_position = True
#команда отмены и возврата на 1 шаг назад
@admin_router.message(StateFilter(Add_Pre_Products, Add_Pre_Positions), F.text.casefold() == 'отмена')
@admin_router.message(StateFilter(Add_Pre_Products, Add_Pre_Positions), Command('start'))
async def pre_exit_handler(message: types.Message, state: FSMContext):
    global pre_starts_with, pre_is_first_page, pre_is_first_position, pre_position_counter
    pre_starts_with = 1
    pre_is_first_page = True
    pre_is_first_position = True
    pre_position_counter = 1

    await state.clear()
    await message.answer(text='Действия отменены', reply_markup=admin_pannel.choose_option())

@admin_router.message(StateFilter(Add_Pre_Products, Add_Pre_Positions), F.text.casefold() == 'назад')
async def pre_calncel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == Add_Pre_Products.pages:
        await message.answer(text='Предыдущего шага нет. Введите кол-во. страниц или "отмена", чтобы выйти из создания заказа')
        return
    if not pre_is_first_page and current_state == Add_Pre_Products.photo:
        await message.answer(text='Изменить прошлую страницу не получится. Отправьте фото для страницы или введите "отмена", чтобы выйти из создания заказа')
        return

    if current_state == Add_Pre_Positions.total_positions:
        await message.answer(text='Предыдущего шага нет. Введите кол-во. позиций или "отмена", чтобы выйти из создания заказа')
        return
    if not pre_is_first_position and current_state == Add_Pre_Positions.name:
        await message.answer(text='Изменить прошлую позицию не получится. Введите название товара или "отмена", чтобы выйти из создания заказа')
        return


    previous = None
    if current_state in Add_Pre_Products.__all_states__:
        for step in Add_Pre_Products.__all_states__:
            if step.state == current_state:
                await state.set_state(previous)
                await message.answer(f'Вы вернулись к прошлому шагу\n\n{Add_Pre_Products.texts[previous.state]}')
                return
            previous = step

    elif current_state in Add_Pre_Positions.__all_states__:
        for step in Add_Pre_Positions.__all_states__:
            if step.state == current_state:
                await state.set_state(previous)
                await message.answer(f'Вы вернулись к прошлому шагу\n\n{Add_Pre_Positions.texts[previous.state]}')
                return
            previous = step



@admin_router.callback_query(StateFilter(None), F.data == 'pre_create_table')
async def pre_b_create_table(callback: types.CallbackQuery):
    await callback.message.answer(
        text='Вы уверены, что хотите создать новый ПРЕД - Заказ? Существующий на данный момент заказ удалится.',
        reply_markup=admin_pannel.check(path='admin', y_path='pre_create_table_yes')
    )
    await callback.answer()

@admin_router.callback_query(StateFilter(None), F.data == 'pre_create_table_yes')
async def pre_create_table(callback: types.CallbackQuery, state: FSMContext):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        tables = ['pre_product_list', 'pre_pages']
        for k in tables:
            c.execute(f'''DROP TABLE IF EXISTS {k}''')

        c.execute('''CREATE TABLE pre_product_list
        (position INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        is_paper INT,
        price INT)''')
        c.execute('''CREATE TABLE pre_pages
        (page INTEGER PRIMARY KEY AUTOINCREMENT,
        photo TEXT,
        positions INT,
        starts_with INT)''')

    await callback.message.answer(
        text='Введите кол-во. страниц\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Add_Pre_Products.pages)
    await callback.answer()


@admin_router.message(Add_Pre_Products.pages, F.text)
async def pre_add_pages(message: types.Message, state: FSMContext):
    await state.update_data(pages=int(message.text))
    await message.answer(text='Отправьте фото товаров для данной страницы\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
    await state.set_state(Add_Pre_Products.photo)


@admin_router.message(Add_Pre_Products.photo, F.photo)
async def pre_add_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer(text='Введите кол-во. позиций на данной странице\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
    await state.set_state(Add_Pre_Products.positions)


#демонстрация кнопок
@admin_router.message(Add_Pre_Products.positions, F.text)
async def pre_add_positions(message: types.Message, state: FSMContext):
    await state.update_data(positions=int(message.text))
    user_data = await state.get_data()
    await message.answer_photo(
        photo = user_data['photo'],
        caption = '''\
**Кнопки для демонстрации**
        
*Для выхода напишите "отмена"*.
*Для отмены предыдущего шага напишите "назад"*''',
        reply_markup = sales_kbs.demonstration(user_data['positions'], pre_starts_with)
    )
    await message.answer(
        text='Верно?',
        reply_markup=admin_pannel.check()
    )
    await state.set_state(Add_Pre_Products.again_check)

@admin_router.callback_query(Add_Pre_Products.again_check, F.data == 'yes')
@admin_router.callback_query(Add_Pre_Products.again_check, F.data == 'no')
async def pre_correcting(callback: types.CallbackQuery, state: FSMContext):
    global pre_starts_with, pre_is_first_page
    if callback.data == 'yes':
        user_data = await state.get_data()
        with sqlite3.connect("main.db") as connection:
            c = connection.cursor()
            c.execute(f'''INSERT INTO pre_pages (photo, positions, starts_with)
            VALUES
                ('{user_data['photo']}',
                {user_data['positions']},
                {pre_starts_with})
            ''')
            
            print("done")

        await state.update_data(pages=user_data['pages']-1)
        pre_is_first_page = False
        user_data = await state.get_data()

        if user_data['pages'] != 0:
            pre_starts_with += user_data['positions']
            await callback.message.answer(text='Страница сохранена\n*создание следующей страницы*\nОтправьте фото для данной страницы')
            await state.set_state(Add_Pre_Products.photo)

        else:
            pre_is_first_page = True
            pre_starts_with = 1
            await callback.message.answer(text='Первый этап создания заказа завершён.\n\nТеперь давайте заполним позиции. Введите сколько всего позиций присутствует в заказе')
            await state.set_state(Add_Pre_Positions.total_positions)
    
    elif callback.data == 'no':
        await callback.message.answer(text='Прогресс удалён\n*повторное создание страницы*\nОтправьте фото для данной страницы')
        await state.set_state(Add_Pre_Products.photo)

    await callback.answer()


#------------ЗАПОЛНЕНИЕ ПОЗИЦИЙ-------------------
#class Add_Positions(StatesGroup):
    #total_positions = State()
    #name = State()
    #price = State()
    #again_check_position = State()

pre_position_counter = 1
@admin_router.message(Add_Pre_Positions.total_positions, F.text)
async def pre_add_total_positions(message: types.Message, state: FSMContext):
    await state.update_data(total_positions = int(message.text))
    await message.answer(text=f'Позиция №{pre_position_counter}\nВведите название товара\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*')
    await state.set_state(Add_Pre_Positions.name)

@admin_router.message(Add_Pre_Positions.name, F.text)
async def pre_add_name(message: types.Message, state: FSMContext):
    await state.update_data(name = message.text)
    await message.answer(
        text=f'Позиция №{pre_position_counter}\nЯвляется ли товар бумажным?\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*',
        reply_markup=admin_pannel.check()
    )
    await state.set_state(Add_Pre_Positions.is_paper)

@admin_router.callback_query(Add_Pre_Positions.is_paper, F.data == 'yes')
@admin_router.callback_query(Add_Pre_Positions.is_paper, F.data == 'no')
async def pre_add_is_paper(callback: types.CallbackQuery, state: FSMContext):
    text = f'Позиция №{pre_position_counter}\nВведите цену за 1 единицу товара (только цифра)\n\n*Для выхода напишите "отмена"*.\n*Для отмены предыдущего шага напишите "назад"*'
    if callback.data == 'yes':
        await state.update_data(is_paper = 1)
        await callback.message.answer(text=text)
        await state.set_state(Add_Pre_Positions.price)

    else:
        await state.update_data(is_paper = 0)
        await callback.message.answer(text=text)
        await state.set_state(Add_Pre_Positions.price)

    await callback.answer()


@admin_router.message(Add_Pre_Positions.price, F.text)
async def pre_add_price(message: types.Message, state: FSMContext):
    await state.update_data(price = int(message.text))
    user_data = await state.get_data()
    
    if user_data['is_paper']:
        is_paper_text = 'Является'
    else:
        is_paper_text = 'НЕ Является'

    await message.answer(
        text=f'''\
Позиция №{pre_position_counter}
{user_data['name']} - {user_data['price']}руб.

(Является ли продукция бумажной: Вы указали, что *{is_paper_text}*)
Верно?''',
        reply_markup=admin_pannel.check()
    )
    await state.set_state(Add_Pre_Positions.again_check_position)

@admin_router.callback_query(Add_Pre_Positions.again_check_position, F.data == 'yes')
@admin_router.callback_query(Add_Pre_Positions.again_check_position, F.data == 'no')
async def pre_again_check_position(callback: types.CallbackQuery, state: FSMContext):
    global pre_position_counter, pre_is_first_position
    if callback.data == 'yes':
        user_data = await state.get_data()
        with sqlite3.connect("main.db") as connection:
            c = connection.cursor()
            c.execute(f'''INSERT INTO pre_product_list (name, is_paper, price)
            VALUES
                ('{user_data['name']}',
                {user_data['is_paper']},
                {user_data['price']})''')
            
            print("done")

        pre_is_first_position = False
        pre_position_counter += 1
        if pre_position_counter <= user_data['total_positions']:
            await callback.message.answer(text=f'Позиция №{pre_position_counter - 1} сохранена\n*создание следующей Позиции*\nПозиция №{pre_position_counter}\nВведите название товара')
            await state.set_state(Add_Pre_Positions.name)
        
        else:
            await callback.message.answer(text='Создание заказа полностью завершено.\nПосмотреть результат можно в панели пользователя /start')
            await state.clear()
            pre_position_counter = 1
            pre_is_first_position = True

    else:
        await callback.message.answer(text=f'Прогресс удалён\n*повторное создание позиции*\nПозиция №{pre_position_counter}\nВведите название товара')
        await state.set_state(Add_Pre_Positions.name)
    
    await callback.answer()


#--------------СТАТУС ПРЕД ЗАКАЗОВ----------------
class Pre_Timer(StatesGroup):
    status = State()
    date = State()
    time = State()
    check = State()

pre_sales_status = False

@admin_router.callback_query(F.data == 'pre_sales_check')
async def pre_sales_check(callback: types.CallbackQuery, state: FSMContext):
    if pre_sales_status:
        await callback.message.answer(
            text='Статус ПРЕД Заказов: ПРЕД Заказы включены ✅',
            reply_markup=admin_pannel.pre_sales_status_switcher(pre_sales_status)
        )

    else:
        await callback.message.answer(
            text='Статус ПРЕД Заказов: ПРЕД Заказы выключены ❌',
            reply_markup=admin_pannel.pre_sales_status_switcher(pre_sales_status)
        )
        await state.set_state(Pre_Timer.status)

    await callback.answer()


@admin_router.callback_query(Pre_Timer.status, F.data == 'pre_sales_switch_to_on')
async def pre_sales_switch_to_on(callback: types.CallbackQuery, state: FSMContext):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute('''DROP TABLE IF EXISTS pre_sales_closing_date''')

        c.execute('''CREATE TABLE pre_sales_closing_date (date TEXT)''')

    await callback.message.answer(
        text='Новый статус ПРЕД Заказов: ПРЕД Заказы включены ✅\nТеперь введите до какого числа они будут активны в формате:\nдень:месяц:год 00:00:0000'
    )
    await callback.answer()
    await state.set_state(Pre_Timer.date)


@admin_router.message(Pre_Timer.date, F.text)
async def pre_sales_take_data(message: types.Message, state: FSMContext):
    await state.update_data(date = time_correcter(message.text.split(':')))
    await message.answer(text='Теперь введите время в формате:\nчасы:минуты 00:00')
    await state.set_state(Pre_Timer.time)


@admin_router.message(Pre_Timer.time, F.text)
async def pre_sales_take_time(message: types.Message, state: FSMContext):
    await state.update_data(time = time_correcter(message.text.split(':')))
    user_data = await state.get_data()
    await message.answer(
        text=f'''ПРЕД Заказы будут закрыты {time_correcter_2(user_data['date'][0])}-{time_correcter_2(user_data['date'][1])}-{user_data['date'][2]} в {time_correcter_2(user_data['time'][0])}:{time_correcter_2(user_data['time'][1])}\nВерно?''',
        reply_markup=admin_pannel.check('pre_sales_check')
    )
    await state.set_state(Pre_Timer.check)

@admin_router.callback_query(Pre_Timer.check, F.data == 'yes')
async def pre_sales_are_on(callback: types.CallbackQuery, state: FSMContext):
    global pre_sales_status
    pre_sales_status = True
    user_data = await state.get_data()

    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute(f'''INSERT INTO pre_sales_closing_date (date)
        VALUES
            ("{user_data['date'][0]}-{user_data['date'][1]}-{user_data['date'][2]}_{user_data['time'][0]}:{user_data['time'][1]}")''')

    await callback.message.answer(
        text='ПРЕД Заказы включены ✅',
        reply_markup=admin_pannel.choose_option()
    )
    await callback.answer()
    await state.clear()


@admin_router.callback_query(F.data == 'pre_sales_switch_to_off')
async def pre_sales_switch_to_off(callback: types.CallbackQuery):
    global pre_sales_status
    pre_sales_status = False
    await callback.message.answer(
        text='Новый статус заказов: Заказы выключены ❌',
        reply_markup=admin_pannel.choose_option()
    )
    await callback.answer()


#---------ДАННЫЕ ПРЕД ЗАКАЗОВ-----------

@admin_router.callback_query(F.data == 'pre_sales_data')
async def pre_sales_data(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text='Создать новую таблицу ПРЕД Заказов? Данные старой удалятся, но отправятся вам сюда',
        reply_markup=admin_pannel.pre_sales_data()
    )
    await callback.answer()
    await state.clear()

@admin_router.callback_query(F.data == 'pre_create_sales_data')
async def pre_delete_sales_data(callback: types.CallbackQuery):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        await show_data(c=c, callback=callback, db_name='pre_sales_data')
        c.execute('DROP TABLE pre_sales_data')
            
        c.execute('''CREATE TABLE pre_sales_data
        (position INTEGER PRIMARY KEY AUTOINCREMENT,
        id INT,
        username TEXT,
        full_name TEXT,
        shipping TEXT,
        adress TEXT,
        contact TEXT,
        price INT,
        comment TEXT,
        goods TEXT)''')

    await callback.message.answer(
        'Новая таблица создана',
        reply_markup=admin_pannel.choose_option()
    )
    await callback.answer()

@admin_router.callback_query(F.data == 'pre_show_sales_data')
async def pre_show_sales_data(callback: types.CallbackQuery):
    await callback.answer()

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        if await show_data(c=c, callback=callback, db_name='pre_sales_data'):
            await callback.message.answer(
                text='Конец ПРЕД Заказов',
                reply_markup=admin_pannel.pre_sales_data()
            )
        else:
            await callback.message.answer(
                text='ПРЕД Заказов пока нет',
                reply_markup=admin_pannel.pre_sales_data()
            )
    
    

#просмотр сводки предзаказов

@admin_router.callback_query(F.data == 'show_overall_pre_sales')
async def show_overall_pre_sales(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        text='Начинаю составлять сводку...'
    )

    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT goods FROM pre_sales_data')
        temp = c.fetchall()
    
    counter = dict()
    for i in temp:
        temp2 = [k.split(' - ') for k in i[0][16:].split('\n')]

        for n in temp2:
            temp_name = n[0]
            temp_count = int(n[1][:-3])
            if temp_name in counter:
                counter[temp_name] += temp_count
            else:
                counter[temp_name] = temp_count
    
    temp_final = []
    for i in counter:
        temp_final.append(f'{i} - {counter[i]}')
    
    def position_finder(text):
        position = 0
        for i in text:
            if i.isdigit():
                position +=1
            else:
                digit = int(text[:position])
                return digit

    temp_final.sort(key=lambda text: position_finder(text))
    text = ''
    for i in temp_final:
        if 'ЛАКИ' in i:
            text += i[:14] + i[i.rfind(' -'):]
        else:
            text += i + '\n'

    await callback.message.answer(text)
    await callback.message.answer(
        text='Конец',
        reply_markup=admin_pannel.pre_sales_data()
    )

#ручной ввод товаров для предзаказов



class Pre_Add_Sales_Data(StatesGroup):
    username = State()
    shipping = State()
    full_name = State()
    adress = State()
    contact = State()
    price = State()
    goods = State()

    check = State()

@admin_router.callback_query(F.data == 'pre_add_sales_data')
async def pre_add_sales_data(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await state.set_state(Pre_Add_Sales_Data.username)
    await callback.message.answer('Введите юзернейм покупателя. Если его нет, то введите -')

@admin_router.message(Pre_Add_Sales_Data.username, F.text)
async def pre_add_username(message: types.Message, state: FSMContext):
    text = message.text
    if text == '-':
        username = '*юзернейм отсутствует*'
    else:
        username = text
    await state.update_data(username = username)
    await message.answer(
        text='Выберите способ доставки',
        reply_markup=admin_pannel.pre_add_shipping()
    )
    await state.set_state(Pre_Add_Sales_Data.shipping)


@admin_router.callback_query(Pre_Add_Sales_Data.shipping, F.data == 'y_go')
async def pre_add_y_go(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(full_name = '-', shipping = 'ЯндексGo')
    await callback.message.answer('Введите телефон, начиная с 8')
    await state.set_state(Pre_Add_Sales_Data.contact)

@admin_router.callback_query(Pre_Add_Sales_Data.shipping, F.data == 'rf')
async def pre_add_rf(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(shipping = 'Почта России')
    await callback.message.answer('Введите ФИО')
    await state.set_state(Pre_Add_Sales_Data.full_name)


@admin_router.message(Pre_Add_Sales_Data.full_name, F.text)
async def pre_add_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name = message.text)
    await message.answer('Введите телефон, начиная с 8')
    await state.set_state(Pre_Add_Sales_Data.contact)

@admin_router.message(Pre_Add_Sales_Data.contact, F.text)
async def pre_add_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact = message.text)
    await message.answer('Введите адрес')
    await state.set_state(Pre_Add_Sales_Data.adress)


@admin_router.message(Pre_Add_Sales_Data.adress, F.text)
async def pre_add_adress(message: types.Message, state: FSMContext):
    await state.update_data(adress = message.text)
    await message.answer('Введите сумму заказа, включая цену за доставку')
    await state.set_state(Pre_Add_Sales_Data.price)

@admin_router.callback_query(Pre_Add_Sales_Data.shipping, F.data == 'av')
async def pre_add_av(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(
        shipping = 'Авито',
        full_name = '-',
        contact = '-',
        adress = '-'
    )
    await callback.message.answer('Введите сумму заказа, включая цену за доставку')
    await state.set_state(Pre_Add_Sales_Data.price)

@admin_router.message(Pre_Add_Sales_Data.price, F.text)
async def pre_add_goods(message: types.Message, state: FSMContext):
    await state.update_data(price = int(message.text))
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        c.execute('SELECT position, name FROM pre_product_list')
        temp = c.fetchall()
    text = 'Список товаров:\n'
    for i in temp:
        text += f'{i[0]}. {i[1]}\n'
    await message.answer(text)

    await message.answer('''\
Введите список товаров одним сообщением по следующему формату БЕЗ ПРОБЕЛОВ:
(Номер товара)-(Количество)
                         
Например:
57-3
58-24
97-5''')
    await state.set_state(Pre_Add_Sales_Data.goods)

@admin_router.message(Pre_Add_Sales_Data.goods, F.text)
async def pre_add_check(message: types.Message, state: FSMContext):
    temp = message.text.split('\n')
    temp_dict = dict()
    
    with sqlite3.connect('main.db') as connection:
        c = connection.cursor()
        for i in temp:
            k = i.split('-')
            pos = k[0].strip()
            name = c.execute(f'''SELECT name FROM pre_product_list WHERE position = {pos}''').fetchone()[0]
            temp_dict[f'{pos}. {name}'] = int(k[1].strip())
    
    text = 'Список товаров:'
    for i in temp_dict:
        text += f'\n{i} - {temp_dict[i]}шт.'
    await state.update_data(goods = text)
    user_data = await state.get_data()
    await message.answer('В таблицу внесутся следующие данные:')
    await message.answer(f'''\
id: 0
username: {user_data['username']}
ФИО: {user_data['full_name']}
Способ доставки: {user_data['shipping']}
Адресс: {user_data['adress']}
Контакты: {user_data['contact']}
Сумма заказа: {user_data['price']}
Комментарий к заказу: -

{user_data['goods']}''')
    await message.answer('Верно?', reply_markup=admin_pannel.check(path='pre_sales_data'))
    await state.set_state(Pre_Add_Sales_Data.check)

#c.execute('''CREATE TABLE pre_sales_data
        #(position INTEGER PRIMARY KEY AUTOINCREMENT,
        #id INT,
        #username TEXT,
        #full_name TEXT,
        #shipping TEXT,
        #adress TEXT,
        #contact TEXT,
        #price INT,
        #comment TEXT,
        #goods TEXT)''')
@admin_router.callback_query(Pre_Add_Sales_Data.check, F.data == 'yes')
async def pre_add_yes(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await state.get_data()
    try:
        with sqlite3.connect('main.db') as connection:
            c = connection.cursor()
            c.execute(f'''INSERT INTO pre_sales_data (id, username, full_name, shipping, adress, contact, price, comment, goods)
            VALUES
                (0,
                '{user_data['username']}',
                '{user_data['full_name']}',
                '{user_data['shipping']}',
                '{user_data['adress']}',
                '{user_data['contact']}',
                {user_data['price']},
                '***добавлено вручную***',
                '{user_data['goods']}')''')
        await callback.message.answer(
            text='Заказ добавлен✅️',
            reply_markup=admin_pannel.pre_table()
        )
    except Exception:
        await callback.message.answer(
            text='Что-то пошло не так❌',
            reply_markup=admin_pannel.pre_table()
        )
    
    await state.clear()
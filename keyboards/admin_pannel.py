from aiogram import types

from handlers import admin_handler



#'''CREATE TABLE product_list
    #(position INT PRIMARY KEY AUTOINCREMENT,
    #name TEXT,
    #count INT,
    #price INT)'''

    #SELECT name FROM sqlite_master WHERE type="table"

kb = types.InlineKeyboardButton

def choose_option():
    buttons = [
        [kb(text='заказы', callback_data='sales_options')],
        [kb(text='ПРЕД заказы', callback_data='pre_sales_options')],
        [kb(text='оповещения', callback_data='notifications_options')],
        [kb(text='вернуться', callback_data='greetings')],
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

#-----------------ЗАКАЗЫ----------------------------
def table():
    buttons = [
        [kb(text='создать новый заказ', callback_data='create_table')],
        [kb(text='статус заказов', callback_data='sales_check')],
        [kb(text='таблица заказов', callback_data='sales_data')],
        [kb(text='назад', callback_data='admin')]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def sales_status_switcher():
    if admin_handler.sales_status:   
        buttons = [
            [kb(text='выключить', callback_data='sales_switch_to_off')]
        ]
    else:
        buttons = [
            [kb(text='включить', callback_data='sales_switch_to_on')]
        ]
    
    buttons.append([kb(text='назад', callback_data='admin')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def check(path = 'no', y_path = 'yes', b_text = 'нет'):
    buttons = [
        [
            kb(text='да', callback_data = y_path)
        ],
        [
            kb(text = b_text, callback_data = path)
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def sales_data():
    buttons = [
        [kb(text='создать', callback_data='create_sales_data')],
        [kb(text='показать', callback_data='show_sales_data')],
        [kb(text='отмена', callback_data='admin')]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard



#-----------------ОПОВЕЩЕНИЯ--------------
def notification_pannel():
    buttons = [
        [kb(text='отправить оповещение', callback_data='make_notification')],
        [kb(text='кол-во. подписанных', callback_data='subs')],
        [kb(text='спасти оплативших', callback_data='save_payers')],
        [kb(text='авито предзаказы', callback_data='pre_a_notify')],
        [kb(text='назад', callback_data='admin')]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard



#-------------ПРЕДЗАКАЗЫ-----------------

def pre_table():
    buttons = [
        [kb(text='создать новый ПРЕД - Заказ', callback_data='pre_create_table')],
        [kb(text='статус ПРЕД - Заказов', callback_data='pre_sales_check')],
        [kb(text='таблица ПРЕД - Заказов', callback_data='pre_sales_data')],
        [kb(text='назад', callback_data='admin')]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


#---------СТАТУС ПРЕД ЗАКАЗОВ-----------

def pre_sales_status_switcher(status):
    if status:   
        buttons = [
            [kb(text='выключить', callback_data='pre_sales_switch_to_off')]
        ]
    else:
        buttons = [
            [kb(text='включить', callback_data='pre_sales_switch_to_on')]
        ]
    
    buttons.append([kb(text='назад', callback_data='admin')])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard



def pre_sales_data():
    buttons = [
        [kb(text='создать', callback_data='pre_create_sales_data')],
        [kb(text='показать', callback_data='pre_show_sales_data')],
        [kb(text='сводка по товарам', callback_data='show_overall_pre_sales')],
        [kb(text='ввести вручную', callback_data='pre_add_sales_data')],
        [kb(text='отмена', callback_data='admin')]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def pre_add_shipping():
    buttons = [
        [kb(text='ЯндексGo', callback_data='y_go')],
        [kb(text='Почта России', callback_data='rf')],
        [kb(text='Авито', callback_data='av')]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def denier(path):
    buttons = [
        [kb(text='отмена', callback_data=path)]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
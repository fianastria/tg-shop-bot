import sqlite3
from aiogram import types


kb = types.InlineKeyboardButton

def for_even_buttons(positions, starts_with, is_test):
    buttons = []
    temp = []
    if is_test:
        c_text = 'тест'
    else:
        c_text = 'position_'

    if starts_with%2 != 0:
        for i in range(starts_with, starts_with + positions):
            temp.append(kb(text=str(i), callback_data=c_text+str(i)))
            if i%2 == 0:
                buttons.append(temp.copy())
                temp.clear()

    else:
        for i in range(starts_with, starts_with + positions):
            temp.append(kb(text=str(i), callback_data=c_text+str(i)))
            if i%2 != 0:
                buttons.append(temp.copy())
                temp.clear()
    
    buttons.append(temp.copy())
    return buttons

    
def sales_processing(basket, page = 1, pre = ''):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        c.execute(f'''SELECT * FROM {pre}pages WHERE page = {page}''')
        page_data = c.fetchall()[0]
        c.execute(f'''SELECT * FROM {pre}pages''')
        total_pages = len(c.fetchall())

    #кнопки товаров
    buttons = for_even_buttons(page_data[-2], page_data[-1], False)
    
    #кнопки для переключения страниц
    if page == 1 and page != total_pages:
        buttons.append(
            [
                kb(text='выйти', callback_data='finish'),
                kb(text='далее ->', callback_data=f'page_{page+1}')
            ]
        )
    elif page == 1:
        buttons.append(
            [
                kb(text='выйти', callback_data='finish')
            ]
        )
    elif page == total_pages:
        buttons.append(
            [
                kb(text='<- назад', callback_data=f'page_{page-1}'),
                kb(text='выйти', callback_data='finish')
            ]
        )
    else:
        buttons.append(
            [
                kb(text='<- назад', callback_data=f'page_{page-1}'),
                kb(text='выйти', callback_data='finish'),
                kb(text='далее ->', callback_data=f'page_{page+1}')
            ]
        )
    
    #кнопка "готово"
    if len(basket) != 0:
        buttons.append(
            [
                kb(text='готово', callback_data='go_to_purcase')
            ]
        )

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

#-----------кнопки для заполнения данных и покупки----------------
def choosing_shipping():
    buttons = [
        [
            kb(text='ЯндексGo', callback_data='y_notification')
        ],
        [
            kb(text='Почта России', callback_data='rf_notification')
        ],
        [
            kb(text='Авито (любые ПВЗ)', callback_data='av')
        ],
        [
            kb(text='назад', callback_data='page_1')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def give_contact():
    buttons = [
        [types.KeyboardButton(text='отправить номер', request_contact=True)]
    ]

    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, one_time_keyboard=True, resize_keyboard= True)
    return keyboard

def rf_notification_kb():
    buttons = [
        [
            kb(text='продолжить', callback_data='rf')
        ],
        [
            kb(text='выбрать другой способ доставки', callback_data='go_to_purcase')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def y_notification_kb():
    buttons = [
        [
            kb(text='продолжить', callback_data='y_go')
        ],
        [
            kb(text='выбрать другой способ доставки', callback_data='go_to_purcase')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def y_check():
    buttons = [
        [
            kb(text='перейти к оплате', callback_data='paying')
        ],
        [
            kb(text='нет', callback_data='go_to_purcase')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

#-------------
def av_check():
    buttons = [
        [
            kb(text='перейти к оплате', callback_data='paying')
        ],
        [
            kb(text='выбрать другой способ доставки', callback_data='go_to_purcase')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

#-------------
def paying_kb_1(link):
    buttons = [
        [
            kb(text='Оплатить', url=link)
        ],
        [
            kb(text='Проверить состояние оплаты', callback_data='check_payment')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

#-------------



def demonstration(positions, starts_with):
    buttons = for_even_buttons(positions, starts_with, True)

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def leaving_check_e():
    buttons = [
        [
            kb(text='да', callback_data='greetings'),
            kb(text='нет', callback_data='page_1')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def leaving_check(path = 'page_1'):
    buttons = [
        [
            kb(text='очистить', callback_data='clear'),
            kb(text='нет', callback_data=path)
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def leaving_check_2():
    buttons = [
        [
            kb(text='вернуться', callback_data='greetings')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
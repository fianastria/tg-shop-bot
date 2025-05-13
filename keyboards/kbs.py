from filters import is_admin
from aiogram import types

kb = types.InlineKeyboardButton



def greetings_kb(user = None, pre_a = False):
    buttons = [
        [
            #kb(text="онлайн-заказы", callback_data="sales"),
            kb(text="заказы", callback_data="pre_sales"),
        ],
        [
            kb(text="рассылка", callback_data="messages"),
            kb(text="соц. сети автора", callback_data="author"),
        ]
    ]

    if pre_a:
        buttons.append([kb(text="отправить код авито", callback_data="send_pre_a_code")])

    if is_admin(user):
        buttons.append([kb(text="панель админа", callback_data="admin")])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def back_to_greetings_kb():
    buttons = [
        [kb(text="назад", callback_data="greetings")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def back_to_greetings_from_messages_is_on_kb():
    buttons = [
        [kb(text="отключить рассылку", callback_data="messages_off")],
        [kb(text="назад", callback_data="greetings")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def back_to_greetings_from_messages_is_off_kb():
    buttons = [
        [kb(text="подключить рассылку", callback_data="messages_on")],
        [kb(text="назад", callback_data="greetings")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

#---------СПАСИТЕЛЬНАЯ----------

def save():
    buttons = [
        [kb(text='подтвердить', callback_data='check_payment')],
        [kb(text='отменить', callback_data='deny_help')]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def save2():
    buttons = [
        [kb(text='да, отменить оплату', callback_data='deny_help2')],
        [kb(text='нет, вернуться обратно', callback_data='greetings')]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
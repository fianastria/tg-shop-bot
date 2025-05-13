
from aiogram.types import Message
import sqlite3
from typing import List
from aiogram.filters import BaseFilter


def is_admin(user):
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        admin_list = c.execute("SELECT tg_id FROM admins").fetchall()
        for admin in admin_list:
            if user in admin:
                return True
        return False

def admin_list_maker():
    admin_list = []
    with sqlite3.connect("main.db") as connection:
        c = connection.cursor()
        temp_list = c.execute("SELECT tg_id FROM admins").fetchall()
        for admin in temp_list:
            admin_list.append(admin[0])
    
    return admin_list

class IsAdmin(BaseFilter):
    def __init__(self, user_ids: int | List[int]) -> None:
        self.user_ids = user_ids

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.user_ids, int):
            return message.from_user.id == self.user_ids
        return message.from_user.id in self.user_ids
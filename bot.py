import asyncio
import logging
from aiogram import Bot, Dispatcher


from config_reader import config
from handlers import body_handler, admin_handler, sales_handler, pre_sales_handler



# Включаем логирование, чтобы не пропустить важные сообщения
async def main():
    # Объект бота
    bot = Bot(token=config.bot_token.get_secret_value())
    # Диспетчер
    dp = Dispatcher()
    dp.include_routers(
        body_handler.router,
        admin_handler.admin_router,
        sales_handler.sales_router,
        pre_sales_handler.pre_sales_router
    )


    await bot.delete_webhook(drop_pending_updates=True) # Запускаем бота и пропускаем все накопленные входящие
    await dp.start_polling(bot)

logging.basicConfig(level=logging.INFO)




if __name__ == "__main__":
    asyncio.run(main())
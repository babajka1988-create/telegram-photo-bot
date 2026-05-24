from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

PROTECTION_TEXT = (
    "🤍 Канал находится под защитой.\n"
    "Отписавшиеся пользователи автоматически блокируются "
    "без возможности вернуться в канал."
)

CHANNEL_ID = -100XXXXXXXXXX
CHAT_ID = -100YYYYYYYYYY


@dp.message(F.new_chat_members)
async def welcome_new_members(message: Message):
    for user in message.new_chat_members:
        name = user.first_name or "Привет"

        await message.answer(
            f"{name}, привет 🤍\n"
            "Рада видеть тебя в чате. Осваивайся ✨"
        )


@dp.message(F.is_automatic_forward == True)
async def post_comment(message: Message):
    await message.reply(PROTECTION_TEXT)


async def check_subscribers():
    while True:
        members = await bot.get_chat_administrators(CHAT_ID)

        for member in members:
            try:
                status = await bot.get_chat_member(
                    CHANNEL_ID,
                    member.user.id
                )

                if status.status == "left":
                    await bot.ban_chat_member(
                        CHAT_ID,
                        member.user.id
                    )

            except:
                pass

        await asyncio.sleep(300)


async def main():
    asyncio.create_task(check_subscribers())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

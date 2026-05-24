from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatMemberUpdated
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

@dp.chat_member()
async def track_channel_leave(event: ChatMemberUpdated):
    if event.chat.type != "channel":
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    user_id = event.from_user.id

    if old_status in ["member", "administrator"] and new_status in ["left", "kicked"]:
        try:
            await bot.ban_chat_member(chat_id=event.chat.id, user_id=user_id)
        except Exception as e:
            print(f"Ban error: {e}")

@dp.message(F.new_chat_members)
async def welcome_new_members(message: Message):
    for user in message.new_chat_members:
        name = user.first_name or "Привет"
        await message.answer(
            f"{name}, привет 🤍\n"
            "Рада видеть тебя в чате. Осваивайся, здесь про нейрофото, реализм и промпты ✨"
        )

@dp.message(F.is_automatic_forward == True)
async def first_comment_under_channel_post(message: Message):
    try:
        await message.reply(PROTECTION_TEXT)
    except Exception as e:
        print(f"Comment error: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

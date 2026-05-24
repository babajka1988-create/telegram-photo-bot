from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import CommandStart, Command
import asyncio
import os
import time

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

PROTECTION_TEXT = (
    "🤍 Канал находится под защитой.\n"
    "Отписавшиеся пользователи автоматически блокируются "
    "без возможности вернуться в канал."
)

processed_posts = {}


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Бот работает 🤍")


@dp.message(Command("id"))
async def show_id(message: Message):
    await message.answer(f"ID этого чата: `{message.chat.id}`")


@dp.chat_member()
async def block_left_channel_member(event: ChatMemberUpdated):
    if event.chat.type != "channel":
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    user_id = event.new_chat_member.user.id

    if old_status in ["member", "administrator"] and new_status == "left":
        try:
            await bot.ban_chat_member(event.chat.id, user_id)
            print(f"Blocked user {user_id} in channel {event.chat.id}")
        except Exception as e:
            print(f"Ban error: {e}")


@dp.message(F.new_chat_members)
async def welcome_new_members(message: Message):
    for user in message.new_chat_members:
        if user.is_bot:
            continue

        name = user.first_name or "Привет"

        await message.answer(
            f"{name}, привет 🤍\n"
            "Рада видеть тебя в чате. Осваивайся, здесь про нейрофото, реализм и промпты ✨"
        )


@dp.message(F.is_automatic_forward == True)
async def comment_under_channel_post(message: Message):
    now = time.time()

    for key, saved_time in list(processed_posts.items()):
        if now - saved_time > 3600:
            del processed_posts[key]

    post_key = message.media_group_id or message.forward_from_message_id or message.message_id

    if post_key in processed_posts:
        return

    processed_posts[post_key] = now

    try:
        await message.reply(PROTECTION_TEXT)
    except Exception as e:
        print(f"Comment error: {e}")


async def main():
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())

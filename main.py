from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import CommandStart, Command
import asyncio
import os
import time
import re

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

PROTECTION_TEXT = (
    "🖤 Канал находится под защитой.\n"
    "Отписавшиеся пользователи автоматически блокируются "
    "без возможности вернуться в канал."
)

WARNING_TEXT = (
    "{user}, канал под защитой.\n\n"
    "Рекламные ссылки и сообщения от имени каналов или чатов запрещены.\n\n"
    "Это первое предупреждение.\n"
    "При повторном нарушении вы заноситесь в ЧС."
)

BAN_TEXT = (
    "{user} занесён в ЧС.\n\n"
    "Повторное нарушение правил канала."
)

processed_posts = {}
violations = {}

DELETE_BOT_MESSAGES_AFTER = 24 * 60 * 60


def get_user_name(user):
    if user.username:
        return f"@{user.username}"
    full_name = " ".join(
        part for part in [user.first_name, user.last_name] if part
    )
    return full_name or "Пользователь"


def has_link_entities(message: Message) -> bool:
    if message.entities:
        for entity in message.entities:
            if entity.type in ("url", "text_link"):
                return True

    if message.caption_entities:
        for entity in message.caption_entities:
            if entity.type in ("url", "text_link"):
                return True

    return False


def has_obvious_links(text: str) -> bool:
    if not text:
        return False

    text_lower = text.lower()

    link_patterns = [
        r"http://",
        r"https://",
        r"www\.",
        r"t\.me/",
        r"telegram\.me/",
        r"telegra\.ph/",
    ]

    return any(re.search(pattern, text_lower) for pattern in link_patterns)


def extract_usernames(text: str):
    if not text:
        return []

    return re.findall(r"(?<!\w)@([A-Za-z0-9_]{5,32})", text)


async def username_is_channel_or_chat(username: str) -> bool:
    try:
        chat = await bot.get_chat(f"@{username}")
        return chat.type in ("channel", "group", "supergroup")
    except Exception:
        return False


async def has_channel_or_chat_username(text: str) -> bool:
    usernames = extract_usernames(text)

    for username in usernames:
        if await username_is_channel_or_chat(username):
            return True

    return False


async def is_admin(message: Message) -> bool:
    if not message.from_user:
        return False

    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


async def delete_after_delay(message: Message, delay: int = DELETE_BOT_MESSAGES_AFTER):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        print(f"Delete delayed message error: {e}")


async def send_temp_message(message: Message, text: str):
    try:
        bot_message = await message.answer(text)
        asyncio.create_task(delete_after_delay(bot_message))
    except Exception as e:
        print(f"Send temp message error: {e}")


async def register_violation(message: Message):
    try:
        await message.delete()
    except Exception as e:
        print(f"Delete violation message error: {e}")

    if not message.from_user:
        chat_name = "@" + message.sender_chat.username if message.sender_chat and message.sender_chat.username else (
            message.sender_chat.title if message.sender_chat else "Канал или чат"
        )

        await send_temp_message(
            message,
            WARNING_TEXT.format(user=chat_name)
        )
        return

    user_id = message.from_user.id
    user_name = get_user_name(message.from_user)

    count = violations.get(user_id, 0) + 1
    violations[user_id] = count

    if count == 1:
        await send_temp_message(
            message,
            WARNING_TEXT.format(user=user_name)
        )
        return

    try:
        await bot.ban_chat_member(message.chat.id, user_id)
    except Exception as e:
        print(f"Ban violation user error: {e}")

    await send_temp_message(
        message,
        BAN_TEXT.format(user=user_name)
    )


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Бот работает 🖤")


@dp.message(Command("id"))
async def show_id(message: Message):
    await message.answer(f"ID этого чата: {message.chat.id}")


@dp.chat_member()
async def block_left_channel_member(event: ChatMemberUpdated):
    if event.chat.type != "channel":
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    user_id = event.new_chat_member.user.id

    if old_status in ("member", "administrator") and new_status == "left":
        try:
            await bot.ban_chat_member(event.chat.id, user_id)
            print(f"Blocked user {user_id} in channel {event.chat.id}")
        except Exception as e:
            print(f"Ban error: {e}")


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


@dp.message()
async def protect_chat(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    if message.from_user and message.from_user.is_bot:
        return

    if await is_admin(message):
        return

    if message.is_automatic_forward:
        return

    if message.sender_chat:
        await register_violation(message)
        return

    text = message.text or message.caption or ""

    if has_link_entities(message):
        await register_violation(message)
        return

    if has_obvious_links(text):
        await register_violation(message)
        return

    if await has_channel_or_chat_username(text):
        await register_violation(message)
        return


async def main():
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())

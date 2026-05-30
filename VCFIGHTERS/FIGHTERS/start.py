import asyncio
import random
import time

import aiohttp
import psutil
from pyrogram import filters as pyro_filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

import Config
from VCFIGHTERS.core.bot import app
from VCFIGHTERS.database.mangodb import (
    active_userbot_count,
    get_all_targets,
    get_mode,
)
from VCFIGHTERS.logging import LOGGER

log = LOGGER("Start")

_boot_time = time.time()

# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════

EFFECT_FIRE = "5104841245755180586"

VC_PICS = getattr(
    Config,
    "VC_PICS",
    [
        "https://files.catbox.moe/eje8y8.jpeg",
        "https://files.catbox.moe/ey2jzp.jpeg",
        "https://files.catbox.moe/ah5y0f.jpeg",
        "https://files.catbox.moe/we4yju.jpeg",
    ],
)

FIRE_FRAMES = [
    "🔥",
    "🔥🔥",
    "🔥🔥🔥",
    "⚔️ VCFIGHTER...",
    "⚡ STARTING...",
    "💀 AWAKENING...",
]

FIRE_DELAY = 0.4

# ══════════════════════════════════════════════════════════════
# BUTTON HELPER
# ══════════════════════════════════════════════════════════════


def _api_btn(
    text: str,
    callback_data: str = None,
    url: str = None,
) -> dict:

    btn = {"text": text}

    if callback_data:
        btn["callback_data"] = callback_data

    if url:
        if not url.startswith("http") and not url.startswith("tg://"):
            url = f"https://t.me/{url.replace('@', '')}"

        btn["url"] = url

    return btn


# ══════════════════════════════════════════════════════════════
# CONVERT MARKUP TO PYROGRAM KEYBOARD
# ══════════════════════════════════════════════════════════════


def _markup_to_keyboard(markup: list) -> InlineKeyboardMarkup:
    """Convert raw button markup to Pyrogram InlineKeyboardMarkup"""
    buttons = []
    for row in markup:
        button_row = []
        for btn in row:
            if btn.get("url"):
                button_row.append(
                    InlineKeyboardButton(
                        text=btn["text"],
                        url=btn["url"]
                    )
                )
            elif btn.get("callback_data"):
                button_row.append(
                    InlineKeyboardButton(
                        text=btn["text"],
                        callback_data=btn["callback_data"]
                    )
                )
        if button_row:
            buttons.append(button_row)
    
    return InlineKeyboardMarkup(buttons)


# ══════════════════════════════════════════════════════════════
# SEND PHOTO WITH PYROGRAM
# ══════════════════════════════════════════════════════════════


async def _send_magic(
    chat_id: int,
    photo_url: str,
    caption: str,
    markup: list,
    reply_to: int = None,
    effect_id: str = None,
) -> int | None:

    try:
        # Convert markup to Pyrogram keyboard
        keyboard = _markup_to_keyboard(markup)
        
        # Send photo using Pyrogram with HTML parse mode
        message = await app.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=reply_to,
            reply_markup=keyboard,
        )
        
        return message.id
        
    except Exception as e:
        log.error(f"Send photo failed: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# RAW BOT API (for reactions only)
# ══════════════════════════════════════════════════════════════


async def _raw_api(method: str, payload: dict) -> dict:

    url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/{method}"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()


# ══════════════════════════════════════════════════════════════
# PANELS
# ══════════════════════════════════════════════════════════════


async def _private_panel() -> list:

    me = await app.get_me()

    support_url = getattr(
        Config,
        "SUPPORT_URL",
        "https://t.me/+WzyoJkg4bzhlNTFl",
    )

    source_url = getattr(
        Config,
        "SOURCE_URL",
        "https://t.me/+WzyoJkg4bzhlNTFl",
    )

    owner_id = Config.OWNER_ID

    return [
        [
            _api_btn(
                "˹ Support ˼",
                url=support_url,
            ),
            _api_btn(
                "˹ Updates ˼",
                url=support_url,
            ),
        ],
        [
            _api_btn(
                "˹ Config ˼",
                callback_data="vc_config",
            ),
            _api_btn(
                "˹ Help ˼",
                callback_data="vc_help",
            ),
        ],
        [
            _api_btn(
                "˹ Source Code ˼",
                url=source_url,
            ),
        ],
        [
            _api_btn(
                "˹ My Master ˼",
                url=f"tg://user?id={owner_id}",
            ),
        ],
    ]


async def _group_panel() -> list:

    me = await app.get_me()

    support_url = getattr(
        Config,
        "SUPPORT_URL",
        "https://t.me/+WzyoJkg4bzhlNTFl",
    )

    return [
        [
            _api_btn(
                "˹ Support ˼",
                url=support_url,
            ),
            _api_btn(
                "˹ Config ˼",
                url=f"https://t.me/{me.username}?start=config",
            ),
        ],
        [
            _api_btn(
                "˹ DM Me ˼",
                url=f"https://t.me/{me.username}",
            ),
        ],
    ]


# ══════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════


def _uptime() -> str:

    secs = int(time.time() - _boot_time)

    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)

    return f"{h}h:{m:02d}m:{s:02d}s"


def _sys_stats() -> tuple[float, float, float]:

    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    return cpu, ram, disk


# ══════════════════════════════════════════════════════════════
# CAPTIONS
# ══════════════════════════════════════════════════════════════


async def _private_caption(mention: str) -> str:

    me = await app.get_me()

    cpu, ram, disk = _sys_stats()

    ub_count = await active_userbot_count()

    targets = await get_all_targets()

    mode = await get_mode()

    return (
        f"┌─── ˹ <b>VCFIGHTER</b> ˼ ─── ●\n"
        f"😈 ┆ <b>Hey, {mention}</b>\n"
        f"😎 ┆ <b>I am @{me.username}</b>\n"
        f"└──────────────────────•\n\n"

        f"<blockquote>"
        f"<b>💀 THE ULTIMATE VC FIGHTER BOT!</b>"
        f"</blockquote>\n"

        f"<blockquote>"
        f"<b>⏰ Uptime:</b> {_uptime()}\n"
        f"<b>☠️ CPU Load:</b> {cpu}%\n"
        f"<b>🐾 RAM:</b> {ram}%\n"
        f"<b>💾 Disk:</b> {disk}%"
        f"</blockquote>\n"

        f"<blockquote>"
        f"<b>💀 Userbots:</b> {ub_count} Active\n"
        f"<b>😈 Targets:</b> {len(targets)}\n"
        f"<b>⚡ Mode:</b> {mode.upper()}"
        f"</blockquote>\n"

        f"•──────────────────────•\n"

        f"<blockquote>"
        f"<b>Powered By » "
        f"<a href='{getattr(Config, 'SUPPORT_URL', 'https://t.me/+WzyoJkg4bzhlNTFl')}'>"
        f"VCFIGHTER</a></b>"
        f"</blockquote>\n"

        f"•──────────────────────•"
    )


async def _group_caption(group_name: str) -> str:

    ub_count = await active_userbot_count()

    mode = await get_mode()

    return (
        f"<blockquote>"
        f"🐾 Hello~ <b>I'm VCFIGHTER</b> and I'm Alive! ✨\n\n"

        f"☠️ <b>Uptime :</b> <code>{_uptime()}</code>\n"
        f"💀 <b>Userbots:</b> {ub_count} Active\n"
        f"⚡ <b>Mode :</b> {mode.upper()}\n\n"

        f"⚡ VC FIGHTER — Powered By Villain"
        f"</blockquote>"
    )


# ══════════════════════════════════════════════════════════════
# FIRE ANIMATION
# ══════════════════════════════════════════════════════════════


async def _fire_animation(message: Message):

    try:

        anim = await message.reply_text(FIRE_FRAMES[0])

        for frame in FIRE_FRAMES[1:]:

            await asyncio.sleep(FIRE_DELAY)

            await anim.edit_text(frame)

        return anim

    except Exception as e:

        log.warning(f"Fire animation failed: {e}")

        return None


# ══════════════════════════════════════════════════════════════
# PRIVATE START
# ══════════════════════════════════════════════════════════════


@app.on_message(pyro_filters.command("start") & pyro_filters.private)
async def start_private(client, message: Message):

    user = message.from_user

    mention = (
        f"<a href='tg://user?id={user.id}'>"
        f"{user.first_name}</a>"
    )

    anim = await _fire_animation(message)

    caption = await _private_caption(mention)

    panel = await _private_panel()

    sent_id = await _send_magic(
        chat_id=message.chat.id,
        photo_url=random.choice(VC_PICS),
        caption=caption,
        markup=panel,
        effect_id=EFFECT_FIRE,
    )

    if anim:
        try:
            await anim.delete()
        except Exception:
            pass

    if sent_id:
        try:
            await _raw_api(
                "setMessageReaction",
                {
                    "chat_id": message.chat.id,
                    "message_id": sent_id,
                    "reaction": [
                        {
                            "type": "emoji",
                            "emoji": "🔥",
                        }
                    ],
                    "is_big": True,
                },
            )
        except Exception:
            pass

    if Config.LOG_CHANNEL:
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"🐾 {mention} started the bot.\n"
                f"<b>ID ➠</b> <code>{user.id}</code>",
            )
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# GROUP START
# ══════════════════════════════════════════════════════════════


@app.on_message(pyro_filters.command("start") & pyro_filters.group)
async def start_group(client, message: Message):

    caption = await _group_caption(
        message.chat.title or "Group"
    )

    panel = await _group_panel()

    await _send_magic(
        chat_id=message.chat.id,
        photo_url=random.choice(VC_PICS),
        caption=caption,
        markup=panel,
        reply_to=message.id,
    )


# ══════════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════════


@app.on_callback_query(pyro_filters.regex("^vc_config$"))
async def cb_config(client, cq):

    from VCFIGHTERS.FIGHTERS.Settings import is_authorized

    if not await is_authorized(cq.from_user.id):
        return await cq.answer(
            "⛔ Access Denied",
            show_alert=True,
        )

    await cq.answer()

    await client.send_message(
        cq.message.chat.id,
        "⚙️ /config",
    )


@app.on_callback_query(pyro_filters.regex("^vc_help$"))
async def cb_help(client, cq):

    await cq.answer()

    await client.send_message(
        cq.message.chat.id,
        "ℹ️ /help",
    )


# ══════════════════════════════════════════════════════════════
# BOT ADDED TO GROUP
# ══════════════════════════════════════════════════════════════


@app.on_message(pyro_filters.new_chat_members)
async def on_bot_added(client, message: Message):

    me = await client.get_me()

    for member in message.new_chat_members:

        if member.id != me.id:
            continue

        panel = await _group_panel()

        # Convert markup to keyboard
        keyboard = _markup_to_keyboard(panel)

        run = await message.reply_text(
            f"😎 <b>Hello {message.chat.title}!</b>\n"
            f"💖 Thanks for adding me!",
            reply_markup=keyboard,
        )

        async def _auto_del():

            await asyncio.sleep(15)

            try:
                await run.delete()
            except Exception:
                pass

        asyncio.create_task(_auto_del())

        if Config.LOG_CHANNEL:
            try:
                await client.send_message(
                    Config.LOG_CHANNEL,
                    f"🎉 <b>Added To Group!</b>\n\n"
                    f"<b>📌 Name :</b> {message.chat.title}\n"
                    f"<b>🆔 ID :</b> <code>{message.chat.id}</code>",
                )
            except Exception:
                pass

        break

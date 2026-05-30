from pyrogram import filters as pyro_filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pyrogram.enums import ParseMode

from VCFIGHTERS.core.bot import app
from VCFIGHTERS.FIGHTERS.Settings import is_authorized

# ──────────────────────────────────────────────────────────────
# HELP CONTENT
# ──────────────────────────────────────────────────────────────

_SECTIONS = {
    "vc": (
        "🎙️ **VC COMMANDS**\n\n"
        "`/stop` — Stop VC & Leave\n"
        "`/pause` — Pause Audio\n"
        "`/resume` — Resume Audio\n"
        "`/vcstatus` — Current VC Status"
    ),
    "config": (
        "⚙️ **CONFIG COMMANDS**\n\n"
        "`/config` — Main Config Panel\n\n"
        "**Panel Menu:**\n"
        "˹ 𝐋ᴏɢɢєʀ ˼ — Set Log Group\n"
        "˹ 𝐅𝐅ϻρєɢ ˼ — Audio Weapon Controls\n"
        "˹ 𝐌ᴏᴅє ˼ — Auto or DM Mode\n"
        "˹ 𝐔sєʀ𝐁ᴏᴛs ˼ — Add/Remove Userbots\n"
        "˹ 𝐓ᴀʀɢєᴛ ˼ — Set Target Group\n"
        "˹ ριηɢs ˼ — System Pings Check"
    ),
    "modes": (
        "🎮 **MODES**\n\n"
        "🟢 **AUTO MODE**\n"
        "Owner/Sudo turns mic ON in VC →\n"
        "Userbot auto starts recording\n"
        "Turn OFF mic → Recording loops\n\n"
        "🔵 **DM MODE**\n"
        "Send voice note to bot DM →\n"
        "Userbot loops in target VC\n"
        "Send new voice note → Old removed, new plays"
    ),
    "ffmpeg": (
        "🛠️ **FFMPEG WEAPONS**\n\n"
        "🔊 **VOLUME** — 100% to MAX 💥\n"
        "🎛️ **COMPRESSOR** — Boost Low Sound\n"
        "🔒 **LIMITER** — Control Loud Sound\n"
        "🎸 **BASS** — Normal → Heavy → 🌍 Earthquake\n"
        "👹 **PITCH** — Normal → Demon → 🐹 Chipmunk\n"
        "🦇 **ECHO** — Ghost Protocol Reverb\n\n"
        "💀 **FULL POWER MODE** = All MAX Together"
    ),
    "sudo": (
        "👑 **SUDO SYSTEM**\n\n"
        "`/addsudo` — Reply or give ID → Add Sudo\n"
        "`/delsudo` — Remove Sudo\n"
        "`/sudolist` — List All Sudos\n\n"
        "⚠️ Only **OWNER** can add/remove sudos"
    ),
}

# ──────────────────────────────────────────────────────────────
# KEYBOARDS
# ──────────────────────────────────────────────────────────────

def _main_help_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("˹ 🎙️ VC CMDS ˼",    callback_data="hlp_vc"),
            InlineKeyboardButton("˹ ⚙️ CONFIG ˼",      callback_data="hlp_config"),
        ],
        [
            InlineKeyboardButton("˹ 🎮 MODES ˼",       callback_data="hlp_modes"),
            InlineKeyboardButton("˹ 🛠️ FFMPEG ˼",      callback_data="hlp_ffmpeg"),
        ],
        [
            InlineKeyboardButton("˹ 👑 SUDO ˼",        callback_data="hlp_sudo"),
        ],
        [
            InlineKeyboardButton("˹ ❌ CLOSE ˼",       callback_data="hlp_close"),
        ],
    ])


def _back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("˹ ◀️ BACK ˼", callback_data="hlp_main")]
    ])


# ──────────────────────────────────────────────────────────────
# /help COMMAND
# ──────────────────────────────────────────────────────────────

@app.on_message(pyro_filters.command("help") & pyro_filters.private)
async def cmd_help(client, message: Message):
    if not await is_authorized(message.from_user.id):
        await message.reply("⛔ Access Denied - Owner/Sudo Only")
        return
    await message.reply(
        "⚔️ **VCFIGHTER HELP**\n\nSelect a section:",
        reply_markup=_main_help_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )


# ──────────────────────────────────────────────────────────────
# CALLBACKS
# ──────────────────────────────────────────────────────────────

@app.on_callback_query(pyro_filters.regex("^hlp_main$"))
async def cb_hlp_main(client, query: CallbackQuery):
    if not await is_authorized(query.from_user.id):
        await query.answer("⛔ Access Denied", show_alert=True)
        return
    await query.answer()
    await query.edit_message_text(
        "⚔️ **VCFIGHTER HELP**\n\nSelect a section:",
        reply_markup=_main_help_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )


@app.on_callback_query(pyro_filters.regex("^hlp_(vc|config|modes|ffmpeg|sudo)$"))
async def cb_hlp_section(client, query: CallbackQuery):
    if not await is_authorized(query.from_user.id):
        await query.answer("⛔ Access Denied", show_alert=True)
        return
    key  = query.data.split("_")[1]
    text = _SECTIONS.get(key, "Not found.")
    await query.answer()
    await query.edit_message_text(
        text,
        reply_markup=_back_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )


@app.on_callback_query(pyro_filters.regex("^hlp_close$"))
async def cb_hlp_close(client, query: CallbackQuery):
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass

import asyncio
import re
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from ads import get_ads

# =========================
# Environment Variables
# =========================
API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")
USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", "your_session_string")
CHANNEL = os.environ.get("CHANNEL", "@your_channel_username")

# =========================
# Clients
# =========================
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user", api_id=API_ID, api_hash=API_HASH, session_name=USER_SESSION_STRING)

# =========================
# Video Expiry Storage
# =========================
video_expiry = {}

# =========================
# /start Command
# =========================
@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    btn = [[InlineKeyboardButton("🔍 Search Episodes", switch_inline_query_current_chat="")]]
    await message.reply_text(
        "👋 Welcome to JacpotFilm Bot!\nType any episode keyword to search.",
        reply_markup=InlineKeyboardMarkup(btn)
    )

# =========================
# Search Handler
# =========================
@bot.on_message(filters.text & ~filters.command("start"))
async def search_handler(client, message):
    query = message.text.strip()
    if not query:
        return

    results = []
    async with user:
        async for msg in user.search_messages(CHANNEL, query, limit=50):
            if msg.video or msg.document:
                results.append(msg)

    if not results:
        await message.reply_text("❌ No results found.")
        return

    season_dict = {}
    for msg in results:
        season = 1
        if msg.caption:
            match = re.search(r"Season (\d+)", msg.caption, re.IGNORECASE)
            if match:
                season = int(match.group(1))
        season_dict.setdefault(season, []).append(msg)

    buttons = [[InlineKeyboardButton(f"Season {s}", callback_data=f"season_{s}_{query}")]
               for s in sorted(season_dict.keys())]

    await message.reply_text("📂 Select a season:", reply_markup=InlineKeyboardMarkup(buttons))

# =========================
# Season → Episode List
# =========================
@bot.on_callback_query(filters.regex(r"^season_(\d+)_(.+)"))
async def season_handler(client, callback_query):
    season, query = callback_query.data.split("_")[1], "_".join(callback_query.data.split("_")[2:])
    season = int(season)

    results = []
    async with user:
        async for msg in user.search_messages(CHANNEL, query, limit=50):
            if msg.video or msg.document:
                msg_season = 1
                if msg.caption:
                    match = re.search(r"Season (\d+)", msg.caption, re.IGNORECASE)
                    if match:
                        msg_season = int(match.group(1))
                if msg_season == season:
                    results.append(msg)

    if not results:
        await callback_query.message.edit("❌ No episodes found.")
        return

    buttons = [[InlineKeyboardButton(f"{msg.caption or 'Episode'}", callback_data=f"episode_{msg.id}")]
               for msg in results]

    await callback_query.message.edit(f"🎬 Season {season} Episodes:",
                                      reply_markup=InlineKeyboardMarkup(buttons))

# =========================
# Episode → Intermediate + Video + Expiry + Ads
# =========================
@bot.on_callback_query(filters.regex(r"^episode_(\d+)"))
async def episode_handler(client, callback_query):
    msg_id = int(callback_query.data.split("_")[1])

    async with user:
        msg = await user.get_messages(CHANNEL, msg_id)

    now = datetime.now()
    if msg_id in video_expiry and now > video_expiry[msg_id]:
        await callback_query.message.edit("⏰ This video has expired.")
        return

    # Dynamic ads links
    links = get_ads()
    verify_url = links["verify"]
    tutorial_url = links["tutorial"]

    btn = [
        [InlineKeyboardButton("✅ Verify Link", url=verify_url)],
        [InlineKeyboardButton("📖 Tutorial", url=tutorial_url)],
        [InlineKeyboardButton("📋 Copy Verify Link", url=verify_url)]
    ]
    await callback_query.message.edit(f"🔒 {msg.caption or 'Episode'}\n\nPlease verify to get the video.",
                                      reply_markup=InlineKeyboardMarkup(btn))

    # Send video (forward-protected)
    async with user:
        sent = await user.copy_message(
            chat_id=callback_query.from_user.id,
            from_chat_id=CHANNEL,
            message_id=msg.id,
            protect_content=True
        )

    video_expiry[sent.id] = now + timedelta(days=5)

    # Auto-delete after 5 minutes
    await asyncio.sleep(300)
    try:
        await sent.delete(revoke=True)
    except:
        pass

# =========================
# Run Bot
# =========================
async def main():
    async with bot, user:
        print("✅ JacpotFilm Bot running with dynamic ads!")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

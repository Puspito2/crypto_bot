
import os
import logging
import asyncio
import aiohttp
import feedparser
import nest_asyncio
from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

nest_asyncio.apply()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def healthcheck(request):
    return web.Response(text="Bot is live")

app_web = web.Application()
app_web.router.add_get("/", healthcheck)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/start triggered")
    menu = [["/news", "/airdrops"], ["/chart btc", "/exchanges", "/trending"]]
    markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)
    await update.message.reply_text("🤖 Welcome to *CryptoBot!*\nChoose a command below 👇", parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/news triggered")
    try:
        feed = feedparser.parse("https://cryptopanic.com/feed")
        entries = feed.entries[:5]
        msg = "\n\n".join(f"[{e.title}]({e.link})" for e in entries)
        await update.message.reply_text(f"📰 *Top Crypto News:*\n{msg}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text("❌ Failed to fetch news.")
        logger.error(f"/news error: {e}")

async def airdrops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/airdrops triggered")
    try:
        feed = feedparser.parse("https://airdrops.io/feed/")
        entries = feed.entries[:5]
        msg = "\n".join(f"[{e.title}]({e.link})" for e in entries)
        await update.message.reply_text(f"🚀 *Top Airdrops:*\n{msg}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text("❌ Failed to fetch airdrops.")
        logger.error(f"/airdrops error: {e}")

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/chart triggered")
    try:
        if not context.args:
            await update.message.reply_text("Usage: /chart <symbol>\nExample: /chart btc")
            return
        symbol = context.args[0].lower()
        symbol_map = {
            "btc": "bitcoin", "eth": "ethereum", "bnb": "binancecoin",
            "sol": "solana", "ada": "cardano", "xrp": "ripple"
        }
        coin_id = symbol_map.get(symbol, symbol)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                data = await res.json()
                price = data.get(coin_id, {}).get("usd")
                if price:
                    await update.message.reply_text(f"💰 *{coin_id.title()}* = `${price}` USD", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Token not found.")
    except Exception as e:
        await update.message.reply_text("❌ Failed to fetch chart.")
        logger.error(f"/chart error: {e}")

async def exchanges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/exchanges triggered")
    try:
        url = "https://api.coingecko.com/api/v3/exchanges"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                exchanges = await res.json()
                msg = "\n\n".join(f"*{e['name']}* (Trust Rank {e['trust_score_rank']}):\n{e['url']}" for e in exchanges[:5])
                await update.message.reply_text(f"🏦 *Top Exchanges:*\n{msg}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text("❌ Failed to fetch exchanges.")
        logger.error(f"/exchanges error: {e}")

async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/trending triggered")
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                data = await res.json()
                coins = data.get("coins", [])[:5]
                msg = "\n\n".join(f"*{c['item']['name']}* ({c['item']['symbol']})\nRank {c['item']['market_cap_rank']}\nhttps://www.coingecko.com/en/coins/{c['item']['id']}" for c in coins)
                await update.message.reply_text(f"🔥 *Trending Coins:*\n{msg}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text("❌ Failed to fetch trending coins.")
        logger.error(f"/trending error: {e}")

async def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("airdrops", airdrops))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("exchanges", exchanges))
    app.add_handler(CommandHandler("trending", trending))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("✅ Bot polling started")

async def start_web_server():
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", "10000"))
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.info(f"✅ Web server running on port {port}")

async def main():
    await asyncio.gather(run_bot(), start_web_server())

if __name__ == '__main__':
    asyncio.run(main())

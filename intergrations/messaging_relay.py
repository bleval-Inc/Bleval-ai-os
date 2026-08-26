import os
import asyncio
import httpx
import discord
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

FCC_SERVER_URL = os.getenv("FCC_SERVER_URL", "http://127.0.0.1:8082/v1/messages")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

# --- Core Request Handler ---
async def query_fcc(prompt: str) -> str:
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            res = await client.post(FCC_SERVER_URL, json=payload)
            if res.status_code == 200:
                data = res.json()
                return data["content"][0]["text"]
            return f"Error from FCC Server: HTTP {res.status_code}"
        except Exception as e:
            return f"Failed to reach FCC Server: {str(e)}"

# --- Telegram Bot Setup ---
async def tg_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = " ".join(context.args)
    if not user_prompt:
        await update.message.reply_text("Usage: /task <your prompt>")
        return
    await update.message.reply_text("Dispatching task to FCC Agent...")
    response = await query_fcc(user_prompt)
    await update.message.reply_text(response)

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

@discord_client.event
async def on_ready():
    print(f"Discord Relay online as {discord_client.user}")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return
    if message.channel.id == DISCORD_CHANNEL_ID and message.content.startswith("!task"):
        user_prompt = message.content[6:].strip()
        if not user_prompt:
            await message.channel.send("Usage: !task <your prompt>")
            return
        await message.channel.send("Dispatching task to FCC Agent...")
        response = await query_fcc(user_prompt)
        await message.channel.send(response[:2000])  # Discord 2k char limit guard

# --- Runner ---
async def main():
    tg_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_app.add_handler(CommandHandler("task", tg_task))
    
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling()
    
    await discord_client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
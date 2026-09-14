import os
import asyncio
import subprocess
import re
import shutil
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID_RAW = os.getenv("DISCORD_CHANNEL_ID", "0")

if not DISCORD_TOKEN:
    raise ValueError("ERROR: DISCORD_BOT_TOKEN is not set in .env")

CHANNEL_ID = int(CHANNEL_ID_RAW)
TMUX_SESSION = "fcc_session"
TMUX_BIN = shutil.which("tmux") or "/opt/homebrew/bin/tmux" or "/usr/local/bin/tmux"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Track text states to detect when Claude finishes typing
last_sent_hash = None
pending_screen_text = ""
stable_counter = 0

def clean_ansi(text: str) -> str:
    """Strips color codes, cursor positions, and terminal control sequences."""
    ansi_regex = re.compile(
        r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|\x1B[78]|\x1B\(B\x0F?'
    )
    return ansi_regex.sub('', text).strip()

def capture_tmux_screen() -> str:
    """Captures the visible text buffer from the active tmux window."""
    try:
        result = subprocess.run(
            [TMUX_BIN, "capture-pane", "-pt", TMUX_SESSION],
            capture_output=True,
            text=True,
            check=True
        )
        return clean_ansi(result.stdout)
    except Exception:
        return ""

async def monitor_tmux_buffer():
    """Waits until the screen output stabilizes before sending the final response."""
    global last_sent_hash, pending_screen_text, stable_counter
    
    while True:
        await asyncio.sleep(1.5)
        
        current_screen = capture_tmux_screen()
        if not current_screen:
            continue

        current_hash = hash(current_screen)

        # If the screen hasn't changed since the last poll, increment the stability counter
        if current_screen == pending_screen_text:
            stable_counter += 1
        else:
            pending_screen_text = current_screen
            stable_counter = 0

        # Output has been stable for ~3 seconds (2 polls) and hasn't been posted yet
        if stable_counter >= 2 and current_hash != last_sent_hash:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                # Capture the relevant tail end of the output (up to 1800 chars for Discord)
                payload = current_screen[-1800:]
                if payload:
                    await channel.send(f"```text\n{payload}\n```")
                    last_sent_hash = current_hash

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}. Anti-spam bridge active on '{TMUX_SESSION}'")
    bot.loop.create_task(monitor_tmux_buffer())

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != CHANNEL_ID:
        return

    user_input = message.content
    
    # Send full text into tmux followed by Enter
    subprocess.run([TMUX_BIN, "send-keys", "-t", TMUX_SESSION, user_input, "Enter"])

def ensure_tmux_session():
    has_session = subprocess.run(
        [TMUX_BIN, "has-session", "-t", TMUX_SESSION],
        capture_output=True
    ).returncode == 0

    if not has_session:
        print(f"Creating new tmux session '{TMUX_SESSION}'...")
        subprocess.run([
            TMUX_BIN, "new-session", "-d", "-s", TMUX_SESSION, 
            "zsh -c 'fcc-claude; exec zsh'"
        ])
        subprocess.run([TMUX_BIN, "set-option", "-t", TMUX_SESSION, "mouse", "off"])
        subprocess.run([TMUX_BIN, "set-option", "-ga", "terminal-overrides", "xterm*:smcup@:rmcup@"])

if __name__ == "__main__":
    ensure_tmux_session()
    bot.run(DISCORD_TOKEN)
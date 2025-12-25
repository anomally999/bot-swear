import discord
import os
import asyncio
import json
import logging
import aiohttp
import random
from dotenv import load_dotenv
from datetime import timedelta
from discord.utils import get
from aiohttp import web  # For Render web service

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load token
load_dotenv()
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("TOKEN not found in environment variables!")
    exit(1)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
PREFIX = ","

# Data file
DATA_FILE = "bot_data.json"

# Default data
default_data = {
    "bad_words": [
        "fuck", "f u c k", "f*ck", "f**k", "f@ck", "fck", "fuk", "fucc", "fukk",
        "fucking", "f*cking", "fuckin", "fukin", "fcking",
        "fucker", "fuckers", "motherfucker", "m0therfucker", "mothafucka", "mf",
        "shit", "sh1t", "sh*t", "shite", "shitt", "bullshit", "bullsh*t",
        "ass", "a s s", "a**", "asshole", "a**hole", "assh0le", "a55hole", "arse",
        "bitch", "b1tch", "b*tch", "bitc h", "bich",
        "cunt", "c*nt", "c u n t",
        "dick", "d1ck", "d*ck", "cock", "c0ck", "c*ck",
        "pussy", "p*ssy", "pu55y",
        "bastard", "b@stard",
        "damn", "d@mn", "goddamn", "goddammit",
        "wanker", "bollocks", "twat", "prick",
        "nigger", "n1gger", "n*gg*r",
        "fag", "f@g", "faggot",
        "retard", "r3tard",
        "son of a bitch", "s0b", "sonofabitch",
        "fuck off", "piss off", "go fuck yourself", "eat shit",
        "cocksucker", "tits", "t1ts", "boobs", "b00bs",
        "whore", "wh0re", "slut", "sl*t",
        "wtf", "w t f", "wt f", "what the fuck", "what the f",
        "wth", "what the hell", "what the heck", "wtheck",
        "omfg", "oh my fucking god",
        "fml", "fuck my life",
        "lmao", "lmfao", "laughing my fucking ass off",
        "bs", "bullshit",
        "crap", "cr@p", "cr4p",
        "hell", "h3ll", "h*ll",
        "bloody hell", "bloody",
        "frick", "fr1ck", "frickin", "fricking",
        "dang", "darn",
        "jesus christ", "jesus f christ", "jc",
        "holy shit", "holy crap",
        "stfu", "shut the fuck up", "shut the f up",
        "gtfo", "get the fuck out",
        "smh", "ffs", "for fucks sake", "for fuck's sake",
        "af", "as fuck",
        "smd", "suck my dick",
        "nsfw"
    ],
    "moderation_active": {},
    "swear_counts": {}
}

# Load/save data
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    logger.warning("bot_data.json empty, using defaults")
                    return default_data.copy()
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Load error: {e}, using defaults")
    return default_data.copy()

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "bad_words": bad_words,
                "moderation_active": moderation_active,
                "swear_counts": swear_count
            }, f, indent=2)
        logger.info("Data saved")
    except Exception as e:
        logger.error(f"Save failed: {e}")

data = load_data()
bad_words = data.get("bad_words", default_data["bad_words"])
moderation_active = data.get("moderation_active", {})
swear_count = data.get("swear_counts", {})

MAX_SWEARS = 5
TIMEOUT_MINUTES = 5
WEBHOOK_NAME = "SwearWordModerator"
WEBHOOK_AVATAR_URL = "https://i.imgur.com/3jZ7q.jpg"

# Bro-style warnings
BRO_WARNINGS = [
    "Yo {user}, come on bro, chill with the language. ({count}/{max})",
    "Hey dude {user}, let's keep it clean, yeah? ({count}/{max})",
    "Bro {user}, not cool man. Watch the words. ({count}/{max})",
    "Aye {user}, easy there champ. No need for that. ({count}/{max})",
    "Duuude {user}, really? We don't talk like that here. ({count}/{max})",
    "My guy {user}, you're better than that. Tone it down. ({count}/{max})",
    "Bro {user}, that's a no from me dawg. ({count}/{max})",
    "Hold up {user}, language bro! Let's be chill. ({count}/{max})",
    "Nah fam {user}, not in this server. Keep it PG. ({count}/{max})",
    "Yo {user}, relax dude. We good without the swears. ({count}/{max})",
    "Bruh {user}... seriously? Come on man. ({count}/{max})",
    "Easy there {user}, let's not go full sailor mode. ({count}/{max})",
    "Hey friend {user}, mind the language? Thanks bro. ({count}/{max})"
]

DM_MESSAGES = [
    "Hey bro, just a heads up — I caught a swear. We're keeping it chill here. You're at {count}/{max}.",
    "Yo dude, language! That's {count}/{max}. Let's keep the server clean.",
    "My guy, had to delete that. No hard feelings — count's at {count}/{max}.",
    "Bruh, come on — watch it. You're on {count}/{max}. Don't make me timeout ya!",
    "Hey {user}, friendly reminder: no swearing. Count: {count}/{max}. Stay cool."
]

async def download_avatar(session, url):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
    except:
        pass
    return None

async def get_or_create_webhook(channel):
    try:
        webhooks = await channel.webhooks()
        webhook = get(webhooks, name=WEBHOOK_NAME)
        if webhook:
            return webhook
        async with aiohttp.ClientSession() as session:
            avatar = await download_avatar(session, WEBHOOK_AVATAR_URL)
            webhook = await channel.create_webhook(name=WEBHOOK_NAME, avatar=avatar)
        logger.info(f"Webhook created in #{channel.name}")
        return webhook
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return None

async def send_webhook(channel, content=None, embed=None):
    webhook = await get_or_create_webhook(channel)
    if webhook:
        try:
            await webhook.send(content=content, embed=embed, username="Swear Word Moderator",
                               avatar_url=WEBHOOK_AVATAR_URL, allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")

@client.event
async def on_ready():
    logger.info(f'Bot online: {client.user}')
    for guild in client.guilds:
        if guild.id not in moderation_active:
            moderation_active[guild.id] = True
    save_data()

@client.event
async def on_guild_join(guild):
    moderation_active[guild.id] = True
    save_data()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(PREFIX):
        await handle_command(message)
        return

    if not moderation_active.get(message.guild.id, True):
        return

    content_lower = message.content.lower()
    detected = any(word in content_lower for word in bad_words)

    if detected:
        key = f"{message.guild.id}:{message.author.id}"
        swear_count[key] = swear_count.get(key, 0) + 1
        count = swear_count[key]

        try:
            await message.delete()

            # Public bro warning
            warning_text = random.choice(BRO_WARNINGS).format(user=message.author.mention, count=count, max=MAX_SWEARS)
            embed = discord.Embed(description=warning_text, color=0xffa500)
            embed.set_footer(text="Keep it up and timeout incoming, bro.")
            await send_webhook(message.channel, embed=embed)

            # DM
            dm_text = random.choice(DM_MESSAGES).format(user=message.author.display_name, count=count, max=MAX_SWEARS)
            try:
                dm_embed = discord.Embed(title="Yo, heads up bro...", description=dm_text, color=0xffa500)
                dm_embed.set_footer(text="Just keeping the server chill 😎")
                await message.author.send(embed=dm_embed)
            except:
                pass  # DM blocked

            if count >= MAX_SWEARS:
                await message.author.timeout(timedelta(minutes=TIMEOUT_MINUTES), reason="Excessive swearing")
                timeout_embed = discord.Embed(
                    title="⛔ Timeout, Bro",
                    description=f"{message.author.mention} — too many swears, dude.\nTimeout for **{TIMEOUT_MINUTES} minutes**.",
                    color=0xff0000
                )
                await send_webhook(message.channel, embed=timeout_embed)
                del swear_count[key]

            save_data()

        except discord.Forbidden:
            await send_webhook(message.channel, content="Yo bro, I need permissions to delete/timeout!")
        except Exception as e:
            logger.error(f"Error: {e}")

# [send_paginated_list and handle_command same as before — omitted for brevity but include them]

# Web server for Render
async def health(request):
    return web.Response(text="Swear Word Moderator is alive and chilling, bro! 😎")

async def web_server():
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Render web server running on port 8080")

# Main runner
async def main():
    await asyncio.gather(
        web_server(),
        client.start(TOKEN)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
    finally:
        save_data()

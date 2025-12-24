import discord
import os
import asyncio
import json
import logging
import aiohttp
import random  # Added for random warnings
from dotenv import load_dotenv
from datetime import timedelta
from discord.utils import get

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load token
load_dotenv()
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    logger.error("Token not found in .env file!")
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

# Default data with full English swear list
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
    "moderation_active": {}
}

# Load/save data
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    logger.warning("bot_data.json is empty. Using defaults.")
                    return default_data.copy()
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Corrupted JSON: {e}. Using defaults.")
        except Exception as e:
            logger.warning(f"Failed to load data: {e}. Using defaults.")
    return default_data.copy()

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "bad_words": bad_words,
                "moderation_active": moderation_active
            }, f, indent=2)
        logger.info("Data saved.")
    except Exception as e:
        logger.error(f"Failed to save data: {e}")

data = load_data()
bad_words = data.get("bad_words", default_data["bad_words"])
moderation_active = data.get("moderation_active", {})
swear_count = {}

MAX_SWEARS = 5
TIMEOUT_MINUTES = 5
WEBHOOK_NAME = "SwearWordModerator"
WEBHOOK_AVATAR_URL = "https://i.imgur.com/3jZ7q.jpg"

# Chill bro/dude/friend style random warnings
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
        logger.info(f"Created webhook in #{channel.name}")
        return webhook
    except discord.Forbidden:
        logger.warning(f"No webhook permission in #{channel.name}")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return None

async def send_webhook(channel, content=None, embed=None):
    webhook = await get_or_create_webhook(channel)
    if webhook:
        try:
            await webhook.send(
                content=content,
                embed=embed,
                username="Swear Word Moderator",
                avatar_url=WEBHOOK_AVATAR_URL,
                allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")

@client.event
async def on_ready():
    logger.info(f'Bot connected as {client.user}')
    for guild in client.guilds:
        if guild.id not in moderation_active:
            moderation_active[guild.id] = True
    save_data()

@client.event
async def on_guild_join(guild):
    moderation_active[guild.id] = True
    save_data()
    logger.info(f"Joined guild: {guild.name}")

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
        key = (message.guild.id, message.author.id)
        swear_count[key] = swear_count.get(key, 0) + 1
        count = swear_count[key]

        try:
            await message.delete()

            # Random chill bro warning
            warning_text = random.choice(BRO_WARNINGS).format(
                user=message.author.mention,
                count=count,
                max=MAX_SWEARS
            )

            embed = discord.Embed(
                description=warning_text,
                color=0xffa500
            )
            embed.set_footer(text="Keep it up and you'll get a timeout, bro.")
            await send_webhook(message.channel, embed=embed)

            if count >= MAX_SWEARS:
                await message.author.timeout(timedelta(minutes=TIMEOUT_MINUTES), reason="Excessive profanity")
                embed = discord.Embed(
                    title="⛔ Timeout, Bro",
                    description=f"{message.author.mention} — too many swears, dude.\nChillin' in timeout for **{TIMEOUT_MINUTES} minutes**.",
                    color=0xff0000
                )
                embed.set_footer(text="Come back cleaner next time.")
                await send_webhook(message.channel, embed=embed)
                swear_count[key] = 0

        except discord.Forbidden:
            embed = discord.Embed(description="Yo, I can't delete messages or timeout — give me perms, bro!", color=0xff0000)
            await send_webhook(message.channel, embed=embed)
        except Exception as e:
            logger.error(f"Error: {e}")

async def send_paginated_list(channel):
    if not bad_words:
        embed = discord.Embed(description="List is empty, bro.", color=0x00ff00)
        await send_webhook(channel, embed=embed)
        return

    pages = []
    current = ""
    page_num = 1

    for word in sorted(bad_words):
        line = f"`{word}`\n"
        if len(current) + len(line) > 1900:
            embed = discord.Embed(title=f"Filtered Words — Page {page_num}", description=current, color=0x3498db)
            embed.set_footer(text=f"Total: {len(bad_words)} words")
            pages.append(embed)
            current = line
            page_num += 1
        else:
            current += line

    if current:
        embed = discord.Embed(title=f"Filtered Words — Page {page_num}", description=current, color=0x3498db)
        embed.set_footer(text=f"Total: {len(bad_words)} words")
        pages.append(embed)

    for embed in pages:
        await send_webhook(channel, embed=embed)
        await asyncio.sleep(0.5)

async def handle_command(message):
    args = message.content[len(PREFIX):].strip().split()
    if not args:
        return
    cmd = args[0].lower()

    perms = message.author.guild_permissions
    is_admin = perms.administrator or perms.manage_guild

    if cmd == "help":
        embed = discord.Embed(title="Yo, Swear Word Moderator Here", color=0x9b59b6)
        embed.add_field(name="Public Commands", value="`,help` • `,status` • `,list`", inline=False)
        embed.add_field(name="Admin Only", value="`,activate` • `,deactivate` • `,addword <word>` • `,removeword <word>`", inline=False)
        embed.set_footer(text="Prefix: , | I'm just tryna keep it chill in here, bro.")
        await send_webhook(message.channel, embed=embed)

    elif cmd == "status":
        status = "Enabled ✅" if moderation_active.get(message.guild.id, True) else "Disabled ❌"
        await send_webhook(message.channel, content=f"Moderation is **{status}**, bro.")

    elif cmd == "activate":
        if not is_admin: return await send_webhook(message.channel, content="Nah bro, admins only.")
        moderation_active[message.guild.id] = True
        save_data()
        await send_webhook(message.channel, content="✅ Moderation back on, dude.")

    elif cmd == "deactivate":
        if not is_admin: return await send_webhook(message.channel, content="Admins only, my guy.")
        moderation_active[message.guild.id] = False
        save_data()
        await send_webhook(message.channel, content="❌ Moderation off for now.")

    elif cmd == "addword" and len(args) > 1:
        if not is_admin: return await send_webhook(message.channel, content="Only admins can do that, bro.")
        word = " ".join(args[1:]).lower()
        if word not in bad_words:
            bad_words.append(word)
            save_data()
            await send_webhook(message.channel, content=f"✅ Added `{word}` to the list, dude.")
        else:
            await send_webhook(message.channel, content="Already got that one, bro.")

    elif cmd == "removeword" and len(args) > 1:
        if not is_admin: return await send_webhook(message.channel, content="Admins only, fam.")
        word = " ".join(args[1:]).lower()
        if word in bad_words:
            bad_words.remove(word)
            save_data()
            await send_webhook(message.channel, content=f"❌ Removed `{word}`, cool.")
        else:
            await send_webhook(message.channel, content="Wasn't even there, bro.")

    elif cmd in ["list", "listwords"]:
        await send_paginated_list(message.channel)

@client.event
async def on_disconnect():
    save_data()

try:
    client.run(TOKEN)
except discord.LoginFailure:
    logger.error("Invalid token")
except KeyboardInterrupt:
    logger.info("Bot stopped")
except Exception as e:
    logger.error(f"Fatal error: {e}")

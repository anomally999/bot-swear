import discord
import os
import asyncio
import json
import logging
import random
from dotenv import load_dotenv
from datetime import timedelta, datetime
from aiohttp import web

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("TOKEN not found!")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
PREFIX = ","

DATA_FILE = "bot_data.json"

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

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    return default_data.copy()
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Load error: {e}")
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
bad_words = [word.lower().replace(" ", "") for word in data.get("bad_words", default_data["bad_words"])]
moderation_active = data.get("moderation_active", {})
swear_count = data.get("swear_counts", {})

# Partial swear tracking
partial_swears = {}  # key: (guild_id, user_id) → {"current": str, "last_time": datetime, "target": str}

MAX_SWEARS = 5
TIMEOUT_MINUTES = 5
PARTIAL_TIMEOUT = 30  # seconds to complete partial swear

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

    content_lower = message.content.lower().strip()
    content_no_space = content_lower.replace(" ", "")

    # Check for full swear
    detected = any(word in content_no_space for word in bad_words)

    key = f"{message.guild.id}:{message.author.id}"
    partial_key = (message.guild.id, message.author.id)

    if detected:
        # Full swear detected
        swear_count[key] = swear_count.get(key, 0) + 1
        count = swear_count[key]

        try:
            await message.delete()

            warning_text = random.choice(BRO_WARNINGS).format(user=message.author.mention, count=count, max=MAX_SWEARS)
            embed = discord.Embed(description=warning_text, color=0xffa500)
            embed.set_footer(text="Keep it up and timeout incoming, bro.")
            await message.channel.send(embed=embed)

            dm_text = random.choice(DM_MESSAGES).format(user=message.author.display_name, count=count, max=MAX_SWEARS)
            try:
                dm_embed = discord.Embed(title="Yo, heads up bro...", description=dm_text, color=0xffa500)
                dm_embed.set_footer(text="Just keeping the server chill 😎")
                await message.author.send(embed=dm_embed)
            except:
                pass

            if count >= MAX_SWEARS:
                await message.author.timeout(timedelta(minutes=TIMEOUT_MINUTES), reason="Excessive swearing")
                timeout_embed = discord.Embed(
                    title="⛔ Timeout, Bro",
                    description=f"{message.author.mention} — too many swears, dude.\nTimeout for **{TIMEOUT_MINUTES} minutes**.",
                    color=0xff0000
                )
                await message.channel.send(embed=timeout_embed)
                del swear_count[key]

            save_data()

        except discord.Forbidden:
            await message.channel.send("Yo bro, I need permissions to delete and timeout!")
        except Exception as e:
            logger.error(f"Error: {e}")

        # Reset partial for this user
        if partial_key in partial_swears:
            del partial_swears[partial_key]

    else:
        # Check for partial swear building
        current_time = datetime.utcnow()
        if partial_key in partial_swears:
            partial = partial_swears[partial_key]
            time_diff = (current_time - partial["last_time"]).total_seconds()
            if time_diff > PARTIAL_TIMEOUT:
                del partial_swears[partial_key]  # Too slow, reset
            else:
                partial["current"] += content_no_space
                partial["last_time"] = current_time
                # Check if now completes a swear
                if any(word in partial["current"] for word in bad_words):
                    # Completed a swear!
                    del partial_swears[partial_key]
                    # Trigger the same as normal swear
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Nice try splitting it up, bro — still counts! 😏")
                    # Reuse the normal swear logic
                    message.content = " ".join(list(partial["current"]))  # Fake full message
                    await on_message(message)  # Recurse once
                    return

                partial_swears[partial_key] = partial
        else:
            # Start new partial if message is short and could be part of swear
            if len(content_no_space) <= 3 and any(content_no_space in word for word in bad_words):
                partial_swears[partial_key] = {
                    "current": content_no_space,
                    "last_time": current_time
                }

# [send_paginated_list and handle_command same as before — include from previous version]

async def health(request):
    return web.Response(text="Swear Word Moderator is alive and chilling, bro! 😎")

async def web_server():
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Render health check on port 8080")

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

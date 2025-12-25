# ======================================
# Section 1: Imports
# ======================================
# Core libraries for the bot
import discord
import os
import asyncio
import json
import logging
import random
from datetime import timedelta, datetime

# Environment and security
from dotenv import load_dotenv
import hashlib  # For potential hashing if needed (e.g., secure keys)

# Render health check (for web service)
from aiohttp import web

# ======================================
# Section 2: Constants and Configurations
# ======================================
# Security: Rate limiting cooldown (in seconds) for commands to prevent spam
COMMAND_COOLDOWN = 5

# Max partial swear timeout (seconds)
PARTIAL_TIMEOUT = 30

# Swear limits
MAX_SWEARS = 5
TIMEOUT_MINUTES = 5

# Bro-style warnings and DMs (randomly selected)
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

# Data file for persistence
DATA_FILE = "bot_data.json"

# ======================================
# Section 3: Global Variables (Initialized Later)
# ======================================
bad_words = []
moderation_active = {}
swear_count = {}
partial_swears = {}  # (guild_id, user_id) → {"current": str, "last_time": datetime}
command_cooldowns = {}  # (guild_id, user_id): last_command_time

# ======================================
# Section 4: Helper Functions
# ======================================
# Security: Sanitize input (strip, lower for comparison)
def sanitize_input(text):
    return text.strip().lower()

# Rate limiting check
def is_on_cooldown(guild_id, user_id):
    key = f"{guild_id}:{user_id}"
    last_time = command_cooldowns.get(key)
    if last_time:
        time_diff = (datetime.utcnow() - last_time).total_seconds()
        if time_diff < COMMAND_COOLDOWN:
            return True
    return False

def update_cooldown(guild_id, user_id):
    key = f"{guild_id}:{user_id}"
    command_cooldowns[key] = datetime.utcnow()

# Load data (secure file handling)
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    logger.warning("bot_data.json empty")
                    return default_data.copy()
                data = json.loads(content)
                return data
        except Exception as e:
            logger.error(f"Load error: {e}")
    return default_data.copy()

# Save data (secure write)
def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "bad_words": [w for w in bad_words],  # No sensitive info
                "moderation_active": moderation_active,
                "swear_counts": swear_count
            }, f, indent=2)
        logger.info("Data saved securely")
    except Exception as e:
        logger.error(f"Save failed: {e}")

# ======================================
# Section 5: Event Handlers
# ======================================
@client.event
async def on_ready():
    global bad_words, moderation_active, swear_count
    data = load_data()
    bad_words = [word.lower().replace(" ", "") for word in data.get("bad_words", default_data["bad_words"])]
    moderation_active = data.get("moderation_active", {})
    swear_count = data.get("swear_counts", {})
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

    content_lower = sanitize_input(message.content)
    content_no_space = content_lower.replace(" ", "")

    detected = any(word in content_no_space for word in bad_words)

    key = f"{message.guild.id}:{message.author.id}"
    partial_key = (message.guild.id, message.author.id)

    if detected:
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

        if partial_key in partial_swears:
            del partial_swears[partial_key]

    else:
        current_time = datetime.utcnow()
        if partial_key in partial_swears:
            partial = partial_swears[partial_key]
            time_diff = (current_time - partial["last_time"]).total_seconds()
            if time_diff > PARTIAL_TIMEOUT:
                del partial_swears[partial_key]
            else:
                partial["current"] += content_no_space
                partial["last_time"] = current_time
                if any(word in partial["current"] for word in bad_words):
                    del partial_swears[partial_key]
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Nice try splitting it up, bro — still counts! 😏")
                    swear_count[key] = swear_count.get(key, 0) + 1
                    count = swear_count[key]
                    embed = discord.Embed(description=f"{message.author.mention} Split swear detected! Count: {count}/{MAX_SWEARS}", color=0xffa500)
                    await message.channel.send(embed=embed)
                    save_data()
                else:
                    partial_swears[partial_key] = partial
        elif len(content_no_space) <= 4 and any(content_no_space in word for word in bad_words):
            partial_swears[partial_key] = {"current": content_no_space, "last_time": current_time}

# ... [send_paginated_list same as before]

async def handle_command(message):
    if is_on_cooldown(message.guild.id, message.author.id):
        await message.channel.send("Chill bro, wait a sec before another command.")
        return

    update_cooldown(message.guild.id, message.author.id)

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
        embed.set_footer(text="Prefix: , | Keeping it chill, bro 😎")
        await message.channel.send(embed=embed)

    elif cmd == "status":
        status = "Enabled ✅" if moderation_active.get(message.guild.id, True) else "Disabled ❌"
        await message.channel.send(f"Moderation is **{status}**, bro.")

    elif cmd == "activate":
        if not is_admin:
            await message.channel.send("Nah bro, admins only.")
            return
        moderation_active[message.guild.id] = True
        save_data()
        await message.channel.send("✅ Moderation enabled, dude.")

    elif cmd == "deactivate":
        if not is_admin:
            await message.channel.send("Admins only, my guy.")
            return
        moderation_active[message.guild.id] = False
        save_data()
        await message.channel.send("❌ Moderation disabled.")

    elif cmd == "addword" and len(args) > 1:
        if not is_admin:
            await message.channel.send("Only admins, bro.")
            return
        original_word = " ".join(args[1:])
        word = sanitize_input(original_word).replace(" ", "")
        if word not in bad_words:
            bad_words.append(word)
            save_data()
            await message.channel.send(f"✅ Added `{original_word}`, dude.")
        else:
            await message.channel.send("Already got it, bro.")

    elif cmd == "removeword" and len(args) > 1:
        if not is_admin:
            await message.channel.send("Admins only, fam.")
            return
        original_word = " ".join(args[1:])
        word = sanitize_input(original_word).replace(" ", "")
        if word in bad_words:
            bad_words.remove(word)
            save_data()
            await message.channel.send(f"❌ Removed `{original_word}`, cool.")
        else:
            await message.channel.send("Not in list, bro.")

    elif cmd in ["list", "listwords"]:
        await send_paginated_list(message.channel)

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
    

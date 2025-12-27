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
from aiohttp import web
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Load token
load_dotenv()
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("Token not found in .env file!")
    exit(1)
# Intents - IMPORTANT: Enable 'SERVER MEMBERS INTENT' and 'MESSAGE CONTENT INTENT' in Discord Developer Portal > Bot > Privileged Gateway Intents
# Otherwise, the bot won't receive message content or member events, and you'll see a fatal error in logs.
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
client = discord.Client(intents=intents)
PREFIX = ","
# Data file
DATA_FILE = "bot_data.json"
# Default data with full English and French swear list
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
        "nsfw",
        # French swears and variations
        "mince", "m i n c e", "m*nc*",
        "putain", "p u t a i n", "p*t**n", "put4in", "p*tain",
        "merde", "m e r d e", "m*rd*", "m**de", "m3rd3",
        "sa mère", "sa mere", "s a m e r e", "s a m è r e",
        "con", "c o n", "c*n",
        "conne", "c o n n e", "c*nn*",
        "ducon", "d u c o n", "d*c*n",
        "connard", "c o n n a r d", "c*nn*rd", "c0nnard",
        "connasse", "c o n n a s s e", "c*nn*ss*",
        "enculé", "e n c u l é", "encule", "3ncul3", "encul3",
        "enculée", "e n c u l é e",
        "bordel", "b o r d e l", "b*rd*l",
        "bâtard", "batard", "b â t a r d", "b*t*rd",
        "bâtarde", "batarde",
        "enfoiré", "e n f o i r é", "3nf0ir3", "enf0ire",
        "enfoirée", "e n f o i r é e",
        "poufiasse", "p o u f i a s s e", "p*uf**ss*",
        "pute", "p u t e", "p*t*", "put3",
        "pétasse", "petasse", "p é t a s s e", "p*t*ss*",
        "bite", "b i t e", "b*t*", "b1te",
        "chatte", "c h a t t e", "ch*tt*", "ch4tte",
        "chiant", "c h i a n t", "ch**nt",
        "chiante", "c h i a n t e",
        "niquer", "n i q u e r", "n*q**r", "n1qu3r",
        "baiser", "b a i s e r", "b**s*r", "b4iser",
        "dégage", "degage", "d é g a g e", "d*g*g*",
        "salaud", "s a l a u d", "s*l**d",
        "salope", "s a l o p e", "s*l*p*", "s4lope",
        "ta gueule", "t a g u e u l e", "ferme ta gueule", "f e r m e t a g u e u l e",
        "sa race", "ta race",
        "mange tes morts", "m a n g e t e s m o r t s",
        "nique tes morts", "n i q u e t e s m o r t s",
        "bordel de merde", "b o r d e l d e m e r d e",
        "putain de bordel de merde", "p u t a i n d e b o r d e l d e m e r d e",
        "sa mère la pute", "sa mere la pute", "s a m e r e l a p u t e",
        "putain de sa mère", "p u t a i n d e s a m e r e",
        "putain de sa mère la pute", "p u t a i n d e s a m e r e l a p u t e",
        "fils de chien", "f i l s d e c h i e n",
        "fils de pute", "f i l s d e p u t e",
        "trou du cul", "t r o u d u c u l",
        "casser les couilles", "c a s s e r l e s c o u i l l e s",
        "partir en couilles", "p a r t i r e n c o u i l l e s",
        "casse-couilles", "c a s s e c o u i l l e s",
        "s’en ficher", "s en ficher", "s e n f i c h e r",
        "s’en foutre", "s en foutre",
        "s’en battre les couilles", "s en battre les couilles",
        "faire chier", "f a i r e c h i e r",
        "à chier", "a chier", "a c h i e r"
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
# Chill bro/dude/friend style random warnings (English)
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
# French versions of warnings
FRENCH_WARNINGS = [
    "Yo {user}, allez mec, calme-toi avec le langage. ({count}/{max})",
    "Hé dude {user}, on garde ça propre, ouais ? ({count}/{max})",
    "Mec {user}, pas cool. Attention aux mots. ({count}/{max})",
    "Allez {user}, facile champion. Pas besoin de ça. ({count}/{max})",
    "Duuude {user}, vraiment ? On parle pas comme ça ici. ({count}/{max})",
    "Mon pote {user}, t'es mieux que ça. Baisse le ton. ({count}/{max})",
    "Mec {user}, c'est non de ma part dawg. ({count}/{max})",
    "Attends {user}, langage mec ! Soyons chill. ({count}/{max})",
    "Nah fam {user}, pas dans ce serveur. Garde ça PG. ({count}/{max})",
    "Yo {user}, relax dude. On est bien sans les jurons. ({count}/{max})",
    "Bruh {user}... sérieusement ? Allez mec. ({count}/{max})",
    "Facile {user}, évitons le mode marin. ({count}/{max})",
    "Hé ami {user}, attention au langage ? Merci mec. ({count}/{max})"
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
    # Detect if any bad word is in the message
    detected_words = [word for word in bad_words if word in content_lower]
    if detected_words:
        # Determine if it's French by checking if any detected word is typically French
        french_words = set([
            "mince", "putain", "merde", "sa mère", "con", "conne", "ducon", "connard", "connasse",
            "enculé", "enculée", "bordel", "bâtard", "bâtarde", "enfoiré", "enfoirée", "poufiasse",
            "pute", "pétasse", "bite", "chatte", "chiant", "chiante", "niquer", "baiser", "dégage",
            "salaud", "salope", "ta gueule", "ferme ta gueule", "sa race", "ta race", "mange tes morts",
            "nique tes morts", "bordel de merde", "putain de bordel de merde", "sa mère la pute",
            "putain de sa mère", "putain de sa mère la pute", "fils de chien", "fils de pute",
            "trou du cul", "casser les couilles", "partir en couilles", "casse-couilles", "s’en ficher",
            "s’en foutre", "s’en battre les couilles", "faire chier", "à chier"
        ])  # Base French words without variations
        is_french = any(any(fw in dw for fw in french_words) for dw in detected_words)
        key = (message.guild.id, message.author.id)
        swear_count[key] = swear_count.get(key, 0) + 1
        count = swear_count[key]
        try:
            await message.delete()
            # Choose warnings based on language
            warnings = FRENCH_WARNINGS if is_french else BRO_WARNINGS
            warning_text = random.choice(warnings).format(
                user=message.author.mention,
                count=count,
                max=MAX_SWEARS
            )
            embed = discord.Embed(
                description=warning_text,
                color=0xffa500
            )
            footer_text = "Continue comme ça et tu auras un timeout, mec." if is_french else "Keep it up and you'll get a timeout, bro."
            embed.set_footer(text=footer_text)
            await send_webhook(message.channel, embed=embed)
            if count >= MAX_SWEARS:
                await message.author.timeout(timedelta(minutes=TIMEOUT_MINUTES), reason="Excessive profanity")
                embed_title = "⛔ Timeout, Mec" if is_french else "⛔ Timeout, Bro"
                embed_desc = f"{message.author.mention} — trop de jurons, mec.\nChillin' en timeout pour **{TIMEOUT_MINUTES} minutes**." if is_french else f"{message.author.mention} — too many swears, dude.\nChillin' in timeout for **{TIMEOUT_MINUTES} minutes**."
                embed = discord.Embed(
                    title=embed_title,
                    description=embed_desc,
                    color=0xff0000
                )
                embed_footer = "Reviens plus propre la prochaine fois." if is_french else "Come back cleaner next time."
                embed.set_footer(text=embed_footer)
                await send_webhook(message.channel, embed=embed)
                swear_count[key] = 0
        except discord.Forbidden:
            embed = discord.Embed(description="Yo, je ne peux pas supprimer les messages ou timeout — donne-moi les perms, mec !" if is_french else "Yo, I can't delete messages or timeout — give me perms, bro!", color=0xff0000)
            await send_webhook(message.channel, embed=embed)
        except Exception as e:
            logger.error(f"Error: {e}")
async def send_paginated_list(channel):
    if not bad_words:
        embed = discord.Embed(description="La liste est vide, mec.", color=0x00ff00)
        await send_webhook(channel, embed=embed)
        return
    pages = []
    current = ""
    page_num = 1
    for word in sorted(bad_words):
        line = f"`{word}`\n"
        if len(current) + len(line) > 1900:
            embed = discord.Embed(title=f"Mots Filtrés — Page {page_num}", description=current, color=0x3498db)
            embed.set_footer(text=f"Total: {len(bad_words)} mots")
            pages.append(embed)
            current = line
            page_num += 1
        else:
            current += line
    if current:
        embed = discord.Embed(title=f"Mots Filtrés — Page {page_num}", description=current, color=0x3498db)
        embed.set_footer(text=f"Total: {len(bad_words)} mots")
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
        embed = discord.Embed(title="Yo, Swear Word Moderator Ici", color=0x9b59b6)
        embed.add_field(name="Commandes Publiques", value="`,help` • `,status` • `,list`", inline=False)
        embed.add_field(name="Admin Seulement", value="`,activate` • `,deactivate` • `,addword <mot>` • `,removeword <mot>`", inline=False)
        embed.set_footer(text="Préfixe: , | J'essaie juste de garder ça chill ici, mec.")
        await send_webhook(message.channel, embed=embed)
    elif cmd == "status":
        status = "Activé ✅" if moderation_active.get(message.guild.id, True) else "Désactivé ❌"
        await send_webhook(message.channel, content=f"La modération est **{status}**, mec.")
    elif cmd == "activate":
        if not is_admin: return await send_webhook(message.channel, content="Nah mec, admins seulement.")
        moderation_active[message.guild.id] = True
        save_data()
        await send_webhook(message.channel, content="✅ Modération activée, dude.")
    elif cmd == "deactivate":
        if not is_admin: return await send_webhook(message.channel, content="Admins seulement, mon pote.")
        moderation_active[message.guild.id] = False
        save_data()
        await send_webhook(message.channel, content="❌ Modération désactivée pour l'instant.")
    elif cmd == "addword" and len(args) > 1:
        if not is_admin: return await send_webhook(message.channel, content="Seuls les admins peuvent faire ça, mec.")
        word = " ".join(args[1:]).lower().strip()
        if not word or len(word) > 100 or any(c in word for c in ['\n', '\r', '\\']):  # Added security: prevent newlines/escapes/long inputs
            return await send_webhook(message.channel, content="Mot invalide (trop long, vide ou contient des caractères spéciaux), mec.")
        if word not in bad_words:
            bad_words.append(word)
            save_data()
            await send_webhook(message.channel, content=f"✅ Ajouté `{word}` à la liste, dude.")
        else:
            await send_webhook(message.channel, content="Déjà là, mec.")
    elif cmd == "removeword" and len(args) > 1:
        if not is_admin: return await send_webhook(message.channel, content="Admins seulement, fam.")
        word = " ".join(args[1:]).lower().strip()
        if not word or len(word) > 100 or any(c in word for c in ['\n', '\r', '\\']):
            return await send_webhook(message.channel, content="Mot invalide (trop long, vide ou contient des caractères spéciaux), mec.")
        if word in bad_words:
            bad_words.remove(word)
            save_data()
            await send_webhook(message.channel, content=f"❌ Supprimé `{word}`, cool.")
        else:
            await send_webhook(message.channel, content="N'était même pas là, mec.")
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

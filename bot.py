import discord
import os
import asyncio
import json
import logging
import random
from dotenv import load_dotenv
from datetime import timedelta, datetime
from aiohttp import web

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chargement du token
load_dotenv()
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("TOKEN non trouvé!")
    exit(1)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
PREFIX = ","

# Fichier de données
DATA_FILE = "bot_data.json"

# Données par défaut avec tous les gros mots français et variantes
default_data = {
    "bad_words": [
        "merde", "m3rde", "m*rd*", "merd3", "m3rd3", "merd",
        "putain", "put@1n", "put1n", "p*tain", "put@in", "putein", "put4in",
        "pute", "put3", "p*t*", "put*",
        "connard", "c0nnard", "conard", "c*nnard", "conn@rd", "konnard",
        "connasse", "c0nnasse", "conasse", "c*nnasse", "conn@ss*",
        "con", "c0n", "c*n",
        "salaud", "sal@ud", "s*laud", "sal0ud",
        "salope", "sal0pe", "s@lope", "s*lop*", "salop3",
        "enculé", "encul3", "3ncul*", "encul@",
        "enculée", "encul33", "3ncul**",
        "bordel", "b0rdel", "b*rdel", "bord3l",
        "cul", "c*l", "ku1",
        "chatte", "ch@tte", "ch*tt*", "chatt3",
        "bite", "b1te", "b*t*", "bit3",
        "couilles", "c0uilles", "c*uill*s", "cou1ll3s",
        "branleur", "br@nl3ur", "br*nl*ur",
        "emmerde", "3mm3rd*", "emm*rd*",
        "chier", "chi3r", "ch1*r",
        "niquer", "n1qu3r", "n*qu*r",
        "baiser", "b@1s3r", "b*is*r",
        "batard", "b@tard", "b*tard", "bat@rd",
        "enfoiré", "3nfoir*", "enf0ir3",
        "pouffiasse", "pouff1@ss*", "p*uffi*ss*",
        "pétasse", "p3t@ss*", "p*tass*",
        "trou du cul", "tr0u du cul", "tr*u d* c*l",
        "fils de pute", "f1ls d* put*", "f*ls de put3",
        "fils de chien", "f1ls d* chi3n",
        "sa mère", "s@ m3r*", "sa m*r*",
        "ta mère", "t@ m3r*", "ta m*r*",
        "nique ta mère", "n1qu* t@ m3r*",
        "ta mère la pute", "t@ m3r* l@ put*",
        "sa mère la pute", "s@ m3r* l@ put*",
        "va te faire foutre", "v@ t* f@ir* f0utr*",
        "va te faire enculer", "v@ t* f@ir* 3ncul*r",
        "ferme ta gueule", "f3rm* t@ gu3ul*",
        "ta gueule", "t@ gu3ul*",
        "casse les couilles", "c@ss* l*s c0uill*s",
        "casse-couilles", "c@ss*-c0uill*s",
        "fait chier", "f@it chi3r",
        "putain de merde", "put@1n d* m3rd*",
        "bordel de merde", "b0rd3l d* m3rd*",
        "putain de bordel de merde", "put@1n d* b0rd3l d* m3rd*",
        "nom de dieu", "n0m d* di3u",
        "ostie", "0sti3", "0st1*",
        "tabarnak", "t@b@rn@k", "tab@rn@k",
        "crisse", "cr1ss*", "cr*ss*",
        "calisse", "c@1iss*", "c*liss*",
        "sacrament", "s@cr@m3nt", "s*cr*m*nt",
        "plotte", "pl0tt*", "pl*tt*",
        "va te crosser", "v@ t* cr0ss*r",
    ],
    "moderation_active": {},
    "swear_counts": {}
}

# Chargement/sauvegarde des données
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    logger.warning("bot_data.json vide")
                    return default_data.copy()
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Erreur de chargement: {e}")
    return default_data.copy()

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "bad_words": bad_words,
                "moderation_active": moderation_active,
                "swear_counts": swear_count
            }, f, indent=2)
        logger.info("Données sauvegardées")
    except Exception as e:
        logger.error(f"Échec de sauvegarde: {e}")

data = load_data()
bad_words = [word.lower().replace(" ", "") for word in data.get("bad_words", default_data["bad_words"])]
moderation_active = data.get("moderation_active", {})
swear_count = data.get("swear_counts", {})

partial_swears = {}

MAX_SWEARS = 5
TIMEOUT_MINUTES = 5
PARTIAL_TIMEOUT = 30

# Avertissements aléatoires en style amical
BRO_WARNINGS = [
    "Yo {user}, allez bro, calme-toi avec le langage. ({count}/{max})",
    "Hey dude {user}, on garde ça propre, ouais? ({count}/{max})",
    "Bro {user}, pas cool mec. Attention aux mots. ({count}/{max})",
    "Aye {user}, facile champion. Pas besoin de ça. ({count}/{max})",
    "Duuude {user}, vraiment? On parle pas comme ça ici. ({count}/{max})",
    "Mon gars {user}, tu vaux mieux que ça. Baisse le ton. ({count}/{max})",
    "Bro {user}, c'est non pour moi dawg. ({count}/{max})",
    "Attends {user}, langage bro! Soyons chill. ({count}/{max})",
    "Nah fam {user}, pas dans ce server. Garde ça PG. ({count}/{max})",
    "Yo {user}, relax dude. On est bien sans les gros mots. ({count}/{max})",
    "Bruh {user}... sérieusement? Allez mec. ({count}/{max})",
    "Facile {user}, évitons le mode marin. ({count}/{max})",
    "Hey friend {user}, attention au langage? Merci bro. ({count}/{max})"
]

# Messages DM aléatoires
DM_MESSAGES = [
    "Hey bro, juste un heads up — j'ai capté un gros mot. On garde ça chill ici. T'es à {count}/{max}.",
    "Yo dude, langage! C'est {count}/{max}. Gardons le server propre.",
    "Mon gars, j'ai dû supprimer ça. Pas de rancune — compte à {count}/{max}.",
    "Bruh, allez — attention. T'es à {count}/{max}. Me force pas à te timeout!",
    "Hey {user}, rappel amical: pas de gros mots. Compte: {count}/{max}. Reste cool."
]

@client.event
async def on_ready():
    logger.info(f'Bot en ligne: {client.user}')
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

    has_text = bool(message.content.strip())
    content_lower = message.content.lower().strip()
    content_no_space = content_lower.replace(" ", "")

    detected = any(word in content_no_space for word in bad_words)

    key = f"{message.guild.id}:{message.author.id}"
    partial_key = (message.guild.id, message.author.id)

    if detected:
        swear_count[key] = swear_count.get(key, 0) + 1
        count = swear_count[key]

        try:
            if has_text:
                await message.delete()

            warning_text = random.choice(BRO_WARNINGS).format(user=message.author.mention, count=count, max=MAX_SWEARS)
            embed = discord.Embed(description=warning_text, color=0xffa500)
            embed.set_footer(text="Continue et timeout incoming, bro.")
            await message.channel.send(embed=embed)

            dm_text = random.choice(DM_MESSAGES).format(user=message.author.display_name, count=count, max=MAX_SWEARS)
            try:
                dm_embed = discord.Embed(title="Yo, heads up bro...", description=dm_text, color=0xffa500)
                dm_embed.set_footer(text="Just keeping the server chill 😎")
                await message.author.send(embed=dm_embed)
            except:
                pass

            if count >= MAX_SWEARS:
                await message.author.timeout(timedelta(minutes=TIMEOUT_MINUTES), reason="Trop de gros mots")
                timeout_embed = discord.Embed(
                    title="⛔ Timeout, Bro",
                    description=f"{message.author.mention} — trop de gros mots, dude.\nTimeout pour **{TIMEOUT_MINUTES} minutes**.",
                    color=0xff0000
                )
                await message.channel.send(embed=timeout_embed)
                del swear_count[key]

            save_data()

        except discord.Forbidden:
            await message.channel.send("Yo bro, j'ai besoin des permissions 'Gérer les messages' et 'Modérer les membres'!")
        except Exception as e:
            logger.error(f"Erreur: {e}")

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
                    if has_text:
                        await message.delete()
                    await message.channel.send(f"{message.author.mention} Nice try to split it, bro — still counts! 😏")
                    swear_count[key] = swear_count.get(key, 0) + 1
                    count = swear_count[key]
                    embed = discord.Embed(description=f"Split swear detected! Count: {count}/{MAX_SWEARS}", color=0xffa500)
                    await message.channel.send(embed=embed)
                    save_data()
                else:
                    partial_swears[partial_key] = partial
        elif len(content_no_space) <= 4 and any(content_no_space in word for word in bad_words):
            partial_swears[partial_key] = {"current": content_no_space, "last_time": current_time}

async def send_paginated_list(channel):
    if not bad_words:
        await channel.send("La liste est vide, bro.")
        return

    pages = []
    current = ""
    page_num = 1

    for word in sorted(bad_words):
        line = f"`{word}`\n"
        if len(current) + len(line) > 1900:
            await channel.send(current)
            current = line
            page_num += 1
        else:
            current += line

    if current:
        await channel.send(current)

async def handle_command(message):
    args = message.content[len(PREFIX):].strip().split()
    if not args:
        return
    cmd = args[0].lower()

    perms = message.author.guild_permissions
    is_admin = perms.administrator or perms.manage_guild

    if cmd == "help":
        embed = discord.Embed(title="Yo, Modérateur de Gros Mots Ici", color=0x9b59b6)
        embed.add_field(name="Commandes Publiques", value="`,help` • `,status` • `,list`", inline=False)
        embed.add_field(name="Admin Seulement", value="`,activate` • `,deactivate` • `,addword <mot>` • `,removeword <mot>`", inline=False)
        embed.set_footer(text="Préfixe: , | Je garde ça chill ici, bro 😎")
        await message.channel.send(embed=embed)

    elif cmd == "status":
        status = "Activé ✅" if moderation_active.get(message.guild.id, True) else "Désactivé ❌"
        await message.channel.send(f"La modération est **{status}**, bro.")

    elif cmd == "activate":
        if not is_admin:
            await message.channel.send("Nah bro, admins seulement.")
            return
        moderation_active[message.guild.id] = True
        save_data()
        await message.channel.send("✅ Modération activée, dude.")

    elif cmd == "deactivate":
        if not is_admin:
            await message.channel.send("Admins seulement, my guy.")
            return
        moderation_active[message.guild.id] = False
        save_data()
        await message.channel.send("❌ Modération désactivée.")

    elif cmd == "addword" and len(args) > 1:
        if not is_admin:
            await message.channel.send("Seulement les admins, bro.")
            return
        word = " ".join(args[1:]).lower()
        if word not in bad_words:
            bad_words.append(word)
            save_data()
            await message.channel.send(f"✅ Ajouté `{word}`, dude.")
        else:
            await message.channel.send("Déjà dans la liste, bro.")

    elif cmd == "removeword" and len(args) > 1:
        if not is_admin:
            await message.channel.send("Admins seulement, fam.")
            return
        word = " ".join(args[1:]).lower()
        if word in bad_words:
            bad_words.remove(word)
            save_data()
            await message.channel.send(f"❌ Retiré `{word}`, cool.")
        else:
            await message.channel.send("Pas dans la liste, bro.")

    elif cmd in ["list", "listwords"]:
        await send_paginated_list(message.channel)

async def health(request):
    return web.Response(text="Bot is alive, bro!")

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

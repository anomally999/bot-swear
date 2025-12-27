import discord
from discord.ext import commands
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# File to store swear words
SWEAR_FILE = 'swear_words.json'

# Initial list of French swear words (lowercase)
initial_swears = [
    "merde", "putain", "bordel", "con", "connard", "salope", "enfoiré",
    "foutre", "bite", "cul", "fils de pute", "ta gueule", "nique", "enculé",
    "salopard", "pétasse", "couillon", "abruti", "chiant", "dégage",
    "casse-toi", "va te faire foutre", "putain de merde", "bordel de merde"
]

# Load swear words from file or initialize
def load_swears():
    if os.path.exists(SWEAR_FILE):
        with open(SWEAR_FILE, 'r') as f:
            return set(json.load(f))
    else:
        return set(word.lower() for word in initial_swears)

# Save swear words to file
def save_swears(swears):
    with open(SWEAR_FILE, 'w') as f:
        json.dump(list(swears), f)

# Bot setup
bot = commands.Bot(command_prefix=',', intents=discord.Intents.default())
bot.remove_command('help')  # Optional: remove default help

swear_words = load_swears()

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logging.info('------')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check for swear words
    msg_lower = message.content.lower()
    if any(swear in msg_lower for swear in swear_words):
        try:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, veuillez éviter les gros mots ! (Message supprimé)")
        except discord.Forbidden:
            logging.warning("Bot lacks permission to delete messages.")

    # Process commands
    await bot.process_commands(message)

# Owner check
def is_owner():
    async def predicate(ctx):
        return await bot.is_owner(ctx.author)
    return commands.check(predicate)

@bot.command(name='add_word', help='Ajoute un mot grossier (propriétaire seulement)')
@is_owner()
async def add_word(ctx, *, word: str):
    word_lower = word.lower()
    if word_lower in swear_words:
        await ctx.send(f"Le mot '{word}' est déjà dans la liste.")
    else:
        swear_words.add(word_lower)
        save_swears(swear_words)
        await ctx.send(f"Le mot '{word}' a été ajouté à la liste des gros mots.")

@bot.command(name='remove_word', help='Supprime un mot grossier (propriétaire seulement)')
@is_owner()
async def remove_word(ctx, *, word: str):
    word_lower = word.lower()
    if word_lower in swear_words:
        swear_words.remove(word_lower)
        save_swears(swear_words)
        await ctx.send(f"Le mot '{word}' a été supprimé de la liste des gros mots.")
    else:
        await ctx.send(f"Le mot '{word}' n'est pas dans la liste.")

@bot.command(name='list_words', help='Liste les mots grossiers (propriétaire seulement)')
@is_owner()
async def list_words(ctx):
    if not swear_words:
        await ctx.send("La liste des gros mots est vide.")
    else:
        words_list = ', '.join(sorted(swear_words))
        await ctx.send(f"Liste des gros mots : {words_list}")

@bot.command(name='status', help='Affiche le statut du bot')
async def status(ctx):
    await ctx.send(f"Le bot est en ligne ! Nombre de gros mots surveillés : {len(swear_words)}")

@bot.command(name='clear_words', help='Efface tous les mots grossiers (propriétaire seulement)')
@is_owner()
async def clear_words(ctx):
    swear_words.clear()
    save_swears(swear_words)
    await ctx.send("La liste des gros mots a été effacée.")

@bot.command(name='help', help='Affiche l\'aide')
async def help_command(ctx):
    help_text = """
Commandes disponibles :
- ,add_word <mot> : Ajoute un mot (propriétaire)
- ,remove_word <mot> : Supprime un mot (propriétaire)
- ,list_words : Liste les mots (propriétaire)
- ,clear_words : Efface tous les mots (propriétaire)
- ,status : Statut du bot
- ,help : Cette aide
"""
    await ctx.send(help_text)

# Run the bot
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set.")

bot.run(DISCORD_TOKEN)

import discord
import random
import asyncio
import math
import time
from discord.ext import commands
from threading import Thread
from pymongo import MongoClient

TOKEN = ""

intents = discord.Intents.all()
intents.messages = True

client = MongoClient("mongodb+srv://hanyangzhou:bFWwgIC9glFPa6GL@cluster0.4wffiju.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

bot = commands.Bot(command_prefix=lambda bot, message: "!", intents=intents, help_command=None)

configuration = {
    "mutations": {},
    "rarity_weights": {
        "Common": 55,
        "Uncommon": 20,
        "Rare": 12,
        "Epic": 8,
        "Legendary": 3,
        "Mythical": 1.5,
        "Secret": 0.5
    },
    "fishes": {
        "Common": {
            "Largemouth Bass": {"value": 12, "weight_range": (1.4, 2.6)},
            "Smallmouth Bass": {"value": 14, "weight_range": (1.1, 2.2)},
            "Salmon": {"value": 9, "weight_range": (2.7, 4.7)},
            "Cod": {"value": 5, "weight_range": (4.0, 6.6)},
            "Tuna": {"value": 3, "weight_range": (10.1, 20.1)},
            "Carp": {"value": 8, "weight_range": (2.2, 5.1)},
            "Perch": {"value": 21, "weight_range": (0.4, 0.9)},
            "Flounder": {"value": 9, "weight_range": (1.2, 3.6)},
            "Anchovy": {"value": 46, "weight_range": (0.1, 0.3)},
            "Sardine": {"value": 35, "weight_range": (0.2, 0.5)},
            "Mackerel": {"value": 9, "weight_range": (1.3, 2.9)}
        },
        "Rare": {
            "Pike": {"value": 8, "weight_range": (4.8, 7.6)},
            "Red Snapper": {"value": 12, "weight_range": (2.6, 4.4)},
            "Barracuda": {"value": 10, "weight_range": (3.9, 5.7)},
            "Sea Trout": {"value": 14, "weight_range": (2.1, 3.6)},
            "Tilapia": {"value": 17, "weight_range": (1.8, 3.2)},
            "Bluefish": {"value": 13, "weight_range": (2.3, 4.1)},
            "Walleye": {"value": 12, "weight_range": (2.2, 4.7)},
            "Catfish": {"value": 6, "weight_range": (5.6, 9.4)},
            "Rockfish": {"value": 11, "weight_range": (2.5, 5.3)},
            "Grouper": {"value": 6, "weight_range": (6.5, 10.4)}
        },
        "Epic": {
            "Swordfish": {"value": 3, "weight_range": (20.5, 40.0)},
            "Sturgeon": {"value": 4, "weight_range": (17.5, 29.5)},
            "Halibut": {"value": 4, "weight_range": (14.0, 24.0)},
            "Paddlefish": {"value": 3, "weight_range": (20.0, 40.0)},
            "Giant Trevally": {"value": 6, "weight_range": (8.0, 14.0)},
            "Tarpon": {"value": 4, "weight_range": (12.0, 20.0)},
            "Amberjack": {"value": 5, "weight_range": (10.0, 16.0)},
            "Opah": {"value": 3, "weight_range": (21.5, 40.0)},
            "Mahi-Mahi": {"value": 6, "weight_range": (8.0, 15.0)},
            "Arctic Char": {"value": 8, "weight_range": (5.5, 9.5)}
        },
        "Legendary": {
            "Great White Shark": {"value": 0.4, "weight_range": (450.0, 1150.0)},
            "Blue Marlin": {"value": 0.9, "weight_range": (150.0, 650.0)},
            "Colossal Squid": {"value": 1.5, "weight_range": (200.0, 450.0)},
            "Goliath Grouper": {"value": 1.1, "weight_range": (150.0, 400.0)},
            "Sailfish": {"value": 2.4, "weight_range": (85.0, 120.0)},
            "Beluga Sturgeon": {"value": 0.6, "weight_range": (300.0, 650.0)},
            "Oarfish": {"value": 0.8, "weight_range": (200.0, 500.0)},
            "Ocean Sunfish": {"value": 0.6, "weight_range": (250.0, 800.0)},
            "Mako Shark": {"value": 1.2, "weight_range": (200.0, 500.0)},
            "Thresher Shark": {"value": 1.4, "weight_range": (150.0, 350.0)}
        },
        "Mythical": {
            "Megalodon": {"value": 0.8, "weight_range": (15000.0, 35000.0)},
            "Orca": {"value": 2.6, "weight_range": (3000.0, 6000.0)},
            "Kraken": {"value": 0.7, "weight_range": (15000.0, 30000.0)},
            "Leviathan": {"value": 1.4, "weight_range": (8000.0, 20000.0)},
            "Narwhal": {"value": 20, "weight_range": (800.0, 1600.0)},
            "Sea Dragon": {"value": 2.1, "weight_range": (5000.0, 12000.0)}
        },
        "Secret": {
            "Shadow Serpent": {"value": 5.5, "weight_range": (8000.0, 20000.0)}
        }
    }
}

@bot.event
async def on_ready():
    guild = discord.Object(id=1292978415552434196)
    try:
        synced = await bot.tree.sync()
    except Exception as e:
        pass

@bot.event
async def on_disconnect():
    print("Bot disconnected. Attempting to reconnect in 5 seconds...")
    await asyncio.sleep(5)

@bot.event
async def on_resumed():
    print("Bot reconnected!")

@bot.command(help="Make the bot say something.", aliases=["s"])
async def say(ctx, *, text: str = ""):
    if text:
        await ctx.message.delete()
        await ctx.send(embed=discord.Embed(
            description=text,
            color=int("50B4E6", 16)
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@bot.command(help="Catch a fish!", aliases=[])
async def fish(ctx):
    rarities = configuration["rarity_weights"];
    chosen_rarity = random.choices(list(rarities.keys()), weights=list(rarities.values()), k=1)[0]

    fish_pool = list(fishes.get(chosen_rarity, {}).items())
    if not fish_pool:
        return

    fish_name, fish_data = random.choice(fish_pool)

    min_w, max_w = fish_data["weight_range"]
    weight = round(random.uniform(min_w, max_w), 1)
    price = round(fish_data["value"] * weight, 2)

    embed = discord.Embed(
        description=f"🎣 You caught a **{fish_name}** ({chosen_rarity})!\n"
                    f"💪 Weight: `{weight} kg`\n"
                    f"💰 Value: `${price}`",
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)
    
bot.run(TOKEN)

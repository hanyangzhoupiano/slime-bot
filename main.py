import discord
import random
import asyncio
from discord.ext import commands, tasks
from pymongo import MongoClient
from groq import Groq
import time

TOKEN = ""
URL = ""
API_KEY = ""

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

groq_client = Groq(api_key=API_KEY)
client = MongoClient(URL)
db = client["fishing_bot"]
users_collection = db["users"]

user_cache = {}
messages = [
    {"role": "system", "content": "You are a helpful assistant named 'Slime Bot' that loves fishing."}
]

configuration = {
    "base_weights": {
        "Common": 55,
        "Rare": 25,
        "Epic": 12,
        "Legendary": 6,
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
            "Megalodon": {"value": 1.2, "weight_range": (15000.0, 35000.0)},
            "Orca": {"value": 3, "weight_range": (3000.0, 6000.0)},
            "Kraken": {"value": 1.1, "weight_range": (15000.0, 30000.0)},
            "Leviathan": {"value": 1.8, "weight_range": (8000.0, 20000.0)}
        },
        "Secret": {
            "Shadow Serpent": {"value": 5.5, "weight_range": (8000.0, 20000.0)}
        }
    }
}

# Helper Functions

def load_user(user_id):
    if user_id in user_cache:
        return user_cache[user_id]
    user = users_collection.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "money": 0, "inventory": []}
        users_collection.insert_one(user)
    user_cache[user_id] = user
    return user

def save_user(user_id):
    if user_id in user_cache:
        users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "money": user_cache[user_id]["money"],
                "inventory": user_cache[user_id]["inventory"]
            }},
            upsert=True
        )

@tasks.loop(seconds=30)
async def periodic_save():
    for user_id in list(user_cache.keys()):
        save_user(user_id)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    periodic_save.start()

@bot.command(help="Catch a fish!")
async def fish(ctx):
    user_id = ctx.author.id
    user = load_user(user_id)

    rarity = random.choices(
        list(configuration["base_weights"].keys()),
        weights=list(configuration["base_weights"].values()),
        k=1
    )[0]

    fish_name, fish_data = random.choice(list(configuration["fishes"][rarity].items()))
    weight = round(random.uniform(*fish_data["weight_range"]), 1)
    value = round(fish_data["value"] * weight)

    fish_obj = {
        "name": fish_name,
        "weight": weight,
        "value": value,
        "rarity": rarity,
        "mutations": []
    }

    user["inventory"].append(fish_obj)

    embed = discord.Embed(
        description=f"🎣 You caught a **{fish_name}** ({rarity}) at {weight}kg!",
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.command(help="Clear chat history with Slime Bot!")
async def clear(ctx):
    global messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant named 'Slime Bot' that loves fishing."}
    ]

    await ctx.send(embed = discord.Embed(
        description="✅ Successfully cleared chat history.",
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@bot.command(help="Chat with Slime Bot!")
async def chat(ctx, message: str):
    messages.append({"role": "user", "content": message})

    response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False
    )
    reply = response.choices[0].message.content

    messages.append({"role": "assistant", "content": reply})

    await ctx.send(embed = discord.Embed(
        description=reply,
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@bot.command(help="Sell your fish!")
async def sell(ctx):
    user_id = ctx.author.id
    user = load_user(user_id)

    if not user["inventory"]:
        await ctx.send(embed=discord.Embed(
            description="❌ You have no fish to sell!",
            color=int("FA3939", 16)
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        return

    total = sum(f["value"] for f in user["inventory"])
    user["money"] += total
    user["inventory"] = []

    embed = discord.Embed(
        description=f"💰 You sold your fish for {total} coins!",
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.command(help="Check your or another user's balance!")
async def balance(ctx, name: str = None):
    target_member = None

    if name:
        matching_members = [
            member for member in ctx.guild.members
            if name.lower() in member.name.lower() and not member.bot
        ]

        if not matching_members:
            await ctx.send(embed=discord.Embed(
                description="❌ No matching users found.",
                color=int("FA3939", 16)
            ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
            return

        if len(matching_members) == 1:
            target_member = matching_members[0]
        else:
            options = "\n".join(f"{i+1}. {m.name}" for i, m in enumerate(matching_members))
            await ctx.send(embed=discord.Embed(
                description=f"🔍 Multiple users found. Type the number to select, or `cancel`:\n{options}",
                color=int("50B4E6", 16)
            ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

            try:
                response = await bot.wait_for(
                    "message",
                    check=lambda msg: msg.author == ctx.author and msg.channel == ctx.channel,
                    timeout=15.0
                )
                if response.content.lower() == "cancel":
                    await ctx.send(embed=discord.Embed(
                        description="❌ The command has been canceled.",
                        color=int("FA3939", 16)
                    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                    return

                index = int(response.content) - 1
                if 0 <= index < len(matching_members):
                    target_member = matching_members[index]
                else:
                    await ctx.send(embed=discord.Embed(
                        description="❌ Invalid selection.",
                        color=int("FA3939", 16)
                    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

            except (asyncio.TimeoutError, ValueError):
                await ctx.send(embed=discord.Embed(
                    description="⏳ The command has been canceled because you took too long to reply.",
                    color=int("FA3939", 16)
                ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                return
    else:
        target_member = ctx.author

    user_data = load_user(target_member.id)
    await ctx.send(embed=discord.Embed(
        description=f"💵 **{target_member.name}** has {user_data['money']} coins.",
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@bot.command(help="Check your inventory!")
async def inventory(ctx):
    user = load_user(ctx.author.id)
    if not user["inventory"]:
        await ctx.send(embed=discord.Embed(
            description="🎒 Your inventory is empty!",
            color=int("50B4E6", 16)
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        return

    lines = [f"• **{f['name']}** ({f['rarity']}) - {f['weight']}kg, Value: {f['value']}" for f in user["inventory"]]
    await ctx.send(embed=discord.Embed(
        title="🎒 Your Inventory",
        description="\n".join(lines),
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@bot.command(help="Force save your data to the database.")
async def save(ctx):
    save_user(ctx.author.id)
    await ctx.send(embed=discord.Embed(
        description="✅ Your data has been saved to the database. Note: data autosaves every 30 seconds",
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

bot.run(TOKEN)

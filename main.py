import discord
import random
import asyncio
from discord.ext import commands, tasks
from pymongo import MongoClient
import time

TOKEN = ""
URL = ""

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

client = MongoClient(URL)
db = client["fishing_bot"]
users_collection = db["users"]

user_cache = {}

configuration = {
    "rarity_weights": {
        "Common": 70,
        "Rare": 30
    },
    "fishes": {
        "Common": {
            "Salmon": {"value": 10, "weight_range": (2.0, 4.0)}
        },
        "Rare": {
            "Pike": {"value": 20, "weight_range": (4.0, 6.0)}
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
        list(configuration["rarity_weights"].keys()),
        weights=list(configuration["rarity_weights"].values()),
        k=1
    )[0]

    fish_name, fish_data = random.choice(list(configuration["fishes"][rarity].items()))
    weight = round(random.uniform(*fish_data["weight_range"]), 1)
    value = round(fish_data["value"] * weight)

    fish_obj = {
        "name": fish_name,
        "weight": weight,
        "value": value,
        "rarity": rarity
    }

    user["inventory"].append(fish_obj)

    embed = discord.Embed(
        description=f"🎣 You caught a **{fish_name}** ({rarity}) at {weight}kg!",
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

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
async def balance(ctx, user: str = None):
    if name is not None:
        matching_names = []
        for member in ctx.guild.members:
            if name.lower() in member.name.lower() and not member.bot:
                matching_names.append(member.name)
        if matching_names:
            if len(matching_names) > 1:
                msg = ""
                for i, n in enumerate(matching_names):
                    msg += str(i + 1) + ". " + n
                    if i != len(matching_names) - 1:
                        msg += "\n"
                try:
                    await ctx.send(embed=discord.Embed(
                        color=int("50B4E6", 16),
                        description=f"Mutiple users found. Please select a user below, or type cancel:\n{msg}"
                    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

                    selection = None
                    response = await bot.wait_for('message', check=lambda msg: msg.channel == ctx.channel and msg.author == ctx.author, timeout=10.0)

                    if "cancel" in response.content.lower():
                        await ctx.send(embed=discord.Embed(
                            color=int("FA3939", 16),
                            description="❌ The command has been canceled."
                        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                        return
                    try:
                        selection = int(response.content)
                    except ValueError:
                        await ctx.send(embed=discord.Embed(
                            color=int("FA3939", 16),
                            description="❌ Invalid selection."
                        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                        return
                    else:
                        if selection is not None:
                            if (selection - 1) >= 0 and (selection - 1) <= (len(matching_names) - 1):
                                matching_name = matching_names[selection - 1]
                                for member in ctx.guild.members:
                                    if member.name.lower() == matching_name.lower():
                                        user = load_user(member.id)
                                        await ctx.send(embed=discord.Embed(
                                            description=f"💵 {member.name} has {user['money']} coins.",
                                            color=int("50B4E6", 16)
                                        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                                        break
                            else:
                                await ctx.send(embed=discord.Embed(
                                    color=int("FA3939", 16),
                                    description="❌ Invalid selection."
                                ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                                return
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(
                        color=int("FA3939", 16),
                        description="⏳ The command has been canceled because you took too long to reply."
                    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                    return
            else:
                for member in ctx.guild.members:
                    if member.name.lower() == matching_names[0].lower():
                        user = load_user(member.id)
                        break
        else:
            user = load_user(ctx.author.id)
            await ctx.send(embed=discord.Embed(
                description=f"💵 You have {user['money']} coins.",
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

    lines = [f"• **{f['name']}** ({f['rarity']}) - {f['weight']}kg, 💰 {f['value']}" for f in user["inventory"]]
    await ctx.send(embed=discord.Embed(
        title="🎒 Your Inventory",
        description="\n".join(lines[:10]),
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

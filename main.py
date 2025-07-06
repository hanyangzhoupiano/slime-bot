import os
import sys
import discord
import json
import random
import asyncio
import math
import time
import datetime
import pytz
from discord.ext import commands

from threading import Thread

warnings = {}

TIME_ZONE = "US/Eastern"
TOKEN = ""

intents = discord.Intents.all()
intents.messages = True

bot = commands.Bot(command_prefix=lambda bot, message: "!", intents=intents, help_command=None)

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
    await ctx.send(embed=discord.Embed(
        description="fish",
        color=int("50B4E6", 16)
    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

bot.run(TOKEN)

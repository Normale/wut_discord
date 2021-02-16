import os
import random

import discord
from discord.member import Member

from config import TOKEN

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')
    guild = client.get_guild(508018083311517717)
    user = client.get_user(353235384395628567)
    await user.send("first")
    async for member in guild.fetch_members():
        print(member.name, member.id, member.bot)
        if member.bot: continue
        await member.send("second")

@client.event
async def on_member_join(member):
    await member.send("Welcome!")


@client.event
async def on_message(message):
    print("On_message triggered")
    if message.author == client.user:
        return
    print(repr(message.author))

    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]

    if message.content == '99!':
        response = random.choice(brooklyn_99_quotes)
        await message.channel.send(response)
    elif message.content == 'raise-exception':
        raise discord.DiscordException

client.run(TOKEN)
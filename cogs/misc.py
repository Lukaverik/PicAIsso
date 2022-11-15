import disnake
from disnake.ext import commands

import emotes
from aiba import aiba


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Sends a friendly greeting")
    async def greet(self, inter):
        await inter.response.send_message("Hi, there! :wave:")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author == self.bot.user:
            return

        if self.bot.user in message.mentions and "hello" in message.content.lower():
            await message.add_reaction(emotes.wave)
            await message.channel.send("Hi, there!")

from datetime import datetime

import disnake
from disnake.ext import commands

import emotes
import util
from util import Interaction


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Sends a friendly greeting")
    async def greet(self, inter: Interaction):
        await inter.response.send_message("Hi, there! :wave:")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author == self.bot.user:
            return

        if self.bot.user in message.mentions:
            if "hello" in message.content.lower():
                await message.add_reaction(emotes.wave)
                await message.channel.send("Hi, there!")
            if "good girl" in message.content.lower():
                await message.add_reaction(emotes.flushed)

    @commands.slash_command(
        name="patch_notes",
        description="Provides a description of the most recent changes to Aiba!",
    )
    async def patch_notes(self, inter: Interaction):
        embed = disnake.Embed(
            title="Aiba Patch Notes",
            timestamp=datetime.now(),
        )
        embed.add_field(name="Last Update", value="December 16th, 2022")
        embed.description = " - Restructured system framework, backend is more stable and streamlined now."
        embed.description += (
            "\n - Added and currently testing out a scoring sytem for requests."
        )
        embed.description += "\n - Prompts are now automatically cleaned (bad tags, those with weights higher than 1.75, are removed)"
        embed.description += "\n - The tags `(masterpiece: 1.5)` and `(best quality: 1.5)` are now invisibily added to prompts by default."
        embed.description += "\n\tThis can be configured on the server level, but currently no command exists to do so. Ask Luka if you want this changed for any reason."
        embed.description += "\n - Added logging for guilds, users, and requests in a more accessible way in preparation for planned features."
        embed.description += "\n - Other minor bug fixes and improvements."
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="pause")
    async def pause(self, inter: Interaction):
        if inter.author.id == 189101288083030017:
            util.paused = True
        await inter.response.send_message("Aiba is now paused.", ephemeral=True)

    @commands.slash_command(name="unpause")
    async def unpause(self, inter: Interaction):
        if inter.author.id == 189101288083030017:
            util.paused = False
        await inter.response.send_message("Aiba is now unpaused.", ephemeral=True)

from datetime import datetime

import disnake
from disnake.ext import commands

import emotes
from api import sorted_stats


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

    @commands.slash_command(name="top", description="Provides a list of the 10 people who have used the bot the most")
    async def top_users(self, inter):
        data = await sorted_stats(guild=str(inter.guild_id))
        embed = disnake.Embed(
            title="Most Frequent Users",
            timestamp=datetime.now(),
        )
        top_users = list(data.keys())[:10]
        for index, user in enumerate(top_users, 1):
            embed.add_field(name=index, value=f"{user}: {data[user]}", inline=False)
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="usage", description="Provides stats on the user, or on a given user")
    async def usage(self, inter, username=None):
        data = await sorted_stats(guild=str(inter.guild_id))
        if username:
            if username in list(data.keys()):
                field_val = f"{username} has used Aiba {data[username]} times."
            else:
                field_val = f"{username} has not used Aiba."
        else:
            if inter.author.name in list(data.keys()):
                field_val = f"You have used Aiba {data[inter.author.name]} times."
            else:
                field_val = "You have not used Aiba."
        embed = disnake.Embed(title=field_val, timestamp=datetime.now())
        await inter.response.send_message(embed=embed)
from disnake.ext import commands

from models.embed import Field, EmbedBuilder
from models.guild import Guild
from models.user import User
from util import Interaction


class Records(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="top",
        description="Provides a list of the 10 people who have used the bot the most in this server.",
        dm_permission=False,
    )
    async def top_users(self, inter: Interaction):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        # Dictionaries don't preserve order!!
        # Get all users in guild as a pair of ids and runs
        data_list = [
            {"id": key, "runs": stats.requests} for key, stats in guild.users.items()
        ]
        # Sort them by runs, and grab the top 10
        top = [
            datum for datum in sorted(data_list, key=lambda x: x["runs"], reverse=True)
        ][:10]
        # Make a formatter string to represent the field value in the response embed
        fields = [
            f"{User.construct_mention(datum['id'])}: {datum['runs']} requests"
            for datum in top
        ]
        builder = EmbedBuilder(
            title=f"Most Frequent Aiba Users in {guild.name}",
            # Grab those formatted strings
            fields=[
                Field(name=index, value=field, inline=False)
                for index, field in enumerate(fields, 1)
            ],
        )
        await inter.response.send_message(embed=await builder.build())

    @commands.slash_command(
        name="usage",
        description="Provides stats on the user, or on a given user",
        dm_permission=False,
    )
    async def usage(self, inter: Interaction, username=None):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        if username is not None:
            if user := await User.find_by_username(username=username):
                if user.discord_id in guild.users.keys():
                    field_val = f"{username} has used Aiba {guild.users[user.discord_id].requests} times."
                else:
                    field_val = f"{username} has not used Aiba in this server."
            else:
                field_val = f"{username} has not used Aiba."
        else:
            if user := await User.find_or_create(disnake_user=inter.author):
                if user.discord_id in guild.users.keys():
                    field_val = f"You have used Aiba {guild.users[user.discord_id].requests} times."
                else:
                    field_val = f"You have not used Aiba in this server."
            else:
                field_val = f"You have not used Aiba."
        builder = EmbedBuilder(title=field_val)
        await inter.response.send_message(embed=await builder.build())


#
# #safdjshdbfjk
#     @commands.user_command(
#         name="req"
#     )

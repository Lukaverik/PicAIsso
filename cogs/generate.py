import disnake
from disnake.ext import commands

from api import generate


class Generate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Generate an AIArt image according to the given prompt")
    async def generate(self, inter, prompt: str):
        await inter.response.send_message(f"Processing `{prompt}` from {inter.author.mention}")
        try:
            embed = await generate(prompt=prompt, requestor=inter.author)
            await inter.followup.send(embed=embed)
        except ValueError as e:
            await inter.followup.send(e)

        # (f"Here's what I generated for the prompt `{prompt}`!", files=images)


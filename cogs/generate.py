import disnake
from disnake.ext import commands

from api import generate


class Generate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Generate an AIArt image according to the given prompt")
    async def generate(self, inter: disnake.ApplicationCommandInteraction, prompt: str):
        await inter.response.send_message(f"Processing `{prompt}`, requested by {inter.author.mention}")
        await generate(inter=inter, prompt=prompt, requestor=inter.author)

    @commands.message_command(description="Generate an AIArt image with this message as a prompt")
    async def artify(self, inter: disnake.ApplicationCommandInteraction):
        prompt = inter.target.content
        await inter.response.send_message(
            f"Processing `{prompt}`, requested by {inter.author.mention}, original message by {inter.target.author.mention}"
        )
        await generate(inter=inter, prompt=prompt, requestor=inter.author)

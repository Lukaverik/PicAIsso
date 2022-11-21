import disnake
from disnake.ext import commands

from api import generate, record, resolve_queue_pos


class Generate(commands.Cog):
    queue_length = 0
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Generate an AIArt image according to the given prompt")
    async def generate(self, inter: disnake.ApplicationCommandInteraction, prompt: str):
        """
        Generate an AIArt image according to the given prompt

        Parameters
        ----------
        prompt: The prompt to send to the AI
        """
        self.queue_length += 1
        await record(guild=str(inter.guild_id), user=inter.author)
        await inter.response.send_message(f"Processing `{prompt}`, requested by {inter.author.mention}. {resolve_queue_pos(queue_length=self.queue_length)}")
        await generate(inter=inter, prompt=prompt, requestor=inter.author)
        self.queue_length -= 1

    @commands.message_command(name="Artify", description="Generate an AIArt image with this message as a prompt")
    async def artify(self, inter: disnake.ApplicationCommandInteraction):
        self.queue_length += 1
        prompt = inter.target.content
        await record(guild=str(inter.guild_id), user=inter.author)
        await inter.response.send_message(
            f"Processing `{prompt}`, requested by {inter.author.mention}, original message by {inter.target.author.mention}. {resolve_queue_pos(queue_length=self.queue_length)}"
        )
        await generate(inter=inter, prompt=prompt, requestor=inter.author)
        self.queue_length -= 1

from datetime import datetime

import disnake
from disnake.ext import commands

from api import generate, record, resolve_queue_pos
from settings import SettingsCache


class Generate(commands.Cog):
    queue_length = 0
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Generate an AIArt image according to the given prompt")
    async def generate(
            self,
            inter: disnake.ApplicationCommandInteraction,
            prompt: str,
            cfg_scale: commands.Range[1, 30.0] = None,
            sample_steps: commands.Range[1, 150] = None,
    ):
        """
        Generate an AIArt image according to the given prompt

        Parameters
        ----------
        prompt - string: The prompt to send to the AI
        cfg_scale - Optional, float, 1-30: Your server may not allow you to specify this. "Classifier-Free Guidance", how much the AI sticks to the prompt. Low = Higher quality, far from prompt. High = Lower quality, close to prompt
        sample_steps - Optional, int, 1-150: Your server may not allow you to specify this. The number of iterations the AI uses to process the image. Higher = More time to process, higher quality.
        """
        self.queue_length += 1
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        await record(guild=str(inter.guild_id), user=inter.author)
        embed = disnake.Embed(
            title="Prompt Recieved",
            description=f"`{prompt}` by {inter.author.mention}",
            timestamp=datetime.now()
        )
        if not settings.cfg_override and cfg_scale:
            embed.description += "\nYour server does not allow you to specify CFG Scale, the default will be used."
        if not settings.steps_override and sample_steps:
            embed.description += "\nYour server does not allow you to specify sample steps, the default will be used."
        embed.add_field(name="Queue Position", value=resolve_queue_pos(self.queue_length), inline=True)
        embed.add_field(name="Sample Stemps", value=sample_steps if cfg_scale and settings.cfg_override else settings.steps, inline=True)
        embed.add_field(name="CFG Scale", value=cfg_scale if sample_steps and settings.steps_override else settings.cfg_scale, inline=True)
        await inter.response.send_message(embed=embed)
        await generate(
            inter=inter,
            prompt=prompt,
            requestor=inter.author,
            cfg_scale=cfg_scale if cfg_scale and settings.cfg_override else None,
            sample_steps=sample_steps if sample_steps and settings.steps_override else None
        )
        self.queue_length -= 1

    @commands.message_command(name="Artify", description="Generate an AIArt image with this message as a prompt")
    async def artify(self, inter: disnake.ApplicationCommandInteraction):
        self.queue_length += 1
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        prompt = inter.target.content
        await record(guild=str(inter.guild_id), user=inter.author)
        embed = disnake.Embed(
            title="Prompt Recieved",
            description=f"`{prompt}` by {inter.author.mention}, original message by {inter.target.author.mention}",
            timestamp=datetime.now()
        )
        embed.add_field(name="Queue Position", value=resolve_queue_pos(self.queue_length), inline=True)
        embed.add_field(name="Sample Stemps",value=settings.steps, inline=True)
        embed.add_field(name="CFG Scale",value=settings.cfg_scale,inline=True)
        await inter.response.send_message(embed=embed)
        await generate(inter=inter, prompt=prompt, requestor=inter.author)
        self.queue_length -= 1

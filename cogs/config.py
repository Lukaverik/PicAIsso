from datetime import datetime

import disnake
from disnake import TextInputStyle
from disnake.ext import commands

from settings import SettingsCache


class NegativePromptAppendModal(disnake.ui.Modal):
    def __init__(self, inter_id: str):
        components = [
            disnake.ui.TextInput(
                label="Tags to Append",
                placeholder="Use Comma Separated Values",
                custom_id="value",
                style=TextInputStyle.paragraph
            )
        ]
        super().__init__(
            title="Update Negative Prompt",
            custom_id=f"new_prompt-{inter_id}",
            components=components
        )

    async def callback(self, inter:disnake.ModalInteraction):
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        settings.neg_prompt += ", " + inter.text_values["value"]
        await SettingsCache.update(settings=settings)
        await inter.response.send_message(
            f"{inter.author.mention} has updated this server's default negative prompt to ```{settings.neg_prompt}```")


class NegativePromptOverwriteModal(disnake.ui.Modal):
    def __init__(self, inter_id: str, current_val: str):
        components = [
            disnake.ui.TextInput(
                label="New Negative Prompt",
                placeholder="Use Comma Separated Values",
                value=current_val,
                custom_id="value",
                style=TextInputStyle.paragraph
            )
        ]
        super().__init__(
            title="Update Negative Prompt",
            custom_id=f"new_prompt-{inter_id}",
            components=components
        )

    async def callback(self, inter: disnake.ModalInteraction):
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        settings.neg_prompt = inter.text_values["value"]
        await SettingsCache.update(settings=settings)
        await inter.response.send_message(
            f"{inter.author.mention} has updated this server's default negative prompt to ```{settings.neg_prompt}```")


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="configuration")
    async def config(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @config.sub_command(name="overview", description="Review this server's current generation settings.")
    async def overview(self, inter: disnake.ApplicationCommandInteraction):
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        embed = disnake.Embed(
            title="Aiba Configuration",
            timestamp=datetime.now()
        )
        embed.add_field(name="Sample Steps", value=settings.steps, inline=True)
        embed.add_field(name="Sample Steps Override", value=settings.steps_override, inline=True)
        embed.add_field(name="CFG Scale", value=settings.cfg_scale, inline=True)
        embed.add_field(name="CFG Scale Override", value=settings.cfg_override, inline=True)
        embed.add_field(name="Resolution", value=f"{settings.width}x{settings.height}", inline=True)
        embed.add_field(name="Denoising Strength", value=settings.denoising_strength, inline=True)
        embed.add_field(name="Sampler Index", value=settings.sampler_index, inline=True)
        embed.add_field(name="Negative Prompt", value=settings.neg_prompt, inline=False)
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="update")
    @commands.default_member_permissions(administrator=True)
    async def update(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @update.sub_command(name="cfg_scale", description="Update this server's default CFG Scale")
    async def update_cfg_scale(
            self,
            inter: disnake.ApplicationCommandInteraction,
            new_cfg_scale: commands.Range[1, 30.0]
    ):
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        settings.cfg_scale = new_cfg_scale
        await SettingsCache.update(settings=settings)
        await inter.response.send_message(f"{inter.author.mention} has updated this server's default CFG Scale to {new_cfg_scale}.")

    @update.sub_command(name="steps", description="Update this server's default number of Sample Steps")
    async def update_sample_steps(
            self,
            inter: disnake.ApplicationCommandInteraction,
            new_sample_steps: commands.Range[1, 150]
    ):
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        settings.steps = new_sample_steps
        await SettingsCache.update(settings=settings)
        await inter.response.send_message(f"{inter.author.mention} has updated this server's default number of sample steps to {new_sample_steps}.")

    @update.sub_command(
        name="resolution",
        description="Update this server's default generation resolution. Height = Width"
    )
    async def update_resolution(
            self,
            inter: disnake.ApplicationCommandInteraction,
            new_width: commands.Range[1, 1024]
    ):
        if new_width % 64 != 0:
            await inter.response.send_message("Height and Width of generated images must be a multiple of 64.")
        else:
            settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
            settings.width = new_width
            settings.height = new_width
            await SettingsCache.update(settings=settings)
            await inter.response.send_message(f"{inter.author.mention} has updated this server's default resolution to {new_width}x{new_width}.")

    @update.sub_command(name="denoising_strength", description="Update this server's default denoising strength")
    async def update_sample_steps(
            self,
            inter: disnake.ApplicationCommandInteraction,
            new_denoising_strength: commands.Range[0, 1.0]
    ):
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        settings.denoising_strength = new_denoising_strength
        await SettingsCache.update(settings=settings)
        await inter.response.send_message(f"{inter.author.mention} has updated this server's default denoising strength to {new_denoising_strength}.")

    @update.sub_command(name="negative_prompt", description="Update this server's default negative prompt.")
    async def update_sample_steps(
            self,
            inter: disnake.ApplicationCommandInteraction,
            mode: commands.Range[1,2]
    ):
        """
        Update this server's default negative prompt through a modal.

        Parameters
        ----------
        mode: 1 to overwrite the existing negative prompt, 2 to append to it
        """
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        if mode == 1:
            await inter.response.send_modal(modal=NegativePromptOverwriteModal(inter_id=str(inter.id), current_val=settings.neg_prompt))
        elif mode == 2:
            await inter.response.send_modal(modal=NegativePromptAppendModal(inter_id=str(inter.id)))

    @update.sub_command(name="cfg_override", description="Update whether users can manually specify CFG scale.")
    async def update_cfg_override(
            self,
            inter: disnake.ApplicationCommandInteraction,
            new_cfg_override: bool
    ):
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        settings.cfg_override = new_cfg_override
        await SettingsCache.update(settings=settings)
        await inter.response.send_message(f"{inter.author.mention} has updated this server's CFG Scale Override to {settings.cfg_override}.")

    @update.sub_command(name="steps_override", description="Update whether users can manually specify sample steps.")
    async def update_steps_override(
            self,
            inter: disnake.ApplicationCommandInteraction,
            new_steps_override: bool
    ):
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        settings.steps_override = new_steps_override
        await SettingsCache.update(settings=settings)
        await inter.response.send_message(f"{inter.author.mention} has updated this server's Sample Steps Override to {settings.steps_override}.")
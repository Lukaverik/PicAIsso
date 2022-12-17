import disnake
from disnake.ext import commands

from models.guild import Guild
from models.modal import NegativePromptAppendModal, NegativePromptOverwriteModal


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="configuration", dm_permission=False)
    async def config(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @config.sub_command(
        name="overview", description="Review this server's current generation settings."
    )
    async def overview(self, inter: disnake.ApplicationCommandInteraction):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        embed = await guild.settings.get_overview_embed()
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="update", dm_permission=False)
    @commands.default_member_permissions(administrator=True)
    async def update(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @update.sub_command(
        name="visible_prompts",
        description="Update whether prompt messages are visible.",
    )
    async def update_visible_prompts(
        self, inter: disnake.ApplicationCommandInteraction, new_visible_prompts: bool
    ):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        guild.settings.visible_prompts = new_visible_prompts
        await guild.save_changes()
        response = "visible" if new_visible_prompts else "invisible"
        await inter.response.send_message(
            f"{inter.author.mention} has set prompt messages to be {response} in this server by default."
        )

    @update.sub_command(
        name="delete_prompts", description="Update whether prompt messages are deleted."
    )
    async def update_delete_prompts(
        self, inter: disnake.ApplicationCommandInteraction, new_delete_prompts: bool
    ):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        guild.settings.delete_prompts_prompts = new_delete_prompts
        response = "to be deleted" if new_delete_prompts else "to not be deleted"
        await guild.save_changes()
        await inter.response.send_message(
            f"{inter.author.mention} has set prompt messages {response} in this server by default."
        )

    @update.sub_command(
        name="cfg_scale", description="Update this server's default CFG Scale"
    )
    async def update_cfg_scale(
        self,
        inter: disnake.ApplicationCommandInteraction,
        new_cfg_scale: commands.Range[1, 30.0],
    ):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        guild.settings.cfg_scale = new_cfg_scale
        await guild.save_changes()
        await inter.response.send_message(
            f"{inter.author.mention} has updated this server's default CFG Scale to {new_cfg_scale}."
        )

    @update.sub_command(
        name="steps", description="Update this server's default number of Sample Steps"
    )
    async def update_sample_steps(
        self,
        inter: disnake.ApplicationCommandInteraction,
        new_sample_steps: commands.Range[1, 150],
    ):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        guild.settings.steps = new_sample_steps
        await guild.save_changes()
        await inter.response.send_message(
            f"{inter.author.mention} has updated this server's default number of sample steps to {new_sample_steps}."
        )

    @update.sub_command(
        name="resolution",
        description="Update this server's default generation resolution. Height = Width",
    )
    async def update_resolution(
        self,
        inter: disnake.ApplicationCommandInteraction,
        new_width: commands.Range[1, 1024],
    ):
        if new_width % 64 != 0:
            await inter.response.send_message(
                "Height and Width of generated images must be a multiple of 64.",
                ephemeral=True,
            )
        else:
            guild = await Guild.find_or_create(disnake_guild=inter.guild)
            guild.settings.width = new_width
            guild.settings.height = new_width
            await guild.save_changes()
            await inter.response.send_message(
                f"{inter.author.mention} has updated this server's default resolution to {new_width}x{new_width}."
            )

    @update.sub_command(
        name="denoising_strength",
        description="Update this server's default denoising strength",
    )
    async def update_denoising_strength(
        self,
        inter: disnake.ApplicationCommandInteraction,
        new_denoising_strength: commands.Range[0, 1.0],
    ):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        guild.settings.denoising_strength = new_denoising_strength
        await guild.save_changes()
        await inter.response.send_message(
            f"{inter.author.mention} has updated this server's default denoising strength to {new_denoising_strength}."
        )

    @update.sub_command(
        name="negative_prompt",
        description="Update this server's default negative prompt.",
    )
    async def update_neg_prompt(
        self, inter: disnake.ApplicationCommandInteraction, mode: commands.Range[1, 2]
    ):
        """
        Update this server's default negative prompt through a modal.

        Parameters
        ----------
        mode: 1 to overwrite the existing negative prompt, 2 to append to it
        """
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        if mode == 1:
            await inter.response.send_modal(
                modal=NegativePromptOverwriteModal(inter_id=str(inter.id), guild=guild)
            )
        elif mode == 2:
            await inter.response.send_modal(
                modal=NegativePromptAppendModal(inter_id=str(inter.id), guild=guild)
            )

    @update.sub_command(
        name="cfg_override",
        description="Update whether users can manually specify CFG scale.",
    )
    async def update_cfg_override(
        self, inter: disnake.ApplicationCommandInteraction, new_cfg_override: bool
    ):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        guild.settings.cfg_override = new_cfg_override
        if new_cfg_override:
            message = "updated this server's settings so that the default CFG scale may now be overridden."
        else:
            message = "updated this server's settings so that the default CFG scale may not be overridden."
        await guild.save_changes()
        await inter.response.send_message(f"{inter.author.mention} has {message}")

    @update.sub_command(
        name="steps_override",
        description="Update whether users can manually specify sample steps.",
    )
    async def update_steps_override(
        self, inter: disnake.ApplicationCommandInteraction, new_steps_override: bool
    ):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        guild.settings.steps_override = new_steps_override
        await guild.save_changes()
        if new_steps_override:
            message = "updated this server's settings so that the default Sample Steps may now be overridden."
        else:
            message = "updated this server's settings so that the default Sample Steps may not be overridden."
        await inter.response.send_message(f"{inter.author.mention} has {message}")

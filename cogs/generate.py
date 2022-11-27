from datetime import datetime
from io import BytesIO

import PIL.Image
import aiohttp
import disnake
from disnake import TextInputStyle
from disnake.ext import commands

from api import txt2img, record, resolve_queue_pos, img2img
from settings import SettingsCache, QueueHandler


class ImageCache:
    cache: dict = None

    @classmethod
    async def set(cls, author_id: str, image_url: str):
        if not cls.cache:
            cls.cache = {}
        cls.cache[author_id] = image_url

    @classmethod
    async def get(cls, author_id: str):
        if not cls.cache:
            cls.cache = {}
        if image_url := cls.cache.get(author_id):
            return image_url


class Img2ImgModal(disnake.ui.Modal):
    def __init__(self, author_id: str):
        components = [
            disnake.ui.TextInput(
                label="Img2Img Prompt",
                custom_id="prompt",
                style=TextInputStyle.paragraph
            ),
            disnake.ui.TextInput(
                label="CFG Scale",
                placeholder="How much the AI sticks to the prompt. Low = Stick to Prompt More",
                custom_id="cfg_scale",
                style=TextInputStyle.short,
                required=False
            ),
            disnake.ui.TextInput(
                label="Sample Steps",
                placeholder="How many times the image is iterated on.",
                custom_id="steps",
                style=TextInputStyle.short,
                required=False
            ),
            disnake.ui.TextInput(
                label="Denoising Strength",
                placeholder="How close to the original image the AI stays. Low = Little Change",
                custom_id="denoising_strength",
                style=TextInputStyle.short,
                required=False
            )
        ]
        super().__init__(
            title="Img2Img",
            custom_id=f"Img2Img-{author_id}",
            components=components
        )

    async def callback(self, inter: disnake.ModalInteraction):
        image_url = await ImageCache.get(author_id=str(inter.author.id))
        if not image_url:
            await inter.response.send_message("An Unexpected Error has occurred: Image Not Found")
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        prompt = inter.text_values.get('prompt')
        cfg_scale = inter.text_values.get('cfg_scale')
        sample_steps = inter.text_values.get('steps')
        denoising_strength = inter.text_values.get('denoising_strength')
        embed = disnake.Embed(
            title="Prompt Recieved",
            description=f"`{prompt}` by {inter.author.mention}",
            timestamp=datetime.now(),
        )

        # Permissions and Data Validation
        if cfg_scale:
            cfg_scale = float(cfg_scale)
            if not settings.cfg_override:
                embed.description += "\nYour server does not allow you to specify CFG Scale, the default will be used."
            elif cfg_scale > 30 or cfg_scale < 0:
                embed.description += "\nCFG Scale format not recognized -- using default. Please enter a decimal value between 0.0 and 30.0."
        if sample_steps:
            sample_steps = int(sample_steps)
            if not settings.steps_override:
                embed.description += "\nYour server does not allow you to specify sample steps, the default will be used."
            if sample_steps > 150 or sample_steps < 0:
                embed.description += "\nSample Steps format not recognized -- using default. Please enter an integer value between 0 and 150."
        if denoising_strength:
            denoising_strength = float(denoising_strength)
            if denoising_strength < 0 or denoising_strength > 1:
                embed.description += "\nDenoising strength format not recognized -- using default. Please enter a decimal value between 0.0 and 1.0."

        embed.add_field(name="Queue Position", value=resolve_queue_pos(QueueHandler.get_length()), inline=True)
        embed.add_field(name="Sample Steps", value=sample_steps if sample_steps and settings.steps_override else settings.steps, inline=True)
        embed.add_field(name="CFG Scale", value=cfg_scale if cfg_scale and settings.cfg_override else settings.cfg_scale, inline=True)
        embed.add_field(name="Denoising Strength", value=denoising_strength if denoising_strength else settings.denoising_strength, inline=True)
        embed.set_thumbnail(url=image_url)
        await inter.response.send_message(embed=embed, ephemeral=not settings.visible_prompts)
        await img2img(
            inter=inter,
            image_url=image_url,
            prompt=prompt,
            requestor=inter.author,
            cfg_scale=cfg_scale if cfg_scale and settings.cfg_override else None,
            sample_steps=sample_steps if sample_steps and settings.steps_override else None,
            denoising_strength=denoising_strength if denoising_strength else None
        )
        if settings.delete_prompts:
            await inter.delete_original_response()
        QueueHandler.decrement()


class Generate(commands.Cog):
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
        QueueHandler.increment()
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
        embed.add_field(name="Queue Position", value=resolve_queue_pos(QueueHandler.get_length()), inline=True)
        embed.add_field(name="Sample Steps", value=sample_steps if sample_steps and settings.steps_override else settings.steps, inline=True)
        embed.add_field(name="CFG Scale", value=cfg_scale if cfg_scale and settings.cfg_override else settings.cfg_scale, inline=True)
        await inter.response.send_message(embed=embed, ephemeral=not settings.visible_prompts)
        await txt2img(
            inter=inter,
            prompt=prompt,
            requestor=inter.author,
            cfg_scale=cfg_scale if cfg_scale and settings.cfg_override else None,
            sample_steps=sample_steps if sample_steps and settings.steps_override else None
        )
        if settings.delete_prompts:
            await inter.delete_original_response()
        QueueHandler.decrement()

    @commands.message_command(name="Artify", description="Generate an AIArt image with this message as a prompt")
    async def artify(self, inter: disnake.MessageCommandInteraction):
        QueueHandler.increment()
        settings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
        prompt = inter.target.content
        await record(guild=str(inter.guild_id), user=inter.author)
        embed = disnake.Embed(
            title="Prompt Recieved",
            description=f"`{prompt}` by {inter.author.mention}, original message by {inter.target.author.mention}",
            timestamp=datetime.now()
        )
        embed.add_field(name="Queue Position", value=resolve_queue_pos(QueueHandler.get_length()), inline=True)
        embed.add_field(name="Sample Steps",value=settings.steps, inline=True)
        embed.add_field(name="CFG Scale",value=settings.cfg_scale,inline=True)
        await inter.response.send_message(embed=embed, ephemeral=not settings.visible_prompts)
        await txt2img(inter=inter, prompt=prompt, requestor=inter.author, artify=True)
        if settings.delete_prompts:
            await inter.delete_original_response()
        QueueHandler.decrement()

    @commands.message_command(name="Img2Img", description="Transform a given image according to a prompt")
    async def img2img(self, inter: disnake.MessageCommandInteraction):
        QueueHandler.increment()
        await record(guild=str(inter.guild_id), user=inter.author)
        message = inter.target
        image_url = None
        for embed in message.embeds:
            if embed.image:
                image_url = embed.image.url
                break
        if not image_url:
            for attachment in message.attachments:
                if attachment.content_type.startswith("image"):
                    image_url = attachment.url
                    break
        if not image_url:
            await inter.response.send_message("No image found in target message!")
        else:
            await ImageCache.set(author_id=str(inter.author.id), image_url=image_url)
            await inter.response.send_modal(Img2ImgModal(author_id=str(inter.author.id)))
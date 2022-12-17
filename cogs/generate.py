import asyncio
from zoneinfo import ZoneInfo

import disnake
from disnake.ext import commands, tasks

import util
from api import generate
from models.guild import Guild
from models.modal import Img2ImgModal
from models.request import (
    Txt2ImgRequest,
    ArtifyRequest,
    Img2ImgRequest,
    RequestStatus,
)
from models.request_queue import RequestQueue

from models.user import User


class Generate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.dequeue.start()

    @commands.slash_command(
        name="generate",
        description="Generate an AIArt image according to the given prompt",
        dm_permission=False,
    )
    async def txt2txt(
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
        cfg_scale - Optional, float, 1-30: "Classifier-Free Guidance", how much the AI sticks to the prompt. Low = Higher quality, far from prompt. High = Lower quality, close to prompt
        sample_steps - Optional, int, 1-150: The number of iterations the AI uses to process the image. Higher = More time to process, higher quality.
        """
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        requestor = await User.find_or_create(disnake_user=inter.author)
        request = Txt2ImgRequest(
            requestor_id=requestor.discord_id,
            source_guild_id=guild.discord_id,
            source_channel_id=inter.channel_id,
            date=inter.created_at.replace(tzinfo=ZoneInfo("UTC")),
            prompt=prompt,
            cfg_scale=cfg_scale,
            sample_steps=sample_steps,
        )
        request = guild.validate_request(req=request)
        await request.save()
        await requestor.log_request(
            request_id=request.request_id, prompt=request.prompt
        )
        await guild.log_request(discord_id=requestor.discord_id)
        await RequestQueue.add(
            req=request, guild=guild, inter=inter, requestor=requestor
        )
        embed = await request.get_prompt_embed(
            queue_pos=await RequestQueue.resolve_queue_pos(req_id=request.request_id),
        )
        await inter.response.send_message(
            embed=embed, ephemeral=not guild.settings.visible_prompts
        )

    @commands.message_command(
        name="Artify",
        description="Generate an AIArt image with this message as a prompt",
        dm_permission=False,
    )
    async def artify(self, inter: disnake.MessageCommandInteraction):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        requestor = await User.find_or_create(disnake_user=inter.author)
        original_author = await User.find_or_create(disnake_user=inter.target.author)
        request = ArtifyRequest(
            requestor_id=requestor.discord_id,
            original_author_id=original_author.discord_id,
            source_guild_id=guild.discord_id,
            source_channel_id=inter.channel_id,
            date=inter.created_at.replace(tzinfo=ZoneInfo("UTC")),
            prompt=inter.target.content,
        )
        request = guild.validate_request(req=request)
        await request.save()
        await requestor.log_request(
            request_id=request.request_id, prompt=request.prompt
        )
        await guild.log_request(discord_id=requestor.discord_id)
        await RequestQueue.add(
            req=request,
            inter=inter,
            guild=guild,
            requestor=requestor,
            original_author=original_author,
        )
        embed = await request.get_prompt_embed(
            queue_pos=await RequestQueue.resolve_queue_pos(req_id=request.request_id),
        )
        await inter.response.send_message(
            embed=embed, ephemeral=not guild.settings.visible_prompts
        )

    @commands.message_command(
        name="Img2Img",
        description="Transform a given image according to a prompt",
        dm_permission=False,
    )
    async def img2img(self, inter: disnake.MessageCommandInteraction):
        guild = await Guild.find_or_create(disnake_guild=inter.guild)
        requestor = await User.find_or_create(disnake_user=inter.author)
        request = Img2ImgRequest(
            requestor_id=requestor.discord_id,
            source_guild_id=guild.discord_id,
            source_channel_id=inter.channel_id,
            date=inter.created_at.replace(tzinfo=ZoneInfo("UTC")),
        )
        await request.save()
        await guild.log_request(discord_id=requestor.discord_id)
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
            request.status = RequestStatus.error
            await request.save_changes()
        else:
            await request.set_original_img(url=image_url)
            await inter.response.send_modal(
                Img2ImgModal(request=request, guild=guild, requestor=requestor)
            )

    @tasks.loop(seconds=5.0)
    async def dequeue(self):
        if not util.paused:
            async with self.lock:
                if qr := await RequestQueue.dequeue():
                    await generate(
                        inter=qr.inter,
                        request=qr.request,
                        guild=qr.guild,
                        requestor=qr.requestor,
                        original_author=qr.original_author,
                    )

    @dequeue.before_loop
    async def wait_until_ready(self):
        await self.bot.wait_until_ready()

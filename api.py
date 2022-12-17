import os
from datetime import datetime
from io import BytesIO
import PIL.Image
import aiohttp
import base64

import disnake
from PIL import PngImagePlugin

from models.guild import Guild
from models.request import RequestType, Request, Img2ImgRequest, RequestStatus
from models.user import User
from models.view import ScoreView
from util import sanitized_file_name, base_url, outputs_dir, Interaction


async def generate(
    inter: Interaction,
    request: Request,
    guild: Guild,
    requestor: User,
    original_author: User = None,
):
    if request.req_type == RequestType.img2img:
        await img2img(
            inter=inter,
            request=request,
            guild=guild,
            requestor=requestor,
        )
    else:
        await txt2img(
            inter=inter,
            request=request,
            guild=guild,
            requestor=requestor,
            original_author=original_author,
        )


async def txt2img(
    inter: disnake.ApplicationCommandInteraction,
    request: Request,
    guild: Guild,
    requestor: User,
    original_author: User = None,
):
    payload = guild.request_to_payload(req=request)
    request.status = RequestStatus.in_progress
    await request.save_changes()
    async with aiohttp.ClientSession() as session:
        start = datetime.now()
        async with session.post(
            f"{base_url}/sdapi/v1/txt2img", json=payload
        ) as response:
            delta = datetime.now() - start
            if response.status == 200:
                request.status = RequestStatus.finished
                request.runtime = float(f"{delta.seconds}.{delta.microseconds//10000}")
                r = await response.json()
                request.output_filename = sanitized_file_name(
                    request.prompt, request.requestor_id
                )
                bio = BytesIO(base64.b64decode(r["images"][0]))
                PIL.Image.open(bio).save(
                    os.path.join(outputs_dir, request.output_filename)
                )
                embed = await request.get_output_embed()
                await request.save_changes()
                await inter.channel.send(
                    embed=embed, view=ScoreView(request_id=request.request_id)
                )
            else:
                request.status = RequestStatus.error
                await request.save_changes()
                await inter.channel.send(
                    f"Bad response received from Stable Diffusion API (Status: {response.status})"
                )
    if guild.settings.delete_prompts:
        await inter.delete_original_response()


async def get_img_bytes(request: Img2ImgRequest):
    async with aiohttp.ClientSession() as session:
        async with session.post(request.original_img_url) as response:
            BIO = BytesIO(await response.content.read())
            img = PIL.Image.open(BIO)
            with BytesIO() as output_bytes:
                use_metadata = False
                metadata = PngImagePlugin.PngInfo()
                for key, value in img.info.items():
                    if isinstance(key, str) and isinstance(value, str):
                        metadata.add_text(key, value)
                        use_metadata = True
                img.save(
                    output_bytes, "PNG", pnginfo=(metadata if use_metadata else None)
                )
                return output_bytes.getvalue()


async def img2img(
    inter: disnake.ModalInteraction,
    request: Img2ImgRequest,
    guild: Guild,
    requestor: User,
):
    request.status = RequestStatus.in_progress
    await request.save_changes()
    img_data = await get_img_bytes(request=request)
    img_data = str(base64.b64encode(img_data))
    payload = guild.request_to_payload(req=request, data=img_data)
    async with aiohttp.ClientSession() as session:
        start = datetime.now()
        async with session.post(
            f"{base_url}/sdapi/v1/img2img", json=payload
        ) as response:
            delta = datetime.now() - start
            if response.status == 200:
                request.status = RequestStatus.finished
                request.runtime = float(
                    f"{delta.seconds}.{delta.microseconds // 10000}"
                )
                r = await response.json()
                request.output_filename = sanitized_file_name(
                    request.prompt, request.requestor_id
                )
                bio = BytesIO(base64.b64decode(r["images"][0]))
                PIL.Image.open(bio).save(
                    os.path.join(outputs_dir, request.output_filename)
                )
                embed = await request.get_output_embed()
                await request.save_changes()
                await inter.channel.send(
                    embed=embed, view=ScoreView(request_id=request.request_id)
                )
            else:
                request.status = RequestStatus.error
                await request.save_changes()
                await inter.channel.send(
                    f"Bad response received from Stable Diffusion API (Status: {response.status})"
                )
    if guild.settings.delete_prompts:
        await inter.delete_original_response()

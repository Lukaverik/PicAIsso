from datetime import datetime
from io import BytesIO
from typing import Union

import PIL.Image
import aiohttp
import base64

import disnake
from PIL import PngImagePlugin
from disnake import User, Member, InteractionResponseType

from settings import base_url, SettingsCache, GuildSettings
from util import load, flush, sanitized_file_name

stats_path = "../data/stats.json"


async def record(guild: str, user: Union[User|Member]):
    data = await load(path=stats_path)
    if guild in list(data.keys()):
        if user.name in list(data[guild].keys()):
            data[guild][user.name] += 1
        else:
            data[guild][user.name] = 1
    else:
        data[guild] = {user.name: 1}
    await flush(path=stats_path, data=data)


async def sorted_stats(guild: str):
    data = await load(path=stats_path)
    if guild not in data.keys():
        return {}
    else:
        return {name: value for name, value in sorted(data[guild].items(), key=lambda item: item[1], reverse=True)}


def resolve_queue_pos(queue_length: int):
    pos = str(queue_length)
    match(pos[-1]):
        case "1":
            pos += "st"
        case "2":
            pos += "nd"
        case "3":
            pos += "rd"
        case _:
            pos += "th"
    return pos


async def txt2img(inter: disnake.ApplicationCommandInteraction, prompt: str, requestor: Union[User, Member], cfg_scale: float = None, sample_steps: int = None, artify:bool=False):
    settings: GuildSettings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
    payload = {
        "prompt": prompt + ", masterpiece, best quality",
        "batch_size": 1,
        "neg_prompt": settings.neg_prompt,
        "steps": sample_steps or settings.steps,
        "cfg_scale": cfg_scale or settings.cfg_scale,
        "denoising_strength": settings.denoising_strength,
        "sampler_index": settings.sampler_index,
        "width": settings.width,
        "height": settings.height,
    }
    async with aiohttp.ClientSession() as session:
        start = datetime.now()
        async with session.post(f"{base_url}/sdapi/v1/txt2img", json=payload) as response:
            delta = datetime.now() - start
            delta_string = f"{delta.seconds}.{delta.microseconds//10000} seconds"
            if response.status == 200:
                r = await response.json()
                filename = sanitized_file_name(prompt, requestor.display_name)
                # Image.open(BytesIO(base64.b64decode(r['images'][0]))).save(f"../outputs/{filename}")
                embed = disnake.Embed(
                    title=prompt[:256].title(),
                    color=disnake.Colour.dark_teal(),
                    timestamp=datetime.now(),
                )
                embed.add_field(name="Requestor", value=requestor.mention, inline=True)
                if artify:
                    embed.add_field(name="Original Author", value=inter.target.author.mention, inline=True)
                embed.add_field(name="Generated in", value=delta_string, inline=True)
                # embed.set_image(file=disnake.File(f"../outputs/{filename}"))
                embed.set_image(file=disnake.File(filename=filename, fp=BytesIO(base64.b64decode(r['images'][0]))))
                await inter.followup.send(embed=embed)
            else:
                await inter.followup.send(f"Bad response received from Stable Diffusion API (Status: {response.status})")


async def img2img(inter, image_url: str, prompt: str, requestor: Union[User, Member], denoising_strength: float, cfg_scale: float = None, sample_steps: int = None):
    settings: GuildSettings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
    async with aiohttp.ClientSession() as session:
        async with session.post(image_url) as response:
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
                bytes_data = output_bytes.getvalue()
    img_data = str(base64.b64encode(bytes_data))
    payload = {
        "init_images": [img_data],
        "prompt": prompt + ", masterpiece, best quality",
        "batch_size": 1,
        "neg_prompt": settings.neg_prompt,
        "steps": sample_steps or settings.steps,
        "cfg_scale": cfg_scale or settings.cfg_scale,
        "denoising_strength": denoising_strength or settings.denoising_strength,
        "sampler_index": settings.sampler_index,
        "width": settings.width,
        "height": settings.height
    }
    async with aiohttp.ClientSession() as session:
        start = datetime.now()
        async with session.post(f"{base_url}/sdapi/v1/img2img", json=payload) as response:
            delta = datetime.now() - start
            delta_string = f"{delta.seconds}.{delta.microseconds // 10000} seconds"
            if response.status == 200:
                r = await response.json()
                filename = sanitized_file_name(prompt, requestor.display_name)
                # Image.open(BytesIO(base64.b64decode(r['images'][0]))).save(f"../outputs/{filename}")
                embed = disnake.Embed(
                    title=prompt[:256].title(),
                    color=disnake.Colour.dark_teal(),
                    timestamp=datetime.now(),
                )
                embed.add_field(name="Requestor", value=requestor.mention, inline=True)
                embed.add_field(name="Generated in", value=delta_string, inline=True)
                embed.add_field(name="Denoising Strength", value =denoising_strength or settings.denoising_strength)
                # embed.set_image(file=disnake.File(f"../outputs/{filename}"))
                embed.set_image(file=disnake.File(filename=filename, fp=BytesIO(base64.b64decode(r['images'][0]))))
                embed.set_thumbnail(url=image_url)
                await inter.followup.send(embed=embed)
            else:
                await inter.followup.send(
                    f"Bad response received from Stable Diffusion API (Status: {response.status})")

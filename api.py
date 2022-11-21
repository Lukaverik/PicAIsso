from datetime import datetime
from io import BytesIO
from typing import Union

import aiohttp
import base64

import disnake
from disnake import User, Member

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
    return f"You are {pos} in queue."


async def generate(inter, prompt: str, requestor: Union[User, Member]):
    settings: GuildSettings = await SettingsCache.find_by_guild_id(guild_id=str(inter.guild_id))
    payload = {
        "prompt": prompt,
        "batch_size": 1,
        "neg_prompt": settings.neg_prompt,
        "steps": settings.steps,
        "cfg_scale": settings.cfg_scale,
        "denoising_strength": settings.denoising_strength,
        "sampler_index": settings.sampler_index,
        "width": settings.width,
        "height": settings.height
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
                embed.add_field(name="Requested by", value=requestor.mention, inline=True)
                embed.add_field(name="Generated in", value=delta_string, inline=True)
                # embed.set_image(file=disnake.File(f"../outputs/{filename}"))
                embed.set_image(file=disnake.File(filename=filename, fp=BytesIO(base64.b64decode(r['images'][0]))))
                await inter.followup.send(embed=embed)
            else:
                await inter.followup.send(f"Bad response received from Stable Diffusion API (Status: {response.status})")

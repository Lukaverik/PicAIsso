from datetime import datetime
from io import BytesIO
from PIL import Image
from typing import Union

import aiohttp
import base64

import disnake
from disnake import User, Member

from settings import base_url


async def generate(prompt: str, requestor: Union[User, Member]):
    payload = {
        "prompt": prompt,
        "steps": 20,
        "batch_size": 1
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/sdapi/v1/txt2img", json=payload) as response:
            if response.status == 200:
                r = await response.json()
                filename = f"{prompt}_{requestor.display_name}.png"
                Image.open(BytesIO(base64.b64decode(r['images'][0]))).save(f"../outputs/{filename}")
                embed = await embed_builder(
                    prompt=prompt,
                    requestor_mention=requestor.mention,
                    image_path=f"../outputs/{filename}"
                )
                return embed
            else:
                raise ValueError(f"Bad response received from Stable Diffusion API (Status: {response.status})")


###
# Generation Response Embed Builder
###
async def embed_builder(prompt: str, requestor_mention: str, image_path: str):
    embed = disnake.Embed(
        title=prompt.title(),
        description=f"Requested by {requestor_mention}",
        color=disnake.Colour.dark_teal(),
        timestamp=datetime.now(),
    )
    embed.set_thumbnail(file=disnake.File("../assets/icon.webp"))
    embed.set_image(file=disnake.File(f"../outputs/{image_path}"))
    return embed

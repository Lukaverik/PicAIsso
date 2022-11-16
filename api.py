from datetime import datetime
from io import BytesIO
from PIL import Image
from typing import Union

import aiohttp
import base64

import disnake
from disnake import User, Member

from settings import base_url, base_neg_prompt


async def generate(inter, prompt: str, requestor: Union[User, Member]):
    payload = {
        "prompt": prompt,
        "steps": 20,
        "batch_size": 1,
        "negative_prompt": base_neg_prompt
    }
    async with aiohttp.ClientSession() as session:
        start = datetime.now()
        async with session.post(f"{base_url}/sdapi/v1/txt2img", json=payload) as response:
            delta = datetime.now() - start
            delta_string = f"{delta.seconds}.{delta.microseconds//10000} seconds"
            if response.status == 200:
                r = await response.json()
                filename = f"{prompt}_{requestor.display_name}.png".replace(" ", "_")
                Image.open(BytesIO(base64.b64decode(r['images'][0]))).save(f"../outputs/{filename}")
                embed = disnake.Embed(
                    title=prompt.title(),
                    color=disnake.Colour.dark_teal(),
                    timestamp=datetime.now(),
                )
                embed.add_field(name="Requested by", value=requestor.mention, inline=True)
                embed.add_field(name="Generated in", value=delta_string, inline=True)
                embed.set_image(file=disnake.File(f"../outputs/{filename}"))
                await inter.followup.send(embed=embed)
            else:
                await inter.followup.send(f"Bad response received from Stable Diffusion API (Status: {response.status})")

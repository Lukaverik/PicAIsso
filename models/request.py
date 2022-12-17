import os
from datetime import datetime
from enum import Enum
from typing import Optional, Dict

from beanie import Document
from bson import ObjectId
from disnake import Embed, File

import util
from models.embed import EmbedBuilder, Field

# from models.user import UserCache
from models import user
from models.user import User
from util import outputs_dir


class RequestType(str, Enum):
    txt2img = "txt2img"
    artify = "artify"
    img2img = "img2img"


class RequestStatus(str, Enum):
    building = "building"
    awaiting_prompt = "awaiting_prompt"
    queued = "queued"
    in_progress = "in_progress"
    error = "error"
    finished = "finished"


class Request(Document):
    class Settings:
        use_state_management = True
        state_management_replace_objects = True
        is_root = True
        name = "request"

    requestor_id: str
    source_guild_id: str
    source_channel_id: str
    date: datetime
    req_type: RequestType
    is_rerun: bool = False
    prompt: str
    original_prompt: str = None
    cfg_scale: float = None
    sample_steps: int = None
    original_cfg_scale: Optional[float]
    original_sample_steps: Optional[int]
    status: RequestStatus = RequestStatus.building
    runtime: Optional[float]
    output_filename: Optional[str]
    output_url: Optional[str]
    likes: int = 0
    dislikes: int = 0
    score_dict: Optional[Dict[str, int]]

    @property
    def request_id(self) -> str:
        return str(self.id)

    @property
    def cfg_overridden(self) -> bool:
        return self.original_cfg_scale is not None

    @property
    def sample_steps_overridden(self) -> bool:
        return self.original_sample_steps is not None

    @property
    def score(self):
        return self.likes - self.dislikes

    @classmethod
    async def get_by_id(cls, mongo_id: str):
        return await cls.find_one(Request.id == ObjectId(mongo_id))

    def like(self, source: "user.User"):
        if self.score_dict is None:
            self.score_dict = {}
        match self.score_dict.get(source.discord_id, 0):
            case 1:
                return
            case 0:
                self.likes += 1
                self.score_dict[source.discord_id] = 1
            case -1:
                self.dislikes -= 1
                self.likes += 1
                self.score_dict[source.discord_id] = 1

    def dislike(self, source: "user.User"):
        if self.score_dict is None:
            self.score_dict = {}
        match self.score_dict.get(source.discord_id, 0):
            case -1:
                return
            case 0:
                self.dislikes += 1
                self.score_dict[source.discord_id] = -1
            case 1:
                self.dislikes += 1
                self.likes -= 1
                self.score_dict[source.discord_id] = -11

    async def get_prompt_embed(
        self,
        queue_pos: str,
    ) -> Embed:
        description = ""
        if util.paused:
            description += "**Luka currently needs her graphics card, this request has been logged and will be processed as soon as Aiba is unpaused!**"
        if self.cfg_overridden:
            description += "\nYour server does not allow you to specify CFG Scale, the default will be used."
        if self.sample_steps_overridden:
            description += "\nYour server does not allow you to specify sample steps, the default will be used."
        builder = EmbedBuilder(
            title=f"Prompt Recieved",
            description=description,
            timestamp=self.date,
            fields=[
                Field(name="Prompt", value=self.original_prompt, inline=False),
                Field(
                    name="Requested by",
                    value=User.construct_mention(self.requestor_id),
                    inline=False,
                ),
                Field(
                    name="Queue Position",
                    value=queue_pos,
                ),
                Field(
                    name="Sample Steps",
                    value=self.sample_steps,
                ),
                Field(
                    name="CFG Scale",
                    value=self.cfg_scale,
                ),
            ],
        )
        return await builder.build()

    async def get_output_embed(self) -> Embed:
        builder = EmbedBuilder(
            title=self.original_prompt[:256].title(),
            description=f"Score: {self.score} (+{self.likes}, -{self.dislikes})",
            fields=[
                Field(
                    name="Requestor",
                    value=User.construct_mention(self.requestor_id),
                ),
                Field(name="Generated in", value=str(self.runtime) + " seconds"),
            ],
            timestamp=self.date,
            image=File(os.path.join(outputs_dir, self.output_filename)),
        )
        return await builder.build()


class Txt2ImgRequest(Request):
    def __init__(self, **kwargs):
        super().__init__(req_type=RequestType.txt2img, **kwargs)


class ArtifyRequest(Request):
    original_author_id: int

    def __init__(self, **kwargs):
        super().__init__(req_type=RequestType.artify, **kwargs)

    async def get_prompt_embed(
        self,
        queue_pos: str,
    ) -> Embed:
        description = ""
        if util.paused:
            description += "**Luka currently needs her graphics card, this request has been logged and will be processed as soon as Aiba is unpaused!**"
        builder = EmbedBuilder(
            title="Prompt Recieved",
            description=description,
            fields=[
                Field(name="Prompt", value=self.original_prompt, inline=False),
                Field(
                    name="Requested by",
                    value=User.construct_mention(self.requestor_id),
                    inline=False,
                ),
                Field(
                    name="Original Message by",
                    value=User.construct_mention(self.original_author_id),
                    inline=False,
                ),
                Field(
                    name="Queue Position",
                    value=queue_pos,
                ),
                Field(name="Sample Steps", value=self.sample_steps),
                Field(name="CFG Scale", value=self.cfg_scale),
            ],
            timestamp=self.date,
        )
        return await builder.build()

    async def get_output_embed(self):
        builder = EmbedBuilder(
            title=self.original_prompt[:256].title(),
            description=f"Score: {self.score} (+{self.likes}, -{self.dislikes})",
            fields=[
                Field(
                    name="Requestor", value=User.construct_mention(self.requestor_id)
                ),
                Field(
                    name="Original Author",
                    value=User.construct_mention(self.requestor_id),
                ),
                Field(name="Generated in", value=str(self.runtime) + " seconds"),
            ],
            timestamp=self.date,
            image=File(os.path.join(outputs_dir, self.output_filename)),
        )
        return await builder.build()


class Img2ImgRequest(Request):
    prompt: Optional[str]
    denoising_strength: Optional[float]
    original_denoising_strength: Optional[float]
    original_img_url: Optional[str]
    status: RequestStatus = RequestStatus.awaiting_prompt

    def __init__(self, **kwargs):
        super().__init__(req_type=RequestType.img2img, **kwargs)

    async def set_original_img(self, url: str) -> None:
        self.original_img_url = url

    async def get_prompt_embed(
        self,
        queue_pos: str,
    ) -> Embed:
        description = ""
        if util.paused:
            description += "**Luka currently needs her graphics card, this request has been logged and will be processed as soon as Aiba is unpaused!**"
        if self.original_cfg_scale:
            if self.original_cfg_scale > 30 or self.original_cfg_scale <= 0:
                description += "\nCFG Scale format not recognized -- using default. Please enter a decimal value between 0.0 and 30.0."
            else:
                description += "\nYour server does not allow you to specify CFG Scale, the default will be used."
        if self.original_sample_steps:
            if self.original_sample_steps > 150 or self.original_sample_steps <= 0:
                description += "\nSample Steps format not recognized -- using default. Please enter an integer value between 0 and 150."
            else:
                description += "\nYour server does not allow you to specify sample steps, the default will be used."
        if self.original_denoising_strength:
            description += "\nDenoising strength format not recognized -- using default. Please enter a decimal value between 0.0 and 1.0."

        builder = EmbedBuilder(
            title="Prompt Recieved",
            description=description,
            fields=[
                Field(name="Prompt", value=self.original_prompt, inline=False),
                Field(
                    name="Requested by",
                    value=User.construct_mention(self.requestor_id),
                    inline=False,
                ),
                Field(
                    name="Queue Position",
                    value=queue_pos,
                ),
                Field(
                    name="Sample Steps",
                    value=self.sample_steps,
                ),
                Field(
                    name="CFG Scale",
                    value=self.cfg_scale,
                ),
                Field(
                    name="Denoising Strength",
                    value=self.denoising_strength,
                ),
            ],
            timestamp=self.date,
            thumbnail_url=self.original_img_url,
        )
        return await builder.build()

    async def get_output_embed(self):
        builder = EmbedBuilder(
            title=self.original_prompt[:256].title(),
            description=f"Score: {self.score} (+{self.likes}, -{self.dislikes})",
            fields=[
                Field(
                    name="Requestor",
                    value=User.construct_mention(self.requestor_id),
                    inline=False,
                ),
                Field(name="Generated in", value=str(self.runtime) + " seconds"),
                Field(
                    name="Denoising Strength",
                    value=self.denoising_strength,
                ),
            ],
            timestamp=self.date,
            image=File(os.path.join(outputs_dir, self.output_filename)),
            thumbnail_url=self.original_img_url,
        )
        return await builder.build()

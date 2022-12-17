import re
from enum import Enum
from typing import List, Dict, Optional, Union

import disnake
from beanie import Document
from pydantic import BaseModel, validator

from models import request
from models.embed import EmbedBuilder, Field


class SamplerIndices(Enum):
    euler = "Euler"


class GuildSettings(BaseModel):
    neg_prompt: List[str] = None
    prompt_improvement: List[str] = None
    steps: int = 20
    cfg_scale: int = 7
    denoising_strength: float = 0.75
    sampler_index: SamplerIndices = SamplerIndices.euler
    width: int = 512
    height: int = 512
    cfg_override: bool = True
    steps_override: bool = True
    visible_prompts: bool = True
    delete_prompts: bool = True

    @validator("neg_prompt")
    def default_neg_prompt(cls, v):
        return (
            v
            if v is not None
            else [
                "(blurry:1.5)",
                "lowres",
                "bad anatomy",
                "bad hands",
                "(text:1.5)",
                "error",
                "missing fingers",
                "extra digit",
                "fewer digits",
                "cropped",
                "worst quality",
                "low quality",
                "normal quality",
                "jpeg artifacts",
                "signature",
                "watermark",
                "username",
                "artist name",
                "bad eyes",
            ]
        )

    @validator("prompt_improvement")
    def default_prompt_improvement(cls, v):
        return v if v is not None else ["(masterpiece: 1.5)", "(best quality: 1.5)"]

    @property
    def negative_prompt(self):
        return ", ".join([tag for tag in self.neg_prompt])

    @property
    def prompt_improvement_string(self):
        return ", ".join([tag for tag in self.prompt_improvement])

    async def get_overview_embed(self):
        builder = EmbedBuilder(
            title="Aiba Configuration",
            fields=[
                Field(
                    name="Visible Prompt Messages?",
                    value=self.visible_prompts,
                ),
                Field(
                    name="Delete Prompt Messages?",
                    value=self.delete_prompts,
                ),
                Field(name="Sample Steps", value=self.steps),
                Field(name="Sample Steps Override", value=self.steps_override),
                Field(name="CFG Scale", value=self.cfg_scale),
                Field(name="CFG Scale Override", value=self.cfg_override),
                Field(name="Resolution", value=f"{self.width}x{self.height}"),
                Field(name="Denoising Strength", value=self.denoising_strength),
                Field(name="Sampler Index", value=self.sampler_index.value),
                Field(
                    name="Automatic Prompt Improvement",
                    value=self.prompt_improvement_string,
                    inline=False,
                ),
                Field(name="Negative Prompt", value=self.negative_prompt, inline=False),
            ],
        )
        return await builder.build()


class GuildUserStats(BaseModel):
    name: Optional[str]
    requests: int = 0


class Guild(Document):
    class Settings:
        use_state_management = True
        state_management_replace_objects = True
        name = "guild"

    discord_id: str
    name: str
    settings: GuildSettings = None
    users: Dict[str, GuildUserStats] = None

    @property
    def int_discord_id(self):
        return int(self.discord_id)

    @validator("settings")
    def default_settings(cls, v):
        return v if v is not None else GuildSettings()

    @validator("users")
    def ensure_users(cls, v):
        return v if v is not None else {}

    @classmethod
    async def find_or_create(
        cls, discord_id: int = None, disnake_guild: disnake.Guild = None
    ) -> "Guild":
        qry_id = disnake_guild.id if disnake_guild is not None else discord_id
        if extant := await cls.find_one(Guild.discord_id == str(qry_id)):
            return extant
        else:
            return cls(
                discord_id=qry_id,
                name=disnake_guild.name if disnake_guild is not None else None,
            )

    @staticmethod
    def clean_prompt(prompt: str):
        tags = re.findall("\([a-zA-Z0-9 ]+:\s*\d+\)", prompt)
        cleaned_tags = {}
        for tag in tags:
            number = int(tag.split(":")[1][:-1].strip())
            new_number = number
            if number <= 0:
                new_number = 0.5
            elif number > 1.75:
                new_number = 1.75
            cleaned_tags[tag] = tag.replace(str(number), str(new_number))
        for tag, cleaned_tag in cleaned_tags.items():
            prompt = prompt.replace(tag, cleaned_tag)
        return prompt

    def validate_request(self, req: "request.Request"):
        clean_prompt = self.clean_prompt(req.prompt)
        req.original_prompt = clean_prompt
        req.prompt = clean_prompt + ", " + self.settings.prompt_improvement_string
        if not self.settings.cfg_override or req.cfg_scale is None:
            req.original_cfg_scale = req.cfg_scale
            req.cfg_scale = self.settings.cfg_scale
        if not self.settings.steps_override or req.sample_steps is None:
            req.original_sample_steps = req.sample_steps
            req.sample_steps = self.settings.steps
        return req

    async def load_modal_values(
        self,
        req: "request.Img2ImgRequest",
        prompt: str,
        cfg_scale: str = None,
        sample_steps: str = None,
        denoising_strength: str = None,
    ):
        settings = self.settings
        if cfg_scale:
            cfg_scale = float(cfg_scale)
        if sample_steps:
            sample_steps = int(sample_steps)
        if denoising_strength:
            denoising_strength = float(denoising_strength)
        clean_prompt = self.clean_prompt(prompt)
        req.original_prompt = clean_prompt
        req.prompt = clean_prompt + ", " + self.settings.prompt_improvement_string
        if (
            not settings.cfg_override
            or not cfg_scale
            or cfg_scale > 30
            or cfg_scale < 0
        ):
            req.original_cfg_scale = cfg_scale
            req.cfg_scale = settings.cfg_scale
        else:
            req.cfg_scale = cfg_scale
        if (
            not settings.steps_override
            or not sample_steps
            or sample_steps < 1
            or sample_steps > 150
        ):
            req.original_sample_steps = sample_steps
            req.sample_steps = settings.steps
        else:
            req.sample_steps = sample_steps
        if not denoising_strength or denoising_strength < 0 or denoising_strength > 1:
            req.original_denoising_strength = denoising_strength
            req.denoising_strength = settings.denoising_strength
        else:
            req.denoising_strength = denoising_strength
        return req

    def request_to_payload(
        self, req: Union["request.Request", "request.Img2ImgRequest"], data: str = None
    ):

        payload = {
            "prompt": req.prompt,
            "batch_size": 1,
            "neq_prompt": self.settings.negative_prompt,
            "steps": req.sample_steps,
            "cfg_scale": req.cfg_scale,
            "sampler_index": self.settings.sampler_index.value,
            "width": self.settings.width,
            "height": self.settings.height,
        }
        if data is not None:
            payload["init_images"] = [data]
            payload["denoising_strength"] = req.denoising_strength
        return payload

    async def log_request(
        self,
        discord_id: str,
    ):
        if self.users is None:
            self.users = {}
        stats = self.users.get(discord_id, GuildUserStats())
        stats.requests += 1
        self.users[discord_id] = stats
        await self.save_changes()

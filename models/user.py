from typing import Dict, List, Optional

import disnake
from beanie import Document


class User(Document):
    class Settings:
        use_state_management = True
        state_management_replace_objects = True
        name = "user"

    discord_id: str
    username: str
    req_count: int = 0
    favorites: List[str] = None
    guilds: List[str] = None
    requests: Dict[str, str] = None

    @property
    def int_discord_id(self):
        return int(self.discord_id)

    @property
    def mention(self):
        return f"<@{self.discord_id}>"

    @classmethod
    def construct_mention(cls, discord_id: int | str):
        return f"<@{discord_id}>"

    @classmethod
    async def find_or_create(
        cls, discord_id: int = None, disnake_user: disnake.User = None
    ) -> "User":
        qry_id = disnake_user.id if disnake_user is not None else discord_id
        if extant := await cls.find_one(User.discord_id == str(qry_id)):
            return extant
        else:
            return cls(
                discord_id=qry_id,
                username=disnake_user.name if disnake_user is not None else None,
            )

    @classmethod
    async def find_by_username(cls, username: str) -> Optional["User"]:
        username = username.casefold()
        if extant := await cls.find_one(User.username == username):
            return extant

    async def add_guild(self, guild_id: int):
        if self.guilds is None:
            self.guilds = []
        if guild_id not in self.guilds:
            self.guilds.append(str(guild_id))

    async def log_request(
        self,
        request_id: str,
        prompt: str,
    ):
        if self.requests is None:
            self.requests = {}
        self.requests[request_id] = prompt
        await self.save_changes()

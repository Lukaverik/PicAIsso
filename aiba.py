import logging

import disnake
from beanie import init_beanie
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from models.user import User
from models.guild import Guild
from models.request import Request

# Logging Setup
logger = logging.getLogger("disnake")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="../disnake.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


class Aiba(commands.Bot):
    def __init__(self):
        command_sync_flags = commands.CommandSyncFlags.default()
        command_sync_flags.sync_commands_debug = True
        intents = disnake.Intents.default()
        intents.message_content = True
        activity = disnake.Game(name="Stable Diffusion")
        command_prefix = "/"
        super().__init__(
            intents=intents,
            activity=activity,
            command_prefix=command_prefix,
            command_sync_flags=command_sync_flags,
        )

    # Test/Init commands/events
    async def on_ready(self):
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        await init_beanie(
            database=client["aiba"],
            document_models=[
                User,
                Guild,
                Request,
            ],
        )
        print(f"We have logged in as {self.user}")


aiba = Aiba()

import os
from typing import Union

import disnake
from dotenv import dotenv_values


values = dotenv_values()
token = values.get("DISCORD_TOKEN")
base_url = values.get("BASE_URL", "http://127.0.0.1:7860")
main_dir = os.path.split(os.path.abspath(__file__))[0]
guild_data_path = os.path.join(main_dir, "data/guilds.json")
user_data_path = os.path.join(main_dir, "data/users.json")
request_data_path = os.path.join(main_dir, "data/requests.json")
outputs_dir = os.path.join(main_dir, "outputs")

Interaction = Union[disnake.ApplicationCommandInteraction, disnake.ModalInteraction]

paused = False


def is_english_alphanum(s: str):
    return s.isalnum() and s.isascii()


def sanitized_file_name(prompt, requestor):
    dirty_filename = f"{prompt[:20]}{requestor}"
    dirty_filename = "".join(filter(is_english_alphanum, dirty_filename))
    dirty_filename = dirty_filename.replace(" ", "_")
    return dirty_filename + ".png"

import disnake
from disnake import TextInputStyle

from models.request import Img2ImgRequest
from models.request_queue import RequestQueue
from models.guild import Guild
from models.user import User


class Img2ImgModal(disnake.ui.Modal):
    request: Img2ImgRequest
    guild: Guild
    requestor: User

    def __init__(self, request: Img2ImgRequest, guild: Guild, requestor: User):
        self.request = request
        self.guild = guild
        self.requestor = requestor
        components = [
            disnake.ui.TextInput(
                label="Img2Img Prompt",
                custom_id="prompt",
                style=TextInputStyle.paragraph,
            ),
            disnake.ui.TextInput(
                label="CFG Scale",
                placeholder="How much the AI sticks to the prompt. Low = Stick to Prompt More",
                custom_id="cfg_scale",
                style=TextInputStyle.short,
                required=False,
            ),
            disnake.ui.TextInput(
                label="Sample Steps",
                placeholder="How many times the image is iterated on.",
                custom_id="steps",
                style=TextInputStyle.short,
                required=False,
            ),
            disnake.ui.TextInput(
                label="Denoising Strength",
                placeholder="How close to the original image the AI stays. Low = Little Change",
                custom_id="denoising_strength",
                style=TextInputStyle.short,
                required=False,
            ),
        ]
        super().__init__(
            title="Img2Img",
            custom_id=f"Img2Img-{request.requestor_id}",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction):
        if not self.request.original_img_url:
            await inter.response.send_message(
                "An Unexpected Error has occurred: Image Not Found"
            )
        await self.guild.load_modal_values(
            req=self.request,
            prompt=inter.text_values.get("prompt"),
            cfg_scale=inter.text_values.get("cfg_scale"),
            sample_steps=inter.text_values.get("steps"),
            denoising_strength=inter.text_values.get("denoising_strength"),
        )
        await self.requestor.log_request(
            request_id=self.request.request_id, prompt=self.request.prompt
        )
        await RequestQueue.add(
            req=self.request, inter=inter, guild=self.guild, requestor=self.requestor
        )
        embed = await self.request.get_prompt_embed(
            queue_pos=await RequestQueue.resolve_queue_pos(
                req_id=self.request.request_id
            )
        )
        await inter.response.send_message(
            embed=embed, ephemeral=not self.guild.settings.visible_prompts
        )


class NegativePromptAppendModal(disnake.ui.Modal):
    guild: Guild

    def __init__(self, inter_id: str, guild: Guild):
        self.guild = guild
        components = [
            disnake.ui.TextInput(
                label="Tags to Append",
                placeholder="Use Comma Separated Values",
                custom_id="value",
                style=TextInputStyle.paragraph,
            )
        ]
        super().__init__(
            title="Update Negative Prompt",
            custom_id=f"new_prompt-{inter_id}",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction):
        self.guild.settings.neg_prompt.extend(inter.text_values["value"].split(","))
        await self.guild.save_changes()
        await inter.response.send_message(
            f"{inter.author.mention} has updated this server's default negative prompt to ```{self.guild.settings.neg_prompt}```"
        )


class NegativePromptOverwriteModal(disnake.ui.Modal):
    guild: Guild

    def __init__(self, inter_id: str, guild: Guild):
        self.guild = guild
        components = [
            disnake.ui.TextInput(
                label="New Negative Prompt",
                placeholder="Use Comma Separated Values",
                value=guild.settings.negative_prompt,
                custom_id="value",
                style=TextInputStyle.paragraph,
            )
        ]
        super().__init__(
            title="Update Negative Prompt",
            custom_id=f"new_prompt-{inter_id}",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction):
        self.guild.settings.neg_prompt = inter.text_values["value"].split(",")
        await self.guild.save_changes()
        await inter.response.send_message(
            f"{inter.author.mention} has updated this server's default negative prompt to ```{self.guild.settings.neg_prompt}```"
        )

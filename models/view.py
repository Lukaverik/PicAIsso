import disnake
from disnake.ui import View

from emotes import thumbs_up, thumbs_down
from models.request import Request
from models.user import User


class ScoreView(View):
    request_id: str

    def __init__(self, request_id: str):
        super().__init__(timeout=None)
        self.request_id = request_id

    @disnake.ui.button(emoji=thumbs_up, style=disnake.ButtonStyle.success, row=0)
    async def like(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        request = await Request.get_by_id(mongo_id=self.request_id)
        requestor = await User.find_or_create(disnake_user=inter.author)
        request.like(source=requestor)
        await request.save_changes()
        await inter.message.edit(embed=await request.get_output_embed())
        await inter.response.defer(ephemeral=True)

    @disnake.ui.button(emoji=thumbs_down, style=disnake.ButtonStyle.danger, row=0)
    async def dislike(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        request = await Request.get_by_id(mongo_id=self.request_id)
        requestor = await User.find_or_create(disnake_user=inter.author)
        request.dislike(source=requestor)
        await request.save_changes()
        await inter.message.edit(embed=await request.get_output_embed())
        await inter.response.defer(ephemeral=True)


class RecordsView(View):
    user_id: str

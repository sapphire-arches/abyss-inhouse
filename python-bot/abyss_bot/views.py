import discord
import sqlalchemy as sa
import logging

from . import model
from .client import AbyssClient

logger = logging.getLogger(__name__)

class QueueView(discord.ui.View):
    get_queue_stmt = (sa
        .select(model.QueueEntry, model.User)
        .filter_by(serviced=False)
        .join(model.QueueEntry.user)
        .order_by(
            model.User.vip.desc(),
            model.User.subscriber.desc(),
            model.QueueEntry.enroll_time.asc(),
        ))

    get_skrub_stmt = get_queue_stmt.filter(
            model.User.vip == False,
            model.User.subscriber == False
        )

    def __init__(self, client, offset: int, page_size: int, skrub_mode: bool):
        super().__init__()

        self.offset = offset
        self.page_size = page_size
        self.client = client
        if skrub_mode:
            self.base_query = QueueView.get_skrub_stmt
        else:
            self.base_query = QueueView.get_queue_stmt

    def render_list(self):
        with self.client.sm.begin() as session:
            logger.info('Attempting render')

            query = self.base_query
            queue = session.execute(query.offset(self.offset).limit(self.page_size)).all()

            str = ''
            for (i, (qe, user)) in enumerate(queue):
                idx = i + 1 + self.offset
                str += f'{idx}. <@{user.discord_id}>'

                if user.subscriber:
                    str += ' (sub)'
                if user.vip:
                    str += ' (vip)'
                str += '\n'

                if len(str) > 1500:
                    str += '\n ... and more'
                    break
            return str

    @discord.ui.button(label='Prev', style=discord.ButtonStyle.grey, disabled=True)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.offset -= self.page_size
        if self.offset <= 0:
            self.offset = 0
            button.disabled = True

        await interaction.response.edit_message(
            content=self.render_list(),
            view=self,
        )

    @discord.ui.button(label='Next', style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.offset += self.page_size
        content = self.render_list()
        while len(content) < 2 and self.offset >= self.page_size:
            self.offset -= self.page_size
            content = self.render_list()

        if self.offset > 0:
            self.prev.disabled = False

        await interaction.response.edit_message(
            content=content,
            view=self,
        )

async def respond_with_view(client: AbyssClient, interaction: discord.Interaction, skrub_mode: bool):
    view = QueueView(client, 0, 15, skrub_mode)
    await interaction.response.send_message(
        content=view.render_list(),
        view=view,
        ephemeral=True,
    )

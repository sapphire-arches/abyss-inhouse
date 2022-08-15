import discord

from .config  import config

#===============================================================================
# Guild config
#===============================================================================

BIND_GUILD = config.get('guild', 'id', fallback=None)

#===============================================================================
# Client definition
#===============================================================================

class AbyssClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        if BIND_GUILD is not None:
            guild = discord.Object(id=int(BIND_GUILD))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

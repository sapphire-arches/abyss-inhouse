from discord import app_commands
from discord.ext import commands
from discord.utils import get
import asyncio
import discord
import logging
import os
import random
import signal
import string
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from . import model

#===============================================================================
# Logger setup
#===============================================================================

logging.basicConfig(level=logging.INFO)
logging.getLogger('asyncio').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.orm').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)

logger = logging.getLogger('abyss-bot')
logger.setLevel(level=logging.INFO)

#===============================================================================
# Config
#===============================================================================

# Guild hard-coded to abyss-dev for now
MY_GUILD = discord.Object(id=1000819141596414002)
INHOUSE_CHANNEL_ID = 1000819141596414005
ROLES_CHANNEL_ID = 1006837412787388457
ROLES_MESSAGE_ID = 1006837453870608435

# Mapping from internal name to whatever the guild actually names the roles
ROLE_NAMES = {
    'VIP': 'VIP',
    'SUB': 'SUB',
}

#===============================================================================
# Client definition
#===============================================================================
class AbyssClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = AbyssClient(intents=intents)

#===============================================================================
# Handy queries
#===============================================================================
get_queue_stmt = (sa
    .select(model.QueueEntry, model.User)
    .join(model.QueueEntry.user)
    .order_by(
        model.User.vip,
        model.User.subscriber,
    ))

clear_queue_stmt = sa.delete(model.QueueEntry)


#===============================================================================
# global state
# TODO: persist this to postgresql
#===============================================================================


TeamCompV = 0
TeamCompS = 5
TeamCompNS = 0

#===============================================================================
# Client event handlers
#===============================================================================
@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')
    client.guild = client.get_guild(MY_GUILD.id)
    client.channel = client.guild.get_channel(INHOUSE_CHANNEL_ID)

    react_channel = client.guild.get_channel(ROLES_CHANNEL_ID)
    react_message = await react_channel.fetch_message(ROLES_MESSAGE_ID)
    for react in react_message.reactions:
        logger.info(f'React message reaction: {react.emoji} {react.count} times')

#===============================================================================
# Commands
#===============================================================================

@client.tree.command(
    description='Join the queue for the abyss inhouse'
)
async def join_abyss(interaction: discord.Interaction):
    global FullList, FullListVIP, FullListNonSub
    global Queue, QueueVIP, QueueNonSub
    # TODO: require steam ID to join
    user = interaction.user

    role_vip = None
    role_sub = None

    with client.sm.begin() as session:
        db_user = session.execute(sa.select(model.User).filter_by(discord_id=user.id)).scalar_one_or_none()

        if db_user is None:
            db_user = model.User(
                discord_id=user.id,
            )
            session.add(db_user)

        db_user.discord_username = user.name

        for role in interaction.guild.roles:
            if role.name == ROLE_NAMES['VIP']:
                role_vip = role
            elif role.name == ROLE_NAMES['SUB']:
                role_sub = role

        db_user.vip = user.get_role(role_vip.id) is not None
        db_user.subscriber = user.get_role(role_sub.id) is not None

        # Make sure the user is up to date
        session.flush()

        queue_entry = model.QueueEntry(
            user_id=db_user.id,
            enroll_time=sa.sql.functions.now()
        )

        session.add(
            queue_entry
        )

        try:
            session.commit()
            await interaction.response.send_message(
                content=f'Added {user.name} to the queue. Use /list_abyss to see the current queue'
            )
        except sa.exc.IntegrityError:
            session.rollback()
            await interaction.response.send_message(
                content="You're already in the queue for today!"
            )

@client.tree.command(
    description='View the current queue for the abyss'
)
async def list_abyss(interaction: discord.Interaction):
    str = 'Abyss inhouse queue:\n>>> '

    with client.sm.begin() as session:
        queue = session.execute(get_queue_stmt).all()
        for (i, (qe, user)) in enumerate(queue):
            str += f'{i+1}. {user.discord_username}\n'

    await interaction.response.send_message(
        content=str,
        ephemeral=True
    )

@client.tree.command(
    description='Make random teams'
)
async def make_teams(interaction: discord.Interaction):
    # TODO: restrict this to only people with the "Abyss Inhouse Admin" role
    TeamOne = randomTeam()
    TeamTwo = randomTeam()
    await client.channel.send("Team 1: " + ', '.join(TeamOne))
    await client.channel.send("Team 2: " + ', '.join(TeamTwo))

def randomTeam():
    Team = []
    global QueueNonSub
    global Queue
    global QueueVIP

    if int(TeamCompNS) > 0 :
        NSList = random.sample(QueueNonSub, int(TeamCompNS))
        Team.extend(NSList)
        copyNSQueue = QueueNonSub.copy()
        QueueNonSub.clear()
        QueueNonSub = [x for x in copyNSQueue if x not in NSList]
    if int(TeamCompS) > 0 :
        SubList = random.sample(Queue, int(TeamCompS))
        Team.extend(SubList)
        copySubQueue = Queue.copy()
        Queue.clear()
        Queue = [x for x in copySubQueue if x not in SubList]
    if int(TeamCompV) > 0 :
        VIPList = random.sample(QueueVIP, int(TeamCompV))
        Team.extend(VIPList)
        copyVIPQueue = QueueVIP.copy()
        QueueVIP.clear()
        QueueVIP = [x for x in copyVIPQueue if x not in VIPList]

    return Team

@client.tree.command(
    description='Set the team composition'
)
@app_commands.describe(
    vip_count='The number of VIPs per team',
    sub_count='The number of subscribers per team',
    nonsub_count='The number of non-subscribers per team',
)
async def set_team_comp(interaction: discord.Interaction, vip_count: int, sub_count: int, nonsub_count: int):
    # TODO: restrict this to "Abyss Admin" roles only
    global TeamCompV
    global TeamCompS
    global TeamCompNS
    TeamCompV = vip_count
    TeamCompS = sub_count
    TeamCompNS = nonsub_count
    await interaction.response.send_message(
        content="Team comp set to VIPs:" + TeamCompV + " Subs:" + TeamCompS + " NonSubs:" + TeamCompNS
    )

@client.tree.command(
    description='Create an ephemeral channel for sharing the lobby password'
)
async def create_lobby(interaction: discord.Interaction):
    # TODO: Send the password to the admins first (in an admin channel?), then
    # create the ephemeral channel and add the users from the queue to it
    # TODO: wire up role creation/assignment for the games
    await interaction.response.defer(thinking=True)
    guild = client.guild
    #admin_role = get(guild.roles, name="Admin")
    #await guild.create_role(name="AbyssGame")
    # AG_role = get(guild.roles, name="AbyssGame")
    #overwrites = {
    #    guild.default_role: discord.PermissionOverwrite(read_messages=False),
    #    AG_role: discord.PermissionOverwrite(read_messages=True),
    #    admin_role: discord.PermissionOverwrite(read_messages=True)
    #}
    channel = await guild.create_text_channel('abyss_lobby')
    await channel.send("Lobby Name: The Abyss")
    await channel.send("Lobby Password: " + ''.join(random.choices(string.ascii_lowercase, k=8)))

    channel = await guild.create_voice_channel("abyss_DIRE")
    channel = await guild.create_voice_channel("abyss_RADIANT")

    await interaction.followup.send(
        content='Created epehemeral channels for lobby',
    )

@client.tree.command(
    description='Delete the ephemeral lobby channels'
)
async def delete_lobby(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    guild = client.guild

    async def delete_channel(channel):
        channel = discord.utils.get(guild.channels, name=channel)
        if channel is not None:
            channel.delete()
            await interaction.followup.send(f'Deleted ephemeral channel {channel}')
        else:
            await interaction.followup.send(f'Failed to delet channel {channel}, is it already deleted?')

    await asyncio.gather(
        delete_channel('abyss_lobby'),
        delete_channel('abyss_RADIANT'),
        delete_channel('abyss_DIRE'),
    )

    await interaction.followup.send('Deleted all channels and roles')

@client.tree.command(
    description='Clear all queues'
)
async def restart_abyss(interaction: discord.Interaction):
    with client.sm.begin() as session:
        session.execute(clear_queue_stmt)

    await interaction.response.send_message(
        content="The Abyss has been restarted."
    )

#===============================================================================
# asyncio loop execution
#===============================================================================
def get_env(name):
    val = os.getenv(name)
    if val is None:
        err = f'Missing {name} in the environment'
        logger.error(err)
        raise ValueError(err)
    return val

async def main():
    token = get_env('DISCORD_TOKEN')
    db_client_string = get_env('DB_CLIENT_STRING')

    client.engine = sa.create_engine(db_client_string, future=True)
    client.sm = sessionmaker(client.engine, future=True)

    loop = asyncio.get_running_loop()

    def sigterm_to_keyboardint():
        raise KeyboardInterrupt("SIGTERM recieved")

    loop.add_signal_handler(signal.SIGTERM, sigterm_to_keyboardint)

    try:
        await client.login(token)
        await client.connect()
    except Exception as e:
        logger.error('Bot exploded', exc_info=e)

asyncio.run(main())

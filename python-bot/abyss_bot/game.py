#
# Game management
#

from discord import app_commands
import discord
import sqlalchemy as sa

import logging

from . import model

logger = logging.getLogger(__name__)

class Game(app_commands.Group):
    """ Game management commands

    """
    def __init__(self):
        super().__init__(
            description = "Game management",
            default_permissions=None,
        )

GAME = Game()

def get_current_game(session):
    """ Get the currently running game """
    # TODO: better selection logic than relying on DB id ordering?
    current_game = session.execute(
        sa.select(model.Game)
            .order_by(model.Game.id.desc())
            .filter(model.Game.dota2_match_id == None)
            .limit(1)
    ).scalar_one_or_none()

    if current_game is None:
        current_game = model.Game()

        session.add(current_game)

    return current_game

@GAME.command(
    description='Add new users to the current game (if one isn\'t running, it will be started)'
)
async def add(interaction: discord.Interaction, user: discord.User):
    logger.info(f'Should add {user.id} to a game')

    did_add = False

    guild = interaction.guild

    with interaction.client.sm.begin() as session:
        current_game = get_current_game(session)

        player = session.execute(
            sa.select(model.GamePlayer)
                .join(model.User)
                .filter(model.User.discord_id == user.id)
                .filter(model.GamePlayer.game_id == current_game.id)
        ).scalar_one_or_none()

        if player is None:
            db_user = model.get_db_user(session, user)

            if db_user is None:
                db_user = model.User(
                    discord_id=user.id,
                    discord_username=user.name,
                )
            session.add(db_user)

            player = model.GamePlayer(
                user=db_user,
                game=current_game,
            )

            current_game.players.append(player)
            did_add = True

        if player.removed:
            did_add = True

        member = guild.get_member(user.id)
        if member is None:
            member = await guild.fetch_member(user.id)

        if current_game.role_id is not None:
            role = discord.Object(id=current_game.role_id)
            await member.add_roles(role)

        if current_game.channel_id is not None:
            channel = guild.get_channel(current_game.channel_id)
            if channel is None:
                channel = await guild.fetch_channel(current_game.channel_id)
            await channel.send(
                content=f'Hi <@{user.id}>, welcome to the game!',
            )


        player.removed = False

        session.add(player)
        session.add(current_game)

    if did_add:
        # TODO: Add game role to player, if the game role exists
        await interaction.response.send_message(
            content=f'Added <@{user.id}> to the current game',
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            content=f'<@{user.id}> was already in the game',
            ephemeral=True,
        )

@GAME.command(
    description='Remove a user from a game'
)
async def remove(interaction: discord.Interaction, user: discord.User):
    logger.info(f'Should remove {user.id} from a game')

    with interaction.client.sm.begin() as session:
        current_game = get_current_game(session)

        player = session.execute(
            sa.select(model.GamePlayer)
                .join(model.User)
                .filter(model.User.discord_id == user.id)
                .filter(model.GamePlayer.game_id == current_game.id)
        ).scalar_one_or_none()

        if player is None:
            await interaction.response.send_message(
                content=f'<@{user.id}> was never added to this game',
                ephemeral=True,
            )

        if player.removed:
            await interaction.response.send_message(
                content=f'<@{user.id}> is already not in the game',
                ephemeral=True,
            )
        else:
            # TODO: remove game role from player
            player.removed = True
            await interaction.response.send_message(
                content=f'<@{user.id}> removed from the current game',
                ephemeral=True,
            )

            guild = interaction.guild
            member = guild.get_member(user.id)
            if member is None:
                member = await guild.fetch_member(user.id)
            role = guild.get_role(current_game.role_id)

            try:
                await member.remove_roles(role)
            except Exception as e:
                logger.warn('Failed to remove role {role.id} from {member.id}', exc_info = e)


current_users_query = (
        sa.select(model.User)
            .join(model.GamePlayer)
            .filter(model.GamePlayer.removed == False)
    )

@GAME.command(
    description='List the people currently in the game'
)
async def list(interaction: discord.Interaction):
    with interaction.client.sm.begin() as session:
        current_game = get_current_game(session)

        players = session.execute(
            current_users_query
                .filter(model.GamePlayer.game_id == current_game.id)
        ).scalars().all()

        player_str = 'Currently in the game:'
        for user in players:
            player_str += f'\n- <@{user.discord_id}>'

    await interaction.response.send_message(
        content=player_str,
        ephemeral=True,
    )

@GAME.command(
    description='Start a game (moving users to temporary channel and generating a lobby password)'
)
async def start(interaction: discord.Interaction):
    logger.info(f'Should start a game')

    # TODO: create game channel + role, and add all players to it
    player_str = ''

    guild = interaction.guild
    client = interaction.client

    with client.sm.begin() as session:
        current_game = get_current_game(session)

        users = session.execute(
            current_users_query
                .filter(model.GamePlayer.game_id == current_game.id)
        ).scalars().all()

        player_str = ','.join(map(
            lambda u: f'<@{u.discord_id}>',
            users
        ))

        role = await guild.create_role(
            name=f'Abyss Game {current_game.id}',
        )

        # TODO: things may explode messily from here on out, and we should
        # clean up the role in that case

        # Create the channel
        channel = await guild.create_text_channel(
            name=f'abyss-game-{current_game.id}',
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True),
                client.user: discord.PermissionOverwrite(
                    read_messages=True,
                    manage_channels=True,
                ),
            },
        )

        for user in users:
            member = guild.get_member(user.discord_id)
            if member is None:
                logger.info(f'User {user.discord_id} not in cache, attempting fetch')
                member = await guild.fetch_member(user.discord_id)

            if member is None:
                logger.warn(f'Can not add {user.discord_id} to role {role.id}, not found in guild')
                continue

            logger.info(f'Adding user {user.discord_id} to role {role.id}')

            await member.add_roles(role)
            await channel.send(
                content=f'Hi <@{member.id}>, welcome to the game'
            )

        current_game.role_id = role.id
        current_game.channel_id = channel.id


    await interaction.response.send_message(
        content=f'Started a game with ' + player_str,
        ephemeral=True,
    )

@GAME.command(
    description='Mark a game as complete',
)
async def complete(interaction: discord.Interaction, match_id: int):
    logger.info(f'Marking game as complete')

    guild = interaction.guild

    with interaction.client.sm.begin() as session:
        current_game = get_current_game(session)

        current_game.dota2_match_id = match_id

        role = guild.get_role(current_game.role_id)
        if role is not None:
            await role.delete(reason='Game complete')

        channel = guild.get_channel(current_game.channel_id)
        if channel is None:
            channel = await guild.fetch_channel(current_game.channel_id)

        if channel is not None:
            await channel.delete(reason='Game complete')

        next_game = model.Game()
        session.add(next_game)

    await interaction.response.send_message(
        content=f'Marked game as complete with Dota2 MatchID {match_id}',
        ephemeral=True,
    )

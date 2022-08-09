import discord
from discord.ext import commands
from discord.utils import get
import os
import random
import string

bot = commands.Bot(command_prefix='.')

QueueNonSub = []
Queue = []
QueueVIP = []
FullListNonSub = []
FullList = []
FullListVIP = []
TeamCompV = 0
TeamCompS = 5
TeamCompNS = 0

@bot.command()
async def joinAbyssNonSub(ctx):
  if ctx.author.id in FullListNonSub :
    await ctx.send("You have already queued for the night.")
  else :
    QueueNonSub.append(ctx.author.name)
    FullListNonSub.append(ctx.author.id)
    await ctx.send("Added " + ctx.author.name + " to the queue.")

@bot.command()
@commands.has_role("SUB")
async def joinAbyss(ctx):
  if ctx.author.id in FullList :
    await ctx.send("You have already queued for the night.")
  else :
    Queue.append(ctx.author.name)
    FullList.append(ctx.author.id)
    await ctx.send("Added " + ctx.author.name + " to the queue.")

@bot.command()
@commands.has_role("VIP")
async def joinAbyssVIP(ctx):
  if ctx.author.id in FullListVIP :
    await ctx.send("You have already queued for the night.")
  else :
    QueueVIP.append(ctx.author.name)
    FullListVIP.append(ctx.author.id)
    await ctx.send("Added " + ctx.author.name + " to the queue.")

@bot.command()
async def listAbyss(ctx):
  if len(Queue) > 0 :
    await ctx.send("\nSubs:" + '\n'.join(Queue))
  if len(QueueNonSub) > 0 :
    await ctx.send("\nNon Subs:" + '\n'.join(QueueNonSub))
  if len(QueueVIP) > 0 :
    await ctx.send("\nVIPs:" + '\n'.join(QueueVIP))
  else :
    await ctx.send("No one is in the queue.")

@bot.command()
async def makeTeams(ctx):
  TeamOne = randomTeam()
  TeamTwo = randomTeam()
  await ctx.send("Team 1: " + ', '.join(TeamOne))
  await ctx.send("Team 2: " + ', '.join(TeamTwo))

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

@bot.command()
async def setTeamComp(ctx, arg1, arg2, arg3):
  global TeamCompV
  global TeamCompS
  global TeamCompNS
  TeamCompV = arg1
  TeamCompS = arg2
  TeamCompNS = arg3
  await ctx.send("Team comp set to VIPs:" + TeamCompV + " Subs:" + TeamCompS + " NonSubs:" + TeamCompNS)

@bot.command()
async def createLobby(ctx):
  guild = ctx.guild
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

@bot.command()
async def deleteLobby(ctx):
  guild = ctx.guild
  existing_channel = discord.utils.get(guild.channels, name="abyss_lobby")
  #role_object = discord.utils.get(ctx.message.guild.roles, name="AbyssGame")
  #await role_object.delete()

   # if the channel exists
  if existing_channel is not None:
    await existing_channel.delete()
  # if the channel does not exist, inform the user
  else:
    await ctx.send(f'No channel was found')

  existing_channel = discord.utils.get(guild.channels, name="abyss_RADIANT")

   # if the channel exists
  if existing_channel is not None:
    await existing_channel.delete()
  # if the channel does not exist, inform the user
  else:
    await ctx.send(f'No channel was found')

  existing_channel = discord.utils.get(guild.channels, name="abyss_DIRE")

   # if the channel exists
  if existing_channel is not None:
    await existing_channel.delete()
  # if the channel does not exist, inform the user
  else:
    await ctx.send(f'No channel was found')

@bot.command()
async def restartAbyss(ctx):
  Queue.clear()
  FullList.clear()
  QueueVIP.clear()
  FullListVIP.clear()
  await ctx.send("The Abyss has been restarted.")

@bot.command()
async def make_channel(ctx):
    guild = ctx.guild
    member = ctx.author
    admin_role = get(guild.roles, name="Admin")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True),
        admin_role: discord.PermissionOverwrite(read_messages=True)
    }
    channel = await guild.create_text_channel('secret', overwrites=overwrites)

try:
    bot.run(os.getenv('TOKEN'))
except:
    os.system("kill 1")

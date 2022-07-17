import discord
from discord.ext import commands
import json
import os
from keep_alive import keep_alive
from discord.ext import tasks
import math
import random
import datetime
import time

token = "token"
intents = discord.Intents.default()
intents.members = True
command_prefix = "!" 
bot = commands.Bot(command_prefix=command_prefix)
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f'You are connected to {bot.user.name}')

    members = 0
    for guild in bot.guilds:
        members += guild.member_count - 1

    await bot.change_presence(activity = discord.Activity(
        type = discord.ActivityType.watching,
        name = f'{members} members'
    ))
	
@bot.command()
@commands.has_permissions(ban_members = True)
async def ban(ctx, member : discord.Member, *, reason = None):
    await member.ban(reason = reason)
    await ctx.send("User has been banned.")

@bot.command()
@commands.has_permissions(administrator = True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split("#")

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.mention}')
            return

with open('reports.json', encoding='utf-8') as f:
  try:
    report = json.load(f)
  except ValueError:
    report = {}
    report['users'] = []

@bot.command()
@commands.has_permissions(manage_roles=True, ban_members=True)
async def warn(ctx,user:discord.User,*reason:str):
  author = ctx.author
  if not reason:
    await ctx.send("Please provide a reason")
    return
  reason = ' '.join(reason)
  await ctx.send(f'**{user.mention} has been warned by {author.name}.**')
  await user.send(f'You have been warned in **{ctx.guild.name}** by **{author.name}**.')
  for current_user in report['users']:
    if current_user['name'] == user.name:
      current_user['reasons'].append(reason)
      break
  else:
    report['users'].append({
      'name':user.name,
      'reasons': [reason,]
    })
  with open('reports.json','w+') as f:
    json.dump(report,f)

  with open('reports.json','w+') as f:
    json.dump(report,f)
  if len(report['users']) >= 7:
    await user.kick(reason='You reached 7 warnings')

@bot.command()
async def warnings(ctx,user:discord.User):
  for current_user in report['users']:
    if user.name == current_user['name']:
      await ctx.send(f"**{user.name} has been reported {len(current_user['reasons'])} times : {','.join(current_user['reasons'])}**")
      break
  else:
    await ctx.send(f"**{user.name} has never been reported**")

@bot.command()
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"Set the slowmode delay in this channel to {seconds} seconds!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unmute(ctx, member: discord.Member):
   mutedRole = discord.utils.get(ctx.guild.roles, name="Muted")

   await member.remove_roles(mutedRole)
   await member.send(f" you have unmutedd from: - {ctx.guild.name}")
   embed = discord.Embed(title="unmute", description=f" unmuted-{member.mention}",colour=discord.Colour.light_gray())
   await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    guild = ctx.guild
    mutedRole = discord.utils.get(guild.roles, name="Muted")

    if not mutedRole:
        mutedRole = await guild.create_role(name="Muted")

        for channel in guild.channels:
            await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=False)
    embed = discord.Embed(title="muted", description=f"{member.mention} was muted ", colour=discord.Colour.light_gray())
    embed.add_field(name="reason:", value=reason, inline=False)
    await ctx.send(embed=embed)
    await member.add_roles(mutedRole, reason=reason)
    await member.send(f" you have been muted from: {guild.name} reason: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
  await bot.kick(member)
  await ctx.send(f'User {member} has been kicked')


@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def clean(ctx, limit: int):
        await ctx.channel.purge(limit=limit)
        await ctx.send('Cleared by {}'.format(ctx.author.mention))
        await ctx.message.delete()

@clean.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You cant do that!")

sent_users = []

@bot.command(aliases=["user-info"])
async def userinfo(ctx, member: discord.Member = None):
    if not member:  # if member is no mentioned
        member = ctx.message.author  # set member as the author
    roles = [role for role in member.roles[1:]]  # don't get @everyone
    embed = discord.Embed(colour=discord.Colour.purple(), timestamp=ctx.message.created_at,
                          title=f"User Info - {member}")
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f"Requested by {ctx.author}")

    embed.add_field(name="ID:", value=member.id)
    embed.add_field(name="Display Name:", value=member.display_name)

    embed.add_field(name="Created Account On:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
    embed.add_field(name="Joined Server On:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))

    embed.add_field(name="Roles:", value="".join([role.mention for role in roles]))
    embed.add_field(name="Highest Role:", value=member.top_role.mention)
    print(member.top_role.mention)
    await ctx.send(embed=embed)

@bot.command(aliases= ["server-info"])
async def server(ctx):
    total_text_channels = len(ctx.guild.text_channels)
    total_voice_channels = len(ctx.guild.voice_channels)
    total_channels = total_text_channels  + total_voice_channels 

    emb = discord.Embed(color=discord.Colour.blue(), timestamp=datetime.datetime.utcnow())
    emb.set_author(name=f"Server Info - {ctx.guild.name}")

    emb.add_field(name="Server Name:", value=ctx.guild.name, inline=False)
    emb.add_field(name="Server ID:", value=ctx.guild.id, inline=False)
    emb.add_field(name="Owner:", value=ctx.guild.owner, inline=False)
    emb.add_field(name="Region:", value=ctx.guild.region, inline= False)
    emb.add_field(name= "Members count:", value= ctx.guild.member_count, inline= False)
    emb.add_field(name= "Channels count:", value= f"{total_text_channels} Text channels\n{total_voice_channels} voice channels", inline= False)
    emb.add_field(name= "Created on:", value=ctx.guild.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
    emb.set_footer(text= ctx.author)
    emb.set_thumbnail(url= bot.user.avatar_url)
    await ctx.send(embed=emb)

@bot.command(aliases=['h'])
async def help(ctx):
    print("Help command accepted!")
    embed = discord.Embed(title="Commands", description="Commands avaliable", color=discord.Color.red(), url="https://github.com/S1NSnipez")
    embed.add_field(name="ban",value="Bans a mentioned user")
    embed.add_field(name="clean",value="Purges a number of messages")
    embed.add_field(name="help",value="Shows this message")
    embed.add_field(name="kick",value="Kicks a mentioned user")
    embed.add_field(name="mute",value="Mutes a user")
    embed.add_field(name="server-info",value="Fetches the server's info")
    embed.add_field(name="slowmode",value="Sets slowmode for a certain channel")
    embed.add_field(name="unban",value="Unbans a past banned user")
    embed.add_field(name="unmute",value="Unmutes a user")
    embed.add_field(name="user-info",value="Fetches a user's info")
    embed.add_field(name="warn",value="Warns a user")
    embed.add_field(name="warnings",value="Fetches a user's warnings")
    embed.set_footer(text = "Made by [Paragonii](https://github.com/Paragonii)")
    await ctx.send(embed=embed)

@bot.command(aliases=['sayembed'])
async def embed(ctx, title: str, description: str):
    embed = discord.Embed(
        title=title,
        description=description,
        colour=discord.Color.green()
        )
    
    await ctx.channel.send(embed=embed)
		     
try:
    keep_alive()
    bot.run(token)
except discord.errors.LoginFailure:
    print("That token does not work!")
    exit(0)

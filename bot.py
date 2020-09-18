import os
import random
import discord
import datetime
from dotenv import load_dotenv
from discord.ext import commands

# set to true to read bot info form the config file
# or false to read from env variables
debug = False

load_dotenv()


if debug == True:
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    print(config.sections())
    TOKEN = config['discord']['BOT_TOKEN']
    GUILD = config['discord']['GUILD']
    CHANNEL = config['discord']['CHANNEL']
    bot = commands.Bot(command_prefix='*')
else:
    import environ
    env = environ.Env(DEBUG=(bool, False))  
    TOKEN = env('BOT_TOKEN')
    GUILD = env('GUILD')
    CHANNEL = env('CHANNEL')
    bot = commands.Bot(command_prefix='#')

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="cocktails"))
    print('My Ready is Body')
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    print(f'{bot.user.name} has connected to Discord!')
    print(f'{guild.name}(id: {guild.id})')

@bot.command()
async def newdrink(ctx):
    channel = ctx.channel
    ingredient = []

    async def exit_check():
        print(message_response.content)
        if message_response.content == "exit":
            try: 
                await ctx.message.delete()
            except: 
                print("failed to delete ctx message")
            try:
                await send2.delete()
            except:
                None
            await send.delete()
            await message_response.delete()
            return True
        else:
            return False

    def check(m):
        return m.author == ctx.author and m.channel == channel

    send = await ctx.send('if you want to quit at any time you can just say "exit"')
    send2 = await ctx.send('Name of the drink: ')
    message_response = await bot.wait_for('message', check=check)
    if await exit_check(): return
    name = str(message_response.content)
    await ctx.message.delete()
    await send.delete()
    await send2.delete()
    await message_response.delete()

    send = await ctx.send('discription: ')
    message_response = await bot.wait_for('message', check=check)
    if await exit_check(): return
    description = str(message_response.content)
    await send.delete()
    await message_response.delete()

    send = await ctx.send('image url: ')
    send2 = await ctx.send('imgur is a good place to upload!')
    message_response = await bot.wait_for('message', check=check)
    if await exit_check(): return
    url = str(message_response.content)
    await send.delete()
    await send2.delete()
    await message_response.delete()

    send = await ctx.send('how many ingredients: ')
    message_response = await bot.wait_for('message', check=check)
    if await exit_check(): return
    ingredients = int(message_response.content)
    await send.delete()
    await message_response.delete()

    for i in range(1,ingredients + 1):
        send = await ctx.send('ingredients #' + str(i) + ': ')
        message_response = await bot.wait_for('message', check=check)
        if await exit_check(): return
        ingredient.append(str(message_response.content))
        await send.delete()
        await message_response.delete()


    send = await ctx.send('makeing instructions: ')
    message_response = await bot.wait_for('message', check=check)
    if await exit_check(): return
    instructions = str(message_response.content)
    await send.delete()
    await message_response.delete()

    def list():
        list = ""
        for i in range(ingredients):
            list = list + ingredient[i] + "\n"
        return list

    embed = discord.Embed(title=name, description=description, color=discord.Color.blue())
    embed.set_thumbnail(url=url)
    embed.add_field(name="ingredients", value=list())
    embed.add_field(name="instructions", value=instructions)

    await ctx.send(embed=embed)

@bot.command()
async def randomdrink(ctx):
    print("random")

bot.run(TOKEN)
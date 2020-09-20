import os
import random
import ast
import asyncio
import pyimgur
import discord
from dotenv import load_dotenv
from discord.ext import commands
from databases import Database
from pbwrap import Pastebin

# set to true to read bot info form the config file
# or false to read from env variables
development = False
owner_id = "102131189187358720"

load_dotenv()

#local file for development

if development == True:
    import configparser
    print("development mode")
    config = configparser.ConfigParser()
    config.read('config.ini')
    bot = commands.Bot(command_prefix='*')
    TOKEN = config['discord']['BOT_TOKEN']
    GUILD = config['discord']['GUILD']
    CHANNEL = config['discord']['CHANNEL']
    database = Database(config['discord']['database'])
    im = pyimgur.Imgur(config['discord']['imgur_token'])
    pb = Pastebin(config['discord']['pastebin_key'])
else:
    import environ
    env = environ.Env(DEBUG=(bool, False))
    bot = commands.Bot(command_prefix='#')
    TOKEN = env('BOT_TOKEN')
    GUILD = env('GUILD')
    CHANNEL = env('CHANNEL')
    database = Database(env('CLEARDB_DATABASE_URL'))
    im = pyimgur.Imgur(env('imgur_token'))
    pb = Pastebin(env('pastebin_key'))

#unused, keeping to save the create table command
async def setup_db(creds):
    database = Database(creds)
    query = """CREATE TABLE IF NOT EXISTS `cocktails` (`name` VARCHAR(255), `discription` VARCHAR(255), `image` VARCHAR(255), `ingredients` VARCHAR(255), `instructions` VARCHAR(255), `author` VARCHAR(255));"""
    await database.execute(query=query)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Making Drinks"))
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    print(f'{bot.user.name} has connected to Discord!')
    print(f'{guild.name}(id: {guild.id})')
    await database.connect()

@bot.command()
async def newdrink(ctx):
    if not str(ctx.channel.id) == str(CHANNEL):
        return

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

    send = await ctx.send('description: ')
    message_response = await bot.wait_for('message', check=check)
    if await exit_check(): return
    description = str(message_response.content)
    await send.delete()
    await message_response.delete()

    send = await ctx.send('image: ')
    send2 = await ctx.send('you can either send a image or a direct link to one.')
    message_response = await bot.wait_for('message', check=check)
    if await exit_check(): return
    if not message_response.content:
        attachment = message_response.attachments[0]
        uploaded_image = im.upload_image(url=attachment.url)
        url = str(uploaded_image.link)
    else:
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


    send = await ctx.send('making instructions: ')
    message_response = await bot.wait_for('message', check=check)
    if await exit_check(): return
    if not message_response.content:
        attachment = message_response.attachments[0]
        await attachment.save("instructions.txt")
        with open('instructions.txt', 'r') as file:
            text = file.read()
            paste = pb.create_paste(str(text), api_paste_private=1)
        instructions = str(paste)
    else:
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
    embed.add_field(name="posted By: ", value=ctx.author)

    sent = await ctx.send(embed=embed)
    await sent.add_reaction("\U0001F44D")
    await sent.add_reaction("\U0001F44E")

    await asyncio.sleep(.5)

    message_id = sent.id

    query = "INSERT INTO cocktails(name, discription, image, ingredients, instructions, author, up_vote, downvote, message_id) VALUES (:name, :discription, :image, :ingredients, :instructions, :author, :up_vote, :downvote, :message_id)"
    values = [
        {"name": name, "discription": description, "image": url, "ingredients": str(ingredient), "instructions": instructions, "author": str(ctx.author), "up_vote": int(0), "downvote": int(0), "message_id": str(message_id)}
    ]
    await database.execute_many(query=query, values=values)

@bot.command()
async def randomdrink(ctx):
    if not str(ctx.channel.id) == str(CHANNEL):
        return
    while True:
        try:
            query = "SELECT * FROM cocktails"
            rows = await database.fetch_all(query=query)

            #ok for real dont ever do this, i dont even think its better then the normal random.choice(rows)
            rng = random.choice(range(0,len(rows)))
            drink = len(rows) * rng
            drink = random.choice(range(drink))
            drink = round(drink / rng)
            drink = rows[drink]
        except:
            continue
        else:        
            name = drink[0]
            discription = drink[1]
            image = drink[2]
            ingredients = drink[3]
            instructions = drink[4]
            author = drink[5]

            def list():
                list = ""
                for i in ast.literal_eval(ingredients):
                    list = list + i + "\n"
                return list

            embed = discord.Embed(title=name, description=discription, color=discord.Color.blue())
            embed.set_thumbnail(url=image)
            embed.add_field(name="ingredients", value=list())
            embed.add_field(name="instructions", value=instructions)
            embed.add_field(name="posted By: ", value=author)

            sent = await ctx.send(embed=embed)
            print(sent.id)
            break

@bot.event
async def on_raw_reaction_add(payload):
    
    id = payload.message_id

    async def check(id):
        query = "SELECT * FROM cocktails"
        rows = await database.fetch_all(query=query)
        # print(rows)
        for row in rows:
            # print(row)
            if row[8] is None:
                continue
            if int(row[8]) == id:
                print("MATCH")
                print(str(payload.emoji))
                if str(payload.emoji) == "👍":
                    await add_one_up(row[6], row[8])
                elif str(payload.emoji) == "👎":
                    await add_one_down(row[7], row[8])

    async def add_one_up(current, id):
        if current is None:
            new = 1
        else:
            new = current + 1
        # query = "INSERT INTO cocktails(up_vote) VALUES (:up_vote)"
        query = "UPDATE cocktails SET up_vote = (:up_vote) WHERE message_id = (:id)"
        values = [
            {"up_vote": new, "id": id}
        ]
        await database.execute_many(query=query, values=values)

    async def add_one_down(current, id):
        if current is None:
            new = 1
        else:
            new = current + 1
        query = "UPDATE cocktails SET downvote = (:down_vote) WHERE message_id = (:id)"
        values = [
            {"down_vote": new, "id": id}
        ]
        await database.execute_many(query=query, values=values)
    
    await check(id)

@bot.event
async def on_raw_reaction_remove(payload):
    print("reaction remove")
    id = payload.message_id

    async def check(id):
        query = "SELECT * FROM cocktails"
        rows = await database.fetch_all(query=query)
        # print(rows)
        for row in rows:
            # print(row)
            if row[8] is None:
                continue
            if int(row[8]) == id:
                print("MATCH")
                print(str(payload.emoji))
                if str(payload.emoji) == "👍":
                    await remove_one_up(row[6], row[8])
                elif str(payload.emoji) == "👎":
                    await remove_one_down(row[7], row[8])

    async def remove_one_up(current, id):
        if current is None:
            new = 0
        elif current <= 0:
            print("starting value was less then 0. setting to 0")
            new = 0
        else:
            new = current - 1
        # query = "INSERT INTO cocktails(up_vote) VALUES (:up_vote)"
        query = "UPDATE cocktails SET up_vote = (:up_vote) WHERE message_id = (:id)"
        values = [
            {"up_vote": new, "id": id}
        ]
        await database.execute_many(query=query, values=values)

    async def remove_one_down(current, id):
        if current is None:
            new = 0
        elif current <= 0:
            print("starting value was less then 0. setting to 0")
            new = 0
        else:
            new = current - 1
        query = "UPDATE cocktails SET downvote = (:down_vote) WHERE message_id = (:id)"
        values = [
            {"down_vote": new, "id": id}
        ]
        await database.execute_many(query=query, values=values)
    
    await check(id)

@bot.command(pass_context = True)
async def clear(ctx, number):
    if not str(ctx.channel.id) == str(CHANNEL):
        return
    if not str(ctx.message.author.id) == owner_id:
        return
    async for msg in ctx.channel.history(limit=int(number)+1):
        if not msg.pinned:
            await msg.delete()

@bot.command()
async def rebuild(ctx):
    if not str(ctx.channel.id) == str(CHANNEL):
        return
    if not str(ctx.message.author.id) == owner_id:
        return

    query = "SELECT * FROM cocktails"
    rows = await database.fetch_all(query=query)
    for row in rows:
        drink = row
        name = drink[0]
        discription = drink[1]
        image = drink[2]
        ingredients = drink[3]
        instructions = drink[4]
        author = drink[5]

        def list():
            list = ""
            for i in ast.literal_eval(ingredients):
                list = list + i + "\n"
            return list

        embed = discord.Embed(title=name, description=discription, color=discord.Color.blue())
        embed.set_thumbnail(url=image)
        embed.add_field(name="ingredients", value=list())
        embed.add_field(name="instructions", value=instructions)
        embed.add_field(name="posted By: ", value=author)

        sent = await ctx.send(embed=embed)
        await sent.add_reaction("\U0001F44D")
        await sent.add_reaction("\U0001F44E")
        id = sent.id

        await asyncio.sleep(1)

        query = "UPDATE cocktails SET message_id = (:message_id) WHERE image = (:image)"
        values = [
            {"message_id": id, "image": row[2]}
        ]
        await database.execute_many(query=query, values=values)

@bot.command()
async def top(ctx):
    if not str(ctx.channel.id) == str(CHANNEL):
        return
    embed = discord.Embed(title="Leaderboard", description="The top 3 drink are.", color=discord.Color.red())
    embed.set_thumbnail(url="https://i.imgur.com/hKxdqF0.png")
    query = "SELECT * FROM cocktails"
    rows = await database.fetch_all(query=query)
    top = sorted(rows, key=lambda x: x.up_vote, reverse=True)
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    for x in range(0,3):
        drink = top[x]
        name = drink[0]
        author = drink[5]
        upvotes = drink[6]
        message_id = drink[8]
        link = f"https://discordapp.com/channels/{guild.id}/{ctx.channel.id}/{message_id}"


        embed.add_field(name=f"#{x+1}", value=f"{name}\n with {upvotes} upvotes\n posted by {author}\n {link}")

    await ctx.send(embed=embed)

@bot.command()
async def admin(ctx):
    if not str(ctx.channel.id) == str(CHANNEL):
        return
    if not str(ctx.message.author.id) == owner_id:
        return
    print("admin command")

@bot.command()
async def whoami(ctx):
    if not str(ctx.channel.id) == str(CHANNEL):
        return

    async def roles():
        roles = ""
        for x in ctx.message.author.roles:
            roles = f'{str(roles)} "{str(x)}" '
        return roles.replace("@", "")

    roles = await roles()
    await ctx.send(f"you are: {ctx.message.author}\n your id is: {ctx.message.author.id}\n you joined at: {ctx.message.author.joined_at}\n you have the roles: {roles}")

bot.run(TOKEN)
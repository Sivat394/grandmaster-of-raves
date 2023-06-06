@bot.hybrid_command(name="modtags", description="modifys an event tags - mod only")
@discord.app_commands.describe(tags = "Genre/Event Tags to be added")   
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")

async def modtags(ctx, event_id:int, tags:str):
    if ctx.author.id in tokens.allowed_users:
       results = session.query(Event).filter_by(id=event_id).all()
       results[0].tags = tags
       #print(results)
       session.commit()
       await ctx.send("Event Modified",ephemeral=True)
    else:
        await ctx.send("You're not authorized to use this",ephemeral=True)


@bot.hybrid_command(name="modage", description="modifys an event tags - mod only")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
@discord.app_commands.describe(age = "minimum age or all ages")

async def modage(ctx, event_id:int, age:str):
    if ctx.author.id in tokens.allowed_users:
       results = session.query(Event).filter_by(id=event_id).all()
       results[0].age = age
       #print(results)
       session.commit()
       await ctx.send("Event Modified",ephemeral=True)
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)

@bot.hybrid_command(name="modprice", description="modifys an event price - mod only")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
@discord.app_commands.describe(price = "Price of Event")
async def modprice(ctx, event_id:int, price:str):
    if ctx.author.id in tokens.allowed_users:
       results = session.query(Event).filter_by(id=event_id).all()
       results[0].price = price
       #print(results)
       session.commit()
       await ctx.send("Event Modified",ephemeral=True)
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)


@bot.hybrid_command(name="modorgs", description="modifys an event orgs - mod only")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
@discord.app_commands.describe(organizer = "Org throwing the event")
async def modorg(ctx, event_id:int, organizer:str):
    if ctx.author.id in tokens.allowed_users:
       results = session.query(Event).filter_by(id=event_id).all()
       results[0].organizer = organizer
       #print(results)
       session.commit()
       await ctx.send("Event Modified",ephemeral=True)
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)

@bot.hybrid_command(name="modlink", description="modifys an event link - mod only")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
@discord.app_commands.describe(link = "Link to event")
async def modlink(ctx, event_id:int, link:str):
    if ctx.author.id in tokens.allowed_users:
       results = session.query(Event).filter_by(id=event_id).all()
       results[0].link = link
       #print(results)
       session.commit()
       await ctx.send("Event Modified",ephemeral=True)
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)


@bot.hybrid_command(name="moddate", description="modifys event's date - mod only")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
@discord.app_commands.describe(date = "date in Month D (Time)")
async def modedate(ctx, event_id:int, date:str):
    if ctx.author.id in tokens.allowed_users:
       results = session.query(Event).filter_by(id=event_id).all()
       results[0].date = date
       #print(results)
       session.commit()
       await ctx.send("Date Modified",ephemeral=True)
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)


@bot.hybrid_command(name="modevent", description="mods event name- mod only")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
@discord.app_commands.describe(new_name = "New Name of Event")
async def modevent(ctx, event_id:int, new_name:str):
    if ctx.author.id in tokens.allowed_users:
       results = session.query(Event).filter_by(id=event_id).all()
       results[0].event_name = new_name
       #print(results)
       session.commit()
       await ctx.send("Event Modified",ephemeral=True)
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)
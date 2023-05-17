from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime
from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks
from db_create import get_19hz, update_db
import discord.components
from sqlclass import Event, Raver
from tokens import is_allowed
import tokens
from methods import generate_embeds, add_raver_to_event, add_to_queue, trading_board, remove_from_queue, remove_raver, move_raver_down, move_raver_up,is_raver_in_queue

class Buttons(discord.ui.View):
    def __init__(self, event_id, user, *, timeout=180): 
        super().__init__(timeout=timeout)
        self.event_id = event_id
        self.user = user
        self.guild = user.guild.id
        self.raver_id = user.id
    @discord.ui.button(label="Let's Party", style=discord.ButtonStyle.blurple, emoji='a:SharkParty:1093532139498254486')
    async def on_attend_button_click(self, interaction: discord.Interaction, button: discord.ui.Button,):
        raver = self.user
        raver = add_raver_to_event(raver,'Yes','Accquired',self.event_id,0)
        if is_raver_in_queue(self.event_id,raver):
            remove_from_queue(self.event_id,raver)
        embed = trading_board(self.event_id)
        await interaction.response.edit_message(content=f"<@{raver.discord_id}>added <a:SharkParty:1093532139498254486>",embed=embed, view=self)
    @discord.ui.button(label="Buying tickets", style=discord.ButtonStyle.grey)
    async def on_buy_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        raver = self.user   
        raver = add_raver_to_event(raver,'No','Buying',self.event_id,0)
        embeds = trading_board(self.event_id)
        await interaction.response.edit_message(content=f"<@{raver.discord_id}> added to queue", view=self,embed=embeds)
    @discord.ui.button(label="Selling tickets", style=discord.ButtonStyle.green)
    async def on_sell_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        raver = self.user
        raver = add_raver_to_event(raver,'No','Selling',self.event_id,0)
        embed = trading_board(self.event_id)
        await interaction.response.edit_message(content=f"<@{raver.discord_id}> Added to the sellers list:",embed=embed, view=self)
    ## @discord.ui.button(label="Trading Board", style=discord.ButtonStyle.grey)
    ## async def on_queue_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
    ##     embeds = trading_board(self.event_id)
    ##     await interaction.response.edit_message(content="Trading Board", embed=embeds, view=self)
    ## @discord.ui.button(label="Attendees", style=discord.ButtonStyle.blurple)
    ## async def on_attendees_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
    ##     embeds = embed_raver('Attending',self.event_id)
    ##     await interaction.response.edit_message(content="Ravers going", embed=embeds, view=self)
    @discord.ui.button(label="Remove Me", style=discord.ButtonStyle.red,emoji='a:pain:960332634498674810')
    async def on_remove_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        remove_raver(raver=self.user.name,event_id=self.event_id,guild=self.user.guild.id)
        embed = trading_board(self.event_id)
        await interaction.response.edit_message(content="Removed <a:pain:960332634498674810>", embed=embed,view=self)

class Dropdown(discord.ui.Select):
    def __init__(self,event,user):
        self.user = user
        print('tf \n')
        events = session.query(Event).filter(Event.event_name.like(f'%{event}%')).all()
        print(events)        # Set the options that will be presented inside the dropdown
        options = []
        for event in events[:15]:
            print(event)
            options += [discord.SelectOption(label=f'{event.event_name[0:40]} @ {event.venue}' , value=str(event.event_name))]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Choose and event', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        print ('\n'+self.values[0])
        events = session.query(Event).filter(Event.event_name.like(f'%{self.values[0]}%')).first()
        view=Buttons(events.id ,user=self.user)
        print
        if events.link is not None:
          print(events.link)
          view.add_item(discord.ui.Button(label="Event Page",style=discord.ButtonStyle.link,url=events.link))
        embeds = trading_board(events.id)
        await interaction.response.edit_message(content=f'Event {events.event_name}',view=view,embed=embeds)

class DropdownView(discord.ui.View):
    def __init__(self,event,user):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Dropdown(event,user))

##TO DO:/
#add in emoji selector based on tags
emoji_tag = []
## attending(no,going,hosting,playing) tickets(accquired,buying)
## Bot shit
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)
# create an engine to connect to a SQLite database
engine = create_engine('sqlite:///rave.db')
Session = sessionmaker(bind=engine)
session = Session()

@tasks.loop(minutes=3)  # Run the task once every 24 hours
# Check for new events in the database
async def check_new_events():
    now = datetime.datetime.now()
    two_weeks_out = now + datetime.timedelta(minutes=3)

    # Example: Retrieve upcoming events from the database
    upcoming_events = get_upcoming_events_from_db(two_weeks_out)

    for event in upcoming_events:
        # Create a new channel for the event
        forum = bot.get_channel(1086408274464743515)
        existing_channel = discord.utils.get(category.channels, name=event.event_name)
        
        if existing_channel:
            print(f"Channel '{event.event_name}' already exists. Skipping creation.")
            continue
        
        await forum.create_thread(name=event.event_name,content=f"test",allowed_mentions=discord.mentions.AllowedMentions(users=True),reason='New event')
        
        
        category = discord.utils.get(guild.categories, name="Event Channels")  # Replace with your category name
        channel = await guild.create_text_channel(event.event_name, category=category)

        # Create a new thread in the channel
        thread = await channel.create_thread(name=event.event_name)

        # Optionally, you can add additional content or messages to the thread
        await thread.send(f"Thread for {event.event_name} is created!")

def get_upcoming_events_from_db(end_date):
    start_date = datetime.datetime.now()

    # Example using SQLAlchemy query
    upcoming_events = session.query(Event).filter(Event.date2 >= start_date, Event.date2 <= end_date).all()

    return upcoming_events

@bot.hybrid_command()
@is_allowed()
async def forum_test(ctx, test:str):
     # thread channel ID
    forum = bot.get_channel(1086408274464743515)
   


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.hybrid_command(name="addtoqueue", description="add someone to the queue manually",help="add someone to the queue manually")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
@discord.app_commands.describe(discord_id = "a users discord ID, get it by @ing them and using a \ before it")
@is_allowed()
async def add_to_queue(ctx, event_id:int, discord_id:int):
       results = session.query(Event).filter_by(id=discord_id).all()
       raver = session.query(Raver).filter_by(event_id=event_id, id=discord_id).first()

       await ctx.send("Event Modified",ephemeral=True)
       await ctx.send(f"ADDED",ephemeral=True)

@bot.hybrid_command(name="rave", description="Look up parties", help="keep the name in the black box")
@discord.app_commands.describe(event = "name of the event, can search based on partial words")
async def rave(ctx, event:str):
    """Sends a message with our dropdown containing colours"""
    # Create the view containing our dropdown
    view = DropdownView(event,ctx.message.author)
    print(ctx.message.author.name)

    # Sending a message containing our view
    await ctx.send('an event', view=view, ephemeral=True)
@bot.hybrid_command(name="addevent", description="add events")
@discord.app_commands.describe(name = "Event Name")
@discord.app_commands.describe(venue = "Venue Name")
@discord.app_commands.describe(tags = "Genre/Event Tags to be added")
@discord.app_commands.describe(date2 = " Date in m/d/y format")
@discord.app_commands.describe(venue = "date in may 1st (10pm) format")
async def addevent(ctx, name:str, venue:str,tags:str,date2:str,date:str):
    if ctx.author.id in tokens.allowed_users:
       date2 = datetime.strptime(date, '%m/%d/%Y')
       event = Event(name,venue,tags,date2,date)
       session.add(event)
       session.commit()
       await ctx.send("Event Modified",ephemeral=True)
       await ctx.send(f"ADDED {name} @ {venue} on @ {date}",ephemeral=True)
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
@bot.hybrid_command(name="rmid", description="mods events - mod only")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
async def rmid(ctx, event_id:int):
    if ctx.author.id in tokens.allowed_users:
       results = session.query(Event).filter_by(id=event_id).first()
       session.delete(results)
       session.commit()
       await ctx.send("Removed",ephemeral=True)
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)
@bot.hybrid_command(name="events", description="Shows events from 19hz")
async def events(ctx):
    session = Session()
    events = session.query(Event).filter_by(banned=False).all()
    session.close()
    if len(events) == 0:
        await ctx.send("No events found.")
        return
    embeds = generate_embeds(events)
    page = 0
    msg = await ctx.send(embed=embeds[page])
    await msg.add_reaction('⬅️')
    await msg.add_reaction('➡️')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️']

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == '➡️' and page < len(embeds)-1:
                page += 1
                await msg.edit(embed=embeds[page])
            elif str(reaction.emoji) == '⬅️' and page > 0:
                page -= 1
                await msg.edit(embed=embeds[page])
            await msg.remove_reaction(reaction, user)
        except:
            break
@bot.hybrid_command(name="search", description="Searches events by name")
@discord.app_commands.describe(event = "Name of Event to search for, works with partial matches")
async def search(ctx, event:str):
       args = event
       #print(args)
       results = session.query(Event).filter(Event.event_name.like(f'%{args}%')).all()
       if results:
        embed = discord.Embed(title='Search Results', description='', color=discord.Color.dark_purple())
        text = ''
        for event in results:
          
          print(event.banned)
          text = text + (f'** {event.event_name} ** @ {event.venue} on {event.date} ({event.id})'+ '\n')
        embed.add_field(name="", value=text)
        await ctx.send(embed=embed,ephemeral=True)
       else:
         await ctx.send(f"No events found matching {args[0]}",ephemeral=True)
@bot.hybrid_command(name="dates", description="Searches events by date in m/d/y format ")
@discord.app_commands.describe(date = "date in m/d/y format")
async def dates(ctx, date:str):
       args = datetime.strptime(date, '%m/%d/%Y')
       #print(args)
       results = session.query(Event).filter(Event.date2 == args,Event.banned == False).all()
       if results:
        embed = discord.Embed(title='Search Results', description='', color=discord.Color.dark_purple())
        text = ''
        for event in results:
          text = text + (f'** {event.event_name} ** @ {event.venue}'+ '\n')
        embed.add_field(name="", value=text)
        await ctx.send(embed=embed,ephemeral=True)
       else:
         await ctx.send(f"No events found matching {args[0]}",ephemeral=True)
@bot.hybrid_command(name="update", description="updates event db - mod only")
async def update(ctx):
    #print(ctx.author.id)
    if ctx.author.id in tokens.allowed_users:
        lol = get_19hz()
        update_db(lol,session)
        await ctx.send('updating', ephemeral=True)
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)
@bot.hybrid_command(name="ban_event",description="prevents event from showing up on duplicates - mod only")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
async def bane(ctx, event_id:int):
    if(ctx.author.id == 857270689035059232 or ctx.author.id == 430905941043576843):
         results = session.query(Event).filter_by(id=event_id).first()
         results.banned = True
         session.commit()
    else:
       await ctx.send("You're not authorized to use this",ephemeral=True)

@bot.hybrid_command(name="sync", description="Syncs Commands to Discord, Sivat Only", hidden=True)
async def sync(ctx):
    #print(ctx.author.id)
    if ctx.author.id in tokens.allowed_users:
         guilds = [discord.Object(id='899713834535780382'),discord.Object(id='595366390870048768'),discord.Object(id='1080706918869372948')]
         for guild in guilds:
             #print(f'Syncing {guild.id}')
             bot.tree.copy_global_to(guild=guild)
             await bot.tree.sync(guild=guild)
    else:
        ctx.send("You're not authorized to use this",ephemeral=True)


bot.run(tokens.token2)






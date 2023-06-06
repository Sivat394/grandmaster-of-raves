from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime
from datetime import datetime, timedelta
import discord
from discord.ui import Select, Modal, TextInput
from discord.ext import commands, tasks
from db_create import update_db
import discord.components
from sqlclass import Event, Raver
from tokens import is_allowed
import tokens
from methods import generate_embeds, ButtonView,add_raver_to_event, add_to_queue, trading_board, remove_from_queue, remove_raver, move_raver_down, move_raver_up,is_raver_in_queue
import methods
import asyncio


##TO DO:/

## test out how discord formats @tags when passed into a command

#add in emoji selector based on tags
emoji_tag = []
## attending(no,going,hosting,playing) tickets(accquired,buying)
## Bot shit
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)
# create an engine to connect to a SQLite database
engine = create_engine('sqlite:///rave.db')
Session = sessionmaker(bind=engine)
session = Session()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')



@bot.tree.command()
async def rave(interaction: discord.Interaction):
    view = methods.Menu_Buttons()
    await interaction.response.send_message(view=view,ephemeral=True)

@bot.tree.command(name="addtoqueue", description="add someone to the queue manually")
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
@discord.app_commands.describe(discord_id = "a users discord ID, get it by @ing them and using a \ before it")
@is_allowed()
async def add_queue(interaction: discord.Interaction, event_id:int, discord_id:str):
    raver = interaction.guild.get_member(int(discord_id))
    add_to_queue(event_id, raver)
    await interaction.response.send_message(f"ADDED",ephemeral=True)


@bot.tree.command(name="rmid", description="mods events - mod only")
@is_allowed()
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
async def rmid(interaction: discord.Interaction, event_id:int):
    results = session.query(Event).filter_by(id=event_id).first()
    session.delete(results)
    session.commit()
    await interaction.response.send_message("Removed",ephemeral=True)
   

@bot.tree.command()
async def events(interaction: discord.Interaction):
    session = Session()
    events = session.query(Event).filter_by(banned=False).all()
    session.close()
    if len(events) == 0:
        await interaction.response.send_message("No events found.")
        return
    embeds = generate_embeds(events)
    await interaction.response.send_message(embed=embeds[0], view=ButtonView(embeds),ephemeral=True)


@bot.tree.command()
@is_allowed()
async def update(interaction: discord.Interaction):
    await interaction.response.defer()
    task = asyncio.create_task(update_db())
    await interaction.followup.send(content='Updated', ephemeral=True)
    

@bot.tree.command(name="ban_event",description="prevents event from showing up on duplicates - mod only")
@is_allowed()
@discord.app_commands.describe(event_id = "ID for event (found in /search results in parentesis)")
async def bane(interaction: discord.Interaction, event_id:int):  
    results = session.query(Event).filter_by(id=event_id).first()
    results.banned = True
    session.commit()


@bot.tree.command(name="sync", description="Syncs Commands to Discord, Sivat Only")
@is_allowed()
async def sync(interaction: discord.Interaction):
    #print(ctx.author.id)
    guilds = [discord.Object(id='899713834535780382')]#,discord.Object(id='595366390870048768'),discord.Object(id='1080706918869372948')]
    for guild in guilds:
        print(f'Syncing {guild.id}')
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)

@bot.tree.command(name="setuphook", description="test")
@is_allowed()
async def setup_hook(ctx):
    check_events.start()

@tasks.loop(hours=24)  # Run the task once every 24 hours
async def check_events():
    print("new_forums")
    now = datetime.now()
    two_weeks_out = now + timedelta(days=21)
    # Example: Retrieve upcoming events from the database
    upcoming_events = get_upcoming_events_from_db(two_weeks_out)
    forum = bot.get_channel(1107834622424907836)
    thread_names = []
    for thread in forum.threads:
        thread_names.append(thread.name)
    for event in upcoming_events:
        if event.event_name.strip() in thread_names:
            print(f"Channel '{event.event_name}' already exists. Skipping creation.")
            continue

        event_id = event.id
        ravers = session.query(Raver).filter_by(event_id=event_id).all()
        raver_text =''
        print(ravers)
        for raver in ravers:
            raver_text = raver_text + f'<@{raver.discord_id}>\n'
        print(raver_text)
        if event.link:
            thread = await forum.create_thread(name=event.event_name,content=event.link,reason='New event')
        else:
            thread = await forum.create_thread(name=event.event_name,content='test',reason='New event')
        await thread.thread.send(content=raver_text,allowed_mentions=discord.mentions.AllowedMentions(users=True))

def get_upcoming_events_from_db(end_date):
    start_date = datetime.now()
    upcoming_events = session.query(Event).filter(Event.date2 >= start_date, Event.date2 <= end_date).all()
    events = []
    for event in upcoming_events:
        if event.get_raver_count() > 0:
            events.append(event)
    for event in events:  
        print(event.event_name)
    return events





bot.run(tokens.token2)







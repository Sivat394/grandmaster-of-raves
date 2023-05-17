from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord.ui import Select
from db_create import get_19hz, update_db
import discord.components
from sqlclass import Event, Raver

engine = create_engine('sqlite:///rave.db')
Session = sessionmaker(bind=engine)
session = Session()

def generate_embeds(events): #creates the event list for events.
    chunks = [events[i:i+12] for i in range(0, len(events), 15)]
    embeds = []
    for chunk in chunks:
        embed = discord.Embed(title="Event List", color=0x690420)
        for event in chunk:
            embed.add_field(name=event.event_name, value=f"Date: {event.date}\nVenue: {event.venue}\nTags:{event.tags}", inline=False)
        embeds.append(embed)
    return embeds
def trading_board(event_id): #creates the buy/sell/attending board
    event = session.query(Event).filter_by(id=event_id).first()
    ravers_buying= session.query(Raver).filter_by(event_id=event_id,tickets='Buying').order_by(Raver.queue_pos).all()
    ravers_selling = session.query(Raver).filter_by( event_id=event_id, tickets='Selling')
    ravers =  session.query(Raver).filter_by( event_id=event_id, attending='Yes')
    embed = discord.Embed(title=f"Buying List for {event.event_name} ", color=0x690420)
    text = ''
    for raver in ravers_buying:
          #print(raver.username)
          text += f'<@{raver.discord_id}> \n'
    embed.add_field(name='Buyers Queue (Top is #1)',value=f"{text}")
    text = '' #reset text string
    for raver in ravers_selling:
          #print(raver.username)
          text += f'<@{raver.discord_id}> \n'
    embed.add_field(name='Sellers',value=f"{text}")
    embed.set_footer(text="Grandmaster is in beta")

    text = ''
    for raver in ravers:
          #print(raver.username)
          text += f'<@{raver.discord_id}> \n'
    embed.add_field(name='Ravers',value=f"{text}", inline=False)
    embed.set_footer(text="Grandmaster is in beta")
    return embed
def embed_raver(status,event_id):
    event = session.query(Event).filter_by(id=event_id).first()
    if status =='Attending':
        label = 'Attending'
        ravers =  session.query(Raver).filter_by( event_id=event_id, attending='Yes')
    if ravers != None:
        #print(ravers.first())
        embed = discord.Embed(title=f"{label} List for {event.event_name} ", color=0x690420)
        text = ''
        for raver in ravers:
          #print(raver.username)
          text += f'<@{raver.discord_id}> \n'
        embed.add_field(name='',value=f"{text}", inline=False)
        embed.set_footer(text="Grandmaster is in beta")
    return embed
def add_raver_to_event(user, attending, tickets, event_id, price):
    raver_name = user.name
    raver_id = user.id
    guild = user.guild.id
    event = session.query(Event).get(event_id)
    raver = session.query(Raver).filter_by(username=raver_name, guild=guild, event_id=event.id).first()

    if raver != None:
        raver.attending = attending
        raver.tickets = tickets
        raver.event_id = event_id
        raver.price = price
        session.commit()
        return raver
        #print(f'{raver.username} added to {event.event_name} at {event.venue} on {event.date}')

    else:
         new_raver = Raver(username=raver_name, discord_id=raver_id, attending=attending, tickets=tickets,event_id=event_id, price=price,guild=guild,queue_pos=0)
         event.ravers.append(new_raver)
         session.commit()
         return new_raver
         #print(f'{raver.username} added to {event.event_name} at {event.venue} on {event.date}')
def remove_raver(raver,event_id,guild):
    raver = session.query(Raver).filter_by(username=raver, event_id=event_id, guild=guild).first()
    session.delete(raver)
    session.commit()
def remove_from_queue(event_id, raver):
    # get the event
    event = session.query(Event).filter_by(id=event_id).one()

    # get the raver's queue position
    queue_pos = raver.queue_pos

    # if the raver is not in the queue, do nothing
    if queue_pos is None:
        return False

    # remove the raver from the queue
    raver.queue_pos = 999 #can't be None and 0 would place them at the top.

    # update the queue positions of other ravers
    for other_raver in event.ravers:
        if other_raver.queue_pos > queue_pos:
            move_raver_up(event_id, other_raver)

    session.commit()
    return True
def move_raver_up(event_id, raver):
    # get the event
    event = session.query(Event).filter_by(id=event_id).one()

    # get the raver's queue position
    queue_pos = raver.queue_pos

    # if the raver is already at the front of the queue, do nothing
    if queue_pos == 1:
        return False

    # move the raver up in the queue
    raver.move_up(session)
    session.commit()

    # update the queue positions of other ravers
    for other_raver in event.ravers:
        if other_raver != raver and other_raver.queue_pos < queue_pos:
            other_raver.move_down()

    session.commit()
    return True
def move_raver_down(event_id, raver):
    # get the event
    event = session.query(Event).filter_by(id=event_id).one()

    # get the raver's queue position
    queue_pos = raver.queue_pos

    # if the raver is already at the back of the queue, do nothing
    if queue_pos == len(event.queue):
        return False

    # move the raver down in the queue
    raver.move_down(session)
    session.commit()

    # update the queue positions of other ravers
    for other_raver in event.queue:
        if other_raver != raver and other_raver.queue_pos > queue_pos:
            other_raver.move_up()

    session.commit()
    return True
def is_raver_in_queue(event_id, raver):
    event = session.query(Event).filter_by(id=event_id).first()
    if not event:
        return False
    for queued_raver in event.ravers:
        if queued_raver.discord_id == raver.discord_id:
            return True
    return False
def add_to_queue(event_id, raver):
    # Check if the event exists
    event = session.query(Event).filter_by(id=event_id).first()
    if not event:
        return "Event not found"

    # Check if the Raver is already in the queue
    raver = session.query(Raver).filter_by(event_id=event_id, discord_id=raver.discord_id).first()
    if raver:
        return "Raver is already in the queue"

    # Get the last position in the queue
    last_pos = session.query(Raver.queue_pos).filter_by(event_id=event_id).order_by(Raver.queue_pos.desc()).first()
    if last_pos:
        queue_pos = last_pos[0] + 1
    else:
        queue_pos = 1

    # Create a new Raver and add to the session
    new_raver = Raver(discord_id=raver.discord_id, event_id=event_id, tickets='Buying', attending='No', queue_pos=queue_pos)
    
    session.add(new_raver)
    session.commit()

    return f"Raver <@{raver.discord_id}> added to the queue at position {queue_pos}"    

from typing import Optional
from discord.utils import MISSING
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord.ui import Select, Modal, TextInput
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
            embed.add_field(name=event.event_name, value=f"{event.date} @ {event.venue} \n Tags:{event.tags}", inline=False)
        embeds.append(embed)
    return embeds

def generate_embeds_count(events,keyword): #creates the event list for events.
    chunks = [events[i:i+12] for i in range(0, len(events), 15)]
    embeds = []
    if keyword == "Buying":
        for chunk in chunks:
            embed = discord.Embed(title="Event List", color=0x690420)
            for event in chunk:
                num = len(session.query(Raver).filter_by(event_id=event.id,tickets='Buying').all())
                embed.add_field(name=event.event_name, value=f"Number Buying: {str(num)} \n {event.date} @ {event.venue} \n Tags:{event.tags}", inline=False)
            embeds.append(embed)
    if keyword == "Selling":
        for chunk in chunks:
            embed = discord.Embed(title="Event List", color=0x690420)
            for event in chunk:
                print(event.id)
                num = len(session.query(Raver).filter_by(event_id=event.id,tickets='Selling').all())
                embed.add_field(name=event.event_name, value=f"Number Selling: {str(num)} \n {event.date} @ {event.venue} \n Tags:{event.tags}", inline=False)
            embeds.append(embed)
    if keyword == "Attending":
        for chunk in chunks:
            embed = discord.Embed(title="Event List", color=0x690420)
            for event in chunk:
                num = len(session.query(Raver).filter_by(event_id=event.id,attending='Yes').all())
                embed.add_field(name=event.event_name, value=f"Number Attending: {str(num)} \n {event.date} @ {event.venue} \n Tags:{event.tags}", inline=False)
            embeds.append(embed)
    if keyword == "All":
        for chunk in chunks:
            embed = discord.Embed(title="Event List", color=0x690420)
            for event in chunk:
                num_look = len(session.query(Raver).filter_by(event_id=event.id,tickets='Buying').all())
                num_sell = len(session.query(Raver).filter_by(event_id=event.id,tickets='Selling').all())
                num = len(session.query(Raver).filter_by(event_id=event.id,attending='Yes').all())
                embed.add_field(name=event.event_name+f' ({event.id})', value=f"{event.date} @ {event.venue} \n Attending: {str(num)} | Selling: {str(num_sell)} | Buying: {str(num_look)} \n Tags:{event.tags}", inline=False)
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

def add_raver_to_event(user, attending, tickets, event_id, price, queue_pos):
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
        raver.queue_pos= queue_pos
        session.commit()
        print(f'{raver.username} added to {event.event_name} at {event.venue} on {event.date}')

        return raver
        
    else:
         new_raver = Raver(username=raver_name, discord_id=raver_id, attending=attending, tickets=tickets,event_id=event_id, price=price,guild=guild,queue_pos=0)
         event.ravers.append(new_raver)
         session.commit()
         print(f'{new_raver.username} added to {event.event_name} at {event.venue} on {event.date}')
         return new_raver
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
def add_to_queue(event_id, user):
    # Check if the event exists
    event = session.query(Event).filter_by(id=event_id).first()
    if not event:
        return "Event not found"

    # Check if the Raver is already in the queue
    raver = session.query(Raver).filter_by(queue_pos=True, event_id=event_id, discord_id=user.id).first()
    if raver:
        return "Raver is already in the queue"

    # Get the last position in the queue
    last_pos = session.query(Raver.queue_pos).filter_by(event_id=event_id).order_by(Raver.queue_pos.desc()).first()
    if last_pos:
        queue_pos = last_pos[0] + 1
    else:
        queue_pos = 1

    # Create a new Raver and add to the session
    if raver:
        raver = add_raver_to_event(user = user , event_id=event_id, tickets='Buying', attending='No', queue_pos=queue_pos,price=raver.price)
    else:
        raver = add_raver_to_event(user = user , event_id=event_id, tickets='Buying', attending='No', queue_pos=queue_pos,price=0)


    return f"Raver <@{raver.discord_id}> added to the queue at position {queue_pos}"    


regions = ["BayArea","LA","Texas","Florida","Atlanta","Detroit","Seattle","DC","Iowa","Chicago","Boston","Vegas","Pheonix","PNW"]

regions_str = "SF, LA, TX, FL, ATL, DET, SEA, DC, Iowa, CHI, BOS, Vegas, PHX, PNW"
# Function to get people buying tickets in a specified region


def get_all_events(region):
    if region == 'All':
        events = session.query(Event).filter().order_by(Event.date2.asc()).all()
    else:
        events = session.query(Event).filter(Event.region == region).all()
    return events
def get_attended_events(region):
    if region == 'All':
        events = session.query(Event).join(Raver).filter(Raver.attending == 'Yes').all()
    else:
        events = session.query(Event).join(Raver).filter(Event.region == region, Raver.attending == 'Yes').all()
    return events
def get_events_with_sellers(region):
    if region == 'All':
        Events = session.query(Event).join(Raver).filter(Raver.tickets == 'Selling').all()
    else:
        Events = session.query(Event).join(Raver).filter(Event.region == region, Raver.tickets == 'Selling').all()
    return Events
def get_events_with_buyers(region):
    if region == 'All':
        Events = session.query(Event).join(Raver).filter(Raver.tickets == 'Buying').all()
    else:
        Events = session.query(Event).join(Raver).filter(Event.region == region, Raver.tickets == 'Buying').all()
    return Events


## MODALS


class mRegion(Modal):
    def __init__(self, *, title: str = 'Event Search', timeout: float | None = None, custom_id: str =  "test", keyword:str) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.keyword = keyword
    
    region = TextInput(label='Region',default="BOS",required=False,placeholder="See Help for Region Tags",style=discord.TextStyle.short)
    async def on_submit(self, interaction: discord.Interaction):
        if(self.keyword == 'Attending'):
                embeds = generate_embeds_count(get_attended_events(region=self.region.value),"Attending")
                await interaction.response.send_message(embed=embeds[0], view=ButtonView(embeds),ephemeral=True)
        elif(self.keyword == 'Selling'):
                embeds = generate_embeds_count(get_events_with_sellers(region=self.region.value),'Selling')
                await interaction.response.send_message(embed=embeds[0], view=ButtonView(embeds),ephemeral=True)
        elif(self.keyword == 'Buying'):
                embeds = generate_embeds_count(get_events_with_buyers(region=self.region.value),'Buying')
                await interaction.response.send_message(embed=embeds[0], view=ButtonView(embeds),ephemeral=True)
        elif(self.keyword == 'All'):
                embeds = generate_embeds_count(get_all_events(region=self.region.value),"All")
                await interaction.response.send_message(embed=embeds[0],view=ButtonView(embeds),ephemeral=True)

class mEventSearch(Modal, title='Event Search'):
    #set default region as option per raver
    region = TextInput(label='Region',default="BOS",required=False,placeholder="See Help for Region Tags",style=discord.TextStyle.short)
    event_name = TextInput(label='Event_Name',required=False,placeholder="Event Name, can do partial matches")
    Date = TextInput(label='Date',required=False, placeholder="M/D/YYYY Format", style=discord.TextStyle.short)
    Tags = TextInput(label="Tags",required=False,placeholder="Genre Tags",style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
      region_value = self.region.value
      event_name_value = self.event_name.value
      Date_value = self.Date.value
      Tags_value = self.Tags.value

      if len(region_value) == 0:
          if len(event_name_value) > 0:
             if len(Date_value) > 0 and len(Tags_value) > 0:
                 Date_value = datetime.strptime(self.Date.value, '%m/%d/%Y')
                 results = session.query(Event).filter(Event.event_name.like(f'%{event_name_value}%'),Event.tags.like(f'%{Tags_value}%'),Event.date2==Date_value).all()
             elif len(Date_value) > 0:
                 Date_value = datetime.strptime(self.Date.value, '%m/%d/%Y')
                 results = session.query(Event).filter(Event.event_name.like(f'%{event_name_value}%'),Event.date2==Date_value).all()
             elif len(Tags_value) > 0:
                 results = session.query(Event).filter(Event.event_name.like(f'%{event_name_value}%'),Event.tags.like(f'%{Tags_value}%')).all()
             else:
                 results = session.query(Event).filter(Event.event_name.like(f'%{event_name_value}%')).all()
          else:
              if len(Date_value) > 0 and len(Tags_value) > 0:
                 Date_value = datetime.strptime(self.Date.value, '%m/%d/%Y')
                 results = session.query(Event).filter(Event.tags.like(f'%{Tags_value}%'),Event.date2==Date_value).all()
              elif len(Date_value) > 0:
                 Date_value = datetime.strptime(self.Date.value, '%m/%d/%Y')
                 results = session.query(Event).filter(Event.date2==Date_value).all()
              elif len(Tags_value) > 0:
                 results = session.query(Event).filter(Event.tags.like(f'%{Tags_value}%')).all()
              else:
                 results = session.query(Event).all()
              
      else:
          if len(event_name_value) > 0:
             if len(Date_value) > 0 and len(Tags_value) > 0:
                 results = session.query(Event).filter(Event.region==region_value,Event.event_name.like(f'%{event_name_value}%'),Event.tags.like(f'%{Tags_value}%'),Event.date2==Date_value).all()
             elif len(Date_value) > 0:
                 results = session.query(Event).filter(Event.region==region_value,Event.event_name.like(f'%{event_name_value}%'),Event.date2==Date_value).all()
             elif len(Tags_value) > 0:
                 results = session.query(Event).filter(Event.region==region_value,Event.event_name.like(f'%{event_name_value}%'),Event.tags.like(f'%{Tags_value}%')).all()
             else:
                 results = session.query(Event).filter(Event.region==region_value,Event.event_name.like(f'%{event_name_value}%')).all()
          else:
              if len(Date_value) > 0 and len(Tags_value) > 0:
                 results = session.query(Event).filter(Event.region==region_value,Event.tags.like(f'%{Tags_value}%'),Event.date2==Date_value).all()
              elif len(Date_value) > 0:
                 results = session.query(Event).filter(Event.region==region_value,Event.date2==Date_value).all()
              elif len(Tags_value) > 0:
                 results = session.query(Event).filter(Event.region==region_value,Event.tags.like(f'%{Tags_value}%')).all()
              else:
                 results = session.query(Event).filter(Event.region==region_value).all()

             
      print(self.region)
      print(type(self.event_name.value))
      print(type(self.Date.value))
      print(type(self.Tags.value)) 
      for event in results:
          print(event.event_name)   
      view = DropdownView(results,interaction.user)
      await interaction.response.send_message(view=view,ephemeral=True)
 
class mAddRaver(Modal, title='Event Search'):
    event_name = TextInput(label='Event_Name',default='test',placeholder="test")
    answer = TextInput(label='Answer', placeholder="test", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        print(self.name)
        
        await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)


class mEventModify(Modal, title='Event Search'):
    name = TextInput(label='Name')
    answer = TextInput(label='Answer', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)
class mEventTags(Modal, title='Event Search'):
    name = TextInput(label='Name')
    answer = TextInput(label='Answer', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)

class Menu_Buttons(discord.ui.View):
    def __init__(self, *, timeout=180): 
        super().__init__(timeout=timeout)
        
    @discord.ui.button(label="Search", style=discord.ButtonStyle.grey, emoji='🔍')
    async def on_search_button_click(self, interaction: discord.Interaction, button: discord.ui.Button,):
        await interaction.response.send_modal(mEventSearch())
    @discord.ui.button(label="Show events people are going to", style=discord.ButtonStyle.gray, emoji='a:SharkParty:1093532139498254486')
    async def on_attending_button_click(self, interaction: discord.Interaction, button: discord.ui.Button,):
        await interaction.response.send_modal(mRegion(keyword="Attending"))
    @discord.ui.button(label="Show events with tickets for", style=discord.ButtonStyle.green, emoji='🎟️')
    async def on_sellers_button_click(self, interaction: discord.Interaction, button: discord.ui.Button,):
        await interaction.response.send_modal(mRegion(keyword="Selling"))
    @discord.ui.button(label="Show events with people looking for tickets", style=discord.ButtonStyle.green, emoji='🎟️')
    async def on_buyers_button_click(self, interaction: discord.Interaction, button: discord.ui.Button,):
        await interaction.response.send_modal(mRegion(keyword="Buying"))
    @discord.ui.button(label="Show All Events", style=discord.ButtonStyle.blurple, emoji=':devious:913065426676752464')
    async def on_regionlist_button_click(self, interaction: discord.Interaction, button: discord.ui.Button,):
        await interaction.response.send_modal(mRegion(keyword="All"))
       
class Event_Buttons(discord.ui.View):
    def __init__(self, event_id, user, *, timeout=180): 
        super().__init__(timeout=timeout)
        self.event_id = event_id
        self.user = user
        self.guild = user.guild.id
        self.raver_id = user.id
    @discord.ui.button(label="Let's Party", style=discord.ButtonStyle.blurple, emoji='a:SharkParty:1093532139498254486')
    async def on_attend_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        raver = self.user
        raver = add_raver_to_event(raver,'Yes','Accquired',self.event_id,0,None)
        if is_raver_in_queue(self.event_id,raver):
            remove_from_queue(self.event_id,raver)
        embed = trading_board(self.event_id)
        await interaction.response.edit_message(content=f"<@{raver.discord_id}>added <a:SharkParty:1093532139498254486>",embed=embed, view=self)
    @discord.ui.button(label="Buying tickets", style=discord.ButtonStyle.grey)
    async def on_buy_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        raver = self.user   
        raver = add_raver_to_event(raver,'No','Buying',self.event_id,0,0)
        add_to_queue(self.event_id,self.user)
        embeds = trading_board(self.event_id)
        await interaction.response.edit_message(content=f"<@{raver.discord_id}> added to queue", view=self,embed=embeds)
    @discord.ui.button(label="Selling tickets", style=discord.ButtonStyle.green)
    async def on_sell_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        raver = self.user
        raver = add_raver_to_event(raver,'No','Selling',self.event_id,0,0)
        embed = trading_board(self.event_id)
        await interaction.response.edit_message(content=f"<@{raver.discord_id}> Added to the sellers list:",embed=embed, view=self)
    @discord.ui.button(label="Remove Me", style=discord.ButtonStyle.red,emoji='a:pain:960332634498674810')
    async def on_remove_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        remove_raver(raver=self.user.name,event_id=self.event_id,guild=self.user.guild.id)
        embed = trading_board(self.event_id)
        await interaction.response.edit_message(content="Removed <a:pain:960332634498674810>", embed=embed,view=self)

class Dropdown(discord.ui.Select):
    def __init__(self,events,user):
        self.user = user
        print('tf \n')
        # Set the options that will be presented inside the dropdown
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
        view=Event_Buttons(events.id ,user=self.user)
        print
        if events.link is not None:
          print(events.link)
          view.add_item(discord.ui.Button(label="Event Page",style=discord.ButtonStyle.link,url=events.link))
        embeds = trading_board(events.id)
        await interaction.response.send_message(content=f'Event {events.event_name}',view=view,embed=embeds,ephemeral=True)

class DropdownView(discord.ui.View):
    def __init__(self,event,user):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Dropdown(event,user))

class ButtonView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds
        self.page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, custom_id="prev_btn")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.page])

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="next_btn")
    async def next_button(self, interaction: discord.Interaction , button: discord.ui.Button):
        if self.page < len(self.embeds) - 1:
            self.page += 1
            await interaction.response.edit_message(embed=self.embeds[self.page])
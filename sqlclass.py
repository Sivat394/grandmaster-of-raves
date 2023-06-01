from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy import DateTime
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd

engine = create_engine('sqlite:///rave.db')
Session = sessionmaker(bind=engine)
session = Session()

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the Raver class
class Raver(Base):
    __tablename__ = 'ravers'
    id = Column(Integer, primary_key=True)
    discord_id = Column(Integer)
    username = Column(String)
    attending = Column(String)
    tickets = Column(String)
    price = Column(Integer)
    guild = Column(String)
    event_id = Column(Integer, ForeignKey('events.id'))
    queue_pos = Column(Integer)
   
    event = relationship('Event', back_populates='ravers')
    
    def __init__(self, username, discord_id, attending, tickets,event_id,price,guild,queue_pos):
        self.username = username
        self.attending = attending
        self.tickets = tickets
        self.discord_id = discord_id
        self.event_id= event_id
        self.price = price
        self.guild = guild
        self.queue_pos = queue_pos

    def move_up(self,session):
        event_id = self.event_id
        # Replace with your database session creation

        # Get the current position of the raver in the queue
        current_pos = self.queue_pos

        # Retrieve the raver with the next lower position in the queue
        raver_above = session.query(Raver).filter(Raver.event_id == event_id, Raver.queue_pos < current_pos) \
            .order_by(Raver.queue_pos.desc()).first()

        if raver_above:
            # Swap the positions of the current raver and the raver above
            temp_pos = self.queue_pos
            self.queue_pos = raver_above.queue_pos
            raver_above.queue_pos = temp_pos

            session.commit()
    def move_down(self,session):
        event_id = self.event_id
       

        # Get the current position of the raver in the queue
        current_pos = self.queue_pos

        # Retrieve the raver with the next higher position in the queue
        raver_below = session.query(Raver).filter(Raver.event_id == event_id, Raver.queue_pos > current_pos) \
            .order_by(Raver.queue_pos.asc()).first()

        if raver_below:
            # Swap the positions of the current raver and the raver below
            temp_pos = self.queue_pos
            self.queue_pos = raver_below.queue_pos
            raver_below.queue_pos = temp_pos

            session.commit()

# Define the Event class
class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    event_name = Column(String)
    date = Column(String)
    date2 = Column(DateTime)
    tags = Column(String)
    venue = Column(String)
    link = Column(String)
    organizer = Column(String)
    Price     = Column(String)
    Age       = Column(String)
    banned    = Column(Boolean)
    region = Column(String)
    ravers = relationship('Raver', back_populates='event')
    
    def __init__(self, event_name, venue, tags, date2, date,link,organizer,banned):
        self.event_name = event_name
        self.date = date
        self.venue = venue
        self.tags = tags
        self.date2 = date2
        self.link = link
        self.organizer = organizer
        self.banned = banned

    def get_raver_count(self):
       return session.query(Raver).filter_by(event_id=self.id).count()

      
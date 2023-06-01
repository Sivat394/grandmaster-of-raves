from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy import DateTime
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlclass import Event, Raver


# Create a SQLite database
engine = create_engine('sqlite:///rave.db')

# Create a session factory
Session = sessionmaker(bind=engine)

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
    
    def __init__(self, username, discord_id, attending, tickets,event_id,price,guild):
        self.username = username
        self.attending = attending
        self.tickets = tickets
        self.discord_id = discord_id
        self.event_id= event_id
        self.price = price
        self.guild = guild
        self.queue_pos = None


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

# Create the database schema
Base.metadata.create_all(engine)

region_links = [("BayArea",'https://19hz.info/eventlisting_BayArea.php'),('LA','https://19hz.info/eventlisting_LosAngeles.php'),('Texas','https://19hz.info/eventlisting_Texas.php'),('Florida','https://19hz.info/eventlisting_Miami.php'),('Atlanta','https://19hz.info/eventlisting_Atlanta.php'),('Detroit','https://19hz.info/eventlisting_Detroit.php'),('Seattle','https://19hz.info/eventlisting_Seattle.php'),('DC','https://19hz.info/eventlisting_DC.php'),('Iowa','https://19hz.info/eventlisting_Iowa.php'),('Chicago','https://19hz.info/eventlisting_CHI.php'),('Boston','https://19hz.info/eventlisting_Massachusetts.php'),('Vegas','https://19hz.info/eventlisting_LasVegas.php'),('Pheonix','https://19hz.info/eventlisting_Phoenix.php'),('PNW','https://19hz.info/eventlisting_PNW.php')]


#get the website data to use
def get_19hz(url): 
      
    # Send a request to the website and get the HTML content
    response = requests.get(url)
    html_content = response.text
    
    # Parse the HTML content with Beautiful Soup
    soup = BeautifulSoup(html_content, "html.parser")
    # Find the table in the HTML document
    table = soup.find("table")
    
    # Extract the column headers from the table
    headers = []
    for th in table.find_all("th"):
      headers.append(th.text.strip())
    
 # Find the index of the column that contains the links
    link_column_index = headers.index("Links")
    
    # Extract the rows from the table
    rows = []
    for tr in table.find_all("tr"):
        row = []
        for index, td in enumerate(tr.find_all("td")):
            # If the column is the one containing links, extract the link
            if index == link_column_index:
                link = td.find("a")
                if link:
                    href = link.get("href")
                    row.append(href)
                else:
                    row.append(None)
            else:
                row.append(td.text.strip())

        rows.append(row)
    
    # Convert the table data into a pandas DataFrame
    df = pd.DataFrame(data=rows, columns=headers)
    
    return df.drop(0)


def update_db(lol,session,region):
 
    for row in lol.itertuples():
     
      name_venue =      row[2]
      name_venue =      name_venue.split('@')
      event_name =      name_venue[0]
      venue =           name_venue[1].split(')')[0]+')'
      date =            row[1].split('(')[0]
      date2=            datetime.strptime(row[7], '%Y/%m/%d')
      tags =            row[3]
      link =            row[6]
      organizer =       row[5]
      event =           Event(event_name,venue,tags,date2,date,link,organizer,False)
      existing_event =  session.query(Event).filter_by(venue=venue, date=date).all()
      yesterday = datetime.now() + timedelta(days=-1)
      region = region
      
      if (date2 == yesterday):
          event = existing_event
      elif len(existing_event) == 1:
          event = existing_event  
      else:
          if len(event.event_name)> 25: print("larger than 25")
          print(f'added {event.event_name}')
          session.add(event)


def remove_past_events(session):
    now = datetime.now()
    yesterday = now + timedelta(days=-1)
    past_events = session.query(Event).all()
    past_events = list(filter(lambda x: x.date2 < yesterday, past_events))
    for event in past_events:
        session.delete(event)
    session.commit()

session = Session()


for link in region_links:
    lol = get_19hz(link[1])
    update_db(lol,session,link[0])
remove_past_events(session=session)



  
session.commit()



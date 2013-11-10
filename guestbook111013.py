import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from sys import argv

import datetime
import pickle 

import sys
sys.path.insert(0, 'libs')

import BeautifulSoup
from bs4 import BeautifulSoup
import requests

import json

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
    autoescape=True)

url = 'http://www.njtransit.com/sf/sf_servlet.srv?hdnPageAction=TrainSchedulesFrom'
pu_code = "124_PRIN"
ny_code = "105_BNTN"
prs = "Princeton"
nyp = "New York Penn Station"

# get date
today = datetime.date.today()
str_date = today.__format__("%m/%d/%Y")

# trip info
toNY_dict = {'selOrigin': pu_code, 'selDestination': ny_code, 'datepicker': str_date, 'OriginDescription': prs, 'DestDescription': nyp}
toPU_dict = {'selOrigin': ny_code, 'selDestination': pu_code, 'datepicker': str_date, 'OriginDescription': nyp, 'DestDescription': prs}

# get to webpage with data for the day
with requests.Session() as re:
    toNY = re.post(url, data=toNY_dict)
    toPU = re.post(url, data=toPU_dict)

toPUhtml = toPU.text
toNYhtml = toNY.text


#Reads in html file and name of destination and outputs csv file with comma spliced file of train information
def scrape(html,destination):
    title = str(today) + str(destination) 

    soup = BeautifulSoup(html)

    # Improvements: instead of being so hacky with 10 search for td
    # Gather all lines in table
    table1 = soup.find_all("tr")
    table2 = table1[10] #table1[10] contains the table of interest
    table3 = table2.find_all('span')

    # Create 7 lists
    origin = [] #Times for departure at origin
    origintrain = []
    transferarrive = [] #Times for arrival at transfer 
    transferdepart = [] #Time for departure at transfer
    transfertrain = [] #Train or bus number
    destination = [] #Time of arrival at destination
    total = [] #Total time of Travel

    #Create 3 Columns of Text File
    origin.append("Origin Departure") #Times for departure at origin
    origintrain.append("Origin Train")
    transferarrive.append("Transfer Arrival") #Times for arrival at transfer 
    transferdepart.append("Transfer Departure") #Time for departure at transfer
    transfertrain.append("Transfer Train or Bus")
    destination.append("Destination Arrival") #Time of arrival at destination
    total.append("Total Travel Time") #Total time of Travel

    #Store 4 columns into 4 lists
    #Regex and pull approapriate data

    for i in range(4, len(table3)-3, 4):
        
        #origin.append(str(table3[i].text)[0:len(table3[i].text)])
        origin.append(str(table3[i].text)[0:8])
        origintrain.append(str(table3[i].text)[-5:])

        transferarrive.append(str(table3[i+1].text)[7:15])
        transferdepart.append(str(table3[i+1].text)[39:48])
        transfertrain.append(str(table3[i+1].text)[-5:])

        destination.append(str(table3[i+2].text)[0:len(table3[i+2].text)])

        total.append(str(table3[i+3].text)[0:len(table3[i+3].text)])

    #text_file = open(str(title) + ".csv", "w")

    Dict = {'origin': origin[1:], 'transferarrive' : transferarrive[1:], 'transferdepart': transferdepart[1:], 'destination':destination[1:]}

    return Dict

#Create csv files for to Princeton and to New York
toPUDict = scrape(toPUhtml, 'PU')
toNYDict = scrape(toNYhtml, 'NY')

class njdata(ndb.Model):
    """Models an individual Guestbook entry with author, content, and date."""
    originstring = ndb.StringProperty(repeated = True) 
    transferarrivestring = ndb.StringProperty(repeated = True) 
    transferdepartstring = ndb.StringProperty(repeated = True) 
    destinationstring = ndb.StringProperty(repeated = True)
    date = ndb.DateTimeProperty(auto_now_add=True) #Need date to get most recent data

globalPUDict = {}

class Test123(webapp2.RequestHandler):

    def get(self):
        toPUdata = njdata()
        #toNYdata = njdata()

        #toPUdata.content = pickle.dumps(toPUDict)
        toPUdata.originstring = toPUDict['origin']
        toPUdata.transferarrivestring = toPUDict['transferarrive']
        toPUdata.transferdepartstring = toPUDict['transferdepart']
        toPUdata.destinationstring = toPUDict['destination']

        #Save data into data models
        toPUdata.put()
        #toNYdata.put()
        toPUdata_query = toPUdata.query().order(-njdata.date)
        a = toPUdata_query.fetch(1)

        global globalPUDict
        globalPUDict = {'origin': a[0].originstring, 'transferarrive': a[0].transferarrivestring, 'transferdepart': a[0].transferdepartstring, 'destination': a[0].destinationstring}

        self.response.write(globalPUDict)
        self.response.write(toPUDict)


class MainPage(webapp2.RequestHandler):

    def get(self):

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())


class ToNY(webapp2.RequestHandler):

    def get(self):

        template = JINJA_ENVIRONMENT.get_template('toNY.html')
        self.response.write(template.render(toNYDict))

class ToPU(webapp2.RequestHandler):

    def get(self):

        self.response.write(globalPUDict)
        template = JINJA_ENVIRONMENT.get_template('toPU.html')
        self.response.write(template.render(globalPUDict))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/toNY', ToNY),
    ('/toPU', ToPU),
    ('/test', Test123),
], debug=True)

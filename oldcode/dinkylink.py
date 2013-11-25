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

def getPost():

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

    return [toPUhtml, toNYhtml]
##Reads in html file and name of destination and outputs csv file with comma spliced file of train information
def getSoonestTrain(times):
    from datetime import time
    import datetime
    from pytz import timezone
    import pytz

    noTrain = 'No more trains today!'
    current_dt = datetime.datetime.now() 
    eastern = timezone('US/Eastern')
    current_dt_est = eastern.localize(current_dt)
    curr_est = datetime.datetime.time(current_dt_est)
    print curr_est
    for str_time in times:
        print str_time
        parts = str_time.split(' ')
        hrmin = parts[0].split(':')
        hr = int(hrmin[0])
        minute = int(hrmin[1])
        if parts[1] == 'A.M.' and hr == 12:
            hr = 0
        elif parts[1] == 'P.M.':
            hr = hr+12
        dt = time(hr, minute)
        print hr
        print dt
        if dt > curr_est:
            hrdiff = hr - curr_est.hour
            mindiff = minute-curr_est.minute
            if mindiff < 0:
                mindiff = mindiff + 60
                hrdiff = hrdiff-1
            str_diff = str(hrdiff) + " hour " + str(mindiff) + " minutes"
            return str_diff
    return noTrain

def scrape(html,destination):
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


class njdata(ndb.Model):
    originstring = ndb.StringProperty(repeated = True) 
    transferarrivestring = ndb.StringProperty(repeated = True) 
    transferdepartstring = ndb.StringProperty(repeated = True) 
    destinationstring = ndb.StringProperty(repeated = True)
    date = ndb.DateTimeProperty(auto_now_add=True) #Need date to get most recent data
    identifier = ndb.StringProperty()

globalPUDict = {}
globalNYDict = {}
toPUdata = njdata()
toNYdata = njdata() 

class Test123(webapp2.RequestHandler):

    def get(self):

        #self.response.write(toPUdata)
        #self.response.write(toNYdata)

        toPUdata_query = toPUdata.query().order(-njdata.date)
        a = toPUdata_query.fetch(2)
        if a[0].identifier == 'NY':
            ny = a[0]
            pu = a[1]
        else:
            ny = a[1]
            pu = a[0]

        #toNYdata_query = toNYdata.query().order(-njdata.date)
        #b = toNYdata_query.fetch(1)

        #self.response.write(a[1])
        #self.response.write(b)
        global globalPUDict
        globalPUDict = {'origin': pu.originstring, 'transferarrive': pu.transferarrivestring, 'transferdepart': pu.transferdepartstring, 'destination': pu.destinationstring}

        global globalNYDict
        globalNYDict = {'origin': ny.originstring, 'transferarrive': ny.transferarrivestring, 'transferdepart': ny.transferdepartstring, 'destination': ny.destinationstring}

        #self.response.write(toPUdata)
        #self.response.write(toNYdata)

class MainPage(webapp2.RequestHandler):

    def get(self):

        toPUDict = scrape(getPost()[0], 'PU')
        toNYDict = scrape(getPost()[1], 'NY')

        global toPUdata
        toPUdata.originstring = toPUDict['origin']
        toPUdata.transferarrivestring = toPUDict['transferarrive']
        toPUdata.transferdepartstring = toPUDict['transferdepart']
        toPUdata.destinationstring = toPUDict['destination']
        toPUdata.identifier = "PU"

        global toNYdata
        toNYdata.originstring = toNYDict['origin']
        toNYdata.transferarrivestring = toNYDict['transferarrive']
        toNYdata.transferdepartstring = toNYDict['transferdepart']
        toNYdata.destinationstring = toNYDict['destination']
        toNYdata.identifier = "NY"

        toPUdata_query = toPUdata.query().order(-njdata.date)
        a = toPUdata_query.fetch(2)
        if a[0].identifier == 'NY':
            ny = a[0]
            pu = a[1]
        else:
            ny = a[1]
            pu = a[0]

        #toNYdata_query = toNYdata.query().order(-njdata.date)
        #b = toNYdata_query.fetch(1)

        #self.response.write(a[1])
        #self.response.write(b)
        global globalPUDict
        globalPUDict = {'origin': pu.originstring, 'transferarrive': pu.transferarrivestring, 'transferdepart': pu.transferdepartstring, 'destination': pu.destinationstring}

        global globalNYDict
        globalNYDict = {'origin': ny.originstring, 'transferarrive': ny.transferarrivestring, 'transferdepart': ny.transferdepartstring, 'destination': ny.destinationstring}


        #Save data into data models
        toPUdata.put()
        toNYdata.put()

        #########Main Page Needs this###############
        puSoon = getSoonestTrain(globalPUDict['origin'])
        nySoon = getSoonestTrain(globalNYDict['origin'])
        tempSoon = {'puSoon': puSoon, 'nySoon': nySoon}

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(tempSoon))


class TimedScraper(webapp2.RequestHandler):

    def get(self):
        toPUDict = scrape(getPost()[0], 'PU')
        toNYDict = scrape(getPost()[1], 'NY')

        global toPUdata
        toPUdata.originstring = toPUDict['origin']
        toPUdata.transferarrivestring = toPUDict['transferarrive']
        toPUdata.transferdepartstring = toPUDict['transferdepart']
        toPUdata.destinationstring = toPUDict['destination']
        toPUdata.identifier = "PU"

        global toNYdata
        toNYdata.originstring = toNYDict['origin']
        toNYdata.transferarrivestring = toNYDict['transferarrive']
        toNYdata.transferdepartstring = toNYDict['transferdepart']
        toNYdata.destinationstring = toNYDict['destination']
        toNYdata.identifier = "NY"

        #Save data into data models
        toPUdata.put()
        toNYdata.put()

        self.response.write(toPUdata)
        self.response.write(toNYdata)

class ToNY(webapp2.RequestHandler):

    def get(self):

        template = JINJA_ENVIRONMENT.get_template('toNY.html')
        self.response.write(template.render(globalNYDict))

class ToPU(webapp2.RequestHandler):

    def get(self):

        template = JINJA_ENVIRONMENT.get_template('toPU.html')
        self.response.write(template.render(globalPUDict))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/toNY', ToNY),
    ('/toPU', ToPU),
    ('/test', Test123),
    ('/scrape', TimedScraper)
], debug=True)

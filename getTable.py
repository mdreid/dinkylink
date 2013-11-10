from sys import argv
from bs4 import BeautifulSoup
import requests
import datetime

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


#text = open('njtransittime2.txt')
toPUhtml = toPU.text
toNYhtml = toNY.text

title = str(today) + "hello" #str(destination) 

#soup = BeautifulSoup(html)

soup = BeautifulSoup(toPUhtml)

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

	text_file = open(str(title) + ".csv", "w")

	Dict = {'origin': origin[1:], 'transferarrive' : transferarrive[1:], 'transferdepart': transferdepart[1:], 'destination':destination[1:]}


	#Write to text filed
	for lines in range(len(origin)):
		text_file.write(origin[lines] + "," + origintrain[lines] + "," + transferarrive[lines] + "," + transferdepart[lines] + "," + transfertrain[lines] + "," + destination[lines] + "\n")

	text_file.close()

	return Dict

#Create csv files for to Princeton and to New York
scrape(toPUhtml, 'PU')
scrape(toNYhtml, 'NY')
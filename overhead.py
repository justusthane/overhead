import requests
import json
import re
from datetime import datetime
from string import Template

# Tighter
#url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1&bounds=48.395%2C48.382%2C-89.279%2C-89.229&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1"
# Wider
url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1&bounds=48.409%2C48.372%2C-89.303%2C-89.204&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1&enc=2pTPB4GJMn0wdAbgolLJRTUxG5Nlh_09-NywvmbUW1o"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.flightradar24.com/',
    'Origin': 'https://www.flightradar24.com',
    'Alt-Used': 'data-live.flightradar24.com',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'TE': 'trailers'
}

def getAirportInfo(airport):
    url = f"https://www.flightradar24.com/airports/traffic-stats/?airport={airport}"
    return requests.get(url, headers=headers).json()
    
def exists(input):
    if input:
        return input
    else:
        return "???"

def getAirportName(airport):
    if airport:
        url = f"https://www.flightradar24.com/airports/traffic-stats/?airport={airport}"
        response = requests.get(url, headers=headers).json()
        if response['details']['name']:
            return response['details']['name']
    return "No airport info found"


#def getPlaneJson(input):
#    for key in input:
#        if key != "full_count" and key != "version" and key != "stats":
#            return input[key]           


# The JSON key representing the plane object (if there is one) is an 8-digit hexadecimal number. This is for finding it.
planeKeyRegEx = re.compile('[0-9a-f]{8}')
def getPlaneKey(input):
    for key in input:
        if planeKeyRegEx.match(key):
            return key          

# Load the HTML template
f = open("/var/www/overhead/template.html","r")
template = Template(f.read())
f.close()

# Call the API
response = requests.get(url, headers=headers)
responseJson = response.json()

# If no planes are in the sky right now, load the JSON from the last plane.
# This is so the HTML can be regenerated each time in case any changes
# have been made
if responseJson['stats']['visible']['ads-b'] == 0:
    print("No planes in the sky" + "\n")
    f = open("/var/www/overhead/plane.json")
    responseJson = json.load(f)
    f.close()
# A plane is in the sky
else:
    # Get the key representing the plane data
    key = getPlaneKey(responseJson)
    # Write the current date and time into the JSON data so it can be
    # reused next time
    responseJson['stats']['date'] = datetime.now().strftime("%b %d")
    responseJson['stats']['time'] = datetime.now().strftime("%H:%M")
    # Log to the text file
    f = open("/root/planelog.txt","a")
    f.write(responseJson['stats']['date'] + " " + responseJson['stats']['time'] + "\n")
    f.write("Plane! Plane! Plane!\n")
    f.write("Key: " + key + "\n")
    #f.write(json.dumps(responseJson[key]))
    # Loop through each element of the plane data array and print it along with the index.
    for i in range(len(responseJson[key])):
            f.write(str(i) + ": " + str(responseJson[key][i]) + "\n")
    f.write("\n\n")
    f.close()
    # Write the JSON to a file so it can be read next time if there's no plane.
    f = open("/var/www/overhead/plane.json","w")
    f.write(json.dumps(responseJson))
    f.close()

# Generate the HTML file, using either the current JSON data or the JSON data of the previous plane,
# loaded from the file.
key = getPlaneKey(responseJson)
dptAirportJson = getAirportInfo(responseJson[key][11])
arrAirportJson = getAirportInfo(responseJson[key][12])
flightNumberList = []
if responseJson[key][13]:
    flightNumberList.append(responseJson[key][13])
if responseJson[key][16]:
    flightNumberList.append(responseJson[key][16])
planeDict = {
    'time': responseJson['stats']['time'],
    'date': responseJson['stats']['date'],
    'reg': responseJson[key][9],
    'dptAirport': exists(responseJson[key][11]),
    'dptCity': getAirportName(responseJson[key][11]),
    'arrAirport': exists(responseJson[key][12]),
    'arrCity': getAirportName(responseJson[key][12]),
    'altitude': responseJson[key][4],
    'flight': "/".join(flightNumberList),
    'type': responseJson[key][8]
    }
f = open("/var/www/overhead/index.html","w")
f.write(template.safe_substitute(planeDict))
f.close()

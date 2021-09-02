# overhead.py
#
# Each time this script runs, it looks for planes in the airspace above, and generates and HTML file
# containing the plane (or regenerates the HTML file using the data of the most recent plane if there's 
# not a plane). It's intended to be run every 60 seconds or so (e.g. with a cron job).

# Need this one to make HTTP requests
import requests
# And this one to to work with the returned JSON data
import json
# This one is for regular expressions
import re
# This one for returning the date in a format someone would want to look at
from datetime import datetime
# And this is used for creating an HTML template for the output
from string import Template

# Copied these HTTP headers from Firefox
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

# This is the meat and potatoes. Get visible planes in the airspace
def getPlanes():
    # This is a tight little airspace
    #url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1&bounds=48.395%2C48.382%2C-89.279%2C-89.229&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1"
    # This is a wider airspace to give us a better chance of capturing the planes as they fly overhead
    url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1&bounds=48.409%2C48.372%2C-89.303%2C-89.204&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1&enc=2pTPB4GJMn0wdAbgolLJRTUxG5Nlh_09-NywvmbUW1o"
    # Call the API, save the response.
    response = requests.get(url, headers=headers)
    return response.json()

# This is just a silly function to check if the input exists and return "???" if not
# It's used if the airport codes aren't listed in the API response.
def exists(input):
    if input:
        return input
    else:
        return "???"

# Let's see if we can get the name of the airport
def getAirportName(airport):
    # Check if an airport code was provided
    if airport:
        # If it was, query the flightradar24 API for the airport code
        url = f"https://www.flightradar24.com/airports/traffic-stats/?airport={airport}"
        response = requests.get(url, headers=headers).json()
        # If airport details and a name are returned...well...return them.
        if response['details']['name']:
            return response['details']['name']
    # No airport info, so sad :(
    return "No airport info found"

# Since the flightradar24 API only returns the ICAO typecode (e.g. "B789"), 
# let's try and get a model number (e.g. "Boeing 787-9 Dreamliner") from 
# opensky-network.org using the plane's registration number (e.g. "PH-BHO")
# The ICAO typecode is also provdided as a fallback.
def getPlaneModel(registration, type):
    # Check if a registration number was provided
    if registration:
        # If it was, call the API
        url = f"https://opensky-network.org/api/metadata/aircraft/list?n=50&p=1&q={registration}"
        response = requests.get(url).json()
        # Check if the response contains model info
        if 0 in response['content']:
            if 'model' in response['content'][0]:
                # If it does, return it!
                return response['content'][0]['model']
    # If any or all of the above failes, just return the ICAO typecode that was provided
    return type

def concatFlightNums(flightNums):
    flightNumberList = []
    for flightNum in flightNums:
        if flightNum:
            flightNumberList.append(flightNum)
    return "/".join(flightNumberList)


# The JSON key representing the plane object (if there is one) is an 8-digit hexadecimal number. This is for finding it.
# Note that if there are multiple planes in the airspace, only one will be returned.
planeKeyRegEx = re.compile('[0-9a-f]{8}')
def getPlaneKey(input):
    for key in input:
        if planeKeyRegEx.match(key):
            return key          

# Load the HTML template and save it to the `template` variable for later use.
f = open("/var/www/overhead/template.html","r")
template = Template(f.read())
f.close()

# Let's get our planes!
planeJson = getPlanes()
# If no planes are in the sky right now, load the JSON from the last plane.
# This is so the HTML can be regenerated each time in case any changes
# have been made
if planeJson['stats']['visible']['ads-b'] == 0:
    print("No planes in the sky" + "\n")
    f = open("/var/www/overhead/plane.json")
    planeJson = json.load(f)
    f.close()
# Plane! Plane! Plane!
else:
    # Get the key representing the plane data
    key = getPlaneKey(planeJson)
    # Write the current date and time into the JSON data so it can be
    # reused each time this HTML file is generated for this particular plane. 
    planeJson['stats']['date'] = datetime.now().strftime("%b %d")
    planeJson['stats']['time'] = datetime.now().strftime("%H:%M")
    # Log to the text file
    f = open("/root/planelog.txt","a")
    f.write(planeJson['stats']['date'] + " " + planeJson['stats']['time'] + "\n")
    f.write("Plane! Plane! Plane!\n")
    f.write("Key: " + str(key) + "\n")
    #f.write(json.dumps(planeJson[key]))
    # Loop through each element of the plane data array and print it along with the index.
    for i in range(len(planeJson[key])):
            f.write(str(i) + ": " + str(planeJson[key][i]) + "\n")
    f.write("\n\n")
    f.close()
    # Write the JSON to a file so it can used below since there's no new plane.
    f = open("/var/www/overhead/plane.json","w")
    f.write(json.dumps(planeJson))
    f.close()

# Whether or not there's a new plane, regenerate the HTML file
key = getPlaneKey(planeJson)
# Map the JSON from the API to meaningful properties. These properties
# are used directly in the HTML template.
planeDict = {
    'time': planeJson['stats']['time'],
    'date': planeJson['stats']['date'],
    'icao24': planeJson[key][0], # ICAO Mode S code
    'reg': planeJson[key][9],
    'dptAirport': exists(planeJson[key][11]),
    'dptCity': getAirportName(planeJson[key][11]),
    'arrAirport': exists(planeJson[key][12]),
    'arrCity': getAirportName(planeJson[key][12]),
    'altitude': planeJson[key][4],
    'flight': concatFlightNums([planeJson[key][13], planeJson[key][16]]),
    'type': planeJson[key][8], # ICAO Typecode
    'model': getPlaneModel(planeJson[key][9],planeJson[key][8])
    }
# Open the HTML file
f = open("/var/www/overhead/index.html","w")
# Write the template, substituting the values from the above dictionary.
f.write(template.safe_substitute(planeDict))
f.close()

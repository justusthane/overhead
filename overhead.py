import requests
import json
from datetime import datetime

url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1&bounds=48.395%2C48.382%2C-89.279%2C-89.229&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1"
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
response = requests.get(url, headers=headers)
responseJson = response.json()
if responseJson['stats']['visible']['ads-b'] == 0:
    f = open("planelog.txt","a")
    f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    f.write("\n")
    f.write("No planes in the sky" + "\n\n")
    f.close()
else:
    for key in responseJson:
        if key != "full_count" and key != "version" and key != "stats":
            f = open("planelog.txt","a")
            f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
            f.write("Plane! Plane! Plane!\n")
            f.write("Key: " + key + "\n")
            f.write(responseJson[key])
            f.write("\n\n")
            f.close()

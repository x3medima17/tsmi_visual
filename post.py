import json
import requests
from time import gmtime, strftime


f_data = open("data/states.out").read()
curr_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

data = {
    "data" : f_data,
    "time" : curr_time
}
url = 'http://localhost:8080'

r = requests.post(url, data=data, allow_redirects=True)

print r.content
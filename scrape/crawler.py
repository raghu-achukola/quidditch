import re, urllib
from bs4 import BeautifulSoup
from datetime import date
import requests
import pymysql
import scrapeteam as st

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
# Teams that improperly registered multiple times have game data on multiple sites
# e.g           'https://www.usquidditch.org/team/texas-cavalry-1'
# as well as    'https://www.usquidditch.org/team/texas-cavalry'
# Only one of which is listed on the team page that we will be crawling
# From one of the above, we wish to get all of them. Hence: recursive scanning
def recursive_scan(name,db,table):
    # Break url into prefix below, team name, and a tag for example:
    # 'https://www.usquidditch.org/team/texas-cavalry-1'
    # PREFIX: 'https://www.usquidditch.org/team/'
    # name : 'texas-cavalry-1'
    # tag: '-1'
    URLPREFIX = 'https://www.usquidditch.org/team/'
    tag = name[len(name)-2:]
    # the tag is the last two characters of the name.
    # if this is an int (-1,-2,...) it means there are multiple versions
    # and recursive scanning is necessary
    if(is_int(tag)):
        url = URLPREFIX+name+'/pastGames'
        #Scan this version
        st.scan(url,db,table)
        # If the tag is not -1, the next version is found by adding 1 to the tag
        # i.e 'texas-cavalry-2' -> 'texas-cavalry-1' (-2 +1 = -1)
        if(int(tag)!=-1):
            recursive_scan(name[:len(name)-2]+str(int(tag)+1),db,table)
        # If the tag is -1, the next version is found by deleting the tag:
        # i.e 'texas-cavalry-1' -> 'texas-cavalry'
		else:
            recursive_scan(name[:len(name)-2],db,table)
    # If the tag is not an int, this is the original version
    # and a simple scan will suffice.
    else:
        st.scan(url,db,table)
# Start the crawler here.
DATABASE = 'quidditch'
TABLE = 'games'
qurl ='https://www.usquidditch.org/teams'
response = requests.get(qurl)
html = response.content
soup = BeautifulSoup(html,"lxml")

# BeautifulSoup has trouble reading in javascript rendered content
# So we use a raw string splitting to find the urls of all the team pages
# The first (index 0) instance of javascript with no src in the html is to generate a map
# The second (index 1)instance of javascript w no src in the html is to generate team list

scr= str(soup).split('<script type="text/javascript">')[1].split('</script>')[0]

# team list is stored in var teams as:
# ,{"Team":{"name":"Wizengamot Quidditch at VCU","slug":"vcu-wizengamot-1",
# "city":"Richmond","state_province":"VA","zip":"23220","team_type":"College",
# "latitude":"37.5498","longitude":"-77.4588","region_id":"2"}},
# The important data is after the first occurence of var teams and before 
# the occurence of var team. splitting by , gets  a list of data in a key-valueformat

tlist=scr.split('var teams')[1].split('var team')[0].split(',')
for att in tlist:
    #tlist = [...'{"Team":{"name":"Wizengamot"', '"slug":"vcu-wizengamot-1"',...]
    #slug: contains the suffix for the team url.
	if(att[0:6]=='"slug"'):
		team=att.split(':')[1]
        #get the corresponding value of the slug/suffix '"vcu-wizengamot-1"'
        #delete the double quotes
		name =str(team).replace('"','')
        #recursive_scan using this suffix.
		recursive_scan(name,DATABASE,TABLE)

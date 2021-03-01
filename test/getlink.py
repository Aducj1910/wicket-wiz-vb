from re import search
from types import prepare_class
from bs4 import BeautifulSoup
import requests, os, re, seltest2, time, json
#FIND WINNERS OF EACH GAME AFTERWARDS FROM YAML
#FIND HOME, NEUTRAL, AWAY BY CITY IN YAML
from requests.api import head
headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}

tId = '1244026'
matchLinkPattern = re.compile(r"http(?:s|):\/\/www\.espncricinfo.com\/series\/.+?(?=\/)\/.+?(?=-\d{4})-(.+(?=\/))") #group1 - matchID
shortLinkPattern = re.compile(r"http(?:s|):\/\/www\.espncricinfo.com\/series\/\d+\/(game|coverage|commentary|report|scorecard)\/(\d+)") #group1 - type #group2 - matchID
fullLinkPattern = re.compile(r"https:\/\/www.espncricinfo.com\/series\/.+?(?=\/)\/.+(?=\/)\/")


def getMatch(matchID):
    res = requests.get(f"https://www.bing.com/search?q={matchID}+site:espncricinfo.com", headers= headers).text
    soup = BeautifulSoup(res, 'lxml')
    resultLinks = soup.findAll('a', href=True)
    found = False
    for r in resultLinks:
        link_ = r.get('href') #starts but doesn't finish
        if found == False:
            if matchLinkPattern.match(link_) != None:
                if matchLinkPattern.match(link_).group(1) == matchID:
                    link_ = link_.replace("url?q=", "")
                    link_ = matchLinkPattern.match(link_).group(0) + "/"
                    found = True
                    seltest2.MyBot(link_, matchID)
            elif shortLinkPattern.match(link_) != None:
                if shortLinkPattern.match(link_).group(2) == matchID:
                    link_ = link_.replace("url?q=", "")
                    link_ = shortLinkPattern.match(link_).group(0)
                    r = requests.get(link_) 
                    link_ = r.url
                    match_ = fullLinkPattern.match(link_)
                    if match_ != None:
                        link_ = match_.group(0)
                        found = True
                        seltest2.MyBot(link_, matchID)
        else:
            pass

        # if matchID in link_ and '/full-scorecard' in link_:
        #     link_ = link_.replace("/url?q=", "")
        #     link_ = matchLinkPattern.match(link_)
        #     link_ = link_.group(0)
        #     seltest2.MyBot(link_, matchID)

def tes():
    res = requests.get(f"https://www.bing.com/search?q={tId}+site:espncricinfo.com", headers= headers).text
    soup = BeautifulSoup(res, 'lxml')
    resultLinks = soup.findAll('a', href=True)
    found = False
    for r in resultLinks:
        link_ = r.get('href') #starts but doesn't finish
        if found == False:
            if matchLinkPattern.match(link_) != None:
                if matchLinkPattern.match(link_).group(1) == tId:
                    link_ = link_.replace("url?q=", "")
                    link_ = matchLinkPattern.match(link_).group(0) + "/"
                    found = True
                    seltest2.MyBot(link_, tId)
            elif shortLinkPattern.match(link_) != None:
                if shortLinkPattern.match(link_).group(2) == tId:
                    link_ = link_.replace("url?q=", "")
                    link_ = shortLinkPattern.match(link_).group(0)
                    r = requests.get(link_) 
                    link_ = r.url
                    match_ = fullLinkPattern.match(link_)
                    if match_ != None:
                        link_ = match_.group(0)
                        print(link_)
                        found = True
                        seltest2.MyBot(link_, tId)
        else:
            pass

        # if matchID in link_ and '/full-scorecard' in link_:
        #     link_ = link_.replace("/url?q=", "")
        #     link_ = matchLinkPattern.match(link_)
        #     link_ = link_.group(0)
        #     seltest2.MyBot(link_, matchID)

def getMatchList():
    for filename in os.listdir('data/tests'):
        time.sleep(1)
        filenameToPass = filename.replace(".yaml", "")
        with open("matchInfo.json", "r") as jsonFile:
            data = json.load(jsonFile)
            if filenameToPass in data:
                print(filenameToPass + " passed")
                pass
            else:
                print(filenameToPass + " starting") #start indicator
                getMatch(filenameToPass)

tes()

# indPlayer_link = f"https://search.espncricinfo.com/ci/content/site/search.html?search={nonSplit[-1]}"
# html_request = requests.get(indPlayer_link).text
# soup = BeautifulSoup(html_request, 'lxml')
# playerSearch = soup.findAll('h3', class_='name link-cta')
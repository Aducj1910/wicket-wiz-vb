from re import search
from bs4 import BeautifulSoup
import requests, os, re, seltest2, time, json

from requests.api import head
headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}

tId = '1019987'
matchLinkPattern = re.compile(r".+?(?=full-scorecard)") #match is the link without 'full-scorecard'

def getMatch(matchID):
    res = requests.get(f"https://www.bing.com/search?q={matchID}+site:espncricinfo.com", headers= headers).text
    soup = BeautifulSoup(res, 'lxml')
    resultLinks = soup.findAll('a', href=True)
    for r in resultLinks:
        link_ = r.get('href') #starts but doesn't finish
        print(link_)
        if matchID in link_ and '/full-scorecard' in link_:
            link_ = link_.replace("/url?q=", "")
            link_ = matchLinkPattern.match(link_)
            link_ = link_.group(0)
            seltest2.MyBot(link_, matchID)

def tes():
    res = requests.get(f"https://www.bing.com/search?q={tId}+site:espncricinfo.com", headers = headers).text
    soup = BeautifulSoup(res, 'lxml')
    resultLinks = soup.findAll('a', href=True)
    for r in resultLinks:
        link_ = r.get('href')
        if tId in link_ and '/full-scorecard' in link_:
            link_ = link_.replace("/url?q=", "")
            link_ = matchLinkPattern.match(link_)
            link_ = link_.group(0)
            seltest2.MyBot(link_, tId)

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

getMatchList()

# indPlayer_link = f"https://search.espncricinfo.com/ci/content/site/search.html?search={nonSplit[-1]}"
# html_request = requests.get(indPlayer_link).text
# soup = BeautifulSoup(html_request, 'lxml')
# playerSearch = soup.findAll('h3', class_='name link-cta')
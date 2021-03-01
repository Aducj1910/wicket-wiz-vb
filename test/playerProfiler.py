import yaml
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.support import select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import infoadd

playerIDPattern = re.compile(r"(\/.+?(?=\/)){3}\/(.+?(?=\.html))") #group2 - playerID
playerBirthPattern = re.compile(r"(.+?(?=\s))(.+?(?=,)),\s(.+?(?=,))") #group1 - month, #group2 - date, #group3 - year
noMiddlePattern = re.compile(r"(.+?(?=,)),(?:\s|)(.+)") #group1 - first, #group2 - last
playerInitPattern = re.compile(r"(.+?(?=\s))\s(.+)") #group1 - first, #group2 - last
googlePattern = re.compile(r".+?(?=espncricinfo\.com)espncricinfo\.com\/.+?(?=player)player\/(.+?(?=\.html))\.html") #group1 - id
fullNamePattern = re.compile(r"([A-Z][a-z]+)\s(.+)")
enginePlayerPattern = re.compile(r".+?(?=\d)(\d+)\.html") #group1 - id

localPlayerList = {}

masterBowlers = {}
masterBatters = {}
masterNonstrikers = {}

masterTeams = {}
masterMatchups = {}

def process(matchId, checkAgainstPlayersList):
    global data
    global driver
    print(str(matchId) + " halfway")

    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    options = webdriver.ChromeOptions()
    options.headless = True
    # options.add_argument(f'user-agent={user_agent}')
    # options.add_argument("--window-size=1024,610")
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--allow-running-insecure-content')
    options.add_argument("--disable-extensions")
    options.add_argument('log-level=3')
    # options.add_argument("--proxy-server='direct://'")
    # options.add_argument("--proxy-bypass-list=*")
    # options.add_argument("--start-maximized")
    options.add_argument('--disable-gpu')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(executable_path="../chromedriver.exe", options=options)
    #getting the url


    def playerProcessing(indPlayer, indPlayer_link):
        global localPlayerList
        inDB = infoadd.checkPlayerJSON(indPlayer)
        if not inDB:
            playerMiddle = True
            nonSplit = indPlayer.split(" ")
            if len(nonSplit[0]) == 1:
                playerMiddle = False

            if not playerMiddle:
                indPlayer_link = f"https://search.espncricinfo.com/ci/content/site/search.html?search={nonSplit[-1]}"
                html_request = requests.get(indPlayer_link).text
                soup = BeautifulSoup(html_request, 'lxml')
                playerSearch = soup.findAll('h3', class_='name link-cta')
    
                for pl in playerSearch:
                    playerMatch = noMiddlePattern.match(pl.text)
                    if playerMatch != None and nonSplit[0] in playerMatch.group(2) and nonSplit[-1] in playerMatch.group(1):
                        match = False
                        playerSearch = pl.find('a')
                        playerSearchLink = playerSearch.get('href')
                        playerSearchMatch = playerIDPattern.match(playerSearchLink)
                        playerID = playerSearchMatch.group(2)

                        for kk in checkAgainstPlayersList:
                            if kk['id'] == playerID:
                                match = True

                        if match == True:
                            html_request = requests.get('https://www.espncricinfo.com' + playerSearchLink).text
                            soup = BeautifulSoup(html_request, 'lxml')
                            playerName = soup.find('h1')
                            playerName = playerName.text
                            country = soup.find("h3", class_="PlayersSearchLink").text
                            country = country.lower()
                            infoadd.addPlayerJSON(playerID, playerName, indPlayer, country)
                            localPlayerList[indPlayer] = {'id': playerID, 'fullName': playerName}
                            break                
                
            else:
                html_request = requests.get(indPlayer_link).text
                soup = BeautifulSoup(html_request, 'lxml')
                playerSearchInit = soup.findAll('h3', class_='name link-cta')

                index_ = 0
                while True:
                    playerSearch = playerSearchInit[index_]
                    playerSearch = playerSearch.find('a')
                    playerSearchLink = playerSearch.get('href')
                    playerSearchMatch = playerIDPattern.match(playerSearchLink)
                    playerID = playerSearchMatch.group(2)
                    match = False
                    for kk in checkAgainstPlayersList:
                        if playerID == kk['id']:
                            match = True
                    if match:
                        break
                    else:
                        index_ += 1

                

                html_request = requests.get('https://www.espncricinfo.com' + playerSearchLink).text
                soup = BeautifulSoup(html_request, 'lxml')
                playerName = soup.find('h1')
                playerName = playerName.text
                playerInfos = soup.findAll('p', class_='ciPlayerinformationtxt')

                country = soup.find("h3", class_="PlayersSearchLink").text
                country = country.lower()

                infoadd.addPlayerJSON(playerID, playerName, indPlayer, country)
                localPlayerList[indPlayer] = {'id': playerID, 'fullName': playerName}
        else:
            returnInfo = infoadd.getPlayerID(indPlayer)
            localPlayerList[indPlayer] = {'id': returnInfo['id'], 'fullName': returnInfo['fullName']}

    def prepLink(name):
        if " " not in name:
            # print(name)

            if name not in localPlayerList:
                res = requests.get(f"https://www.bing.com/search?q={name}+site:espncricinfo.com", headers = headers).text
                soup = BeautifulSoup(res, 'lxml')
                resultLinks = soup.findAll('a', href=True)
                for r in resultLinks:
                    link_ = r.get('href')
                    linkMatch = googlePattern.match(link_)
                    if linkMatch != None:
                        link_ = linkMatch.group(0)
                        playerID = linkMatch.group(1)
                        # print(playerID)
                        link_ = link_.replace("/url?q=", "")
                        # print(link_)
                        html_request = requests.get(link_).text
                        soup = BeautifulSoup(html_request, 'lxml')
                        playerName = soup.find('h1')
                        playerName = playerName.text
                        country = soup.find("h3", class_="PlayersSearchLink").text
                        country = country.lower()
                        infoadd.addPlayerJSON(playerID, playerName, name, country)
                        localPlayerList[name] = {'id': playerID, 'fullName': playerName}

        # elif fullNamePattern.match(name) != None:
        #     pass  
        else:
            nameMatch = playerInitPattern.match(name)
            nameSplit = name.split(" ")
            if len(nameSplit) > 2:
                nameSplit = [nameSplit[-2], nameSplit[-1]]
            name_link = f"https://search.espncricinfo.com/ci/content/site/search.html?search=+{nameSplit[0]}%20+{nameSplit[1]};type=player"
            playerProcessing(name, name_link)

    def selProcessing(name, link):
        global localPlayerList
        global localPlayerList
        inDB = infoadd.checkPlayerJSON(name)
        if not inDB:
            driver.get(link)
            playerTab = driver.find_element_by_id("player")
            # playerTab.click() #click using innings method in original one
            driver.execute_script("arguments[0].click();", playerTab)
            # loopInningsChangeButton.click()

            # wait = WebDriverWait(driver, 1)

            # links = wait.until(EC.visibility_of_all_elements_located((By. XPATH, '//a[@href]')))

            links = driver.find_elements_by_xpath("//a[@href]")
            for link in links:
                match = False
                linkPlayer = None
                id_ = None
                linkTxt = link.get_attribute("href")
                if "https://stats.espncricinfo.com/ci/engine/player" in linkTxt:
                    if enginePlayerPattern.match(linkTxt) != None:
                        id_ = enginePlayerPattern.match(linkTxt).group(1)
                        for kk in checkAgainstPlayersList:
                            if kk['id'] == id_:
                                match = True
                                linkPlayer = enginePlayerPattern.match(linkTxt).group(0)
                
                if match == True:
                    html_request = requests.get(linkPlayer).text
                    soup = BeautifulSoup(html_request, 'lxml')
                    playerName = soup.find('h1')
                    playerName = playerName.text
                    country = soup.find("h3", class_="PlayersSearchLink").text
                    country = country.lower()
                    infoadd.addPlayerJSON(id_, playerName, name, country)
                    localPlayerList[name] = {'id': id_, 'fullName': playerName}
                    break


        else:
            returnInfo = infoadd.getPlayerID(name)
            localPlayerList[name] = {'id': returnInfo['id'], 'fullName': returnInfo['fullName']}
    
    def selPrep(name):
        nameSpl = name.split(" ")
        nameJoined = "+".join(nameSpl)
        link = f"https://stats.espncricinfo.com/ci/engine/stats/analysis.html?search={nameJoined}"
        selProcessing(name, link)

    with open(f'data/tests/{matchId}.yaml', "r") as _file: 
        data = yaml.load(_file)
        teamList = data['info']['teams']
        for t in teamList:
            masterTeams[t.lower()] = {}
        inningsList = data['innings']
        numberInn = len(inningsList)
        for inn in inningsList:      

            trackerListBatter = {}
            trackerListNonstriker = {}
            trackerListBowler = {}
            trackerMatchups = {}

            index = inningsList.index(inn)
            inning = None
            if index == 0:
                inning = "1st innings"
            elif index == 1:
                inning = "2nd innings"
            elif index == 2:
                inning = "3rd innings"
            elif index == 3:
                inning = "4th innings"
            
            innings = inn[inning]
            deliveries = innings['deliveries']
            battingTeam = innings['team'].lower()
            masterTeams[battingTeam][inning] = {"activity": "batting", "info": {'runs': 0, 'wickets': 0, 'ballsList': []}}
            bowlingTeam = None
            for t in teamList:
                if t.lower() != battingTeam:
                    bowlingTeam = t.lower()
            masterTeams[bowlingTeam][inning] = {"activity": "bowling", "info": {'runs': 0, 'wickets': 0, 'ballsList': []}}
            for d in deliveries:
                ball = d[next(iter(d))]
                over = next(iter(d))

                non_striker = ball['non_striker']
                selPrep(non_striker)

                bowler = ball['bowler']
                selPrep(bowler)

                batsman = ball['batsman']
                selPrep(batsman)

                batsman = localPlayerList[batsman]['id']
                bowler = localPlayerList[bowler]['id']
                non_striker = localPlayerList[non_striker]['id']

                extras = ball['runs']['extras']
                batterRuns = ball['runs']['batsman']
                totalRuns = ball['runs']['total']
                runsConceded = totalRuns

                extraKind = None
                howOut = None
                nonStrikerOut = False
                wicket = False
                balls = 1
                wickets = 0

                catcher = None
                stumper = None

                if extras != 0:
                    extraKind = next(iter(ball['extras']))
                    if extraKind == 'noballs':
                        balls = 0
                    if extraKind == 'wides':
                        balls = 0
                    if extraKind == 'byes' or extraKind == 'legbyes':
                        runsConceded = runsConceded - extras

                if 'wicket' in ball:
                    howOut = ball['wicket']['kind']
                    if ball['wicket']['player_out'] == non_striker:
                        nonStrikerOut = True
                    if howOut != 'run out':
                        wickets = 1
                    if howOut == 'caught':
                        catcher = ball['wicket']['fielders'][0]
                        if " (sub)" in catcher:
                            catcher = -101 #ID For substitue
                        else:
                            selPrep(catcher)
                            catcher = infoadd.getPlayerID(catcher)['id']
                    if howOut == 'stumped':
                        stumper = ball['wicket']['fielders'][0]
                        if " (sub)" in stumper:
                            stumper = -101 #ID For substitue
                        else:
                            selPrep(stumper)
                            stumper = infoadd.getPlayerID(stumper)['id']
                    if howOut == 'caught and bowled':
                        catcher = bowler
                    
                    wicket = True
                
                ballObj = {str(over): {'runs': totalRuns, 'extras': extras, 'batterRuns': batterRuns, 'howOut': howOut, 'wicket': wicket, 'extrasKind': extraKind, 'nonStriker': non_striker, 'batter': batsman, 'bowler': bowler, 'catcher': catcher, 'stumper': stumper}}

                if non_striker not in trackerListNonstriker:
                    trackerListNonstriker[non_striker] = {'runs': batterRuns, 'balls': balls, 'extras': extras, 'ballsList': [ballObj]}
                else: 
                    obj = trackerListNonstriker[non_striker]
                    obj['runs'] += totalRuns
                    obj['balls'] += balls
                    obj['extras'] += extras
                    obj['ballsList'].append(ballObj)
                    trackerListNonstriker[non_striker] = obj

                if batsman not in trackerListBatter:
                    trackerListBatter[batsman] = {'runs': batterRuns, 'balls': balls, 'extras': extras, 'ballsList': [ballObj]}
                else:
                    obj = trackerListBatter[batsman] #Match-ups
                    obj['runs'] += totalRuns
                    obj['balls'] += balls
                    obj['extras'] += extras
                    obj['ballsList'].append(ballObj)
                    trackerListBatter[batsman] = obj

                if bowler not in trackerListBowler:
                    trackerListBowler[bowler] = {'runsConceded': runsConceded, 'balls': balls, 'extras': extras, 'wickets': wickets, 'ballsList': [ballObj]}
                else:
                    obj = trackerListBowler[bowler]
                    obj['runsConceded'] += runsConceded
                    obj['balls'] += balls
                    obj['extras'] += extras
                    obj['ballsList'].append(ballObj)
                    obj['wickets'] += wickets
                    trackerListBowler[bowler] = obj   

                batInfo = masterTeams[battingTeam][inning]['info'] 
                batInfo['runs'] += totalRuns
                if wicket:
                    batInfo['wickets'] += 1
                batInfo['ballsList'].append(ballObj)

                bowlInfo = masterTeams[bowlingTeam][inning]['info'] 
                bowlInfo['runs'] += totalRuns
                if wicket:
                    bowlInfo['wickets'] += 1
                bowlInfo['ballsList'].append(ballObj)    

                matchUpKey = bowler + "to" + batsman
                if matchUpKey not in trackerMatchups:
                    trackerMatchups[matchUpKey] = {'runs': totalRuns, 'balls': balls, 'runsConceded': runsConceded, 'runsScored': batterRuns, 'extras': extras, 'wickets': wickets, 'ballsList': [ballObj]}     
                else:
                    obj = trackerMatchups[matchUpKey]
                    obj['runs'] += totalRuns
                    obj['balls'] += balls
                    obj['runsConceded'] += runsConceded
                    obj['runsScored'] += batterRuns
                    obj['wickets'] += wickets
                    obj['extras'] += extras
                    obj['ballsList'].append(ballObj)

            masterBatters[inning] = trackerListBatter             
            masterBowlers[inning] = trackerListBowler
            masterNonstrikers[inning] = trackerListNonstriker
            masterMatchups[inning] = trackerMatchups
    
    print(matchId, "nearly there")
    # print(masterTeams)
    driver.quit()
    return {'batter': masterBatters, 'bowler': masterBowlers, 'nonstriker': masterNonstrikers, 'inningsNumber': numberInn, 'teams' : masterTeams, 'matchups': masterMatchups}

    

                

                
                

                


                
                


                
                
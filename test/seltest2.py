from typing import Match, cast
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.support import select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
from bs4 import BeautifulSoup
import accessDB, requests,retrieveDB, accessJSON
import re, yaml, balls

class MyBot:
    def __init__(self, matchLink, matchID):
        #boilerplate stuff to enhance performance
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        self.options = webdriver.ChromeOptions()
        self.options.headless = True
        # self.options.add_argument(f'user-agent={user_agent}')
        # self.options.add_argument("--window-size=1024,610")
        # self.options.add_argument('--ignore-certificate-errors')
        # self.options.add_argument('--allow-running-insecure-content')
        self.options.add_argument("--disable-extensions")
        self.options.add_argument('log-level=3')
        # self.options.add_argument("--proxy-server='direct://'")
        # self.options.add_argument("--proxy-bypass-list=*")
        # self.options.add_argument("--start-maximized")
        self.options.add_argument('--disable-gpu')
        # self.options.add_argument('--disable-dev-shm-usage')
        # self.options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(executable_path="../chromedriver.exe", options=self.options)
        #getting the url
        self.driver.get(matchLink + "full-scorecard")     

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        playersList = []
        playerMatchUps = {}
        matchUpsList = []
        playersElement = self.driver.find_elements_by_class_name('small')

        for i in playersElement:
            isWK = False
            isCaptain = False
            playerNameList = i.text.split(" ")
            for j in playerNameList:
                if "(c)†" in j:
                    playerNameList.remove(j)
                    isCaptain = True
                    isWK = True
                elif "(" in j:
                    playerNameList.remove(j)
                    isCaptain = True
                elif "†" in j:
                    playerNameList.remove(j)
                    isWK = True
            name = ' '.join(playerNameList)
            if(name.endswith(" ")):
                name = name[:-1]
            if i.get_attribute('href') != None:
                if '/player/' in i.get_attribute('href'):
                    playerLinkList = i.get_attribute('href')
                    playerLinkList = playerLinkList.split('/')
                    playerLinkList = playerLinkList[-1]
                    playerId = playerLinkList.replace(".html", "")
                    inList = False
                    for k in playersList:
                        if(k['id'] == playerId):
                            inList = True
                    if not inList:
                        playersList.append({'id': playerId, 'name': name, 'link': i.get_attribute('href'), 'isCaptain': isCaptain, 'isWK': isWK})

        for i in playersList:
            inList = accessDB.checkPlayer(i)
            if inList:
                i['country'] = retrieveDB.getPlayerCountry(i['id'])
            else:
                self.driver.get(i['link'])
                infoText = self.driver.find_elements_by_class_name('ciPlayerinformationtxt')
                hasBowlStyle = False
                hasBatHand = False
                playerCountry = self.driver.find_element_by_class_name('PlayersSearchLink').text
                i['country'] = playerCountry.lower()
                for j in infoText:
                    if "Born" in j.text:
                        DOB = j.text.replace("Born ", "")
                        i['DOB'] = DOB
                    if "Batting style" in j.text:
                        batHand = j.text.replace("Batting style ", "")
                        i['batHand'] = batHand
                        hasBatHand = True
                    if "Bowling style" in j.text:
                        bowlStyle = j.text.replace("Bowling style ", "")
                        i['bowlStyle'] = bowlStyle
                        hasBowlStyle = True
                if not hasBowlStyle:
                    i['bowlStyle'] = "None"
                if not hasBatHand:
                    i['batHand'] = "None"
            
                accessDB.addPlayer(i)
                self.driver.get(matchLink + "full-scorecard")

        team = self.driver.find_elements_by_class_name("name-link")
        teamList = []
        for i in team:
            if i.get_attribute("href") != None:
                teamLink = i.get_attribute("href")
                teamNamePattern = re.compile(r"(https:\/\/www.espncricinfo\.com\/team\/)(.+?(?=\-\d))")
                teamName = teamNamePattern.match(str(teamLink))
                teamName= teamName.group(2)
                teamName = teamName.replace("-", " ")
                partitionedTeam = teamLink.split("-")
                idTeam = partitionedTeam[-1]
                inList = accessDB.checkTeam(idTeam)
                teamObject = {'id': idTeam, 'name': teamName}
                if inList:
                    pass
                else:
                    accessDB.addTeam(teamObject)
                teamList.append(teamObject)

        matchInfo = {}

        formatTable = self.driver.find_element_by_class_name("table-responsive")
        formatTBody = formatTable.find_element_by_tag_name("tbody")
        formatTr = formatTBody.find_elements_by_tag_name("tr")

        for i in formatTr:
            if("Player Of The Match" in i.text):
                MOTM = i.text.replace("Player Of The Match\n", "")
                for player in playersList:
                    if MOTM == player['name']:
                        matchInfo['MOTM'] = player['id']           

        #Finding series
        seriesElement = self.driver.find_element_by_class_name('d-block')
        matchInfo['series'] = {'seriesName': seriesElement.text, 'seriesLink': seriesElement.get_attribute('href')}
        matchInfo['teamA'] = teamList[0]
        matchInfo['teamB'] = teamList[1]

        def getId(venueLink):
            venueLinkSplit = venueLink.split('/')
            venueLink = venueLinkSplit[-1]
            venueLink = venueLink.replace(".html", "")
            return venueLink

        #Finding venue
        venueToAdd = {}
        venueElement = self.driver.find_element_by_xpath("//a[contains(@href, '/ci/content/ground/')]")
        venueToAdd['name'] = venueElement.text
        venueLink = venueElement.get_attribute('href')
        venueToAdd['id'] = getId(venueLink)
        venueInList = accessDB.checkVenue(venueToAdd['id'])
        if not venueInList:
            res = requests.get(venueLink).text
            soup = BeautifulSoup(res, 'lxml')
            venueLocation = soup.find("p", class_="loc").text
            venArr = venueLocation.split(", ")
            venueCountry = venArr[-1]
            venueToAdd['country'] = venueCountry
            accessDB.addVenue(venueToAdd)

        #     self.driver.get(venueLink)
        #     venueLocation = self.driver.find_element_by_class_name('loc')
        #     venArr = venueLocation.text.split(", ")
        #     venueCountry = venArr[-1]
        #     venueToAdd['country'] = venueCountry
        #     accessDB.addVenue(venueToAdd)

        # self.driver.get(matchLink + "full-scorecard")
        matchInfo['venueId'] = venueToAdd['id']

        caughtPattern = re.compile(r"(c\s)([^&]+?(?=b))(b\s)(.+)") #group2 - catcher #group4 - bowler
        lbwPattern = re.compile(r"(lbw b )(.+)") #group2 - bowler
        bowledPattern = re.compile(r"((?<!.)\bb\b\s)(.+)") #group2 - bowler
        stumpedPattern = re.compile(r"(st\s†)(.+(?=\sb))(\sb\s)(.+)") #group2 - stumper #group4 - bowler
        caughtAndBowledPattern = re.compile(r"(c & b\s)(.+)") #group2 - catcher #group2 - bowler
        soloRunOutPattern = re.compile(r"(run out \()(\w+(?=\)))") #group2 - fielder
        groupRunOutPattern = re.compile(r"(run out \()(\w+(?=\/))\/([^\)]+)") #group2 - fielder1 #group3 - fielder2

        #Other patterns
        byePattern = re.compile(r"(\d)(b|lb)")#group1 - runs
        runOutRunPattern = re.compile(r",.+?(?=\d)(.)")#group1 - runs

        howOutArray = self.driver.find_elements_by_class_name("wicket-details")
        counter = 0

        for i in howOutArray:
            batterNames = self.driver.find_elements_by_xpath("//td[@class='batsman-cell text-truncate out' or @class='batsman-cell text-truncate not-out']")[counter]
            bowlerName = "NONE"
            catcher = "NONE"
            catchBehinder = "NONE"
            stumper = "NONE"
            runOuters = []
            counter += 1
            if batterNames.text.endswith(" "):
                batterNames = batterNames.text[:-1]
            elif batterNames.text.endswith("(c)"):
                batterNames = batterNames.text.replace(" (c)", "")
            elif batterNames.text.endswith("†"):
                batterNames = batterNames.text.replace(" †", "")

            caught = caughtPattern.match(i.text)
            lbw = lbwPattern.match(i.text)
            bowled =  bowledPattern.match(i.text)
            stumped = stumpedPattern.match(i.text)
            caughtAndBowled = caughtAndBowledPattern.match(i.text)
            soloRunOut = soloRunOutPattern.match(i.text)
            groupRunOut = groupRunOutPattern.match(i.text)
            howOut = None

            if caught != None:
                if caught.group(2).startswith("†"):
                    howOut = "caughtBehind"
                    catchBehinder = caught.group(2).replace("†", "")
                    catchBehinder = catchBehinder[:-1]
                else:
                    howOut = "caught"
                    catcher = caught.group(2)
                bowlerName = caught.group(4)
            elif lbw != None:
                howOut = "lbw"
                bowlerName = lbw.group(2)
            elif bowled != None:
                howOut = "bowled"
                bowlerName = bowled.group(2)
            elif stumped != None:
                howOut = "stumped"
                bowlerName = stumped.group(4)
                stumper = stumped.group(2)
            elif caughtAndBowled != None:
                howOut = "caughtAndBowled"
                catcher = caughtAndBowled.group(2)
                bowlerName = catcher
            elif "not out" in i.text:
                howOut="notOut"
            elif soloRunOut != None:
                howOut = "runOut"
                runOuters = [soloRunOut.group(2)]
            elif groupRunOut != None:
                howOut = "runOut"
                runOuters = [groupRunOut.group(2), groupRunOut.group(3)]

            isBowler = False
            isCatcher = False
            isCatchBehinder = False
            isStumper = False
            isRunOuter = False

            runOutersId = []
            for j in playersList:
                nameSplit = j['name'].split(" ")
                multipleNames = False
                initName = nameSplit[0]
                if len(nameSplit) >= 2:
                    multipleNames = True
                    initName = nameSplit[0][0] + " " + nameSplit[1]

                bowlerNameSplit = bowlerName.split(" ")
                bowlerNameSplitTxt = bowlerNameSplit[0]
                if len(bowlerNameSplit) >= 2:
                    bowlerNameSplitTxt = bowlerNameSplit[0][0] + " " + bowlerNameSplit[1]
                catcherSplit = catcher.split(" ")
                catcherSplitTxt = catcherSplit[0]
                if len(catcherSplit) >= 2:
                    catcherSplitTxt = catcherSplit[0][0] + " " + catcherSplit[1]
                catchBehinderSplit = catchBehinder.split(" ")
                catchBehinderSplitTxt = catchBehinderSplit[0]
                if len(catchBehinderSplit) >= 2:
                    catchBehinderSplitTxt = catchBehinderSplit[0][0] + " " + catchBehinderSplit[1]
                stumperSplit = stumper.split(" ")
                stumperSplitTxt = stumperSplit[0]
                if len(stumperSplit) >= 2:
                    stumperSplitTxt = stumperSplit[0][0] + " " + stumperSplit[1]
                runOuterSplitTxtList = []
                for runOuter in runOuters:
                    runOuterSplit = runOuter.split(" ")
                    if len(runOuterSplit) >= 2:
                        runOuterSplitTxt = runOuterSplit[0][0] + " " + runOuterSplit[1]
                        runOuterSplitTxtList.append(runOuterSplitTxt)
                

                if j['name'] == bowlerName:
                    bowlerName = j['id']
                    isBowler = True
                elif multipleNames and nameSplit[1] == bowlerName:
                    bowlerName = j['id']
                    isBowler = True
                elif bowlerName in j['name']:
                    bowlerName = j['id']
                    isBowler = True    
                elif bowlerName in initName:
                    bowlerName = j['id']
                    isBowler = True
                elif bowlerNameSplitTxt in initName:
                    bowlerName = j['id']
                    isBowler = True
                
                if j['name'] == catcher:
                    catcher = j['id']
                    isCatcher = True
                elif multipleNames and nameSplit[1] == catcher:
                    catcher = j['id']
                    isCatcher = True
                elif catcher in j['name']:
                    catcher = j['id']
                    isCatcher = True    
                elif catcher in initName:
                    catcher = j['id']
                    isCatcher = True
                elif catcherSplitTxt in initName:
                    catcher = j['id']
                    isCatcher = True
                
                if j['name'] == catchBehinder:
                    catchBehinder = j['id']
                    isCatchBehinder = True
                elif multipleNames and nameSplit[1] == catchBehinder:
                    catchBehinder = j['id']
                    isCatchBehinder = True
                elif catchBehinder in j['name']:
                    catchBehinder = j['id']
                    isCatchBehinder = True    
                elif catchBehinder in initName:
                    catchBehinder = j['id']
                    isCatchBehinder = True
                elif catchBehinderSplitTxt in initName:
                    catchBehinder = j['id']
                    isCatchBehinder = True          

                if j['name'] == stumper:
                    stumper = j['id']
                    isStumper = True
                elif multipleNames and nameSplit[1] == stumper:
                    stumper = j['id']
                    isStumper = True
                elif stumper in j['name']:
                    stumper = j['id']
                    isStumper = True    
                elif stumper in initName:
                    stumper = j['id']
                    isStumper = True
                elif stumperSplitTxt in initName:
                    stumper = j['id']
                    isStumper = True

                for k, initRunOuter in zip(runOuters, runOuterSplitTxtList): 
                    if k.replace("†", "") == j['name']:
                        runOutersId.append(j['id'])
                        isRunOuter = True
                    elif multipleNames and nameSplit[1] == k.replace("†", ""):
                        runOutersId.append(j['id'])
                        isRunOuter = True
                    elif k.replace("†", "") in j['name']:
                        runOutersId.append(j['id'])
                        isRunOuter = True
                    elif k.replace("†", "") in initName:
                        runOutersId.append(j['id'])
                        isRunOuter = True
                    elif initRunOuter in initName.replace("†", ""):
                        runOutersId.append(j['id'])
                        isRunOuter = True
                    #addsplittxt later

            for j in playersList:
                if j['name'] == batterNames:
                    bowlerId = -1
                    catcherId = -1
                    catchBehinderId = -1
                    stumperId = -1
                    runOuterIdList = -1

                    if isBowler:
                        bowlerId = bowlerName
                    if isCatcher:
                        catcherId = catcher
                    if isCatchBehinder:
                        catchBehinderId = catchBehinder
                    if isStumper:
                        stumperId = stumper
                    if isRunOuter: #Do this next
                        runOuterIdList = []
                        for element in runOutersId:
                            runOuterIdList.append(element)

                    for dismisser in playersList:
                        if isBowler:
                            if dismisser['id'] == bowlerId:
                                if "bowlerWickets" in dismisser:
                                    list1 = dismisser["bowlerWickets"]
                                    list1.append({'batterId': j['id'], "howOut": howOut})
                                else:
                                    dismisser["bowlerWickets"] = [{'batterId': j['id'], "howOut": howOut}]
                        if isCatcher:
                            if dismisser['id'] == catcherId:
                                if "catches" in dismisser:
                                    list1 = dismisser["catches"]
                                    list1.append({'batterId': j['id'], "bowlerId": bowlerId})
                                else:
                                    dismisser["catches"] = [{'batterId': j['id'], "bowlerId": bowlerId}]
                        if isCatchBehinder:
                            if dismisser['id'] == catchBehinderId:
                                if "caughtBehinds" in dismisser:
                                    list1 = dismisser["caughtBehinds"]
                                    list1.append({'batterId': j['id'], "bowlerId": bowlerId})
                                else:
                                    dismisser["caughtBehinds"] = [{'batterId': j['id'], "bowlerId": bowlerId}]
                        if isStumper:
                            if dismisser['id'] == stumperId:
                                if "stumpings" in dismisser:
                                    list1 = dismisser["stumpings"]
                                    list1.append({'batterId': j['id'], "bowlerId": bowlerId})
                                else:
                                    dismisser["stumpings"] = [{'batterId': j['id'], "bowlerId": bowlerId}]
                        if isRunOuter:
                            for element in runOuterIdList:
                                if dismisser['id'] == element:
                                    if "runOuts" in dismisser:
                                        list1 = dismisser["runOuts"]
                                        list1.append({'batterId': j['id']})
                    batterNames = j['id']
                    if "howOut" in j:
                        list1 = j["howOut"]
                        list1.append({"bowlerId": bowlerId, "catcherId": catcherId, "stumperId": stumperId, "howOut": howOut})
                        j["howOut"] = list1
                    else:
                        j["howOut"] = [{"bowlerId": bowlerId, "catcherId": catcherId, "stumperId": stumperId,  "howOut": howOut}]
        
        balls.analyse(matchID, playersList, matchInfo)
        # accessJSON.addMatch(matchInfo)
        # accessJSON.addIndividual(playersList, matchInfo['id'])
        # # accessJSON.addMatchup(playerMatchUps, matchInfo['id'])


        self.driver.quit()
        
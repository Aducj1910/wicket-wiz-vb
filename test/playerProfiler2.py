import yaml, requests, re, accessMongo
from bs4 import BeautifulSoup

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

umpires = {}

masterTeams = {}
masterMatchups = {}



def process(matchId, checkAgainstPlayersList):
    global data
    playerDict = {}



    for c in checkAgainstPlayersList:
        if c['id'] not in playerDict:
            playerDict[c['id']] = {'catches' : {}, 'stumpings' : {}, 'howOut': {}, 'wickets' : {}}

    print(str(matchId) + " halfway")

    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}

    def selProcessing(name, link, umpire_bool):
        global localPlayerList
        global playerDict
        inDB = accessMongo.checkPlayerMongo(name)
        if not inDB:
            resp = requests.get(link).text
            soup = BeautifulSoup(resp, 'lxml')
            links = soup.findAll("a", href=True)
            for link in links:
                match = False
                linkPlayer = None
                id_ = None
                linkTxt = link['href']
                if "/ci/engine/player" in linkTxt:
                    if enginePlayerPattern.match(linkTxt) != None:
                        id_ = enginePlayerPattern.match(linkTxt).group(1)
                        for kk in checkAgainstPlayersList:
                            if kk['id'] == id_:
                                match = True
                                linkPlayer = enginePlayerPattern.match(linkTxt).group(0)
                
                if match == True:
                    html_request = requests.get("http://stats.espncricinfo.com" + linkPlayer).text
                    soup = BeautifulSoup(html_request, 'lxml')
                    playerName = soup.find('h1')
                    playerName = playerName.text
                    country = soup.find("h3", class_="PlayersSearchLink").text
                    country = country.lower()
                    accessMongo.addPlayerJSON(id_, playerName, name, country)
                    localPlayerList[name] = {'id': id_, 'fullName': playerName, 'umpire': umpire_bool}
                    break


        else:
            returnInfo = accessMongo.getPlayerID(name)
            localPlayerList[name] = {'id': returnInfo['id'], 'fullName': returnInfo['fullName'], 'umpire': umpire_bool}
    
    def selPrep(name, umpire_bool = False):
        global playerDict
        nameSpl = name.split(" ")
        for i in nameSpl:
            if "(" in i:
                nameSpl.remove(i)
        nameJoined = "+".join(nameSpl)
        link = f"https://stats.espncricinfo.com/ci/engine/stats/analysis.html?search={nameJoined}"
        selProcessing(name, link, umpire_bool)

    with open(f'data/tests/{matchId}.yaml', "r") as _file: 
        data = yaml.load(_file)
        teamList = data['info']['teams']
        for t in teamList:
            masterTeams[t.lower()] = {}
        inningsList = data['innings']
        numberInn = len(inningsList)

        umpireList = data['info']['umpires']
        for u in umpireList:
            selPrep(u, True)

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
                over = next(iter(d)) #replacing . with , because MongoDB can't handle
                over = str(over).replace(".", ",")

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
                    if type(ball['wicket']) == list:
                        pass
                    if ball['wicket']['kind'] == 'retired hurt':
                        howOut = 'retired hurt'
                    else:
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
                                catcher = accessMongo.getPlayerID(catcher)['id']
                                s_c = playerDict[catcher]['catches']
                                if inning in s_c:
                                    playerDict[catcher]['catches'][inning].append({'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker})
                                else:
                                    playerDict[catcher]['catches'][inning] = [{'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker}]

                        if howOut == 'stumped':
                            stumper = ball['wicket']['fielders'][0]
                            if " (sub)" in stumper:
                                stumper = -101 #ID For substitue
                            else:
                                selPrep(stumper)
                                stumper = accessMongo.getPlayerID(stumper)['id']
                                s_c = playerDict[stumper]['stumpings']
                                if inning in s_c:
                                    playerDict[stumper]['stumpings'][inning].append({'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker})
                                else:
                                    playerDict[stumper]['stumpings'][inning] = [{'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker}]

                        if howOut == 'caught and bowled':
                            catcher = bowler
                            s_c = playerDict[catcher]['catches']
                            if inning in s_c:
                                playerDict[catcher]['catches'][inning].append({'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker})
                            else:
                                playerDict[catcher]['catches'][inning] = [{'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker}]

                        wicket = True
                
                ballObj = {str(over): {'runs': totalRuns, 'extras': extras, 'batterRuns': batterRuns, 'howOut': howOut, 'wicket': wicket, 'extrasKind': extraKind, 'nonStriker': non_striker, 'batter': batsman, 'bowler': bowler, 'catcher': catcher, 'stumper': stumper}}

                if wicket:
                    if nonStrikerOut:
                        playerDict[non_striker]['howOut'][inning] = {'howOut' : howOut, 'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker}
                    else:
                        playerDict[batsman]['howOut'][inning] = {'howOut' : howOut, 'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker}

                if wickets != 0:
                    s_c2 = playerDict[bowler]['wickets']
                    if inning in s_c2:
                        playerDict[bowler]['wickets'][inning].append({'howOut' : howOut, 'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker})
                    else:
                        playerDict[bowler]['wickets'][inning] = [{'howOut' : howOut, 'bowler' : bowler, 'batter' : batsman, 'over' : over, 'nonStriker' : non_striker}]


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
    for player in localPlayerList:
        pl = localPlayerList[player]
        if pl['umpire'] == True:
            umpires[pl['id']] = pl['fullName']

    print(playerDict)
    return {'batter': masterBatters, 'bowler': masterBowlers, 'nonstriker': masterNonstrikers, 'inningsNumber': numberInn, 'teams' : masterTeams, 'matchups': masterMatchups, 'umpires': umpires, 'playerDict' : playerDict}

    

                

                
                

                


                
                


                
                
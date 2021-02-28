import json
from re import match

def addMatch(matchInfo):
    with open("matchInfo.json", "r") as jsonFile:
        data = json.load(jsonFile)
    
    id = matchInfo['matchID']
    data[id] = matchInfo

    with open("matchInfo.json", "w") as jsonFile:
        json.dump(data, jsonFile)

def addIndividual(playersList, matchId):
    with open("individual.json", "r") as jsonFile:
        data = json.load(jsonFile)
    
    for p in playersList:
        if p['id'] in data:
            data[p['id']][matchId] = p
        else:
            data[p['id']] = {matchId : p}
    
    with open("individual.json", "w") as jsonFile:
        json.dump(data, jsonFile)

def addMatchup(matchUps, matchId):
    with open("matchups.json", "r") as jsonFile:
        data = json.load(jsonFile)

    for m in matchUps:
        if m not in data:
            data[m] = {}
            data[m][matchId] = matchUps[m]
        else:
            data[m][matchId] = matchUps[m]
    
    with open("matchups.json", "w") as jsonFile:
        json.dump(data, jsonFile)
            
    

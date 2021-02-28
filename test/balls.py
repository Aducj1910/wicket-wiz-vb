from os import access
from re import match
import yaml,  playerProfiler, accessJSON


def analyse(file, players, matchInfo):
    with open(f'data/tests/{file}.yaml', "r") as _file:
        data = yaml.load(_file)
        info = data['info']
        matchInfo['matchID'] = file
        # matchInfo['dates'] = info['dates']
        matchInfo['format'] = info['match_type'] 
        matchInfo['venue'] = info['venue']

        matchInfo['dates'] = []
        for date in info['dates']:
            matchInfo['dates'].append(str(date))

        ballByBallDict = playerProfiler.process(file, players)
        matchups = {}

        for b in ballByBallDict['batter']:
            bInn = ballByBallDict['batter'][b] #ADD ISCAPTAIN & ISWICKETKEEPER
            for p in players:
                if p['id'] in bInn:
                    if b not in p:
                        p[b] = {}
                    p[b]['batting'] = bInn[p['id']]
                else:
                    pass

        for b in ballByBallDict['nonstriker']:
            bInn = ballByBallDict['nonstriker'][b] #ADD ISCAPTAIN & ISWICKETKEEPER
            for p in players:
                if p['id'] in bInn:
                    if b not in p:
                        p[b] = {}
                    p[b]['nonstriker'] = bInn[p['id']]
                else:
                    pass

        for b in ballByBallDict['bowler']:
            bInn = ballByBallDict['bowler'][b] #ADD ISCAPTAIN & ISWICKETKEEPER
            for p in players:
                if p['id'] in bInn:
                    if b not in p:
                        p[b] = {}
                    p[b]['bowling'] = bInn[p['id']]
                else:
                    pass 

        for b in ballByBallDict['matchups']:
            bInn = ballByBallDict['matchups'][b]

            for p in bInn:
                if p not in matchups:
                    matchups[p] = {}
                    matchups[p][b] = bInn[p]
                else:
                    matchups[p][b] = bInn[p]


        teamA = matchInfo['teamA']['name']
        teamB = matchInfo['teamB']['name']

        matchInfo['teamA']['info'] = ballByBallDict['teams'][teamA]
        matchInfo['teamB']['info'] = ballByBallDict['teams'][teamB]

        accessJSON.addMatch(matchInfo)
        accessJSON.addIndividual(players, matchInfo['matchID'])
        accessJSON.addMatchup(matchups, matchInfo['matchID'])
        print(str(matchInfo['matchID']) + " finished")

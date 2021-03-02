import pymongo, json
from pymongo import MongoClient

# connection = MongoClient('localhost', 27017)

# db = connection['wicket-wiz-db']
# document = db['test']

# post = {"_id":0, "name": "foo", "age":50}

# document.insert_one(post)

connection = MongoClient('localhost', 27017)


def addMatch(matchInfo):
	db = connection['wicket-wiz-db']
	document = db['matchInfo']

	id = matchInfo['matchID']
	post = {"_id": id, "info": matchInfo}

	document.insert_one(post)

def addIndividual(playersList, matchId):
	db = connection['wicket-wiz-db']
	document = db['individual']

	for p in playersList:
		fetch = document.find_one({"_id": p['id']})
		if fetch == None:
			post = {'_id': p['id'], 'matches': {}}
			post['matches'][matchId] = p
			document.insert_one(post)
		else:
			results = document.update_one({"_id": p['id']}, {"$set": {"matches." + str(p['id']) : p}})

def addMatchup(matchups, matchId):
	db = connection['wicket-wiz-db']
	document = db['matchups']

	for m in matchups:
		fetch = document.find_one({"_id": m})
		if fetch == None:
			post = {'_id': m, 'matches': {}}
			post['matches'][matchId] = matchups[m]
			document.insert_one(post)
		else:
			results = document.update_one({"_id": m}, {"$set": {"matches." + str(m) : matchups[m]}})

def addChecker():
    with open("checker.json", "r") as jsonFile:
        data = json.load(jsonFile)

    data['matches'] += 1
    k = data['matches']

    with open("checker.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    return k

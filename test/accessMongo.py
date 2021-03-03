import pymongo, json, unicodedata
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
			results = document.update_one({"_id": p['id']}, {"$set": {"matches." + str(matchId) : p}})

def addMatchup(matchups, matchId):
	db = connection['wicket-wiz-db']
	document = db['matchups']

	print(matchId)

	for m in matchups:
		fetch = document.find_one({"_id": m})
		if fetch == None:
			post = {'_id': m, 'matches': {}}
			post['matches'][matchId] = matchups[m]
			document.insert_one(post)
		else:
			results = document.update_one({"_id": m}, {"$set": {"matches." + str(matchId) : matchups[m]}})

def addChecker():
    with open("checker.json", "r") as jsonFile:
        data = json.load(jsonFile)

    data['matches'] += 1
    k = data['matches']

    with open("checker.json", "w") as jsonFile:
        json.dump(data, jsonFile)

    return k

def checkPlayerMongo(initials):
	db = connection['wicket-wiz-db']
	document = db['playerInit']

	fetch = document.find_one({"initials" : initials})
	if fetch != None:
		return True
	else:
		return False

def addPlayerJSON(id, name, init, country):
		name = unicodedata.normalize("NFKD", name)
		name = name.replace("      \n", "")

		db = connection['wicket-wiz-db']
		document = db['playerInit']

		post = {"_id": id, "name": name, "initials": init, "country": country}
		document.insert_one(post)

def getPlayerID(initials):
	db = connection['wicket-wiz-db']
	document = db['playerInit']

	fetch = document.find_one({"initials": initials})
	
	return {"id": fetch['_id'], "fullName":fetch['name']}

    
	



import sqlite3, unicodedata, json

def addPlayerJSON(id, name, init, country):
    data = {}
    name = unicodedata.normalize("NFKD", name)
    name = name.replace("      \n", "")

    with open("playersInit/playersInit.json", "r") as jsonFile:
        data = json.load(jsonFile)
        data[init] = {'id': id, 'name': name, 'country': country}
    
    with open("playersInit/playersInit.json", "w") as jsonFile:
        json.dump(data, jsonFile)

def checkPlayerJSON(initials):
    with open("playersInit/playersInit.json") as jsonFile:
        data = json.load(jsonFile)
        if initials in data:
            return True
        else:
            return False

def getPlayerID(initials):
    with open("playersInit/playersInit.json") as jsonFile:
        data = json.load(jsonFile)
        return {"id": data[initials]['id'], "fullName":data[initials]['name']}
    
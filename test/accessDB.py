import sqlite3

def addPlayer(player):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    _id = player['id']
    name = player['name']
    batHand = player['batHand']
    bowlStyle = player['bowlStyle']
    country = player['country']
    DOB = player['DOB']

    c.execute("INSERT INTO playerInfo (id, name, batHand, bowlStyle, DOB, country) VALUES (?, ?, ?, ?, ?, ?)", (_id, name, batHand, bowlStyle, DOB, country))
    conn.commit()
    conn.close()

def addTeam(team):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    _id = team['id']
    name = team['name']

    c.execute("INSERT INTO teamInfo (id, name) VALUES (?, ?)", (_id, name))
    conn.commit()
    conn.close()

def addVenue(venue):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    _id = venue['id']
    name = venue['name']
    country = venue['country']
    
    c.execute("INSERT INTO venueInfo (id, name, country) VALUES (?, ?, ?)", (_id, name, country))
    conn.commit()
    conn.close()

def checkPlayer(player):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    _id = player['id']
    c.execute(f"SELECT * FROM playerInfo WHERE id = {_id}")
    if(c.fetchone() == None):
        return False
    else:
        return True

    conn.close()

def checkTeam(team):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    c.execute(f"SELECT * FROM teamInfo WHERE id = {team}")
    if(c.fetchone() == None):
        return False
    else:
        return True
    conn.close()

def checkVenue(venue):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM venueInfo WHERE id = {venue}")
    if c.fetchone() == None:
        return False
    else:
        return True
    conn.close()
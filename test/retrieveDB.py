import sqlite3

def getPlayerCountry(_id):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    c.execute(f"SELECT country FROM playerInfo WHERE id = {_id}")
    return c.fetchone()[0]
    conn.close()

    

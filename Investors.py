from mimesis import Person
import sqlite3
from random import random as rand
from sqlite3 import Error
import sys
 
def db_connect():
    try:
        con = sqlite3.connect('mydatabase.db', check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con
    except Error: 
        print(Error)
        sys.exit()

def create_table(con): 
    # Init the connection
    cursorObj = con.cursor()

    try:
        # drop the table if it already exists
        cursorObj.execute("DROP TABLE IF EXISTS Investors")
        # commit changes to database
        con.commit()

        # Create the Investor table
        cursorObj.execute("CREATE TABLE Investors(Id integer PRIMARY KEY, Name text, Innocence real, Experience real, Charisma real, Status text)")
        # Commit the changes to database
        con.commit()

    except Error as e:
        print(e.args[0])
        sys.exit()

    return cursorObj

def data_iterator(n):
    
    # Instantiate mimesis name generator
    person = Person()
    
    # Supply information to execute the query
    for _ in range(n):
        yield person.full_name(), round(rand(),2), round(rand(),2), round(rand(),2), "Available"


def create_Investors(population_size):

    # Connect to database and create the table Investor
    con = db_connect()
    cursor = create_table(con)

    # Randomly generate 1000 Investors and add them to the Investors table
    cursor.executemany("INSERT INTO Investors(Name, Innocence, Experience, Charisma, Status) VALUES(?,?,?,?,?)", data_iterator(population_size))

    return con, cursor
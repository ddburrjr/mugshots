import mysql.connector
from configure import ConfigDB


def db_connect():
    cf = ConfigDB()
    config = {
        'user': f'{cf.USER}',
        'password': f'{cf.PASS}',
        'host': f'{cf.HOST}',
        'port': cf.PORT,
        'database': f'{cf.DATABASE}',
    }
    try:
        db = mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        print(err)
        db = None
    return db


def db_search(cursor, query):
    try:
        cursor.execute(query)
        return cursor.fetchone() is not None
    except mysql.connector.Error as err:
        print(err)


def db_retrieve(cursor, query):
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(err)


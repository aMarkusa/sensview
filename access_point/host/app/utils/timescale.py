import psycopg2
import json


def timescale_write(cursor, query):
    cursor.execute(query)
        
def timescale_read(cursor, query):
    cursor.execute(query)
    return_val = cursor.fetchall()

    return return_val
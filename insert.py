""" Insert into SQL database """

import datetime
from database_connection import *
from aux import *
import time


def update(data):
    """Function that updates the database"""
    data.log.append("Starting Inserter")
    conn = database_connection()
    last_refresh = time.time()
    last_archive = time.time()

    while True:
        try:
            items = data.insert_queue.pop()

            # Exit condition
            end = False
            if items[-1] == "STOP":
                items = items[:-1]
                end = True

            inserts = {}
            for item in items:
                if item["table"] in updates:
                    inserts[item["table"]].append(item["value"])
                else:
                    inserts[item["table"]] = [item["value"]]

            for table in inserts:
                conn.write(table,sqlize(inserts[table]))
                if table == "ads":
                    data.loaded += len(inserts[table])

            if time.time() - last_refresh > 1000 or end:
                last_refresh = time.time()
                set_models(conn)
            
            if time.time() - last_archive > 86400 or end:
                last_archive = time.time()
                archive(conn)

            if end:
                print("Stop signal received by inserter")
                conn.__del__()
                return


        except Exception as e:
            data.errors.append(e)
            data.log.append("Error occurred while inserting to database : {}".format(str(e)))
            pass


""" Update database """

import datetime
from database_connection import *
import time
from aux import *


def update(data):
    """Function that updates the database"""
    data.log.append("Starting Updater")
    conn = database_connection()
    last_refresh = time.time()
    last_duplicate = time.time()
    last_archive = time.time()

    while True:
        try:
            items = data.update_queue.pop()

            # Exit condition
            end = False
            if items[-1] == "STOP":
                items = items[:-1]
                end = True

            updates = {}
            for item in items:
                if item["table"] in updates:
                    updates[item["table"]].append(item["value"])
                else:
                    updates[item["table"]] = [item["value"]]

            for table in updates:

                conn.write(table,sqlize(updates[table]))
                if table == "ads":
                    data.loaded += len(updates[table])

            if time.time() - last_refresh > 1000 or end:
                last_refresh = time.time()
                set_models(conn)

            if time.time() - last_duplicate > 3600 or end:
                last_duplicate = time.time()
                duplicate_database(conn)

            if time.time() - last_archive > 86400 or end:
                last_archive = time.time()
                archive(conn)


            if end:
                print("Stop signal received by updater")
                conn.__del__()
                return


        except Exception as e:
            data.errors.append(e)
            data.log.append("Error occurred while updating database : {}".format(str(e)))
            pass


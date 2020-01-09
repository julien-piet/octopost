""" Update database """

import datetime
from database_connection import *


def update(data):
    """Function that updates the database"""
    print("Starting Updater")
    conn = database_connection()

    while True:
        try:
            items = data.update_queue.pop()

            updates = {}
            for item in items:
                if item["table"] in updates:
                    updates[item["table"]].append(item["value"])
                else:
                    updates[item["table"]] = [item["value"]]

            for table in updates:
                conn.write(table,sqlize(updates[table]))

        except Exception as e:
            data.errors.append(e)
            print("Error occurred while updated database : {}".format(str(e)))
            pass


def sqlize(ipt):
    """ Returns a sql compatible representation of the input """
    text_fields = ['title', 'make', 'condition', 'color', 'vin', 'type', 'url', 'car_title', 'puid', "model", 'trim', 'series']
    number_fields = ['mileage', 'price']
    date_fields = ["post_date", "update"]

    data = []
    for entry in ipt:
        data_point = {}
        for key in entry:
            value = entry[key]
            if key in text_fields or key in date_fields:
                data_point[key] = "'" + str(value).replace("'",'"') + "'" if value else "null"
            elif key in number_fields:
                data_point[key] = str(value) if value else "null"
            elif key == "year":
                if value:
                    data_point["year"] = "'" + str(datetime.datetime.strptime(str(value) + "-01-02T00:00:00-0000", '%Y-%m-%dT%H:%M:%S%z')) + "'"
                else:
                    data_point["year"] = "null"
            elif key == "geo":
                if value:
                    data_point["geo"] = "'POINT(" + str(value["latitude"]) + " " + str(value["longitude"]) + ")'"
                else:
                    data_point["geo"] = "null"
        data.append(data_point)
    return data


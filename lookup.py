"""VIN decoding - Build a database of makes and models """

import json


def lookup(data, conn, vin, year):

    code = vin[:9]
    base_url = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{}?format=json".format(code)
    if year and year < 1990:
        base_url += "&modelyear=" + str(year)

    cnt = conn.get(base_url)
    info = json.loads(cnt)["Results"]

    # Fetch model and trim
    fields = {"Model": 0, "Series": 0, "Trim": 0, "Make": 0}
    for item in info:
        if "Variable" in item:
            if item["Variable"] in fields:
                fields[item["Variable"]] = item["Value"]
        if all([value != 0 for key, value in fields]):
            break

    if not all([value != 0 for key, value in fields]):
        return

    fields = {key.lower(): value for key, value in fields}

    # Write to database
    data.update_queue.put({"table": "vins", "value": fields})


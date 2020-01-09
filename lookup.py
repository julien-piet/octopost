"""VIN decoding - Build a database of makes and models """

import json
from session import *


def lookup(data):
    """ Handle multiple vins at a time """

    print("Starting Lookup")
    conn = session(data)

    while True:
        try:
            vins = data.lookup_queue.pop()

            post_data = {"DATA": "; ".join([", ".join([vin["vin"][:9], str(vin["year"])]) for vin in vins]), "format": "json"}
            base_url = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"

            cnt = conn.post(base_url, post_data)
            info = json.loads(cnt)["Results"]

            # Fetch model and trim
            fields = [{"vin": item["VIN"], "model": item["Model"], "series": item["Series"], "trim": item["Trim"],
                       "make": item["Make"]} for item in info]

            # Write to database
            for field in fields:
                data.update_queue.put({"table": "vins", "value": field})

        except Exception as e:
            data.errors.append(e)
            print("Error occurred while looking up vins : {}".format(str(e)))
            pass


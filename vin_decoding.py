"""VIN decoding - Build a database of makes and models """
import json
import requests
from aux import *

class vin_decoder():

    def __init__(self, db):
        self.local = {item[0]: {"model": item[1], "series": item[2], "trim": item[3]} for item in db.query("SELECT vin, model, series, trim FROM vins")}
        self.db = db
        cl_adapter = requests.adapters.HTTPAdapter(max_retries=2)
        self.session = requests.Session()
        self.session.mount("http://",cl_adapter)
        self.session.mount("https://",cl_adapter)

    def lookup(self, vin, year=None):
        
        if not vin or len(vin) != 17:
            return {"model": None, "series": None, "trim": None}
        code = vin[:9]
        
        if code in self.local:
            return self.local[code]

        # Lookup online
        base_url = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{}?format=json".format(code)
        if year and year < 1990:
            base_url += "&modelyear=" + str(year)
        
        try:
            cnt = self.session.get(base_url).text
            data = json.loads(cnt)["Results"]
        except Exception as e:
            print(e)
            print(base_url)
            print(cnt)
            return {"model": None, "series": None, "trim": None}

        # Fetch model and trim
        model = 0
        series = 0
        trim = 0
        make = 0
        for item in data:
            if "Variable" in item and item["Variable"] == "Model":
                model = item["Value"]
            if "Variable" in item and item["Variable"] == "Series":
                series = item["Value"]
            if "Variable" in item and item["Variable"] == "Trim":
                trim = item["Value"]
            if "Variable" in item and item["Variable"] == "Make":
                make = item["Value"]
            if model != 0 and series != 0 and trim != 0 and make != 0:
                break

        rtn_val = {"model": model, "series": series, "trim": trim}

        # Write to database 
        self.local[code] = rtn_val
        data_for_db = rtn_val
        data_for_db["make"] = make
        self.write(code, data_for_db)

        # Return model
        return rtn_val


    def write(self, vin, data):
        """Update database"""
        sql_data = {"vin": "'" + vin + "'"}
        for key in data:
            if data[key]:
                sql_data[key] = "'" + data[key] + "'"
            else:
                sql_data[key] = "null"
        
        self.db.write(table="vins", data=[sql_data])


"""VIN decoding - Build a database of makes and models """

# FIXME It would be better if broken vin checks lead to doing a hard search for the model, (3% of cases)

import json
from session import *
from database_connection import *
from static_data import *
from update import sqlize
from extractor import build_model_regex_from_list
import re


def lookup(data):
    """ Handle multiple vins at a time """

    print("Starting Lookup")
    conn = session(data)
    refresh_counter = 0

    while True:
        try:
            vins = data.lookup_queue.pop()

            post_data = {"DATA": "; ".join([", ".join([vin["vin"][:9], str(vin["year"])]) for vin in vins]), "format": "json"}
            base_url = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"

            cnt = conn.post(base_url, post_data)
            info = json.loads(cnt)["Results"]

            # Fetch model and trim
            fields = [{"vin": item["VIN"], "model": norm(item["Model"]), "series": norm(item["Series"]), "trim": norm(item["Trim"]),
                       "make": item["Make"]} for item in info]

            # Write to database
            for field in fields:
                data.update_queue.put({"table": "vins", "value": field})

            # Check for refresh
            refresh_counter += len(vins)
            if refresh_counter > 2500:
                refresh_model_db(data)
                refresh_counter = 0

        except Exception as e:
            data.errors.append(e)
            print("Error occurred while looking up vins : {}".format(str(e)))
            pass


def refresh_model_db(data):
    """ Refreshes the model database """
    """ There are two parts to this :
        
            * We can get fresh models, series and trims from the VIN database, for every new 1000 entries
            * We can load models from the website, every month or so (does not change a lot)
            
        Cannot run concurrently
    """

    # Create database handle
    db = database_connection()

    # First, get fresh models from vin database
    sql = "DELETE FROM models WHERE models.from_vins = 1;" \
          "INSERT INTO models (SELECT DISTINCT make, model, series, trim, 1 FROM vins WHERE make is NOT NULL and model IS NOT NULL);"
    db.query(sql, nofetch=True)

    # Second, see if it is time to refresh from website
    sql = "SELECT update_type, last, freq FROM freshness WHERE update_type = 'get_all_models' AND last + freq < CURRENT_TIMESTAMP;"
    if len(db.query(sql)) > 0:
        from_website_refresh(db, data)
        db.query("UPDATE freshness SET last = CURRENT_TIMESTAMP WHERE update_type = 'get_all_models';",nofetch=True)

    # Finally, update local info
    sql = "SELECT make, model, series, trim FROM models;"
    models_raw = [{'make': item[0].strip(), 'model': item[1], 'series': item[2], 'trim': item[3]} for item in db.query(sql)]
    models = {}
    for item in models_raw:
        make = makes[item["make"].lower()].strip() if item["make"].lower() in makes else item["make"].lower()
        if make not in models:
            models[make] = {'model_to_trim': {}, 'model_to_series': {}, 'trim_to_model':{}, 'series_to_model':{}}

        model = norm(item["model"])
        trim = norm(item["trim"])
        series = norm(item["series"])

        if model not in models[make]["model_to_trim"]:
            models[make]["model_to_trim"][model] = []
        if model not in models[make]["model_to_series"]:
            models[make]["model_to_series"][model] = []
        if trim and trim not in models[make]["trim_to_model"]:
            models[make]["trim_to_model"][trim] = []
        if series and series not in models[make]["series_to_model"]:
            models[make]["series_to_model"][series] = []

        if trim:
            if trim not in models[make]["model_to_trim"][model]:
                models[make]["model_to_trim"][model].append(trim)
            if model not in models[make]["trim_to_model"][trim]:
                models[make]["trim_to_model"][trim].append(model)
        if series:
            if series not in models[make]["model_to_series"][model]:
                models[make]["model_to_series"][model].append(series)
            if model not in models[make]["series_to_model"][series]:
                models[make]["series_to_model"][series].append(model)

    for make in models:
        model_list = models[make]["model_to_trim"].keys()
        models[make]["model_regex"] = build_model_regex_from_list(model_list, make)
        trim_list = models[make]["trim_to_model"].keys()
        models[make]["trim_regex"] = build_model_regex_from_list(trim_list, make)
        series_list = models[make]["series_to_model"].keys()
        models[make]["series_regex"] = build_model_regex_from_list(series_list, make)

    data.models = models

    # Cleanup
    db.__del__()


def from_website_refresh(db, data):
    """ Fetch website info on models """

    conn = session(data)

    # Load items from VINS that might intersect
    baseline = {item[0] + "|" + item[1]: True for item in db.query("SELECT DISTINCT make, model from models WHERE from_vins = 1;")}

    # First load makes :
    makes_all = json.loads(conn.get("https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json"))["Results"]
    makes_rest = []
    for make in makes_all:
        if make["Make_Name"].lower() in makes:
            makes_rest.append(make["Make_Name"].upper())

    # Second, load models :
    models = []
    for make in makes_rest:
        page = conn.get("https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{}?format=json".format(make))
        models.extend({'from_vins': 0, 'make': make, 'model': norm(item["Model_Name"])} for item in json.loads(page)["Results"] if item["Model_Name"] and make + "|" + norm(item["Model_Name"]) not in baseline)

    # Finally, update database
    models = sqlize(models)
    db.query("DELETE FROM models WHERE from_vins IS DISTINCT FROM 1;", nofetch=True)

    db.write(table="models", data=models)


def norm(model):
    """ Removes any extra whitespace, or characters not essential to the model name """
    # TODO : Implement once the database is large enough
    if isinstance(model, str):
        model = model.replace("-","").lower()
        model = re.sub(r"[ ]{2,}"," ",model)
        model = model.strip()
    return model

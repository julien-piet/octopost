"""VIN decoding - Build a database of makes and models """

import json
from session import *
from database_connection import *
from static_data import *
from update import sqlize


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
            if refresh_counter > 1000:
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
          "INSERT INTO models (SELECT DISTINCT make, model, series, trim, 1 FROM vins WHERE v.make is NOT NULL and v.model IS NOT NULL);"
    db.query(sql)

    # Second, see if it is time to refresh from website
    sql = "SELECT update_type, last, freq FROM freshness WHERE update_type = 'get_all_models' AND last + freq < CURRENT_TIMESTAMP;"
    if len(db.query(sql)) > 0:
        from_website_refresh(db, data)
        db.query("UPDATE freshness SET last = CURRENT_TIMESTAMP WHERE update_type = 'get_all_models';")

    # Finally, update local info
    sql = "SELECT make, model, series, trim FROM models;"
    models = [{'make': item[0], 'model': item[1], 'series': item[2], 'trim': item[3]} for item in db.query(sql)]
    data.models = models

    # Cleanup
    db.__del__()


def from_website_refresh(db, data):
    """ Fetch website info on models """

    conn = session(data)

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
        models.extend({'from_vins': 0, 'make': make, 'model': norm(item["Model_Name"])} for item in json.loads(page)["Results"] if item["Model_Name"])

    # Finally, update database
    models = sqlize(models)
    db.query("DELETE FROM models WHERE from_vins is NOT 1;")
    db.write(table="models", data=models)


def norm(model):
    """ Removes any extra whitespace, or characters not essential to the model name """
    # TODO : Implement once the database is large enough
    return model
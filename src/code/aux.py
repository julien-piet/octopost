"""Auxiliary functions"""
import re
import datetime
from .static_data import *


def build_model_regex_from_list(names, make=None):
    """ Builds search regex """
    if make in reverse_makes:
        blacklist = reverse_makes[make]
    else:
        blacklist = []
    items = [escape_re(item) for item in names if item not in blacklist]
    items.sort(key=len, reverse=True)
    return re.compile("(?:^| )(" + "|".join(items) + ")(?:$|[0-9,\.;\* ])")


def norm(model):
    """ Removes any extra whitespace, or characters not essential to the model name """
    # TODO : Implement once the database is large enough
    if isinstance(model, str):
        model = model.replace("-","").lower()
        model = re.sub(r"[ ]{2,}"," ",model)
        model = model.strip()
    return model


def vin_check(vin):
    """ Verify the checksum """
    translit = \
            {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,\
             'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5,         'P': 7, 'R': 9,\
                     'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,\
                     '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '0': 0}
    weights = [8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2]
    try:
        total = sum(translit[vin[i]]*weights[i] for i in range(17))
        check_num = total % 11
        if 0 <= check_num <= 9:
            check = str(check_num)
        else:
            check = 'X'
        if check == vin[8]:
            if vin == '11111111111111111' or vin == '00000000000000000':
                return False
            return True
        else:
            return False
    except Exception:
        return False


def stop_function(data):
    """ Stops the program. To be run by a fetcher """

    def end_func(d):
        # To be run last
        print("Stop signal received by parser")
        d.update_queue.put("STOP")
        d.lookup_queue.put("STOP")
        exit(0)

    def inter_func(d):
        # To be run last by fetch
        print("Stop signal received by fetcher")
        for i in range(data.th_count['parse']):
            d.parse_queue.put(lambda x, y: end_func(x))
        exit(0)

    print("Stop signal received by feeder")
    for i in range(data.th_count['fetch']):
        data.fetch_queue.put(lambda x, y: inter_func(x))
    exit(0)


def escape_re(regex):
    """ Format regex """
    escape_regex = re.compile('(\^|\$|\*|\.|\\|\+|\?|\[|\]|\(|\)|\{|\}|\||\/)')
    return re.sub(escape_regex,r'\\\g<1>',regex) 


def sqlize(ipt, process_year=True, reverse=False):
    """ Returns a sql compatible representation of the input """
    text_fields = ['title', 'make', 'condition', 'color', 'vin', 'type', 'url', 'car_title', 'puid', "model", 'trim', 'series', 'raw', 'cor', 'field', 'model_clean', 'trim_clean', 'series_clean', 'refresh_for']
    number_fields = ['mileage', 'price', 'from_vins', 'new']
    date_fields = ["post_date", "update", "last_fetch"]
    bool_fields = ["expired"]
    if not process_year:
        date_fields.append("year")

    if not reverse:
        # Convert from python format to SQL format
        data = []
        for entry in ipt:
            data_point = {}
            for key in entry:
                value = entry[key]
                if key in text_fields or key in date_fields:
                    data_point[key] = "'" + str(value).replace("'",'"') + "'" if value else "null"
                elif key in number_fields:
                    data_point[key] = str(value) if value and -1073741824 < value < 1073741824 else "null"
                elif key in bool_fields:
                    data_point[key] = "true" if value else "false"
                elif process_year and key == "year":
                    if value:
                        data_point["year"] = "'" + str(datetime.datetime.strptime(str(value) + "-01-02T00:00:00-0000", '%Y-%m-%dT%H:%M:%S%z')) + "'"
                    else:
                        data_point["year"] = "null"
                elif key == "geo":
                    if value:
                        data_point["geo"] = "'POINT(" + str(value["longitude"]) + " " + str(value["latitude"]) + ")'"
                    else:
                        data_point["geo"] = "null"
            data.append(data_point)
        return data

    # Convert from SQL format to python format
    get_geo = re.compile("POINT\((?P<long>[-]?\d*?(?:\.\d*?)?) (?P<lat>[-]?\d*?(?:\.\d*?)?)\)")
    data = []
    for entry in ipt:
        data_point = {}
        for key in entry:
            value = entry[key]
            if key in text_fields:
                data_point[key] = value if value else None
            elif key in date_fields:
                if value:
                    data_point[key] = datetime.datetime.strptime(value + '-0000', '%Y-%m-%d %H:%M:%S%z')
                else:
                    data_point[key] = None
            elif key in number_fields:
                data_point[key] = float(value) if value else None
            elif key == "year":
                if value:
                    data_point[key] = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').year
                else:
                    data_point[key] = None
            elif key == "geo":
                data_point[key] = None
                if value:
                    mtch = get_geo.search(value)
                    if mtch:
                        data_point[key] = {'latitude': float(mtch.group("lat")), "longitude": float(mtch.group("long"))}
            else:
                data_point[key] = value
        data.append(data_point)
    return data


def set_models(conn):
    """ set model names for new listings """

    conn.query("UPDATE ads \
                SET model = vins.model, series = vins.series, trim = vins.trim \
                FROM vins \
                WHERE substring(ads.vin,1,9) = vins.vin AND ads.model is null AND ads.make=lower(vins.make);", True)

    for field in ["model", "trim", "series"]:
        conn.query("UPDATE ads \
                    SET {0}_clean = renaming.cor\
                    FROM renaming \
                    WHERE ads.{0}_clean is null and renaming.field = '{0}' and ads.{0} = renaming.raw and ads.make = LOWER(renaming.make);".format(field), True)

        conn.query("UPDATE ads \
                    SET {0}_clean = {0}\
                    WHERE {0}_clean is null;".format(field), True)


def archive(conn):
    """ Archive ads """

    conn.query("INSERT INTO ads_archive (SELECT * FROM ads where expired or post_date < current_timestamp - interval '30 days');", True)
    conn.query("DELETE from ads where id in (SELECT id FROM ads_archive);", True)


def duplicate_database(conn):
    """ Duplicate database to webdatabase for speed """

    sql = """
    CREATE TABLE ads_web_2 AS (select * from ads where model is not null or vin is null);
    DROP TABLE ads_web;
    ALTER TABLE ads_web_2 RENAME TO ads_web;
    CREATE INDEX make_model_i ON ads_web(make,model);
    CREATE INDEX mileage_i ON ads_web(mileage);
    CREATE INDEX price_i on ads_web(price);
    CREATE INDEX puid_i on ads_web(puid);
    CREATE INDEX year_i on ads_web(year);
    CREATE INDEX post_date_i on ads_web(post_date);
    CREATE INDEX id_i on ads_web(id);
    """
    
    conn.query(sql, True)
    

import requests
import re
from bs4 import BeautifulSoup
from extractor import *
from data import *
import json
from session import *
from static_data import *
from update import sqlize
from aux import *
import sys


def lookup(vins):
    """ Handle multiple vins at a time """

    post_data = {"DATA": "; ".join([", ".join([vin["vin"][:9], str(vin["year"])]) for vin in vins]), "format": "json"}
    base_url = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"

    cnt = requests.post(base_url, post_data).text
    info = json.loads(cnt)["Results"]

    print(info)

    # Fetch model and trim
    fields = [{"vin": item["VIN"], "model": norm(item["Model"]), "series": norm(item["Series"]), "trim": norm(item["Trim"]),
               "make": item["Make"]} for item in info if item["Make"]]

    print(fields)


def parse(data, url, content):
    """Parser for Craigslist pages"""
    ad = {"title":     extractor.get_title(content), \
           "make":      extractor.get_make(content), \
           "post_date": extractor.get_postdate(content), \
           "geo":       extractor.get_geo(content), \
           "mileage":   extractor.get_mileage(content), \
           "year":      extractor.get_year(content), \
           "price":     extractor.get_price(content), \
           "update":    extractor.get_update(content), \
           "url":       url}

    if ad["make"] is None or ad["geo"] is None or (not ad["mileage"] and not ad["price"]):
        data.incompatible.append(url)
        return

    ad.update(extractor.get_details(content))
    ad.update(extractor.get_model(content, data, ad))
    return extractor.get_puid(ad)


data = crawl_data(0,0,0)
page = requests.get(sys.argv[1]).text
bsc = BeautifulSoup(page, features="html.parser")
a = parse(data, sys.argv[1], bsc)

page = requests.get(sys.argv[2]).text
bsc = BeautifulSoup(page, features="html.parser")
b = parse(data, sys.argv[2], bsc)

print(a)
print(b)
print(a[1] == b[1])
#vins = [{'vin': "JTHBJ46G6",'year': '2007'},{'vin': 'azertty', 'year': 'null'},{'vin': '2GTEK19K3', 'year': '1993'}]
#lookup(vins)

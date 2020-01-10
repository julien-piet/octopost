""" Fetch.py - load a craigslist ad """

from extractor import *
from lookup import *


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
    
    if ad["make"] is None:
        data.incompatible += 1
        return
    
    ad.update(extractor.get_details(content))
    ad.update(extractor.get_model(content, data, ad))
    ad["puid"] = extractor.get_puid(ad)

    data.loaded += 1
    data.update_queue.put({"table": "ads", "value": ad})

    # Search for VIN
    if ad["vin"] and 9 <= len(ad["vin"]) <= 17 and ad["vin"][:9] not in data.vins:
        data.vins[ad["vin"][:9]] = True
        vin, year = ad["vin"], ad["year"]
        data.lookup_queue.put({'vin': vin, 'year': year})

""" Fetch.py - load a craigslist ad """

from extractor import *
from lookup import *
import datetime


def parse(data, url, content, prev_content=None):
    """Parser for Craigslist pages"""

	if extractor.is_expired(content):
        if not prev_content:
            return
        data.update_queue.put({"table": "refresh", "value": {"url": url, "expired": True}})
		return

    ad = {"title":     extractor.get_title(content), \
           "make":      extractor.get_make(content), \
           "post_date": extractor.get_postdate(content), \
           "geo":       extractor.get_geo(content), \
           "mileage":   extractor.get_mileage(content), \
           "year":      extractor.get_year(content), \
           "price":     extractor.get_price(content), \
           "update":    extractor.get_update(content), \
           "url":       url}
    
    ad.update(extractor.get_details(content))

    # Seperate functionality if this is an update or an initial ad
    if not prev_content:
        # This is a first ad
        if ad["make"] is None or ad["geo"] is None or not ad["price"]:
            data.incompatible.append(url)
            data.update_queue.put({"table": "inconsistent_ads", "value": {'url': url}})
            return

        ad.update(extractor.get_model(content, data, ad))
        ad["puid"] = extractor.get_puid(ad)
        ad["refresh_for"] = ad["puid"]
    else:
        # If this isn't anything new, write to refresh list so that we don't try again
        if datetime.timestamp(ad["update"]) == datetime.timestamp(prev_content["update"])
            data.update_queue.put({"table": "refresh", "value": {'url': url, 'expired': False}})
            return

        # Only do the slow operations if necessary
        if not prev_content["model"]:
            ad.update(extractor.get_model(content, data, ad))
        
        ad["puid"] = extractor.get_puid(ad)
        ad["refresh_for"] = prev_content["refresh_for"]


    data.update_queue.put({"table": "refresh", "value": {'url': url, 'expired': False}})
    data.update_queue.put({"table": "ads", "value": ad})
    
    # Search for VIN
    if ad["vin"] and ad["vin"][:9] not in data.vins:
        data.debug.append("Adding {}".format(ad["vin"]))
        data.vins[ad["vin"][:9]] = True
        vin, year = ad["vin"], ad["year"]
        data.lookup_queue.put({'vin': vin, 'year': year})


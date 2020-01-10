"""Craigslist specific data extractor"""
import re
import math
import datetime
from static_data import *
from aux import *
# Import constructor specific parsers :
import make_specific.mercedes as mercedes
import make_specific.jaguar as jaguar
import make_specific.mazda as mazda


class extractor():

    @staticmethod
    def get_puid(ad):
        puid = str(ad["make"]) + str(ad["mileage"]) + str(ad["year"])
        if not ad["mileage"]:
            puid += str(ad["price"])
        geo = ad["geo"]
        if geo:
            puid += str(math.floor(int(geo["latitude"]) * 25) / 25) + str(math.floor(int(geo["longitude"]) * 25) / 25)

        vin_regex = re.compile("^(?=.*[0-9])(?=.*[A-z])[0-9A-z-]{17}$")
        if ad["vin"] and vin_regex.match(ad["vin"]):
            puid = str(ad["vin"]) + str(math.floor(ad["mileage"] / 5000) * 5000) if ad["mileage"] is not None else str(
                ad["vin"])

        return puid

    @staticmethod
    def get_model(bsc, data, ad):
        """ Get model from VIN number """

        result = {"model": None, "trim": None, "series": None}

        if ad["vin"] and vin_check(ad["vin"]):
            return result

        make = ad["make"]
        if make not in data.models:
            data.log.append("No known models for make {}. {}".format(make, ad["url"]))
            return result

        # If we get here, we need to determine the vehicle model from the content of the ad
        haystack = [attr.text for attr in bsc.select(".attrgroup span")][0].replace("-","").lower() + " " + bsc.find(id="titletextonly").text.replace("-","").lower()

        model = None
        trim = None
        series = None

        # Make-specific parsers
        if make in ["mercedes-benz", "jaguar", "mazda"]:

            full_text = [attr.text for attr in bsc.select(".attrgroup span")][0].lower() + " " + bsc.find(id="titletextonly").text.lower()
            if make == "mercedes-benz":
                # Mercedes-specific filter
                parse_result = mercedes.get_model(full_text)
                if parse_result:
                    return parse_result

            if make == "jaguar":
                # Jaguar-specific filter
                parse_result = jaguar.get_model(full_text)
                if parse_result:
                    return parse_result

            if make == "mazda":
                # Mazda-specific filter
                parse_result = mazda.get_model(full_text)
                if parse_result:
                    return parse_result


        # Build search regex
        model_regex = data.models[make]["model_regex"]
        mtch = model_regex.search(haystack)
        if mtch:
                model = mtch.group(1)

        trims = None
        series_list = None
        if model:
            trims = data.models[make]["model_to_trim"][model]
            series_list = data.models[make]["model_to_series"][model]
        else:
            trims = data.models[make]["trim_regex"]
            series_list = data.models[make]["series_regex"]

        if trims:
            trim_regex = build_model_regex_from_list(trims, make) if model else trims
            mtch = trim_regex.search(haystack)
            if mtch:
                trim = mtch.group(1)

        if series_list:
            series_regex = build_model_regex_from_list(series_list, make) if model else series_list
            mtch = series_regex.search(haystack)
            if mtch:
                series = mtch.group(1)

        if (not model) and trim:
            if len(data.models[make]["trim_to_model"][trim]) == 1:
                model = data.models[make]["trim_to_model"][trim][0]

        if (not model) and series:
            if len(data.models[make]["series_to_model"][series]) == 1:
                model = data.models[make]["series_to_model"][series][0]

        if (not trim) and model:
            if len(data.models[make]["model_to_trim"][model]) == 1:
                trim = data.models[make]["model_to_trim"][model][0]

        if (not series) and model:
            if len(data.models[make]["model_to_series"][model]) == 1:
                series = data.models[make]["model_to_series"][model][0]


        result = {'model': model, 'trim': trim, 'series': series}
        if all(not result[key] for key in result):
            data.log.append("No recognized models for {} with make {}".format(ad["url"], make))

        return result


    @staticmethod
    def get_details(bsc):
        """ Same method for condition, paint, type and title """
        filters = {"vin": re.compile("[vV][iI][nN]: (.*)"), \
                   "car_title": re.compile("title status: (.*)"), \
                   "condition": re.compile("condition: (.*)"), \
                   "type": re.compile("type: (.*)"), \
                   "color": re.compile("paint color: (.*)")}

        rtn = {key: None for key in filters}
        attr = [attr.text for attr in bsc.select(".attrgroup span")]
        for i in attr:
            for filt in filters:
                mtch = filters[filt].search(i)
                if mtch:
                    if filt == "vin":
                        rtn[filt] = mtch.group(1).upper()
                    else:
                        rtn[filt] = mtch.group(1)
        return rtn

    @staticmethod
    def get_title(bsc):
        try:
            return bsc.select(".postingtitletext")[0].text.replace("-", " ").replace("*", "").strip()
        except Exception as e:
            return None

    @staticmethod
    def get_make(bsc):
        keywords = [elt for attr in bsc.select(".attrgroup span") for elt in
                    attr.text.replace("-", " ").replace("*", "").strip().split(" ")]
        keywords.extend(bsc.select(".postingtitletext")[0].text.replace("-", " ").replace("*", "").strip().split(" "))
        for kw in keywords:
            if kw.lower() in makes:
                return makes[kw.lower()]

    @staticmethod
    def get_geo(bsc):
        geo_obj = bsc.find(id="map")
        try:
            return {"latitude": float(geo_obj["data-latitude"]), "longitude": float(geo_obj["data-longitude"])}
        except TypeError:
            return None

    @staticmethod
    def get_mileage(bsc):
        value = None
        attr = [attr.text for attr in bsc.select(".attrgroup span")]
        for i in attr:
            if not i.find("odometer: "):
                return min(int(i[9:]), 1000000)

        # If we get here, the odometer wasn't specified. Look in body / title
        # Title of ad :

        haystacks = [bsc.select(".postingtitletext")[0].text, bsc.find(id="postingbody").text]

        for haystack in haystacks:
            hsk = haystack.replace("\n", " ").strip().lower()
            hsk = re.sub(r"[*-\.:\[\]]", "", hsk)
            mtch = re.search(r"([1-9]\d*k|\d+(?:,\d+)?)[ ]*(?:original|actual|low){0,2}[ ]*miles", hsk)
            if mtch:
                val = mtch.group(1)
                if val[-1] == 'k':
                    val = val[:-1] + "000"
                val = val.replace(",", "")
                return min(int(val), 1000000)

        return None

    @staticmethod
    def get_year(bsc):
        try:
            return int([attr.text for attr in bsc.select(".attrgroup span")][0][:4])
        except:
            pass

        # The hard way : look for a number between 1970 and this year
        max_year = datetime.datetime.now().year
        ys = [str(i) for i in range(1970, max_year + 1)]
        ys.extend([str(i)[-2:] for i in range(1970, max_year + 1)])
        filt = re.compile(" (" + '|'.join(ys) + ")[']? ")

        haystacks = [bsc.select(".postingtitletext")[0].text, bsc.find(id="postingbody").text]

        for haystack in haystacks:
            hsk = haystack.replace("\n", " ").strip().lower()
            hsk = re.sub(r"[*-\.\[\]]", "", hsk)
            mtch = filt.search(hsk)
            if mtch:
                year = int(mtch.group(1))
                if year < int(str(max_year)[-2:]):
                    year += 2000
                elif year < 100:
                    year += 1900
                return year

        return None

    @staticmethod
    def get_price(bsc):
        try:
            val = int(bsc.select(".price")[0].text.replace("$", ""))
            return val if 0 < val < 70000000 else None
        except:
            pass

        # The hard way
        filt = re.compile("\$[ ]*([1-9]\d*k|\d+(?:,\d+)?)")
        haystacks = [bsc.select(".postingtitletext")[0].text, bsc.find(id="postingbody").text]

        for haystack in haystacks:
            hsk = haystack.replace("\n", " ").strip().lower()
            hsk = re.sub(r"[*-\[\]]", "", hsk)
            mtch = filt.search(hsk)
            if mtch:
                val = mtch.group(1)
                if val[-1] == 'k':
                    val = val[:-1] + "000"
                val = val.replace(",", "")
                return int(val) if 0 < int(val) < 70000000 else None

        return None

    @staticmethod
    def get_postdate(bsc):
        try:
            raw = bsc.select(".postinginfos time")[0]["datetime"]
            return datetime.datetime.strptime(raw, '%Y-%m-%dT%H:%M:%S%z')
        except Exception as e:
            raise e
            return None

    @staticmethod
    def get_update(bsc):
        try:
            raw = bsc.select(".postinginfos time")[-1]["datetime"]
            return datetime.datetime.strptime(raw, '%Y-%m-%dT%H:%M:%S%z')
        except Exception as e:
            raise e
            return None


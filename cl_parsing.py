"""Craigslist specific data extractor"""
import re
import math
import datetime
from bs4 import BeautifulSoup
from static_data import *
from aux import *

class cl_extractor():

    @staticmethod
    def extract(bsc, url, data):
        cnt = {     "title": cl_extractor.get_title(bsc), \
                        "make": cl_extractor.get_make(bsc), \
                        "post_date": cl_extractor.get_postdate(bsc), \
                        "geo":  cl_extractor.get_geo(bsc), \
                        "mileage": cl_extractor.get_mileage(bsc), \
                        "year":  cl_extractor.get_year(bsc), \
                        "price": cl_extractor.get_price(bsc), \
                        "update": cl_extractor.get_update(bsc), \
                        "url" : url}
        cnt.update(cl_extractor.get_details(bsc))
        cnt.update(cl_extractor.get_model(bsc,data,cnt))

        puid = str(cnt["make"]) + str(cnt["mileage"]) + str(cnt["year"])
        if not cnt["mileage"]:
            puid += str(cnt["price"])
        geo = cnt["geo"]
        if geo:
            puid += str(math.floor(int(geo["latitude"]) * 25) / 25) + str(math.floor(int(geo["longitude"]) * 25) / 25)

        vin_regex = re.compile("^(?=.*[0-9])(?=.*[A-z])[0-9A-z-]{17}$")
        if cnt["vin"] and vin_regex.match(cnt["vin"]):
            puid = str(cnt["vin"]) + str(math.floor(cnt["mileage"]/5000) * 5000) if cnt["mileage"] is not None else str(cnt["vin"]) 

        cnt["puid"] = puid
        return cnt
            

    @staticmethod
    def get_model(bsc, data, cnt):
        """ Get model from VIN number """
        vin = cnt["vin"]
        year = cnt["year"]
        model_info = data.vins.lookup(vin.upper() if vin else vin, year)
        return model_info
        

    @staticmethod
    def get_details(bsc):
        """ Same method for condition, paint, type and title """
        filters = { "vin": re.compile("[vV][iI][nN]: (.*)"), \
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
                    rtn[filt] = mtch.group(1)
        return rtn
        


    @staticmethod
    def get_title(bsc):
        try:
            return bsc.select(".postingtitletext")[0].text.replace("-"," ").replace("*","").strip()
        except Exception as e:
            return None
    
    @staticmethod
    def get_make(bsc):
        keywords = [elt for attr in bsc.select(".attrgroup span") for elt in attr.text.replace("-"," ").replace("*","").strip().split(" ")]
        keywords.extend(bsc.select(".postingtitletext")[0].text.replace("-"," ").replace("*","").strip().split(" "))
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
                return min(int(i[9:]),9999999)
       
        # If we get here, the odometer wasn't specified. Look in body / title
        # Title of ad :

        haystacks = [bsc.select(".postingtitletext")[0].text, bsc.find(id="postingbody").text]

        for haystack in haystacks:
            hsk = haystack.replace("\n"," ").strip().lower()
            hsk = re.sub(r"[*-\.:\[\]]","",hsk)
            mtch = re.search(r"([1-9]\d*k|\d+(?:,\d+)?)[ ]*(?:original|actual|low){0,2}[ ]*miles",hsk)
            if mtch:
                val = mtch.group(1)
                if val[-1] == 'k':
                    val = val[:-1] + "000"
                val = val.replace(",","")
                return min(int(val),9999999)
                
        return None


    @staticmethod
    def get_year(bsc):
        try:
            return int([attr.text for attr in bsc.select(".attrgroup span")][0][:4])
        except:
            pass
        
        # The hard way : look for a number between 1970 and this year
        max_year = datetime.datetime.now().year
        ys = [str(i) for i in range(1970,max_year+1)]
        ys.extend([str(i)[-2:] for i in range(1970,max_year+1)])
        filt = re.compile(" (" + '|'.join(ys) + ")[']? ")

        haystacks = [bsc.select(".postingtitletext")[0].text, bsc.find(id="postingbody").text]

        for haystack in haystacks:
            hsk = haystack.replace("\n"," ").strip().lower()
            hsk = re.sub(r"[*-\.\[\]]","",hsk)
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
            return int(bsc.select(".price")[0].text.replace("$",""))
        except:
            pass
        
        # The hard way
        filt = re.compile("\$[ ]*([1-9]\d*k|\d+(?:,\d+)?)")
        haystacks = [bsc.select(".postingtitletext")[0].text, bsc.find(id="postingbody").text]

        for haystack in haystacks:
            hsk = haystack.replace("\n"," ").strip().lower()
            hsk = re.sub(r"[*-\[\]]","",hsk)
            mtch = filt.search(hsk)
            if mtch:
                val = mtch.group(1)
                if val[-1] == 'k':
                    val = val[:-1] + "000"
                val = val.replace(",","")
                return int(val)
                
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

    
    @staticmethod
    def sql_format(ads):
        text_fields = ['title', 'make', 'condition', 'color', 'vin', 'type', 'url', 'car_title', 'puid', "model", 'trim', 'series']
        number_fields = ['mileage', 'price']
        date_fields = ["post_date", "update"]
        data = []
        for ad in ads:
            data_point = {}
            data_point.update({key: str_or_null(ad[key]) for key in number_fields})
            data_point.update({key: "'" + str_or_null(ad[key]) + "'" for key in text_fields})
            data_point.update({key: "'" + str_or_null(ad[key]) + "'" for key in date_fields})
            data_point["year"] = "null"
            data_point["geo"] = "null"
            if "year" in ad and ad["year"] is not None:
                data_point["year"] = "'" + str(datetime.datetime.strptime(str(ad['year'])+"-01-02T00:00:00-0000", '%Y-%m-%dT%H:%M:%S%z')) + "'"
            if 'geo' in ad and ad["geo"] is not None:
                data_point["geo"] = "'POINT(" + str(ad["geo"]["latitude"]) + " " + str(ad["geo"]["longitude"]) + ")'"
            data.append(data_point)
        return data
            
       
def geo_distance(geo1, geo2):
    """Returns the distance bewteen two points on the globe"""
    lo1 = geo1["longitude"] * math.pi / 180
    lo2 = geo2["longitude"] * math.pi / 180
    la1 = geo1["latitude"] * math.pi / 180
    la2 = geo2["latitude"] * math.pi / 180

    if not (la1 and la2 and lo1 and lo2):
        return None

    a = math.sin((la2 - la1) / 2)**2 + \
        math.cos(la1) * math.cos(la2) * \
        math.sin((lo2 - lo1) / 2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    R = 6371000
    return R*c

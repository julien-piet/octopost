""" Get different models and styles from KBB """

import requests
from bs4 import BeautifulSoup
import datetime
import re

def load_all_kbb():
    """ Does what you think it does"""

    api_url = "https://www.kbb.com/vehicleapp/api/"   
    model_list = {}
    
    sess = requests.Session() 
    headers = {"accept":"*/*","accept-language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7","content-type":"application/json","mocks":"undefined","sec-fetch-mode":"cors","sec-fetch-site":"same-origin"}
    
    max_year = datetime.datetime.now().year
    for year in range(1992,max_year+1):
        body = "{\"operationName\":\"MAKES_QUERY\",\"variables\":{\"vehicleClass\":\"usedcar\",\"vehicleType\":\"used\",\"year\":\"" + str(year) + "\"},\"extensions\":{\"persistedQuery\":{\"version\":1,\"sha256Hash\":\"5e9f49f68dfa81f9251ddd7a1a958bebb65ea982a34b7860cf47f47043f1901f\"}}}"
        makes = sess.post(api_url, data=body, headers=headers).json()["data"]["makes"]
        for make in makes:
            make_n = make["name"]
            body = '{\"operationName\":\"MODELS_QUERY\",\"variables\":{\"vehicleClass\":\"usedcar\",\"vehicleType\":\"used\",\"year\":\"' + str(year) + '\",\"make\":\"' + str(make['id']) + '\"},\"extensions\":{\"persistedQuery\":{\"version\":1,\"sha256Hash\":\"2e7f89c39a5e92eecfe7c82bc4fb797c718952bb33b070be36d6d9be68eab163\"}}}'
            models = sess.post(api_url, data=body, headers=headers).json()["data"]["models"]
            for model in models:
                model_n = model["name"]
                print(" ".join([str(year), make_n, model_n]))
                body = '{\"operationName\":\"ROUTE_QUERY\",\
                        \"variables\":{\"microservice\":\"trident\",\"path\":\"KBB.Trident.Web.Areas.Vehicle_PathStyles\",\
                        \"params\":{\"manufacturername\":\"' + make_n + '\",\"modelname\":\"' + model_n + '\",\"yearid\":\"' + str(year) + '\",\
                        \"pricetype\":\"retail\",\"action\":\"styles\",\"intent\":\"buy-used\"}},\
                        \"extensions\":{\"persistedQuery\":{\"version\":1,\"sha256Hash\":\"1f0e112b92f53ee8172dfbadbfd81c4dfde33830164afd46694b9c1db7ef9822\"}}}'
                models_url = sess.post(api_url, data=body, headers=headers).json()["data"]["getRoute"]["url"]
                req = sess.get("https://www.kbb.com" + models_url)
                page = BeautifulSoup(req.text, features="html.parser")
                styles = [style.text for set_of_styles in page.select("#stylesSection > div")[1:] for style in set_of_styles.findChildren('div',recursive=False)[1:]]
                styles = [re.sub(r' +',' ',style.replace("(Lowest-priced)","").replace("\n"," ").replace("\t"," ")).strip() for style in styles]
                if make_n not in model_list:
                    model_list[make_n] = {}
                if year not in model_list[make_n]:
                    model_list[make_n][year] = {}
                model_list[make_n][year][model_n] = styles

    return model_list
                    


def load_all_hagerty():
    """Same but different website"""
    
    model_list = {}
    sess = requests.Session()
    
    years = [item.text for item in BeautifulSoup(sess.get("https://www.hagerty.com/apps/valuationtools/search/Auto?by=year").text,features="html.parser").select(".grid-list a")]
    for year in years:
        makes = [[item.text, item["href"]] for item in BeautifulSoup(sess.get("https://www.hagerty.com/apps/valuationtools/search/Auto/"+year).text,features="html.parser").select(".grid-list a")]
        for make in makes:
            make_n = make[0]
            print(" ".join([year, make_n]))
            models = [item.text for item in BeautifulSoup(sess.get("https://www.hagerty.com" + make[1]).text,features="html.parser").select(".grid-list a")]
            print(models)
            if make_n not in model_list:
                model_list[make_n] = {}
            if year not in model_list[make_n]:
                model_list[make_n][year] = {}             
            model_list[make_n][year] = models
            
            
                
print(load_all_kbb())


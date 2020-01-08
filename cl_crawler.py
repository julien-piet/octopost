import pprint
import requests 
from bs4 import BeautifulSoup
import time 
import random
import math 
import threading
import queue
from static_data import *
from cl_parsing import *
from database_connection import *
from vin_decoding import *
import difflib

class BreakLoop(Exception): pass

class FIFO():
    """Concurrent fifo class"""
    def __init__(self, maxsize=0, chunksize=0):
        self.list = queue.Queue(maxsize) 
        self.chunksize = chunksize

    def put(self, item):
        self.list.put(item)

    def pop(self):
        if not self.chunksize:
            item = self.list.get()
            return item
        else:
            item = [self.list.get() for i in range(self.chunksize)]
            return item


def req(sock, url, data):
    try:
        rq = sock.get(url)
        return rq.text
    except Exception as e:
        data.errors.append(e)
        print("Error occured : " + str(e))
        time.sleep(60)
        return None


def feeder(data):
    """Fills queue with new links"""

    print("Starting feeder")
    cl_adapter = requests.adapters.HTTPAdapter(max_retries=2)
    session = requests.Session()
    session.mount("http://",cl_adapter)
    session.mount("https://",cl_adapter)

    while True:
        start_time = time.time()
        for site in data.places:
            try:
                local_seen = {}
                for loop in range(0,26):
                    sr = req(session, site + "search/cta?s=" + str(loop*120) + "&sort=date&bundleDuplicates=1", data)
                    if not sr:
                        continue
                    sr = BeautifulSoup(sr, features="html.parser")
                    ads = sr.select(".content .rows li  .gallery")

                    if not len(ads):
                        data.seen.update(local_seen)
                        raise BreakLoop()

                    for ad in ads:
                        if ad["href"].find(site) == -1:
                            pass
                        elif ad["href"] in data.seen:
                            print("Got to previously seen posts")
                            data.seen.update(local_seen)
                            raise BreakLoop()
                        elif not ad["href"] in local_seen:
                            local_seen[ad["href"]] = True
                            data.queue.put({"url": ad["href"], "handler": cl_details})
            except BreakLoop:
                pass
        end_time = time.time()
        time.sleep(max(0, 3600 - (end_time-start_time)))


def handler(data):
    """Function that pops items and handles the job"""

    print("Starting handler")
    cl_adapter = requests.adapters.HTTPAdapter(max_retries=2)
    session = requests.Session()
    session.mount("http://",cl_adapter)
    session.mount("https://",cl_adapter)

    while True:
        job = data.queue.pop()
        job["handler"](job["url"], data, session)


def parser(data):
    """Function that pops items and handles the job"""
    print("Starting parser")
    while True:
        #        try:
        job = data.to_be_parsed.pop()
        job["handler"](job["data"], data)
#        except Exception as e:
#            data.errors.append(e)
#            print("Error occured in parser : " + str(e))
#            pass

def sql_updater(data):
    """Function that updates the database"""
    print("Starting updater")
    while True:
        try:
            jobs = data.update_queue.pop()
            jobs[0]["handler"]([job["data"] for job in jobs], data)
        except Exception as e:
            data.errors.append(e)
            print("Error occured in updater : " + str(e))
            pass
            
class crawl_data():

    def __init__(self, db):
        """Initialize global variables"""
        self.queue = FIFO(25000)
        self.places = crawl_data.load_places()
        self.to_be_parsed = FIFO(25000)
        self.errors = []
        self.incompatible = 0
        self.loaded = 0
        self.db = database_connection()
        self.update_queue = FIFO(25000,250)
        self.seen = {url[0]: True for url in self.db.query("SELECT DISTINCT url FROM ads")}
        self.vins = vin_decoder(self.db)

    def load_places():
        ct = BeautifulSoup(requests.get("https://www.craigslist.org/about/sites#US").text, features="html.parser")
        return [a["href"] for a in ct.select(".colmask")[0].select("a")]



def cl_details(href, data, sock):
    """Specific handler for Craigslist pages"""
    sr = req(sock, href, data)
    if not sr:
        return
    data.to_be_parsed.put({'data': {'url': href, 'content': BeautifulSoup(sr, features="html.parser")}, "handler": cl_parser})
    

def cl_parser(page, data):
    """Parser for Craigslist pages"""
    sr = page["content"]
    ad = cl_extractor.extract(sr, page["url"], data)
    if not ad:
        return

    if ad["make"] is None:
        data.incompatible += 1
    else:
        data.loaded += 1
        data.update_queue.put({'data': ad, 'handler': cl_updater})


def cl_updater(item, data):
    """Updates the database"""
    raw_data = cl_extractor.sql_format(item)
    data.db.write("ads", raw_data)


def monitor(data):
    """Thread to monitor queue and seen"""
    start = time.time()
    while True:
        print("T" + str(math.floor(time.time() - start)) + " / Q : " + str(data.queue.list.qsize()) + " / S : " + str(len(data.seen)) + " / P : " + str(data.to_be_parsed.list.qsize()) + " / E : " + str(len(data.errors)) + " / I : " + str(data.incompatible) + " / U : " + str(data.update_queue.list.qsize()) + " / L : " + str(data.loaded))
        time.sleep(60)


def master(feeder_count=1, handler_count=2, parser_count=2, updater_count=1):
    """Master of all threads"""
    data = crawl_data(None)

    f = []
    h = []
    p = []
    u = []

    for i in range(feeder_count):
        f.append(threading.Thread(target=feeder, args=(data,)))
  
    for i in range(handler_count):
        h.append(threading.Thread(target=handler, args=(data,)))

    for i in range(parser_count):
        h.append(threading.Thread(target=parser, args=(data,)))

    for i in range(updater_count):
        u.append(threading.Thread(target=sql_updater, args=(data,)))

    for th in f:
        th.start()
    for th in h:
        th.start()
    for th in p:
        th.start()
    for th in u:
        th.start()

    monitor(data)


master()

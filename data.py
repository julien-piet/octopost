""" Data structures """

import queue
from database_connection import *
from bs4 import BeautifulSoup
import requests
from lookup import refresh_model_db
import time


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
            items = []
            for i in range(self.chunksize):
                item = self.list.get()
                if item == "STOP":
                    items.append("STOP")
                    return items
                items.append(item)
            return items


class crawl_data():

    def __init__(self, feeders, fetchers, parsers):
        """Initialize global variables"""
        self.feed_queue = FIFO(500)
        self.fetch_queue = FIFO(500)
        self.parse_queue = FIFO(500)
        self.lookup_queue = FIFO(500, 25)
        self.update_queue = FIFO(500, 25)

        self.places = crawl_data.load_places()
        self.errors = []
        self.incompatible = []
        self.loaded = 0
        self.db = database_connection()

        self.log = []
        self.models = {}
        self.seen = {url[0]: True for url in self.db.query("SELECT DISTINCT url FROM ads")}
        self.vins = {vin[0]: True for vin in self.db.query("SELECT DISTINCT vin FROM vins")}

        refresh_model_db(self)
        self.start_time = time.time()
        self.stop = False
        self.th_count={'feeder': feeders, 'fetch': fetchers, 'parse': parsers}

    @staticmethod
    def load_places():
        ct = BeautifulSoup(requests.get("https://www.craigslist.org/about/sites#US").text, features="html.parser")
        return [a["href"] for a in ct.select(".colmask")[0].select("a")]

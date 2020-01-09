""" Data structures """

import queue
from database_connection import *
from bs4 import BeautifulSoup
import requests


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


class crawl_data():

    def __init__(self):
        """Initialize global variables"""
        self.feed_queue = FIFO(15000)
        self.fetch_queue = FIFO(15000)
        self.parse_queue = FIFO(15000)
        self.lookup_queue = FIFO(15000)
        self.update_queue = FIFO(15000, 25)

        self.places = crawl_data.load_places()
        self.errors = []
        self.incompatible = 0
        self.loaded = 0
        self.db = database_connection()

        self.log = []
        self.seen = {url[0]: True for url in self.db.query("SELECT DISTINCT url FROM ads")}
        self.vins = {vin[0]: True for vin in self.db.query("SELECT DISTINCT vin FROM vins")}

    @staticmethod
    def load_places():
        ct = BeautifulSoup(requests.get("https://www.craigslist.org/about/sites#US").text, features="html.parser")
        return [a["href"] for a in ct.select(".colmask")[0].select("a")]

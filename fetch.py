""" Fetch.py - load a craigslist ad """

from parse import *
from bs4 import BeautifulSoup

def fetch(data, conn, url):
    """Specific handler for Craigslist pages"""
    content = conn.get(url)
    parsed_content = BeautifulSoup(content, features="html.parser")
    data.parse_queue.put(lambda x, y, url=url, parsed_content=parsed_content: parse(x, url, parsed_content))

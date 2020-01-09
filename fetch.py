""" Fetch.py - load a craigslist ad """

from parse import *


def fetch(data, conn, url):
    """Specific handler for Craigslist pages"""
    content = conn.get(url)
    parsed_content = BeautifulSoup(content, features="html.parser")
    data.parse_queue.put(lambda x, y: parse(x, url, parsed_content))

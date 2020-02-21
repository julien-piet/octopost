""" Fetch.py - load a craigslist ad """

from bs4 import BeautifulSoup

def fetch(data, conn, url, prev_content=None):
    """Specific handler for Craigslist pages"""
    content = conn.get(url)
    parsed_content = BeautifulSoup(content, features="html.parser")
    data.parse_queue.put(lambda x, y, url=url, parsed_content=parsed_content, prev_content=prev_content: dest(x, url, parsed_content, prev_content))

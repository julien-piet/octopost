"""Feeder.py - fetch fresh urls"""

from fetch import *
from bs4 import BeautifulSoup
from aux import *


class BreakLoop(Exception): pass


def feeder(data, conn):
    """Fills fetch queue with new links"""

    for site in data.places:

        posts = []
        seen = {}
        try:
            number_of_seen = 0
            for loop in range(0,26):
                content = conn.get(site + "search/cta?s=" + str(loop*120) + "&sort=date&bundleDuplicates=1")
                if not content: break
                parsed_content = BeautifulSoup(content, features="html.parser")
                ads = parsed_content.select(".content .rows li  .gallery")

                if not len(ads):
                    raise BreakLoop()

                for ad in ads:
                    # If this ad belongs to another craigslist page, pass
                    if ad["href"].find(site) == -1:
                        pass

                    # If this ad has already been seen in a previous iteration, stop
                    elif ad["href"] in data.seen:
                        number_of_seen += 1
                        if number_of_seen > 10:
                            raise BreakLoop()

                    # if this ad hasn't been seen yet in this iteration, add
                    elif not ad["href"] in seen:
                        seen[ad["href"]] = True
                        posts.append(ad["href"])

        except BreakLoop:
            pass

        # Update global variables. Put new posts from oldest to newest, to avoid gaps.
        for url in reversed(posts):
            data.fetch_queue.put(lambda x, y, url=url: fetch(x, y, url))
        data.seen.update(seen)

        data.log.append("{} new posts from {}".format(len(posts), site))

        if data.stop:
            stop_function(data)

    data.feed_queue.put(lambda x, y: feeder(x, y))


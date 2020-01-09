"""Feeder.py - fetch fresh urls"""

import time
from fetch import *

class BreakLoop(Exception): pass


def feeder(data, conn):
    """Fills fetch queue with new links"""

    start_time = time.time()

    for site in data.places:

        posts = []
        seen = {}
        try:
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
                        raise BreakLoop()

                    # if this ad hasn't been seen yet in this iteration, add
                    elif not ad["href"] in seen:
                        seen[ad["href"]] = True
                        posts.append(ad["href"])

        except BreakLoop:
            pass

        # Update global variables. Put new posts from oldest to newest, to avoid gaps.
        for i in range(0, len(posts), -1):
            data.fetch_queue.put(lambda x, y: fetch(x, y, posts[i]))
        data.seen.update(seen)

    data.feed_queue.put(lambda x, y: feeder(x, y))

    end_time = time.time()
    time.sleep(max(0, 3600 - (end_time - start_time)))


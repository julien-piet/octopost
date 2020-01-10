""" Main code for crawler """

import time
import threading
import math

from session import *
from data import *
from update import update
from feeder import *
from lookup import lookup
from interact import interact


def handler(data, job_queue, name, need_session=False):
    """Function that pops items and handles the job"""

    data.log.append("Starting {}".format(name))
    if need_session:
        conn = session(data)
    else:
        conn = None

    while True:
        try:
            job = job_queue.pop()
            job(data, conn)
        except Exception as e:
            data.errors.append(e)
            data.log.append("Error occurred while {} was working on a job : {}".format(name, str(e)))
            pass


def master(feeder_count=1, fetch_count=3, parse_count=3, update_count=1, lookup_count=1):
    """Master of all threads"""

    data = crawl_data()
    ths = []

    for i in range(feeder_count):
        ths.append(threading.Thread(name="Feeder {}".format(i+1), target=handler, args=(data, data.feed_queue, "Feeder {}".format(i+1), True,)))
  
    for i in range(fetch_count):
        ths.append(threading.Thread(name="Fetcher {}".format(i+1), target=handler, args=(data, data.fetch_queue, "Fetcher {}".format(i+1), True,)))

    for i in range(parse_count):
        ths.append(threading.Thread(name="Parser {}".format(i+1), target=handler, args=(data, data.parse_queue, "Parser {}".format(i+1), False,)))

    for i in range(update_count):
        ths.append(threading.Thread(target=update, args=(data, )))

    for i in range(lookup_count):
        ths.append(threading.Thread(name="Lookup {}".format(i+1), target=lookup, args=(data, )))

    for th in ths:
        th.start()

    # Give first job

    data.feed_queue.put(lambda x, y: feeder(x, y))
    interact(data)


master()

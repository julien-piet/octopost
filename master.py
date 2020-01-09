""" Main code for crawler """

import time
import threading
import math

from session import *
from data import *
from update import update
from feeder import *


def handler(data, job_queue, name, need_session=False):
    """Function that pops items and handles the job"""

    print("Starting {}".format(name))
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
            print("Error occurred while {} was working on a job : {}".format(name, str(e)))
            pass


def monitor(data):
    """Thread to monitor queue and seen"""
    start = time.time()
    while True:
        print("T" + str(math.floor(time.time() - start)) + \
              " / F : " + str(data.fetch_queue.list.qsize()) + \
              " / P : " + str(data.parse_queue.list.qsize()) + \
              " / U : " + str(data.update_queue.list.qsize()) + \
              " / L : " + str(data.lookup_queue.list.qsize()) + \
              " / S : " + str(len(data.seen)) + \
              " / E : " + str(len(data.errors)) + \
              " / I : " + str(data.incompatible) + \
              " / A : " + str(data.loaded))
        time.sleep(60)


def master(feeder_count=1, fetch_count=3, parse_count=2, update_count=1, lookup_count=2):
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
        ths.append(threading.Thread(name="Lookup {}".format(i+1), target=handler, args=(data, data.lookup_queue, "Lookup {}".format(i+1), True,)))

    for th in ths:
        th.start()

    # Give first job

    data.feed_queue.put(lambda x, y: feeder(x, y))
    monitor(data)


master()

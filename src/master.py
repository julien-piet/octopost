""" Main code for crawler """

import time
import threading
import math

from code.session import *
from code.data import *
from code.update import update
from code.feeder import *
from code.lookup import lookup
from code.interact import interact


def handler(data, job_queue, name, need_session=False, rate_limit=None):
    """Function that pops items and handles the job"""

    start_time = time.time()

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
        if rate_limit:
            end_time = time.time()
            time.sleep(max(0, rate_limit - (end_time - start_time)))


def master(feeder_count=1, fetch_count=3, parse_count=3, update_count=1, lookup_count=1):
    """Master of all threads"""

    data = crawl_data(feeder_count, fetch_count, parse_count)
    ths = []

    for i in range(feeder_count):
        ths.append(threading.Thread(name="Feeder {}".format(i+1), target=handler, args=(data, data.feed_queue, "Feeder {}".format(i+1), True, 3600)))
  
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

#    vins = [{"vin": item[0], "year": str(math.floor(float(item[1])))} for item in data.db.query("select vin, max(extract(year from year)) from ads where model is null and substr(vin,1,9) not in (select vin from vins) group by vin;")]
#    for vin in vins:
#        data.lookup_queue.put(vin)

    interact(data, ths)


master()

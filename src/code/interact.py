""" Interact - An interactive master thread for querying progess"""
import re
import time
import math
from .aux import duplicate_database
from .database_connection import *


def interact(data, ths):
    """ Code for interact module """

    conn = database_connection()

    help_string = """Help menu - you can use the following commands :
    status --------------------------------- get the advancement stats of the crawler
    dump (errors|inconsistent|log) --------- empty the content of the error buffer, the inconsistent buffer, or the logs
    write (errors|inconsistent|log) file --- write the content of the selected buffer to file
    echo (errors|inconsistent|log) [N=5] --- print the N last entries of the selected buffer
    exit ----------------------------------- exits the program gracefully, after emptying the buffers
    stats ---------------------------------- get advancement stats
    force-update --------------------------- update web database
    help ----------------------------------- show this menu"""

    match_regex = re.compile("(?P<status>status)|(?P<forceupdate>force-update)|(?P<exit>exit)|(?P<stats>stats)|(?P<help>(?:help|h))|(?:(?P<dump>dump)|(?P<write>write)|(?P<echo>echo)) (?P<buffer>errors|debug|inconsistent|log)(?: (?P<param>.*))?")

    while True:
        command = input('octopost : ')
        mtch = match_regex.search(command)
        if not mtch:
            print("Unrecognized command. Please type 'help' to display options")
            continue


        if mtch.group("status"):
            status(data)
            continue

        if mtch.group("help"):
            print(help_string + '\n')
            continue

        if mtch.group("stats"):
            stats(data)
            continue

        if mtch.group("forceupdate"):
            duplicate_database(conn)
            continue

        if mtch.group("exit"):
            exit_gracefully(data, ths)
            continue

        if mtch.group("dump") and mtch.group("buffer"):
            dump(data, mtch.group("buffer"))
            continue

        if mtch.group("write") and mtch.group("buffer") and mtch.group("param"):
            write_to_file(data, mtch.group("buffer"), mtch.group("param"))
            continue

        if mtch.group("echo") and mtch.group("buffer"):
            echo_to_console(data, mtch.group("buffer"), mtch.group("param"))
            continue

        print("Unrecognized command. Please type 'help' to display options")


def status(data):
    """Print the status of the crawler"""

    make_count  = len(data.models.keys())
    model_count = sum(len(data.models[make]["model_to_trim"].keys()) for make in data.models)

    elapsed = math.floor(time.time() - data.start_time)
    hours, minutes, seconds = elapsed // 3600, (elapsed%3600) // 60, elapsed%60

    if minutes < 10:
        minutes = "0" + str(minutes)
    
    if seconds < 10:
        seconds = "0" + str(seconds)

    print("Elapsed : {}:{}:{}".format(hours,minutes,seconds) + \
          "\n * Fetch queue size       : " + str(data.fetch_queue.list.qsize()) + \
          "\n * Parse queue size       : " + str(data.parse_queue.list.qsize()) + \
          "\n * Update queue size      : " + str(data.update_queue.list.qsize()) + \
          "\n * Vin lookup queue size  : " + str(data.lookup_queue.list.qsize()) + \
          "\n\n * Number of seen urls    : " + str(len(data.seen)) + \
          "\n * Number of makes        : " + str(make_count) + \
          "\n * Number of models       : " + str(model_count) + \
          "\n * Number of errors       : " + str(len(data.errors)) + \
          "\n * Number of unparsed ads : " + str(len(data.incompatible)) + \
          "\n * Number of written ads  : " + str(data.loaded) + "\n")


def stats(data):
    """Print stats"""

    try:
        error_ratio = len(data.errors) / data.loaded
        unparsed_ratio = len(data.incompatible) / data.loaded
        average_speed = math.floor(60 * data.loaded / (time.time() - data.start_time))

        print("""Stats :
                * Error ratio          : {}%
                * Unparsed ratio       : {}%
                * Ads saved per minute : {}\n""".format('%.3f'%(100*error_ratio), '%.3f'%(100*unparsed_ratio), average_speed))
    except Exception:
        print("Not enough data yet. Try again soon\n")


    
def select_buffer(data, buf):
    """ Return appropriate object """
    if buf == "errors":
        return data.errors

    if buf == "inconsistent":
        return data.incompatible

    if buf == "log":
        return data.log

    if buf == "debug":
        return data.debug

    return None



def dump(data, buf):
    """ Empty out buffer """
    if buf == "errors":
        data.errors = []
    elif buf == "inconsistent":
        data.incompatible = []
    elif buf == "log":
        data.log = []
    elif buf == "debug":
        data.debug = []

    print("Buffer emptied \n")



def write_to_file(data,buf,filename):
    """ write content of buffer to file """
    with open(filename, 'w') as outfile:
        outfile.write('\n'.join(select_buffer(data, buf)))
    print("Succesfully written to file \n")


def echo_to_console(data,buf,count):
    """ Write some of the buffer to console """
    try:
        count = int(count)
    except Exception as e:
        count = 5

    buf = select_buffer(data, buf)
    count = min(len(buf), count)

    for i in reversed(range(count)):
        print(buf[len(buf)-1-i])
    print("\n")


def exit_gracefully(data, ths):
    """ exit gracefully """

    if data.stop:
        print("Buffers are still emptying, exit procedure has started")
        return

    # Set stop flag to true :
    data.stop = True

    # Join other processes
    for th in ths:
        th.join()

    # Write debug to file
    # write_to_file(data, "debug", "debug.txt")

    # Exit
    exit(0)

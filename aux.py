"""Auxiliary functions"""
import re
from static_data import *


def build_model_regex_from_list(names, make=None):
    """ Builds search regex """
    if make in reverse_makes:
        blacklist = reverse_makes[make]
    else:
        blacklist = []
    items = [re.escape(item) for item in names if item not in blacklist]
    items.sort(key=len, reverse=True)
    return re.compile("(?:^| )(" + "|".join(items) + ")(?:$|[0-9,\.;\* ])")


def norm(model):
    """ Removes any extra whitespace, or characters not essential to the model name """
    # TODO : Implement once the database is large enough
    if isinstance(model, str):
        model = model.replace("-","").lower()
        model = re.sub(r"[ ]{2,}"," ",model)
        model = model.strip()
    return model


def vin_check(vin):
    """ Verify the checksum """
    translit = \
            {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,\
             'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5,         'P': 7, 'R': 9,\
                     'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,\
                     '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '0': 0}
    weights = [8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2]
    try:
        total = sum(translit[vin[i]]*weights[i] for i in range(17))
        check_num = total % 11
        if 0 <= check_num <= 9:
            check = str(check_num)
        else:
            check = 'X'
        if check == vin[8]:
            return True
        else:
            return False
    except Exception:
        return False


def stop_function(data):
    """ Stops the program. To be run by a fetcher """

    def end_func(d):
        # To be run last
        print("Stop signal received by parser")
        d.update_queue.put("STOP")
        d.lookup_queue.put("STOP")
        exit(0)

    def inter_func(d):
        # To be run last by fetch
        print("Stop signal received by fetcher")
        for i in range(data.th_count['parse']):
            d.parse_queue.put(lambda x, y: end_func(x))
        exit(0)

    print("Stop signal received by feeder")
    for i in range(data.th_count['fetch']):
        data.fetch_queue.put(lambda x, y: inter_func(x))
    exit(0)

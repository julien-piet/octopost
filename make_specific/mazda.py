""" Mazda-specific tools """
import re


def get_model(text):
    """ Returns the model found in the text """
    f1 = re.compile("(?:^| )mazda(?:speed)? ?(2|3|6)(?:$|[ ,\.])")
    f2 = re.compile("(?:^| )(mx|rx|cx) ?(30|3|4|5|6|7|8|9)(?:$|[ ,\.])")

    mtch = f1.search(text)
    if mtch:
        return {"model": "mazda{}".format(mtch.group(1)), "trim": None, "series": None}

    mtch = f2.search(text)
    if mtch:
        return {"model": mtch.group(1) + mtch.group(2), 'trim': None, 'series': None}

    # If nothing was found, return none so that the parser goes to default search mode
    return None


"""Auxiliary functions"""

def str_or_null(item):
    """Return the str value or "null" """
    if item == None:
        return "null"
    else:
        return str(item).translate(str.maketrans({"'": '"'}))

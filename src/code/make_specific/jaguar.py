""" Jaguar-specific tools """
import re


def get_model(text):
    """ Returns the model found in the text """
    f1 = re.compile("(?:^| )(type ?e)|(e ?type)|(xk ?e)(?:$|[ ,\.])")

    mtch = f1.search(text)
    if mtch:
        return {"model": "xke", "trim": None, "series": "etype"}

    # If nothing was found, return none so that the parser goes to default search mode
    return None


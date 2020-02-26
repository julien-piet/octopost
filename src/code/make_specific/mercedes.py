""" Mercedes-specific tools """
import re


def get_model(text):
    """ Returns the model found in the text """
    f1 = re.compile("(?:^| )([1-9][0-9]0?)[ ]?(eqc|gla|glb|glc|gle|glk|gls|cla|cls|clk|slc|sel|sec|slk|sls|gl|ml|sl|cl|ce|a|b|c|e|g|s|r|m)(?:$| )")
    f2 = re.compile("(?:^| )(eqc|gla|glb|glc|gle|glk|gls|cla|cls|clk|slc|sel|sec|slk|sls|gl|ml|sl|cl|ce|a|b|c|e|g|s|r|m)[ ]?([1-9][0-9]0?)(?:$| )")
    f3 = re.compile("(?:^| )(eqc|gla|glb|glc|gle|glk|gls|cla|cls|clk|slc|sel|sec|slk|sls|gl|ml|sl|cl|ce|a|b|c|e|g|s|r|m)(?:$| )")

    model  = None
    trim   = None
    series = None

    mtch = f1.search(text)
    if mtch:
        vol = mtch.group(1)
        abbr = mtch.group(2)
        if abbr == "sec":
            abbr = "cl"
        elif abbr == "sel": 
            abbr = "s"
        model = abbr + "class"
        series = abbr + vol 
        result = {"model": model, "trim": trim, "series": series}
        return result

    mtch = f2.search(text)
    if mtch:
        vol = mtch.group(2)
        abbr = mtch.group(1)
        if abbr == "sec":
            abbr = "cl"
        elif abbr == "sel": 
            abbr = "s"
        model = abbr + "class"
        series = abbr + vol 
        result = {"model": model, "trim": trim, "series": series}
        return result

    mtch = f3.search(text)
    if mtch:
        abbr = mtch.group(1)
        if abbr == "sec":
            abbr = "cl"
        elif abbr == "sel": 
            abbr = "s"
        model = abbr + "class"
        result = {"model": model, "trim": trim, "series": series}
        return result

    # If nothing was found, return none so that the parser goes to default search mode
    return None


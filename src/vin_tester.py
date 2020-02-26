from code.aux import *
import sys

try:
    vin = sys.argv[1]
    print("VIN {} is {}".format(vin, "valid" if vin_check(vin) else "invalid"))
except Exception as e:
    print("Invalid command line")



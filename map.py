""" Query results for map display """
from database_connection import *
from math import *


def grid_aggr(params):
    """ Grid """

    corners = {"minlat": 23.4, "maxlat": 52, "minlon": -126, "maxlon": -62}
    side = 1
    sql = """
    SELECT
    avg(price) as price, avg(mileage) as mileage, count(*) as cnt, percentile_disc(0.5) WITHIN GROUP (ORDER BY x) x,
    percentile_disc(0.5) WITHIN GROUP (ORDER BY y) y
    FROM (
    SELECT 
    price, mileage, ST_X(geo::geometry) as x, ST_Y(geo::geometry) as y, round(ST_X(geo::geometry) / {0}) * {0} AS x_round, round(ST_Y(geo::geometry) / {0}) * {0} AS y_round
    FROM
    (
    SELECT row_number() over (partition by puid order by post_date desc) as ln, * from (
    SELECT * from ads where post_date > CURRENT_TIMESTAMP - INTERVAL '30 days') as a
    ) as b WHERE ln = 1 ) as c group by x_round, y_round;
    """.format(side)



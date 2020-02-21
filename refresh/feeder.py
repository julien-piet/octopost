""" Schedule posts for refresh ever 7 days (7-14-21) """

from ..fetch import *
from ..database_connection import *
from ..update import sqlize

def feeder(data, limit=25000):

    sql = """Select make, 
                    model, 
                    trim, 
                    series, 
                    mileage, 
                    price, 
                    ST_AsText(geo) as geo, 
                    url,
                    year,
                    vin,
                    refresh_for,
                    puid
                FROM ads as a
                INNER JOIN 
                (
                    SELECT  url,
                            max(update) as latest,
                            min(update) as first,
                            max(cast(expired AS int)) as expired_or
                    FROM ads
                    GROUP BY url
                ) as b
                ON a.url = b.url AND a.update = b.latest
                WHERE  
                    b.latest < current_timestamp - interval "7 days" 
                    and b.expired_or != 1 
                    and b.first > current_timestamp - interval "27 days"
                LIMIT {};""".format(limit)

    sql = """SELECT make, 
                    model, 
                    trim, 
                    series, 
                    mileage, 
                    price, 
                    ST_AsText(geo) as geo, 
                    url,
                    year,
                    vin,
                    refresh_for,
                    puid
                FROM (   
                    SELECT  *, 
                            row_number() over (partition by url order by update desc) as ln
                    FROM ads as a
                    INNER JOIN 
                    (
                        SELECT  url
                        FROM refresh
                        WHERE expired is false and last_fetch < current_timestamp - interval "8 days"
                    ) as b
                    ON a.url = b.url
                ) as r
                WHERE r.ln = 1
                LIMIT {};""".format(limit)

    db = database_connection()
    scheduled = sqlize(db.query_smart(sql), reverse=True)
    for s in scheduled:
        url = s["url"]
        data.refresh.put(lambda x, y, url=url, cnt=s: fetch(x, y, url, cnt))



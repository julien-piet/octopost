# Octopost
*A Multithreaded used car posting crawler*

Octopost is a web crawler designed to
  * Retrieve all used car ads on every Craigslist site
  * Parse the ad to find features such as make, model, price, mileage, and many more
  * Save useful features in a centralized database
  
 Octopost is most useful when used with its companion webapp https://github.com/julien-piet/car_analytics
 
## Design

Octopost makes use of the Threading API in python to make use of down time during a request.
It has a parallel queue architecture to pipeline the loading process. Furthermore, Octopost uses the NHTSA API at https://vpic.nhtsa.dot.gov/api/ to get detailed information on specific models to complete the data pulled from craigslist


## Usage

Run `python master.py`

Once the interpreter starts, type `help` to see your options


## Setup

To install on your local machine :

1. Setup python virtual env
`virtualenv -p python3 venv`

2. Install pip dependencies 
`pip install -r requirements.txt`

3. Install postgresql from https://www.postgresql.org/download/

4. Install postGIS from https://postgis.net

5. Create database 
`create_db [database_name]`

6. Activate postGIS in that database by running `CREATE EXTENSION postgis;` after you connect with `psql [database_name]`

7. Unzip database dump
`tar xvf db_dump.tar`

8. Install database
`pg_restore -d [database_name] db_dump_file`

9. Update database.ini with your database credentials

10. Run 
`python master.py`


## Disclaimer

This software under the GPL3 license, check the license file for more info. It is in no means intended to be used in a professional setting. It might (and probably does) have bugs. Use with care. 

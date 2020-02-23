# Octopost

### Multithreaded used car posting crawler


### Setup

To install on your local machine :

1. Setup python virtual env
`virtualenv -p python3 venv`

2. Install pip dependencies 
`pip install -r requirements.txt`

3. Install postgresql from https://www.postgresql.org/download/

4. Install postGIS from https://postgis.net

5. Unzip database dump
`tar xvf db_dump.tar`

6. Install database
`createdb cars && pg_restore -d cars db_dump_file`

7. Update database.ini with your database credentials

8. Run 
`python master.py`

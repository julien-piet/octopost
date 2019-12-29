""" Manage postgresql database connection """
from configparser import ConfigParser
import psycopg2
import datetime


class database_connection():

    @staticmethod
    def config(filename='database.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(filename)

        params = {}
        if parser.has_section(section):
            params_list = parser.items(section)
            for param in params_list:
                params[param[0]] = param[1]
        else:
            raise Exception('There is an error in the ' + filename + " file")

        return params


    def __init__(self, filename="database.ini", section="postgresql"):
        try:
            params = config()
            self.conn = psycopg2.connect(**params)
            self.cur = self.conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            exit(0)
       

    def __del__(self):
        if self.conn is not None:
            self.conn.close()

    
    def write(self, table, data):
        if not len(data):
            return
        self.cur.execute("INSERT INTO " + table + " (" + ",".join(data[0].keys()) + ") VALUES (" + "),(".join([",".join(val.values()) for val in data]) + ");") 
        self.conn.commit()

    
    def query(self, sql):
        self.cur.execute(sql)
        rtn = self.cur.fetchall()
        self.cur.commit()
        return rtn



        

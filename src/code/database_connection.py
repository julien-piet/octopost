""" Manage postgresql database connection """

from configparser import ConfigParser
import psycopg2
import os


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


    def __init__(self, filename="cred/database.ini", section="postgresql"):
        try:
            self.params = database_connection.config(filename)
            self.conn = psycopg2.connect(**self.params)
            self.conn.set_session(autocommit=True)
            self.cur = self.conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            exit(0)


    def __del__(self):
        try:
            self.conn.close()
        except:
            pass
    

    def reset(self):
        print("Resetting database connection")
        self.cur.close()
        self.conn.close()
        self.conn = psycopg2.connect(**self.params)
        self.conn.set_session(autocommit=True)
        self.cur = self.conn.cursor()
        

    def write(self, table, data):
        if not len(data):
            return
        try:
            self.cur.execute("INSERT INTO " + table + " (" + ",".join(data[0].keys()) + ") VALUES (" + "),(".join([",".join(val.values()) for val in data]) + ");") 
        except Exception as e:
            self.reset()
            self.cur.execute("INSERT INTO " + table + " (" + ",".join(data[0].keys()) + ") VALUES (" + "),(".join([",".join(val.values()) for val in data]) + ");") 

    
    def query(self, sql, nofetch=False):
        self.cur.execute(sql)
        if nofetch:
            return
        else:
            rtn = self.cur.fetchall()
            return rtn


    def query_smart(self, sql):
        self.cur.execute(sql)
        colnames = [desc[0] for desc in self.cur.description]
        return [{colnames[i]: item[i] for i in range(len(colnames))} for item in self.cur.fetchall()]

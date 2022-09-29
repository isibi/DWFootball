import os
import pyodbc


class Conexion_BBDD:
    SERVER = os.environ.get('DB_SERVER')
    DATABASE = os.environ.get('DB_DATABASE')
    USERNAME = os.environ.get('DB_USERNAME')
    PASSWORD = os.environ.get('DB_PASSWORD')

    def __init__(self):
        self.__server = self.SERVER
        self.__database = self.DATABASE
        self.__username = self.USERNAME
        self.__password = self.PASSWORD

    def conexion(self):
        conexion = pyodbc.connect('Driver={SQL Server};'
                                  'Server=' + self.__server + ';'
                                  'Database=' + self.__database + ';'
                                  'Trusted_Connection=yes;'
                                  )

        return conexion

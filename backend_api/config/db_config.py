import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "crediinversion_creditocentecp",
    "port": 3306
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

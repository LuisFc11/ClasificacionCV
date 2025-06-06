import mysql.connector

def conectar_bd():
    return mysql.connector.connect(
        host="localhost:3300",
        user="root",
        password="110206",
        database="clasificacion_cv"
    )

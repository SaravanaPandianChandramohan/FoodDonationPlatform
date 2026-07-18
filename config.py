import pymysql

def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="food_donation",
        cursorclass=pymysql.cursors.DictCursor
    )
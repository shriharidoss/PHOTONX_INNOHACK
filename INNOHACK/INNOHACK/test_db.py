from db import get_db_connection

connection = get_db_connection()

if connection.is_connected():
    print("Database connected successfully!")

connection.close()
